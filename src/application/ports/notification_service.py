"""Notification service port."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any


class NotificationService(ABC):
    """Port for notification service.

    This interface abstracts notification functionality and can be
    implemented using different backends (email, Slack, Teams, etc.).
    """

    @abstractmethod
    async def send(
        self,
        subject: str,
        message: str,
        recipients: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a notification.

        Args:
            subject: Notification subject
            message: Notification message body
            recipients: List of recipients (emails, channels, etc.)
            attachments: Optional file attachments
            metadata: Additional metadata for the notification

        Returns:
            True if notification was sent successfully
        """
        pass

    @abstractmethod
    async def send_report_notification(
        self,
        report_path: Path,
        statistics: Dict[str, Any],
        recipients: Optional[List[str]] = None,
    ) -> bool:
        """Send a report generation notification.

        Args:
            report_path: Path to generated report
            statistics: Report statistics
            recipients: List of recipients

        Returns:
            True if notification was sent successfully
        """
        pass

    @abstractmethod
    async def send_error_notification(
        self,
        error: str,
        context: Optional[Dict[str, Any]] = None,
        recipients: Optional[List[str]] = None,
    ) -> bool:
        """Send an error notification.

        Args:
            error: Error message
            context: Error context information
            recipients: List of recipients

        Returns:
            True if notification was sent successfully
        """
        pass

    @abstractmethod
    def supports_attachments(self) -> bool:
        """Check if the notification service supports attachments.

        Returns:
            True if attachments are supported
        """
        pass

    @abstractmethod
    def get_max_attachment_size(self) -> int:
        """Get maximum attachment size in bytes.

        Returns:
            Maximum attachment size or -1 for unlimited
        """
        pass
