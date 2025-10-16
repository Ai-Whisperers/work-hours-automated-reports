"""
GitHub Commit Tracker Service

This service fetches GitHub commits from repositories and automatically creates
or updates Clockify time entries based on worked hours calculation.

Features:
- Historical commit fetching with configurable date ranges
- Real-time polling for new commits
- Daily aggregated entries per user per repository
- Deduplication via entry updates instead of creating duplicates
- Cluster-based worked hours calculation
"""

import time
import json
import os
import threading
from datetime import datetime, timedelta, date
from typing import Optional, Set, Dict, Any, List, Tuple
from pathlib import Path

import requests
import pytz

from ...infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from ...infrastructure.config.settings import Settings
from .worked_hours_calculator import WorkedHoursCalculator, CommitCluster


class GitHubCommitTrackerService:
    """
    Service that monitors GitHub commits and creates/updates Clockify entries.

    Features:
    - Fetches historical commits from specified date range
    - Polls for new commits in real-time
    - Creates daily aggregated entries per user per repository
    - Updates existing entries to avoid duplication
    - Uses cluster-based worked hours calculation
    """

    STATE_FILE = "clockify_github_state.json"

    def __init__(
        self,
        clockify_client: ClockifySyncAdapter,
        settings: Settings,
        github_username: Optional[str] = None,
        github_org: Optional[str] = None,
        github_token: Optional[str] = None,
        poll_interval: int = 60,
        timezone: str = "America/Asuncion",
        use_worked_hours: bool = True,
        state_file_path: Optional[str] = None,
        history_days: int = 7,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        Initialize the GitHub commit tracker.

        Args:
            clockify_client: Clockify sync adapter instance
            settings: Application settings
            github_username: GitHub username to monitor (for user mode)
            github_org: GitHub organization to monitor (for org mode)
            github_token: GitHub personal access token (required for private repos)
            poll_interval: Seconds between GitHub API polls (real-time mode)
            timezone: Timezone for worked hours calculation
            use_worked_hours: If True, use cluster-based hours; if False, individual commits
            state_file_path: Optional custom path for state file
            history_days: Number of days to fetch historical commits
            start_date: Optional start date (YYYY-MM-DD format), overrides history_days
            end_date: Optional end date (YYYY-MM-DD format), defaults to today
        """
        self.clockify_client = clockify_client
        self.settings = settings
        self.github_username = github_username
        self.github_org = github_org
        self.github_token = github_token
        self.poll_interval = poll_interval
        self.use_worked_hours = use_worked_hours
        self.timezone = pytz.timezone(timezone)

        # Initialize worked hours calculator
        self.hours_calculator = WorkedHoursCalculator(
            timezone=timezone,
            tau_hours=2.5,
            cluster_threshold=0.1,
            max_session_hours=4.0,
            min_cluster_gap_minutes=30
        )

        # Determine tracking mode
        if not github_username and not github_org:
            raise ValueError("Either github_username or github_org must be provided")

        self.tracking_mode = "org" if github_org else "user"
        self.tracking_target = github_org if github_org else github_username

        # Date range configuration
        self.history_days = history_days
        self.start_date = self._parse_date(start_date) if start_date else None
        self.end_date = self._parse_date(end_date) if end_date else datetime.now(self.timezone).date()

        # State management
        self.state_file = state_file_path or self.STATE_FILE
        self.seen_commits: Set[str] = set()
        self.clockify_entries: Dict[str, str] = {}  # Maps "date_author_repo" -> clockify_entry_id
        self._running: bool = False
        self._lock = threading.Lock()

        # Load existing state
        self._load_state()

    def _parse_date(self, date_str: str) -> date:
        """Parse date string in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD") from e

    def _get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Calculate the date range for fetching commits.

        Returns:
            Tuple of (start_datetime, end_datetime) in timezone-aware format
        """
        # Use explicit start_date if provided, otherwise calculate from history_days
        if self.start_date:
            start = self.start_date
        else:
            start = self.end_date - timedelta(days=self.history_days)

        # Convert to timezone-aware datetimes
        start_dt = self.timezone.localize(datetime.combine(start, datetime.min.time()))
        end_dt = self.timezone.localize(datetime.combine(self.end_date, datetime.max.time()))

        return start_dt, end_dt

    def _load_state(self) -> None:
        """Load seen commits and clockify entries from state file."""
        if not os.path.exists(self.state_file):
            return

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                self.seen_commits = set(data.get("seen_commits", []))
                self.clockify_entries = data.get("clockify_entries", {})
                print(
                    f"[GitHubTracker] Loaded {len(self.seen_commits)} seen commits "
                    f"and {len(self.clockify_entries)} clockify entries"
                )
        except Exception as e:
            print(f"[GitHubTracker] Error loading state: {e}")
            self.seen_commits = set()
            self.clockify_entries = {}

    def _save_state(self) -> None:
        """Save seen commits and clockify entries to state file."""
        try:
            # Ensure directory exists
            state_path = Path(self.state_file)
            state_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, "w") as f:
                json.dump({
                    "seen_commits": list(self.seen_commits),
                    "clockify_entries": self.clockify_entries
                }, f, indent=2)
        except Exception as e:
            print(f"[GitHubTracker] Error saving state: {e}")

    def _get_org_repositories(self) -> List[str]:
        """
        Fetch list of repositories for the organization.

        Returns:
            List of repository full names (org/repo format)
        """
        headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        repos = []
        page = 1
        per_page = 100

        print(f"[GitHubTracker] Fetching repositories for org '{self.github_org}'...")

        while True:
            url = f"https://api.github.com/orgs/{self.github_org}/repos"
            params = {"page": page, "per_page": per_page, "type": "all"}

            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    page_repos = response.json()
                    if not page_repos:
                        break

                    repos.extend([repo["full_name"] for repo in page_repos])
                    page += 1

                    # Check if we've reached the last page
                    if len(page_repos) < per_page:
                        break
                elif response.status_code == 404:
                    print(f"[GitHubTracker] Organization '{self.github_org}' not found")
                    return []
                elif response.status_code == 403:
                    print(f"[GitHubTracker] Rate limit or permission error: {response.json()}")
                    return []
                else:
                    print(f"[GitHubTracker] Error fetching repos: {response.status_code}")
                    return []

            except requests.RequestException as e:
                print(f"[GitHubTracker] Network error fetching repos: {e}")
                return []

        print(f"[GitHubTracker] Found {len(repos)} repositories")
        return repos

    def _fetch_commits_from_repo(
        self,
        repo: str,
        since: datetime,
        until: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch commits from a specific repository within date range.

        Args:
            repo: Repository name (format: owner/repo)
            since: Start datetime (timezone-aware)
            until: End datetime (timezone-aware)

        Returns:
            List of commit data dictionaries
        """
        headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        commits = []
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/repos/{repo}/commits"
            params = {
                "since": since.isoformat(),
                "until": until.isoformat(),
                "page": page,
                "per_page": per_page
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    page_commits = response.json()
                    if not page_commits:
                        break

                    # Transform to our format
                    for commit in page_commits:
                        commits.append({
                            "sha": commit["sha"],
                            "author": commit["commit"]["author"]["name"],
                            "email": commit["commit"]["author"]["email"],
                            "repo": repo,
                            "timestamp": commit["commit"]["author"]["date"],
                            "message": commit["commit"]["message"]
                        })

                    page += 1

                    # Check if we've reached the last page
                    if len(page_commits) < per_page:
                        break
                elif response.status_code == 409:
                    # Empty repository
                    break
                elif response.status_code == 403:
                    print(f"[GitHubTracker] Rate limit for {repo}: {response.json()}")
                    break
                else:
                    print(f"[GitHubTracker] Error fetching commits from {repo}: {response.status_code}")
                    break

            except requests.RequestException as e:
                print(f"[GitHubTracker] Network error fetching commits from {repo}: {e}")
                break

        return commits

    def _fetch_historical_commits(self) -> List[Dict[str, Any]]:
        """
        Fetch historical commits from all repositories within date range.

        Returns:
            List of commit data dictionaries
        """
        start_dt, end_dt = self._get_date_range()
        print(f"[GitHubTracker] Fetching commits from {start_dt.date()} to {end_dt.date()}")

        all_commits = []

        if self.tracking_mode == "org":
            # Fetch from all org repositories
            repos = self._get_org_repositories()
            for repo in repos:
                print(f"[GitHubTracker] Fetching commits from {repo}...")
                commits = self._fetch_commits_from_repo(repo, start_dt, end_dt)
                all_commits.extend(commits)
                print(f"[GitHubTracker] Found {len(commits)} commits in {repo}")
        else:
            # For user mode, we need to fetch user's repositories first
            repos = self._get_user_repositories()
            for repo in repos:
                print(f"[GitHubTracker] Fetching commits from {repo}...")
                commits = self._fetch_commits_from_repo(repo, start_dt, end_dt)
                all_commits.extend(commits)
                print(f"[GitHubTracker] Found {len(commits)} commits in {repo}")

        print(f"[GitHubTracker] Total commits fetched: {len(all_commits)}")
        return all_commits

    def _get_user_repositories(self) -> List[str]:
        """
        Fetch list of repositories for the user.

        Returns:
            List of repository full names (user/repo format)
        """
        headers = {"Accept": "application/vnd.github+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        repos = []
        page = 1
        per_page = 100

        print(f"[GitHubTracker] Fetching repositories for user '{self.github_username}'...")

        while True:
            url = f"https://api.github.com/users/{self.github_username}/repos"
            params = {"page": page, "per_page": per_page, "type": "all"}

            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    page_repos = response.json()
                    if not page_repos:
                        break

                    repos.extend([repo["full_name"] for repo in page_repos])
                    page += 1

                    if len(page_repos) < per_page:
                        break
                elif response.status_code == 404:
                    print(f"[GitHubTracker] User '{self.github_username}' not found")
                    return []
                else:
                    print(f"[GitHubTracker] Error fetching repos: {response.status_code}")
                    return []

            except requests.RequestException as e:
                print(f"[GitHubTracker] Network error: {e}")
                return []

        print(f"[GitHubTracker] Found {len(repos)} repositories")
        return repos

    def _create_or_update_cluster_entry(self, cluster: CommitCluster) -> bool:
        """
        Create or update a Clockify time entry for a work session cluster.

        Args:
            cluster: CommitCluster object representing a work session

        Returns:
            True if entry was created/updated successfully
        """
        # Generate unique key for this cluster (date + author + repo)
        cluster_key = f"{cluster.start.date()}_{cluster.author}_{cluster.repo}"

        try:
            # Check if we already have an entry for this date/author/repo
            existing_entry_id = self.clockify_entries.get(cluster_key)

            if existing_entry_id:
                # Update existing entry
                response = self.clockify_client.update_time_entry(
                    entry_id=existing_entry_id,
                    start=cluster.start,
                    end=cluster.end,
                    description=cluster.detailed_description,
                )

                if response and "id" in response:
                    print(
                        f"[GitHubTracker] Updated session for {cluster.author} @ {cluster.repo}: "
                        f"{cluster.duration_hours:.2f}h ({cluster.commit_count} commits)"
                    )
                    return True
                else:
                    print(f"[GitHubTracker] Failed to update session {cluster_key}, will create new")
                    # Fall through to create new entry

            # Create new entry
            response = self.clockify_client.create_time_entry_with_range(
                start=cluster.start,
                end=cluster.end,
                description=cluster.detailed_description,
                project_id=self.settings.get("CLOCKIFY_DEFAULT_PROJECT_ID"),
            )

            if response and "id" in response:
                # Store the entry ID for future updates
                with self._lock:
                    self.clockify_entries[cluster_key] = response["id"]

                print(
                    f"[GitHubTracker] Created session for {cluster.author} @ {cluster.repo}: "
                    f"{cluster.duration_hours:.2f}h ({cluster.commit_count} commits)"
                )
                return True
            else:
                print(f"[GitHubTracker] Failed to create session for {cluster.author} @ {cluster.repo}")
                return False

        except Exception as e:
            print(f"[GitHubTracker] Error creating/updating cluster entry: {e}")
            return False

    def _process_commits_to_clusters(self, commits: List[Dict[str, Any]]) -> int:
        """
        Process commits into clusters and create/update Clockify entries.

        Args:
            commits: List of commit dictionaries

        Returns:
            Number of clusters created/updated
        """
        if not commits:
            return 0

        try:
            # Filter out already seen commits
            new_commits = []
            for commit in commits:
                sha = commit["sha"]
                with self._lock:
                    if sha not in self.seen_commits:
                        self.seen_commits.add(sha)
                        new_commits.append(commit)

            if not new_commits:
                print("[GitHubTracker] No new commits to process")
                return 0

            print(f"[GitHubTracker] Processing {len(new_commits)} new commits...")

            # Calculate clusters from commits
            clusters = self.hours_calculator.calculate_clusters(new_commits)

            if not clusters:
                return 0

            # Create/update Clockify entries for each cluster
            updated_count = 0
            for cluster in clusters:
                if self._create_or_update_cluster_entry(cluster):
                    updated_count += 1

            # Display summary
            if clusters:
                summary = self.hours_calculator.format_for_display(clusters)
                print(f"\n[GitHubTracker] Work Sessions Summary:\n{summary}\n")

            return updated_count

        except Exception as e:
            print(f"[GitHubTracker] Error processing commits: {e}")
            return 0

    def _poll_loop(self) -> None:
        """Main polling loop that checks GitHub for new commits in real-time."""
        target = self.github_org if self.tracking_mode == "org" else self.github_username
        print(f"[GitHubTracker] Started real-time polling for {self.tracking_mode} '{target}'")

        # Use a small window for real-time polling (last 24 hours)
        while self._running:
            try:
                # Fetch commits from last 24 hours
                end_dt = datetime.now(self.timezone)
                start_dt = end_dt - timedelta(hours=24)

                all_commits = []

                if self.tracking_mode == "org":
                    repos = self._get_org_repositories()
                    for repo in repos:
                        commits = self._fetch_commits_from_repo(repo, start_dt, end_dt)
                        all_commits.extend(commits)
                else:
                    repos = self._get_user_repositories()
                    for repo in repos:
                        commits = self._fetch_commits_from_repo(repo, start_dt, end_dt)
                        all_commits.extend(commits)

                # Process new commits
                if all_commits:
                    self._process_commits_to_clusters(all_commits)
                    self._save_state()

                # Wait before next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                print(f"[GitHubTracker] Error in poll loop: {e}")
                time.sleep(self.poll_interval)

    def start_tracking(self, skip_historical: bool = False) -> None:
        """
        Start tracking GitHub commits.

        Args:
            skip_historical: If True, skip fetching historical commits
        """
        if self._running:
            print("[GitHubTracker] Already running")
            return

        if not self.github_username and not self.github_org:
            print("[GitHubTracker] Error: Neither GitHub username nor organization configured")
            return

        # Phase 1: Fetch and process historical commits
        if not skip_historical:
            print("[GitHubTracker] Phase 1: Fetching historical commits...")
            historical_commits = self._fetch_historical_commits()
            if historical_commits:
                self._process_commits_to_clusters(historical_commits)
                self._save_state()

        # Phase 2: Start real-time polling
        print("[GitHubTracker] Phase 2: Starting real-time polling...")
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
