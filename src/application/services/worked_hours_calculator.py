"""
Worked Hours Calculator Service

Calculates worked hours from GitHub commits using cluster detection algorithm.
Based on temporal proximity analysis with exponential decay.
"""

import pytz
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CommitCluster:
    """Represents a cluster of commits (work session)."""
    author: str
    repo: str
    start: datetime
    end: datetime
    commits: List[Dict[str, Any]]
    duration_hours: float

    @property
    def commit_count(self) -> int:
        """Number of commits in this cluster."""
        return len(self.commits)

    @property
    def description(self) -> str:
        """Generate readable description for Clockify."""
        return f"{self.repo}: {self.commit_count} commits ({self.start:%H:%M}–{self.end:%H:%M})"


class WorkedHoursCalculator:
    """
    Calculate worked hours from GitHub commits using cluster detection.

    Algorithm:
    1. Group commits by author and repository
    2. Detect work sessions using temporal clustering
    3. Calculate duration for each session
    4. Cap maximum session length to avoid outliers

    Based on exponential decay clustering:
    - Weight W_i = e^(-Δt_i / τ)
    - If W_i > threshold (0.1), commits belong to same cluster
    - Typical τ ≈ 2.5h gives natural cutoff near 3h gap
    """

    def __init__(
        self,
        timezone: str = "America/Asuncion",
        tau_hours: float = 2.5,
        cluster_threshold: float = 0.1,
        max_session_hours: float = 4.0,
        min_cluster_gap_minutes: int = 30,
    ):
        """
        Initialize the worked hours calculator.

        Args:
            timezone: Timezone for commit timestamps (e.g., "America/Asuncion", "UTC")
            tau_hours: Exponential decay time constant in hours
            cluster_threshold: Weight threshold for cluster detection (0-1)
            max_session_hours: Maximum session duration cap in hours
            min_cluster_gap_minutes: Merge clusters closer than this (in minutes)
        """
        self.timezone = pytz.timezone(timezone)
        self.tau_hours = tau_hours
        self.cluster_threshold = cluster_threshold
        self.max_session_hours = max_session_hours
        self.min_cluster_gap_minutes = min_cluster_gap_minutes

    def calculate_clusters(
        self,
        commits: List[Dict[str, Any]]
    ) -> List[CommitCluster]:
        """
        Calculate work session clusters from commit data.

        Args:
            commits: List of commit dictionaries with keys:
                - sha: Commit SHA
                - author: Commit author name
                - repo: Repository name
                - timestamp: Commit timestamp (datetime or ISO string)
                - message: Commit message

        Returns:
            List of CommitCluster objects representing work sessions
        """
        if not commits:
            return []

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(commits)

        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Convert to specified timezone
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        df['timestamp'] = df['timestamp'].dt.tz_convert(self.timezone)

        # Sort by author, repo, and timestamp
        df = df.sort_values(['author', 'repo', 'timestamp']).reset_index(drop=True)

        # Calculate time gaps within each author+repo group
        df['gap_hours'] = (
            df.groupby(['author', 'repo'])['timestamp']
            .diff()
            .dt.total_seconds() / 3600
        )

        # Apply exponential decay clustering
        # W_i = e^(-Δt_i / τ)
        # New cluster when W_i < threshold (or first commit in group)
        df['weight'] = np.where(
            df['gap_hours'].isna(),
            1.0,  # First commit in group
            np.exp(-df['gap_hours'] / self.tau_hours)
        )

        # Mark cluster boundaries (weight < threshold means new cluster)
        df['is_new_cluster'] = (df['weight'] < self.cluster_threshold)
        df['cluster_id'] = df.groupby(['author', 'repo'])['is_new_cluster'].cumsum()

        # Create global cluster ID
        df['global_cluster_id'] = (
            df['author'].astype(str) + '_' +
            df['repo'].astype(str) + '_' +
            df['cluster_id'].astype(str)
        )

        # Group by cluster and calculate session times
        clusters = []

        for cluster_id, group in df.groupby('global_cluster_id'):
            author = group['author'].iloc[0]
            repo = group['repo'].iloc[0]
            start = group['timestamp'].min()
            end = group['timestamp'].max()

            # Calculate duration (capped at max_session_hours)
            duration_seconds = (end - start).total_seconds()
            duration_hours = min(
                duration_seconds / 3600,
                self.max_session_hours
            )

            # If only one commit, use a minimum duration
            if len(group) == 1:
                duration_hours = min(0.25, self.max_session_hours)  # 15 minutes minimum

            # Create cluster
            cluster = CommitCluster(
                author=author,
                repo=repo,
                start=start,
                end=end if len(group) > 1 else start + timedelta(minutes=15),
                commits=group.to_dict('records'),
                duration_hours=duration_hours
            )

            clusters.append(cluster)

        # Optional: Merge clusters that are very close together
        clusters = self._merge_close_clusters(clusters)

        return clusters

    def _merge_close_clusters(
        self,
        clusters: List[CommitCluster]
    ) -> List[CommitCluster]:
        """
        Merge clusters that are closer than min_cluster_gap.

        Args:
            clusters: List of CommitCluster objects

        Returns:
            Merged list of clusters
        """
        if not clusters or self.min_cluster_gap_minutes <= 0:
            return clusters

        # Group by author and repo
        from itertools import groupby

        merged = []

        # Sort clusters
        sorted_clusters = sorted(
            clusters,
            key=lambda c: (c.author, c.repo, c.start)
        )

        for (author, repo), group_clusters in groupby(
            sorted_clusters,
            key=lambda c: (c.author, c.repo)
        ):
            group_list = list(group_clusters)

            if len(group_list) == 1:
                merged.extend(group_list)
                continue

            # Merge clusters with small gaps
            current_cluster = group_list[0]

            for next_cluster in group_list[1:]:
                gap = (next_cluster.start - current_cluster.end).total_seconds() / 60

                if gap <= self.min_cluster_gap_minutes:
                    # Merge clusters
                    current_cluster = CommitCluster(
                        author=current_cluster.author,
                        repo=current_cluster.repo,
                        start=current_cluster.start,
                        end=next_cluster.end,
                        commits=current_cluster.commits + next_cluster.commits,
                        duration_hours=min(
                            (next_cluster.end - current_cluster.start).total_seconds() / 3600,
                            self.max_session_hours
                        )
                    )
                else:
                    # Save current cluster and start new one
                    merged.append(current_cluster)
                    current_cluster = next_cluster

            # Don't forget the last cluster
            merged.append(current_cluster)

        return merged

    def calculate_daily_hours(
        self,
        clusters: List[CommitCluster]
    ) -> pd.DataFrame:
        """
        Aggregate worked hours by author and date.

        Args:
            clusters: List of CommitCluster objects

        Returns:
            DataFrame with columns: date, author, hours
        """
        if not clusters:
            return pd.DataFrame(columns=['date', 'author', 'hours'])

        # Create DataFrame from clusters
        data = []
        for cluster in clusters:
            data.append({
                'date': cluster.start.date(),
                'author': cluster.author,
                'hours': cluster.duration_hours
            })

        df = pd.DataFrame(data)

        # Aggregate by date and author
        daily = (
            df.groupby(['date', 'author'])['hours']
            .sum()
            .reset_index()
            .sort_values(['date', 'author'])
        )

        return daily

    def format_for_display(
        self,
        clusters: List[CommitCluster]
    ) -> str:
        """
        Format clusters for human-readable display.

        Args:
            clusters: List of CommitCluster objects

        Returns:
            Formatted string with cluster information
        """
        if not clusters:
            return "No work sessions detected"

        lines = ["Work Sessions Detected:", "=" * 60]

        # Group by author
        from itertools import groupby

        sorted_clusters = sorted(clusters, key=lambda c: (c.author, c.start))

        for author, group in groupby(sorted_clusters, key=lambda c: c.author):
            lines.append(f"\n{author}:")
            lines.append("-" * 60)

            total_hours = 0

            for cluster in group:
                lines.append(
                    f"  {cluster.start:%Y-%m-%d %H:%M} - {cluster.end:%H:%M} "
                    f"({cluster.duration_hours:.2f}h) | {cluster.description}"
                )
                total_hours += cluster.duration_hours

            lines.append(f"  Total: {total_hours:.2f} hours")

        return "\n".join(lines)
