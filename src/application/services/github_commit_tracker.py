"""
GitHub Commit Tracker Service

This service polls GitHub for user commits and automatically creates
Clockify time entries for each detected commit.
"""

import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Optional, Set, Dict, Any
from pathlib import Path

import requests

from ...infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from ...infrastructure.config.settings import Settings


class GitHubCommitTrackerService:
    """
    Service that monitors GitHub commits and creates Clockify entries.

    Features:
    - Polls GitHub user events API for new commits
    - Creates time entries for each new commit
    - Prevents duplicate entries using persistent state
    - Configurable polling interval and commit duration
    """

    STATE_FILE = "clockify_github_state.json"

    def __init__(
        self,
        clockify_client: ClockifySyncAdapter,
        settings: Settings,
        github_username: Optional[str] = None,
        github_org: Optional[str] = None,
        github_token: Optional[str] = None,
        poll_interval: int = 60,  # Poll every 60 seconds
        commit_duration_minutes: int = 10,  # Assume 10 minutes per commit
        state_file_path: Optional[str] = None,
    ):
        """
        Initialize the GitHub commit tracker.

        Args:
            clockify_client: Clockify sync adapter instance
            settings: Application settings
            github_username: GitHub username to monitor (for user mode)
            github_org: GitHub organization to monitor (for org mode)
            github_token: Optional GitHub personal access token (recommended for rate limits)
            poll_interval: Seconds between GitHub API polls
            commit_duration_minutes: Duration to assign to each commit entry
            state_file_path: Optional custom path for state file
        """
        self.clockify_client = clockify_client
        self.settings = settings
        self.github_username = github_username
        self.github_org = github_org
        self.github_token = github_token
        self.poll_interval = poll_interval
        self.commit_duration = timedelta(minutes=commit_duration_minutes)

        # Determine tracking mode
        if not github_username and not github_org:
            raise ValueError("Either github_username or github_org must be provided")

        self.tracking_mode = "org" if github_org else "user"
        self.tracking_target = github_org if github_org else github_username

        # State management
        self.state_file = state_file_path or self.STATE_FILE
        self.seen_commits: Set[str] = set()
        self._running: bool = False
        self._lock = threading.Lock()

        # Load existing state
        self._load_state()

    def _load_state(self) -> None:
        """Load seen commits from state file."""
        if not os.path.exists(self.state_file):
            return

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                self.seen_commits = set(data.get("seen_commits", []))
                print(f"[GitHubTracker] Loaded {len(self.seen_commits)} previously seen commits")
        except Exception as e:
            print(f"[GitHubTracker] Error loading state: {e}")
            self.seen_commits = set()

    def _save_state(self) -> None:
        """Save seen commits to state file."""
        try:
            # Ensure directory exists
            state_path = Path(self.state_file)
            state_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, "w") as f:
                json.dump({"seen_commits": list(self.seen_commits)}, f, indent=2)
        except Exception as e:
            print(f"[GitHubTracker] Error saving state: {e}")

    def _create_commit_entry(
        self,
        sha: str,
        message: str,
        repo: str,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Create a Clockify time entry for a commit.

        Args:
            sha: Commit SHA
            message: Commit message
            repo: Repository name
            timestamp: Optional commit timestamp (defaults to now)

        Returns:
            True if entry was created successfully
        """
        try:
            # Calculate time range
            start_time = timestamp or datetime.utcnow()
            end_time = start_time + self.commit_duration

            # Format description
            description = f"Commit {sha[:7]} @ {repo}: {message[:100]}"

            # Create time entry
            response = self.clockify_client.create_time_entry_with_range(
                start=start_time,
                end=end_time,
                description=description,
                project_id=self.settings.get("CLOCKIFY_DEFAULT_PROJECT_ID"),
            )

            if response and "id" in response:
                print(f"[GitHubTracker] Created entry for commit {sha[:7]}: {message[:50]}")
                return True
            else:
                print(f"[GitHubTracker] Failed to create entry for commit {sha[:7]}")
                return False

        except Exception as e:
            print(f"[GitHubTracker] Error creating commit entry: {e}")
            return False

    def _fetch_recent_commits(self) -> list[Dict[str, Any]]:
        """
        Fetch recent commits from GitHub API.

        Returns:
            List of commit information dictionaries
        """
        headers = {"Accept": "application/vnd.github+json"}

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        # Choose endpoint based on tracking mode
        if self.tracking_mode == "org":
            events_url = f"https://api.github.com/orgs/{self.github_org}/events"
        else:
            events_url = f"https://api.github.com/users/{self.github_username}/events"

        try:
            response = requests.get(events_url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                target = self.github_org if self.tracking_mode == "org" else self.github_username
                print(f"[GitHubTracker] {self.tracking_mode.capitalize()} '{target}' not found")
            elif response.status_code == 403:
                print(f"[GitHubTracker] Rate limit exceeded. Consider adding COMMIT_TRACKER_TOKEN")
            else:
                print(f"[GitHubTracker] API error: {response.status_code} - {response.text}")

            return []

        except requests.RequestException as e:
            print(f"[GitHubTracker] Network error: {e}")
            return []

    def _process_events(self, events: list[Dict[str, Any]]) -> int:
        """
        Process GitHub events and create entries for new commits.

        Args:
            events: List of GitHub event objects

        Returns:
            Number of new commits processed
        """
        new_commits_count = 0

        for event in events:
            if event.get("type") != "PushEvent":
                continue

            repo = event.get("repo", {}).get("name", "unknown-repo")
            commits = event.get("payload", {}).get("commits", [])

            for commit in commits:
                sha = commit.get("sha")
                if not sha:
                    continue

                # Skip if already seen
                with self._lock:
                    if sha in self.seen_commits:
                        continue
                    self.seen_commits.add(sha)

                # Extract commit details
                message = commit.get("message", "No message")
                author = commit.get("author", {}).get("name", "unknown")

                # Create Clockify entry
                if self._create_commit_entry(sha, message, repo):
                    new_commits_count += 1

        return new_commits_count

    def _poll_loop(self) -> None:
        """Main polling loop that checks GitHub for new commits."""
        target = self.github_org if self.tracking_mode == "org" else self.github_username
        print(f"[GitHubTracker] Started polling for {self.tracking_mode} '{target}'")

        while self._running:
            try:
                # Fetch recent events
                events = self._fetch_recent_commits()

                if events:
                    # Process events and create entries for new commits
                    new_count = self._process_events(events)

                    if new_count > 0:
                        # Save state after processing new commits
                        self._save_state()

                # Wait before next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                print(f"[GitHubTracker] Error in poll loop: {e}")
                time.sleep(self.poll_interval)

    def start_tracking(self) -> None:
        """Start tracking GitHub commits."""
        if self._running:
            print("[GitHubTracker] Already running")
            return

        if not self.github_username and not self.github_org:
            print("[GitHubTracker] Error: Neither GitHub username nor organization configured")
            return

        self._running = True

        # Start polling loop in a separate thread
        poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        poll_thread.start()

        print("[GitHubTracker] GitHub commit tracking initialized")

    def stop_tracking(self) -> None:
        """Stop tracking and save state."""
        print("[GitHubTracker] Stopping tracking...")
        self._running = False
        self._save_state()

    @property
    def is_running(self) -> bool:
        """Check if tracking is active."""
        return self._running

    @property
    def commit_count(self) -> int:
        """Get the number of tracked commits."""
        with self._lock:
            return len(self.seen_commits)
