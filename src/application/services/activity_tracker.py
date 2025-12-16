"""
Activity Tracker Service for Clockify

This service monitors user activity (mouse and keyboard) and automatically
manages Clockify time entries based on activity status.
"""

import time
import threading
from typing import Optional, Callable

from ...infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from ...infrastructure.config.settings import Settings


class ActivityTrackerService:
    """
    Service that monitors user activity and manages Clockify time entries.

    Features:
    - Detects mouse and keyboard activity
    - Auto-starts Clockify timer when activity is detected
    - Auto-stops timer after inactivity period
    - Thread-safe operation
    """

    def __init__(
        self,
        clockify_client: ClockifySyncAdapter,
        settings: Settings,
        inactivity_limit: int = 300,  # 5 minutes default
        check_interval: int = 5,  # Check every 5 seconds
        on_activity_callback: Optional[Callable] = None,
        on_inactivity_callback: Optional[Callable] = None,
    ):
        """
        Initialize the activity tracker.

        Args:
            clockify_client: Clockify sync adapter instance
            settings: Application settings
            inactivity_limit: Seconds of inactivity before stopping timer
            check_interval: Seconds between activity checks
            on_activity_callback: Optional callback when activity is detected
            on_inactivity_callback: Optional callback when inactivity is detected
        """
        self.clockify_client = clockify_client
        self.settings = settings
        self.inactivity_limit = inactivity_limit
        self.check_interval = check_interval
        self.on_activity_callback = on_activity_callback
        self.on_inactivity_callback = on_inactivity_callback

        self._last_activity: float = time.time()
        self._timer_running: bool = False
        self._current_entry_id: Optional[str] = None
        self._running: bool = False
        self._lock = threading.Lock()
        self._listeners_started: bool = False

    def on_activity(self, *args, **kwargs) -> None:
        """
        Callback for activity events.
        Updates the last activity timestamp.
        """
        with self._lock:
            self._last_activity = time.time()
            if self.on_activity_callback:
                self.on_activity_callback()

    def _is_active(self) -> bool:
        """Check if there has been recent activity."""
        with self._lock:
            return (time.time() - self._last_activity) < self.inactivity_limit

    def _start_timer(self, description: str = "Active work (auto)") -> None:
        """
        Start a Clockify time entry.

        Args:
            description: Description for the time entry
        """
        with self._lock:
            if self._timer_running:
                return

            try:
                # Start time entry using clockify client
                response = self.clockify_client.start_time_entry(
                    description=description,
                    project_id=self.settings.get("CLOCKIFY_DEFAULT_PROJECT_ID"),
                )

                if response and "id" in response:
                    self._current_entry_id = response["id"]
                    self._timer_running = True
                    print(
                        f"[ActivityTracker] Timer started: {description} | id={self._current_entry_id}"
                    )
                else:
                    print(
                        "[ActivityTracker] Failed to start timer - no entry ID returned"
                    )

            except Exception as e:
                print(f"[ActivityTracker] Error starting timer: {e}")

    def _stop_timer(self) -> None:
        """Stop the current Clockify time entry."""
        with self._lock:
            if not self._timer_running or not self._current_entry_id:
                return

            try:
                # Stop time entry using clockify client
                response = self.clockify_client.stop_time_entry(self._current_entry_id)

                if response:
                    print(
                        f"[ActivityTracker] Timer stopped: id={self._current_entry_id}"
                    )
                    if self.on_inactivity_callback:
                        self.on_inactivity_callback()
                else:
                    print("[ActivityTracker] Failed to stop timer")

            except Exception as e:
                print(f"[ActivityTracker] Error stopping timer: {e}")
            finally:
                self._timer_running = False
                self._current_entry_id = None

    def _monitor_loop(self) -> None:
        """Main monitoring loop that checks activity and manages timers."""
        print("[ActivityTracker] Monitoring started...")

        while self._running:
            try:
                is_active = self._is_active()

                if is_active and not self._timer_running:
                    # Activity detected and timer not running - start it
                    self._start_timer("Active work (auto)")
                elif not is_active and self._timer_running:
                    # No activity and timer is running - stop it
                    self._stop_timer()

                time.sleep(self.check_interval)

            except Exception as e:
                print(f"[ActivityTracker] Error in monitor loop: {e}")
                time.sleep(self.check_interval)

    def start_monitoring(self) -> None:
        """
        Start monitoring user activity.
        This will launch activity listeners and the monitoring loop.
        """
        if self._running:
            print("[ActivityTracker] Already running")
            return

        self._running = True

        # Start activity listeners if not already started
        if not self._listeners_started:
            self._start_listeners()
            self._listeners_started = True

        # Start monitoring loop in a separate thread
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()

        print("[ActivityTracker] Activity monitoring initialized")

    def stop_monitoring(self) -> None:
        """Stop monitoring and clean up."""
        print("[ActivityTracker] Stopping monitoring...")
        self._running = False

        # Stop current timer if running
        if self._timer_running:
            self._stop_timer()

    def _start_listeners(self) -> None:
        """
        Start mouse and keyboard listeners.
        Implemented as a separate method for easier testing/mocking.
        """
        try:
            from pynput import mouse, keyboard

            # Start mouse listener
            mouse_listener = mouse.Listener(
                on_move=self.on_activity,
                on_click=self.on_activity,
            )
            mouse_listener.daemon = True
            mouse_listener.start()

            # Start keyboard listener
            keyboard_listener = keyboard.Listener(
                on_press=self.on_activity,
            )
            keyboard_listener.daemon = True
            keyboard_listener.start()

            print("[ActivityTracker] Input listeners started")

        except ImportError:
            print(
                "[ActivityTracker] Warning: pynput not installed. Activity detection disabled."
            )
            print("[ActivityTracker] Install with: pip install pynput")
        except Exception as e:
            print(f"[ActivityTracker] Error starting listeners: {e}")

    @property
    def is_running(self) -> bool:
        """Check if monitoring is active."""
        return self._running

    @property
    def is_timer_active(self) -> bool:
        """Check if Clockify timer is currently running."""
        with self._lock:
            return self._timer_running
