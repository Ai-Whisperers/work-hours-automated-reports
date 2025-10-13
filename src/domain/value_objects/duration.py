"""Duration value object."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Duration:
    """Represents a time duration in a domain-friendly way.
    
    Internally stores duration as seconds but provides convenient
    methods for working with hours, minutes, and timedelta objects.
    """
    
    _seconds: float
    
    def __post_init__(self) -> None:
        """Validate duration after initialization."""
        if self._seconds < 0:
            raise ValueError(f"Duration cannot be negative: {self._seconds} seconds")
    
    @classmethod
    def from_seconds(cls, seconds: float) -> "Duration":
        """Create duration from seconds."""
        return cls(seconds)
    
    @classmethod
    def from_minutes(cls, minutes: float) -> "Duration":
        """Create duration from minutes."""
        return cls(minutes * 60)
    
    @classmethod
    def from_hours(cls, hours: float) -> "Duration":
        """Create duration from hours."""
        return cls(hours * 3600)
    
    @classmethod
    def from_timedelta(cls, td: timedelta) -> "Duration":
        """Create duration from timedelta."""
        return cls(td.total_seconds())
    
    @classmethod
    def from_iso8601(cls, iso_duration: str) -> "Duration":
        """Create duration from ISO 8601 format (e.g., PT8H30M).
        
        Args:
            iso_duration: ISO 8601 duration string
            
        Returns:
            Duration instance
        """
        import re
        
        # Simple ISO 8601 duration parser for common formats
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?'
        match = re.match(pattern, iso_duration)
        
        if not match:
            raise ValueError(f"Invalid ISO 8601 duration: {iso_duration}")
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = float(match.group(3) or 0)
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return cls(total_seconds)
    
    @property
    def seconds(self) -> float:
        """Get duration in seconds."""
        return self._seconds
    
    @property
    def minutes(self) -> float:
        """Get duration in minutes."""
        return self._seconds / 60
    
    @property
    def hours(self) -> float:
        """Get duration in hours."""
        return self._seconds / 3600
    
    def to_timedelta(self) -> timedelta:
        """Convert to timedelta."""
        return timedelta(seconds=self._seconds)
    
    def format_human_readable(self) -> str:
        """Format duration in human-readable format (e.g., '2h 30m')."""
        hours = int(self._seconds // 3600)
        minutes = int((self._seconds % 3600) // 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours == 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "0m"
    
    def __add__(self, other: "Duration") -> "Duration":
        """Add two durations."""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot add Duration and {type(other)}")
        return Duration(self._seconds + other._seconds)
    
    def __sub__(self, other: "Duration") -> "Duration":
        """Subtract two durations."""
        if not isinstance(other, Duration):
            raise TypeError(f"Cannot subtract {type(other)} from Duration")
        result = self._seconds - other._seconds
        if result < 0:
            raise ValueError("Subtraction would result in negative duration")
        return Duration(result)
    
    def __str__(self) -> str:
        """String representation."""
        return self.format_human_readable()
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"Duration({self._seconds} seconds)"