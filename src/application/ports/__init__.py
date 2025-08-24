"""Application ports (interfaces).

Ports define how the application interacts with external services.
These are interfaces that will be implemented by infrastructure adapters.
"""

from .report_generator import ReportGenerator
from .cache_service import CacheService
from .notification_service import NotificationService
from .time_tracking_api import TimeTrackingAPI
from .work_item_api import WorkItemAPI

__all__ = [
    "ReportGenerator",
    "CacheService",
    "NotificationService",
    "TimeTrackingAPI",
    "WorkItemAPI",
]