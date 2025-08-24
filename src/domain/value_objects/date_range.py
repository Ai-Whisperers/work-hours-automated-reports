"""Date range value object."""

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Iterator, Optional


@dataclass(frozen=True)
class DateRange:
    """Represents a date range for reporting.
    
    Ensures that date ranges are valid and provides useful
    methods for working with date periods.
    """
    
    start: datetime
    end: datetime
    
    def __post_init__(self) -> None:
        """Validate date range after initialization."""
        if not isinstance(self.start, datetime):
            object.__setattr__(self, 'start', datetime.combine(self.start, datetime.min.time()))
        
        if not isinstance(self.end, datetime):
            object.__setattr__(self, 'end', datetime.combine(self.end, datetime.max.time()))
        
        if self.start > self.end:
            raise ValueError(f"Start date {self.start} must be before end date {self.end}")
        
        # Ensure timezone awareness
        if self.start.tzinfo is None:
            from datetime import timezone
            object.__setattr__(self, 'start', self.start.replace(tzinfo=timezone.utc))
        
        if self.end.tzinfo is None:
            from datetime import timezone
            object.__setattr__(self, 'end', self.end.replace(tzinfo=timezone.utc))
    
    @classmethod
    def from_dates(cls, start: date, end: date) -> "DateRange":
        """Create date range from date objects.
        
        Start date will be at 00:00:00, end date at 23:59:59.
        """
        return cls(
            datetime.combine(start, datetime.min.time()),
            datetime.combine(end, datetime.max.time())
        )
    
    @classmethod
    def last_n_days(cls, days: int, from_date: Optional[datetime] = None) -> "DateRange":
        """Create date range for the last N days.
        
        Args:
            days: Number of days to go back
            from_date: Reference date (default: today)
        """
        end = from_date or datetime.now()
        start = end - timedelta(days=days)
        return cls(start, end)
    
    @classmethod
    def current_week(cls, from_date: Optional[datetime] = None) -> "DateRange":
        """Create date range for the current week (Monday to Sunday)."""
        reference = from_date or datetime.now()
        start = reference - timedelta(days=reference.weekday())
        end = start + timedelta(days=6)
        return cls.from_dates(start.date(), end.date())
    
    @classmethod
    def current_month(cls, from_date: Optional[datetime] = None) -> "DateRange":
        """Create date range for the current month."""
        reference = from_date or datetime.now()
        start = reference.replace(day=1)
        
        # Find last day of month
        if reference.month == 12:
            end = reference.replace(year=reference.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = reference.replace(month=reference.month + 1, day=1) - timedelta(days=1)
        
        return cls.from_dates(start.date(), end.date())
    
    @property
    def days(self) -> int:
        """Get number of days in the range."""
        return (self.end.date() - self.start.date()).days + 1
    
    @property
    def duration(self) -> timedelta:
        """Get duration as timedelta."""
        return self.end - self.start
    
    def contains(self, dt: datetime) -> bool:
        """Check if a datetime is within this range."""
        return self.start <= dt <= self.end
    
    def overlaps(self, other: "DateRange") -> bool:
        """Check if this range overlaps with another."""
        return self.start <= other.end and other.start <= self.end
    
    def intersection(self, other: "DateRange") -> Optional["DateRange"]:
        """Get the intersection with another date range."""
        if not self.overlaps(other):
            return None
        
        return DateRange(
            max(self.start, other.start),
            min(self.end, other.end)
        )
    
    def iter_days(self) -> Iterator[date]:
        """Iterate over all days in the range."""
        current = self.start.date()
        end_date = self.end.date()
        
        while current <= end_date:
            yield current
            current += timedelta(days=1)
    
    def format_for_api(self) -> tuple[str, str]:
        """Format for API calls (ISO 8601)."""
        return (
            self.start.isoformat(),
            self.end.isoformat()
        )
    
    def format_for_display(self) -> str:
        """Format for user display."""
        if self.days == 1:
            return self.start.strftime("%Y-%m-%d")
        return f"{self.start.strftime('%Y-%m-%d')} to {self.end.strftime('%Y-%m-%d')}"
    
    def __str__(self) -> str:
        """String representation."""
        return self.format_for_display()
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"DateRange({self.start.isoformat()}, {self.end.isoformat()})"