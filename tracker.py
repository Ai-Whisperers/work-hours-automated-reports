#!/usr/bin/env python3
"""
Clockify Activity and Commit Tracker

This script monitors user activity and GitHub commits, automatically
managing Clockify time entries.

Usage:
    python tracker.py

Requirements:
    - .env file with configuration (see .env.example)
    - Clockify API key and workspace ID
    - Optional: GitHub username and token for commit tracking
    - Optional: pynput for activity tracking

Configuration:
    Set the following environment variables in your .env file:
    - ENABLE_ACTIVITY_TRACKER: Enable/disable activity tracking
    - ENABLE_GITHUB_TRACKER: Enable/disable GitHub commit tracking
    - See docs/activity-tracker.md for full configuration options
"""

import time
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from src.infrastructure.config import get_settings
from src.application.services.activity_tracker import ActivityTrackerService
from src.application.services.github_commit_tracker import GitHubCommitTrackerService


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║         Clockify Activity & Commit Tracker                   ║
║         Automatic time tracking for your workflow            ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_requirements():
    """Check if required packages are installed."""
    issues = []

    # Check for activity tracker requirements
    if os.getenv("ENABLE_ACTIVITY_TRACKER", "false").lower() == "true":
        try:
            import pynput
        except ImportError:
            issues.append("pynput is not installed. Install with: pip install pynput")

    # Check for GitHub tracker requirements
    if os.getenv("ENABLE_GITHUB_TRACKER", "false").lower() == "true":
        try:
            import requests
        except ImportError:
            issues.append("requests is not installed. Install with: pip install requests")

    return issues


def main():
    """Main application entry point."""
    print_banner()

    # Load environment variables
    print("Loading configuration...")
    load_dotenv()

    # Check requirements
    issues = check_requirements()
    if issues:
        print("\n⚠ Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease resolve these issues and try again.")
        return 1

    # Get settings
    try:
        settings = get_settings()
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        print("Ensure your .env file is configured correctly.")
        return 1

    # Initialize Clockify client
    print("Connecting to Clockify...")
    try:
        clockify_client = ClockifySyncAdapter(settings)

        # Test connection
        if not clockify_client.test_connection():
            print("❌ Failed to connect to Clockify.")
            print("Please check your CLOCKIFY_API_KEY and CLOCKIFY_WORKSPACE_ID")
            return 1

        user_info = clockify_client.get_current_user()
        print(f"✓ Connected as: {user_info.get('name', 'Unknown')}")

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return 1

    # Initialize trackers
    trackers = []

    # Activity Tracker
    if os.getenv("ENABLE_ACTIVITY_TRACKER", "false").lower() == "true":
        try:
            print("\nInitializing Activity Tracker...")
            activity_tracker = ActivityTrackerService(
                clockify_client=clockify_client,
                settings=settings,
                inactivity_limit=int(os.getenv("ACTIVITY_TRACKER_INACTIVITY_LIMIT", "300")),
                check_interval=int(os.getenv("ACTIVITY_TRACKER_CHECK_INTERVAL", "5"))
            )
            activity_tracker.start_monitoring()
            trackers.append(("Activity Tracker", activity_tracker))
            print(f"✓ Activity Tracker started (inactivity limit: {os.getenv('ACTIVITY_TRACKER_INACTIVITY_LIMIT', '300')}s)")
        except Exception as e:
            print(f"❌ Failed to start Activity Tracker: {e}")
    else:
        print("\n⊘ Activity Tracker disabled (set ENABLE_ACTIVITY_TRACKER=true to enable)")

    # GitHub Commit Tracker
    if os.getenv("ENABLE_GITHUB_TRACKER", "false").lower() == "true":
        tracker_mode = os.getenv("COMMIT_TRACKER_MODE", "user").lower()
        github_username = os.getenv("COMMIT_TRACKER_USERNAME")
        github_org = os.getenv("COMMIT_TRACKER_ORG")

        # Validate configuration based on mode
        if tracker_mode == "org" and not github_org:
            print("\n⚠ COMMIT_TRACKER_ORG not configured for org mode, skipping GitHub tracker")
        elif tracker_mode == "user" and not github_username:
            print("\n⚠ COMMIT_TRACKER_USERNAME not configured for user mode, skipping GitHub tracker")
        else:
            try:
                print(f"\nInitializing GitHub Commit Tracker (mode: {tracker_mode})...")

                # Get worked hours configuration
                use_worked_hours = os.getenv("COMMIT_TRACKER_USE_WORKED_HOURS", "true").lower() == "true"
                timezone = os.getenv("COMMIT_TRACKER_TIMEZONE", "America/Asuncion")

                github_tracker = GitHubCommitTrackerService(
                    clockify_client=clockify_client,
                    settings=settings,
                    github_username=github_username if tracker_mode == "user" else None,
                    github_org=github_org if tracker_mode == "org" else None,
                    github_token=os.getenv("COMMIT_TRACKER_TOKEN"),
                    poll_interval=int(os.getenv("COMMIT_TRACKER_POLL_INTERVAL", "60")),
                    timezone=timezone,
                    use_worked_hours=use_worked_hours
                )
                github_tracker.start_tracking()
                trackers.append(("GitHub Tracker", github_tracker))

                token_status = "with token" if os.getenv("COMMIT_TRACKER_TOKEN") else "without token"
                target = github_org if tracker_mode == "org" else github_username
                mode_desc = "cluster-based hours" if use_worked_hours else "individual commits"
                print(f"✓ GitHub Tracker started for {tracker_mode} '{target}' ({token_status}, {mode_desc})")
            except Exception as e:
                print(f"❌ Failed to start GitHub Tracker: {e}")
    else:
        print("⊘ GitHub Tracker disabled (set ENABLE_GITHUB_TRACKER=true to enable)")

    # Check if any trackers are running
    if not trackers:
        print("\n❌ No trackers enabled!")
        print("\nTo enable trackers, set these in your .env file:")
        print("  ENABLE_ACTIVITY_TRACKER=true")
        print("  ENABLE_GITHUB_TRACKER=true")
        print("  COMMIT_TRACKER_MODE=user  # or 'org' for organization")
        print("  COMMIT_TRACKER_USERNAME=your_username  # for user mode")
        print("  COMMIT_TRACKER_ORG=your_organization  # for org mode")
        print("\nSee docs/activity-tracker.md for more information.")
        return 1

    # Show status
    print("\n" + "="*60)
    print("Status: Running")
    print("="*60)
    print("Active trackers:")
    for name, tracker in trackers:
        status = "✓ Running"
        if hasattr(tracker, 'is_running'):
            status = "✓ Running" if tracker.is_running else "⊘ Stopped"
        print(f"  • {name}: {status}")

    print("\nPress Ctrl+C to stop all trackers")
    print("="*60 + "\n")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        print("="*60)

        # Stop all trackers
        for name, tracker in trackers:
            try:
                if hasattr(tracker, 'stop_monitoring'):
                    tracker.stop_monitoring()
                elif hasattr(tracker, 'stop_tracking'):
                    tracker.stop_tracking()
                print(f"✓ {name} stopped")
            except Exception as e:
                print(f"⚠ Error stopping {name}: {e}")

        print("="*60)
        print("All trackers stopped. Goodbye!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
