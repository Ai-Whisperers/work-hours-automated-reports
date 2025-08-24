"""Use case for generating reports."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from ...domain.entities import TimeEntry, WorkItem
from ...domain.value_objects import DateRange
from ...domain.services import MatchingService
from ...domain.repositories import TimeEntryRepository, WorkItemRepository
from ..ports import ReportGenerator, CacheService, NotificationService
from ..dto import ReportRequest, ReportResponse


class ReportFormat(Enum):
    """Supported report formats."""
    
    EXCEL = "excel"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


@dataclass
class GenerateReportRequest:
    """Request for generating a report."""
    
    date_range: DateRange
    format: ReportFormat
    output_path: Optional[Path] = None
    user_ids: Optional[List[str]] = None
    project_ids: Optional[List[str]] = None
    include_unmatched: bool = True
    group_by: Optional[List[str]] = None
    
    def validate(self) -> None:
        """Validate the request."""
        if self.date_range.days > 365:
            raise ValueError("Date range cannot exceed 365 days")
        
        if self.group_by:
            valid_groups = ["user", "work_item", "project", "date", "iteration"]
            for group in self.group_by:
                if group not in valid_groups:
                    raise ValueError(f"Invalid group by option: {group}")


@dataclass
class GenerateReportResponse:
    """Response from report generation."""
    
    success: bool
    report_path: Optional[Path]
    total_entries: int
    matched_entries: int
    unmatched_entries: int
    total_hours: float
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class GenerateReportUseCase:
    """Use case for generating time tracking reports.
    
    This use case orchestrates the entire report generation process,
    coordinating between repositories, domain services, and ports.
    """
    
    def __init__(
        self,
        time_entry_repo: TimeEntryRepository,
        work_item_repo: WorkItemRepository,
        matching_service: MatchingService,
        report_generator: ReportGenerator,
        cache_service: Optional[CacheService] = None,
        notification_service: Optional[NotificationService] = None
    ):
        """Initialize the use case with dependencies.
        
        Args:
            time_entry_repo: Repository for time entries
            work_item_repo: Repository for work items
            matching_service: Service for matching entries to work items
            report_generator: Port for generating reports
            cache_service: Optional caching service
            notification_service: Optional notification service
        """
        self.time_entry_repo = time_entry_repo
        self.work_item_repo = work_item_repo
        self.matching_service = matching_service
        self.report_generator = report_generator
        self.cache_service = cache_service
        self.notification_service = notification_service
    
    async def execute(
        self,
        request: GenerateReportRequest
    ) -> GenerateReportResponse:
        """Execute the report generation use case.
        
        Args:
            request: The report generation request
            
        Returns:
            Report generation response
        """
        errors = []
        warnings = []
        
        try:
            # Validate request
            request.validate()
            
            # Step 1: Fetch time entries
            time_entries = await self._fetch_time_entries(request)
            
            if not time_entries:
                warnings.append("No time entries found for the specified criteria")
                return GenerateReportResponse(
                    success=True,
                    report_path=None,
                    total_entries=0,
                    matched_entries=0,
                    unmatched_entries=0,
                    total_hours=0.0,
                    errors=errors,
                    warnings=warnings,
                    metadata={}
                )
            
            # Step 2: Extract work item IDs
            work_item_ids = self._extract_work_item_ids(time_entries)
            
            # Step 3: Fetch work items
            work_items = await self._fetch_work_items(work_item_ids)
            
            # Step 4: Match entries to work items
            matching_results = self.matching_service.match_time_entries_to_work_items(
                time_entries,
                {int(wi.id): wi for wi in work_items}
            )
            
            # Step 5: Calculate statistics
            stats = self.matching_service.get_match_statistics(matching_results)
            
            # Add warnings for low match rate
            if stats["match_rate"] < 0.5:
                warnings.append(
                    f"Low match rate: only {stats['match_rate']:.1%} of entries matched to work items"
                )
            
            # Step 6: Generate report
            report_data = self._prepare_report_data(
                matching_results,
                request.include_unmatched
            )
            
            report_path = await self.report_generator.generate(
                data=report_data,
                format=request.format.value,
                output_path=request.output_path,
                options={
                    "group_by": request.group_by,
                    "date_range": request.date_range.format_for_display(),
                    "stats": stats
                }
            )
            
            # Step 7: Send notifications if configured
            if self.notification_service:
                await self._send_notifications(report_path, stats)
            
            # Calculate total hours
            total_hours = sum(
                entry.duration.hours for entry in time_entries
            )
            
            return GenerateReportResponse(
                success=True,
                report_path=report_path,
                total_entries=len(time_entries),
                matched_entries=stats["matched_entries"],
                unmatched_entries=stats["unmatched_entries"],
                total_hours=total_hours,
                errors=errors,
                warnings=warnings,
                metadata={
                    "date_range": request.date_range.format_for_display(),
                    "format": request.format.value,
                    "statistics": stats,
                    "generation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            errors.append(str(e))
            return GenerateReportResponse(
                success=False,
                report_path=None,
                total_entries=0,
                matched_entries=0,
                unmatched_entries=0,
                total_hours=0.0,
                errors=errors,
                warnings=warnings,
                metadata={}
            )
    
    async def _fetch_time_entries(
        self,
        request: GenerateReportRequest
    ) -> List[TimeEntry]:
        """Fetch time entries based on request criteria.
        
        Args:
            request: The report generation request
            
        Returns:
            List of time entries
        """
        # Check cache first if available
        cache_key = f"time_entries_{request.date_range}_{request.user_ids}_{request.project_ids}"
        
        if self.cache_service:
            cached = await self.cache_service.get(cache_key)
            if cached:
                return cached
        
        # Fetch from repository
        entries = []
        
        if request.user_ids:
            # Fetch for specific users
            for user_id in request.user_ids:
                user_entries = await self.time_entry_repo.get_by_user(
                    user_id,
                    request.date_range
                )
                entries.extend(user_entries)
        elif request.project_ids:
            # Fetch for specific projects
            for project_id in request.project_ids:
                project_entries = await self.time_entry_repo.get_by_project(
                    project_id,
                    request.date_range
                )
                entries.extend(project_entries)
        else:
            # Fetch all entries in date range
            entries = await self.time_entry_repo.get_by_date_range(
                request.date_range
            )
        
        # Cache the results
        if self.cache_service and entries:
            await self.cache_service.set(cache_key, entries, ttl=3600)
        
        return entries
    
    def _extract_work_item_ids(self, time_entries: List[TimeEntry]) -> set[int]:
        """Extract all work item IDs from time entries.
        
        Args:
            time_entries: List of time entries
            
        Returns:
            Set of work item IDs
        """
        all_ids = set()
        
        for entry in time_entries:
            if entry.description:
                ids, _ = self.matching_service.extract_work_item_ids(
                    entry.description
                )
                all_ids.update(ids)
        
        return all_ids
    
    async def _fetch_work_items(self, work_item_ids: set[int]) -> List[WorkItem]:
        """Fetch work items by IDs.
        
        Args:
            work_item_ids: Set of work item IDs
            
        Returns:
            List of work items
        """
        if not work_item_ids:
            return []
        
        # Check cache first
        cache_key = f"work_items_{sorted(work_item_ids)}"
        
        if self.cache_service:
            cached = await self.cache_service.get(cache_key)
            if cached:
                return cached
        
        # Convert to WorkItemId value objects
        from ...domain.value_objects import WorkItemId
        work_item_id_objects = {
            WorkItemId(wi_id) for wi_id in work_item_ids
        }
        
        # Fetch from repository
        work_items = await self.work_item_repo.get_by_ids(work_item_id_objects)
        
        # Cache the results
        if self.cache_service and work_items:
            await self.cache_service.set(cache_key, work_items, ttl=7200)
        
        return work_items
    
    def _prepare_report_data(
        self,
        matching_results,
        include_unmatched: bool
    ) -> Dict[str, Any]:
        """Prepare data for report generation.
        
        Args:
            matching_results: Results from matching service
            include_unmatched: Whether to include unmatched entries
            
        Returns:
            Dictionary with report data
        """
        matched_data = []
        unmatched_data = []
        
        for result in matching_results:
            entry_dict = result.time_entry.to_dict()
            
            if result.is_matched:
                # Add work item information
                for work_item in result.matched_work_items:
                    matched_entry = {
                        **entry_dict,
                        "work_item_id": int(work_item.id),
                        "work_item_title": work_item.title,
                        "work_item_type": work_item.work_item_type.value,
                        "work_item_state": work_item.state.value,
                        "work_item_assigned_to": work_item.assigned_to,
                        "iteration": work_item.get_iteration(),
                        "area": work_item.get_area(),
                        "confidence": result.confidence,
                        "match_strategy": result.strategy_used
                    }
                    matched_data.append(matched_entry)
            else:
                unmatched_entry = {
                    **entry_dict,
                    "work_item_id": None,
                    "work_item_title": "Unmatched",
                    "work_item_type": None,
                    "work_item_state": None,
                    "confidence": 0.0,
                    "match_strategy": "none"
                }
                unmatched_data.append(unmatched_entry)
        
        report_data = {
            "matched_entries": matched_data,
            "unmatched_entries": unmatched_data if include_unmatched else [],
            "total_entries": len(matching_results),
            "match_count": len(matched_data),
            "unmatch_count": len(unmatched_data)
        }
        
        return report_data
    
    async def _send_notifications(
        self,
        report_path: Path,
        stats: Dict[str, Any]
    ) -> None:
        """Send notifications about report generation.
        
        Args:
            report_path: Path to generated report
            stats: Statistics about the report
        """
        if not self.notification_service:
            return
        
        message = f"""
        Report Generated Successfully
        
        Path: {report_path}
        Total Entries: {stats['total_entries']}
        Matched: {stats['matched_entries']} ({stats['match_rate']:.1%})
        Average Confidence: {stats['average_confidence']:.1%}
        """
        
        await self.notification_service.send(
            subject="Time Tracking Report Generated",
            message=message,
            attachments=[report_path] if report_path else []
        )