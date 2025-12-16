"""Work Item ID value object."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WorkItemId:
    """Represents a work item identifier from Azure DevOps.

    This value object ensures that work item IDs are valid and
    provides a consistent way to handle them throughout the domain.
    """

    value: int

    def __post_init__(self) -> None:
        """Validate the work item ID after initialization."""
        if not isinstance(self.value, int):
            raise TypeError(f"Work item ID must be an integer, got {type(self.value)}")

        if self.value < 1:
            raise ValueError(f"Work item ID must be positive, got {self.value}")

        if self.value > 999999:
            raise ValueError(f"Work item ID seems invalid (too large): {self.value}")

    def __str__(self) -> str:
        """String representation of the work item ID."""
        return str(self.value)

    def __int__(self) -> int:
        """Integer representation of the work item ID."""
        return self.value

    @classmethod
    def from_string(cls, value: str) -> Optional["WorkItemId"]:
        """Create a WorkItemId from a string, if valid.

        Args:
            value: String that might contain a work item ID

        Returns:
            WorkItemId instance or None if invalid
        """
        try:
            return cls(int(value))
        except (ValueError, TypeError):
            return None

    def format_for_ado(self) -> str:
        """Format the ID for Azure DevOps API calls."""
        return str(self.value)

    def format_for_display(self) -> str:
        """Format the ID for user display."""
        return f"#{self.value}"
