"""Domain service for matching time entries to work items."""

import re
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..entities import TimeEntry, WorkItem


class MatchingStrategy(Enum):
    """Matching strategies for work item extraction."""

    STRICT = "strict"  # Only explicit patterns
    FUZZY = "fuzzy"  # Include fuzzy matching
    HYBRID = "hybrid"  # Strict first, then fuzzy for unmatched


@dataclass
class MatchingPattern:
    """Represents a pattern for extracting work item IDs."""

    name: str
    pattern: str
    priority: int
    requires_validation: bool = False

    def extract(self, text: str) -> List[int]:
        """Extract work item IDs using this pattern.

        Args:
            text: Text to search in

        Returns:
            List of extracted work item IDs
        """
        matches = re.findall(self.pattern, text, re.IGNORECASE)
        ids = []

        for match in matches:
            try:
                work_item_id = int(match)
                # Validate ID range
                if 1 <= work_item_id <= 999999:
                    ids.append(work_item_id)
            except (ValueError, TypeError):
                continue

        return ids


@dataclass
class MatchingResult:
    """Result of matching a time entry to work items."""

    time_entry: TimeEntry
    matched_work_items: List[WorkItem]
    confidence: float
    strategy_used: str

    @property
    def is_matched(self) -> bool:
        """Check if any work items were matched."""
        return len(self.matched_work_items) > 0

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence match."""
        return self.confidence >= 0.8


class MatchingService:
    """Service for matching time entries to work items.

    This domain service encapsulates the complex business logic
    for extracting work item references from time entry descriptions
    and matching them to actual work items.
    """

    # Default patterns in priority order
    DEFAULT_PATTERNS = [
        MatchingPattern("hash", r"#(\d{4,6})", 1),
        MatchingPattern("ado_dash", r"ADO-(\d{4,6})", 2),
        MatchingPattern("ado_underscore", r"ADO_(\d{4,6})", 2),
        MatchingPattern("wi_colon", r"WI:(\d{4,6})", 3),
        MatchingPattern("wi_underscore", r"WI_(\d{4,6})", 3),
        MatchingPattern("brackets", r"\[(\d{4,6})\]", 4),
        MatchingPattern("parentheses", r"\((\d{4,6})\)", 5),
        MatchingPattern("plain_number", r"\b(\d{4,6})\b", 10, requires_validation=True),
    ]

    def __init__(
        self,
        patterns: Optional[List[MatchingPattern]] = None,
        strategy: MatchingStrategy = MatchingStrategy.HYBRID,
    ):
        """Initialize the matching service.

        Args:
            patterns: Custom patterns to use (defaults to DEFAULT_PATTERNS)
            strategy: Matching strategy to use
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS
        self.strategy = strategy
        # Sort patterns by priority
        self.patterns.sort(key=lambda p: p.priority)

    def extract_work_item_ids(self, text: str) -> Tuple[Set[int], float]:
        """Extract work item IDs from text.

        Args:
            text: Text to extract IDs from

        Returns:
            Tuple of (set of work item IDs, confidence score)
        """
        if not text:
            return set(), 0.0

        all_ids = set()
        confidence = 0.0
        patterns_matched = 0

        for pattern in self.patterns:
            ids = pattern.extract(text)

            if ids:
                all_ids.update(ids)
                patterns_matched += 1

                # Higher confidence for explicit patterns
                if not pattern.requires_validation:
                    confidence = max(confidence, 1.0 - (pattern.priority * 0.1))
                else:
                    confidence = max(confidence, 0.5)

        # Adjust confidence based on number of patterns matched
        if patterns_matched > 1:
            confidence = min(1.0, confidence + 0.1)

        return all_ids, confidence

    def match_time_entries_to_work_items(
        self, time_entries: List[TimeEntry], work_items: Dict[int, WorkItem]
    ) -> List[MatchingResult]:
        """Match time entries to work items.

        Args:
            time_entries: List of time entries to match
            work_items: Dictionary of work items by ID

        Returns:
            List of matching results
        """
        results = []

        for entry in time_entries:
            # Extract work item IDs from description
            extracted_ids, confidence = self.extract_work_item_ids(
                entry.description or ""
            )

            # Find matching work items
            matched_items = []
            for work_item_id in extracted_ids:
                if work_item_id in work_items:
                    matched_items.append(work_items[work_item_id])

            # If no matches found and using hybrid/fuzzy strategy
            if not matched_items and self.strategy in [
                MatchingStrategy.FUZZY,
                MatchingStrategy.HYBRID,
            ]:
                fuzzy_match = self._fuzzy_match_work_item(entry, work_items)
                if fuzzy_match:
                    matched_items.append(fuzzy_match)
                    confidence = 0.6  # Lower confidence for fuzzy matches

            # Update the time entry with extracted IDs
            entry.set_extracted_work_items(
                [int(item.id) for item in matched_items], confidence
            )

            # Create result
            result = MatchingResult(
                time_entry=entry,
                matched_work_items=matched_items,
                confidence=confidence,
                strategy_used="strict" if confidence > 0.7 else "fuzzy",
            )

            results.append(result)

        return results

    def _fuzzy_match_work_item(
        self, entry: TimeEntry, work_items: Dict[int, WorkItem]
    ) -> Optional[WorkItem]:
        """Attempt fuzzy matching between entry description and work item titles.

        Args:
            entry: Time entry to match
            work_items: Dictionary of work items

        Returns:
            Best matching work item or None
        """
        if not entry.description:
            return None

        from difflib import SequenceMatcher

        description_lower = entry.description.lower()
        best_match = None
        best_score = 0.0
        threshold = 0.7

        for work_item in work_items.values():
            # Skip closed items for fuzzy matching
            if work_item.is_completed:
                continue

            title_lower = work_item.title.lower()

            # Calculate similarity
            score = SequenceMatcher(None, description_lower, title_lower).ratio()

            # Check for partial matches (work item title in description)
            if title_lower in description_lower or description_lower in title_lower:
                score = max(score, 0.8)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = work_item

        return best_match

    def validate_matches(
        self, results: List[MatchingResult]
    ) -> Tuple[List[MatchingResult], List[MatchingResult]]:
        """Validate matching results and separate high/low confidence matches.

        Args:
            results: List of matching results

        Returns:
            Tuple of (high confidence results, low confidence results)
        """
        high_confidence = []
        low_confidence = []

        for result in results:
            if result.is_high_confidence:
                high_confidence.append(result)
            else:
                low_confidence.append(result)

        return high_confidence, low_confidence

    def get_unmatched_entries(self, results: List[MatchingResult]) -> List[TimeEntry]:
        """Get time entries that weren't matched to any work items.

        Args:
            results: List of matching results

        Returns:
            List of unmatched time entries
        """
        return [result.time_entry for result in results if not result.is_matched]

    def get_match_statistics(self, results: List[MatchingResult]) -> Dict[str, any]:
        """Calculate statistics about matching results.

        Args:
            results: List of matching results

        Returns:
            Dictionary with statistics
        """
        total = len(results)
        matched = sum(1 for r in results if r.is_matched)
        high_confidence = sum(1 for r in results if r.is_high_confidence)

        strategies_used = {}
        for result in results:
            strategy = result.strategy_used
            strategies_used[strategy] = strategies_used.get(strategy, 0) + 1

        return {
            "total_entries": total,
            "matched_entries": matched,
            "unmatched_entries": total - matched,
            "match_rate": matched / total if total > 0 else 0,
            "high_confidence_matches": high_confidence,
            "high_confidence_rate": high_confidence / total if total > 0 else 0,
            "strategies_used": strategies_used,
            "average_confidence": (
                sum(r.confidence for r in results) / total if total > 0 else 0
            ),
        }
