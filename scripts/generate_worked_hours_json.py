#!/usr/bin/env python3
"""
Generate worked_hours.json for GitHub Pages dashboard.

This script:
1. Fetches GitHub commits using the commit tracker
2. Calculates worked hours using cluster analysis
3. Generates a JSON file with summary statistics, daily hours, repo hours, and sessions
4. Outputs to worked_hours.json for the static dashboard

Usage:
    python scripts/generate_worked_hours_json.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config import get_settings
from src.infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from src.application.services.github_commit_tracker import GitHubCommitTrackerService


def generate_worked_hours_json():
    """Generate worked_hours.json from GitHub commit data."""
    print("=" * 70)
    print("  GENERATING WORKED HOURS JSON FOR GITHUB PAGES")
    print("=" * 70)

    # Load settings
    print("\n📋 Loading settings...")
    settings = get_settings()

    # Get tracker configuration from environment
    tracker_mode = os.getenv('COMMIT_TRACKER_MODE', 'organization')
    github_org = os.getenv('COMMIT_TRACKER_ORG', 'Ai-Whisperers')
    github_username = os.getenv('COMMIT_TRACKER_USERNAME')
    github_token = os.getenv('GH_TOKEN') or os.getenv('COMMIT_TRACKER_TOKEN')
    history_days = int(os.getenv('COMMIT_HISTORY_DAYS', '30'))
    timezone = os.getenv('COMMIT_TRACKER_TIMEZONE', 'UTC')

    print(f"✓ Mode: {tracker_mode}")
    print(f"✓ Organization: {github_org if tracker_mode == 'organization' else 'N/A'}")
    print(f"✓ Username: {github_username if tracker_mode == 'user' else 'N/A'}")
    print(f"✓ History days: {history_days}")
    print(f"✓ Timezone: {timezone}")

    # Initialize Clockify client (required but won't be used for data fetching)
    print("\n🔧 Initializing Clockify adapter...")
    # For dashboard generation, we don't need actual Clockify credentials
    # But the tracker class requires it, so we'll pass the adapter
    # The get_worked_hours_data method doesn't actually use it
    try:
        clockify_client = ClockifySyncAdapter(settings)
    except Exception as e:
        print(f"⚠️ Warning: Clockify adapter init failed ({e}), continuing anyway...")
        clockify_client = None

    # Initialize tracker
    print("\n🔧 Initializing commit tracker...")
    tracker = GitHubCommitTrackerService(
        clockify_client=clockify_client,
        settings=settings,
        github_username=github_username if tracker_mode == 'user' else None,
        github_org=github_org if tracker_mode == 'organization' else None,
        github_token=github_token,
        timezone=timezone,
        history_days=history_days,
        use_worked_hours=True
    )

    # Fetch commits and calculate worked hours
    print("\n🔍 Fetching commits and calculating worked hours...")
    try:
        # Get worked hours data
        worked_hours_data = tracker.get_worked_hours_data()

        if not worked_hours_data or not worked_hours_data.get('sessions'):
            print("⚠️ No commit data found. Generating empty structure...")
            worked_hours_data = {
                'sessions': [],
                'daily_hours': [],
                'repo_hours': []
            }

    except Exception as e:
        print(f"❌ Failed to fetch commit data: {e}")
        print("   Generating empty structure...")
        worked_hours_data = {
            'sessions': [],
            'daily_hours': [],
            'repo_hours': []
        }

    # Process data for dashboard
    print("\n📊 Processing data for dashboard...")

    sessions = worked_hours_data.get('sessions', [])
    print(f"✓ Found {len(sessions)} work sessions")

    # Calculate summary statistics
    total_hours = sum(session['hours'] for session in sessions)
    total_commits = sum(session['commit_count'] for session in sessions)

    # Get unique days
    unique_dates = set()
    for session in sessions:
        date_str = session['start'][:10]  # Extract YYYY-MM-DD
        unique_dates.add(date_str)

    total_days = len(unique_dates)
    avg_hours_per_day = total_hours / total_days if total_days > 0 else 0

    summary = {
        'total_days': total_days,
        'total_hours': round(total_hours, 2),
        'total_commits': total_commits,
        'avg_hours_per_day': round(avg_hours_per_day, 2)
    }

    print(f"✓ Total days: {total_days}")
    print(f"✓ Total hours: {total_hours:.1f}h")
    print(f"✓ Total commits: {total_commits}")
    print(f"✓ Avg hours/day: {avg_hours_per_day:.1f}h")

    # Aggregate daily hours
    daily_hours_map = defaultdict(float)
    for session in sessions:
        date_str = session['start'][:10]
        daily_hours_map[date_str] += session['hours']

    # Sort by date
    daily_hours = [
        {'date': date, 'hours': round(hours, 2)}
        for date, hours in sorted(daily_hours_map.items())
    ]

    print(f"✓ Daily hours calculated for {len(daily_hours)} days")

    # Aggregate repo hours
    repo_hours_map = defaultdict(float)
    for session in sessions:
        repo_hours_map[session['repo']] += session['hours']

    # Sort by hours descending
    repo_hours = [
        {'repo': repo, 'hours': round(hours, 2)}
        for repo, hours in sorted(repo_hours_map.items(), key=lambda x: x[1], reverse=True)
    ]

    print(f"✓ Repository hours calculated for {len(repo_hours)} repos")

    # Build final JSON structure
    output = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'summary': summary,
        'daily_hours': daily_hours,
        'repo_hours': repo_hours,
        'sessions': sessions
    }

    # Write to file
    output_path = project_root / 'worked_hours.json'
    print(f"\n💾 Writing to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ Successfully generated worked_hours.json!")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    print("=" * 70)

    return output_path


if __name__ == '__main__':
    try:
        output_path = generate_worked_hours_json()
        print(f"\n🎉 Done! Dashboard data ready at: {output_path}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
