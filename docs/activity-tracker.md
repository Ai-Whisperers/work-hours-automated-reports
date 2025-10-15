# Activity Tracker

The Activity Tracker is an optional feature that automatically manages Clockify time entries based on user activity and GitHub commits.

## Features

### 1. Activity Monitoring
Automatically starts and stops Clockify timers based on mouse and keyboard activity:
- **Auto-start**: Starts a Clockify timer when activity is detected
- **Auto-stop**: Stops the timer after a configurable period of inactivity
- **Thread-safe**: Runs in the background without blocking other operations

### 2. GitHub Commit Tracking
Monitors GitHub commits and creates Clockify time entries:
- **Automatic detection**: Polls GitHub API for new commits
- **Duplicate prevention**: Tracks seen commits to avoid duplicate entries
- **Two tracking modes**: Individual commits or cluster-based worked hours
- **Persistent state**: Saves tracking state to prevent re-processing commits
- **Organization support**: Track all commits across an entire GitHub organization

#### Worked Hours Calculation (Recommended)

The tracker uses an advanced cluster detection algorithm to calculate actual worked hours from commit patterns:

- **Exponential Decay Clustering**: Groups commits into work sessions using temporal proximity analysis
- **Session Detection**: Automatically identifies work sessions with configurable time gaps (default: ~3 hours)
- **Duration Estimation**: Calculates session duration from first to last commit, capped at maximum (default: 4 hours)
- **Timezone Support**: Converts all timestamps to your local timezone for accurate reporting
- **Cluster Merging**: Combines sessions that are very close together (within 30 minutes)

**Algorithm Details:**
```
Weight = e^(-Δt / τ)
where:
  Δt = time gap between commits
  τ = time constant (default: 2.5 hours)

If Weight > 0.1, commits belong to same work session
Session duration = min(last_commit - first_commit, max_session_hours)
```

This produces more accurate time tracking than arbitrary per-commit durations.

## Installation

### Prerequisites

Install the required dependencies:

```bash
pip install pynput requests
```

Or install all dependencies from requirements.txt:

```bash
pip install -r requirements.txt
```

### Platform-Specific Notes

**Windows**: No additional setup required

**Linux**: You may need to install additional system packages:
```bash
sudo apt-get install python3-xlib  # For X11 systems
```

**macOS**: Grant accessibility permissions when prompted

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# Activity Tracker Configuration
ENABLE_ACTIVITY_TRACKER=true
ACTIVITY_TRACKER_INACTIVITY_LIMIT=300  # 5 minutes
ACTIVITY_TRACKER_CHECK_INTERVAL=5  # 5 seconds

# GitHub Commit Tracker Configuration
ENABLE_GITHUB_TRACKER=true
COMMIT_TRACKER_MODE=user  # Options: 'user' (individual) or 'org' (organization)
COMMIT_TRACKER_USERNAME=your_github_username  # For user mode
COMMIT_TRACKER_ORG=your_organization_name  # For org mode
COMMIT_TRACKER_TOKEN=ghp_your_personal_access_token  # Required for org mode
COMMIT_TRACKER_POLL_INTERVAL=60  # 60 seconds
COMMIT_TRACKER_DURATION=10  # 10 minutes per commit (legacy mode only)
COMMIT_TRACKER_USE_WORKED_HOURS=true  # Use cluster-based worked hours (recommended)
COMMIT_TRACKER_TIMEZONE=America/Asuncion  # Your local timezone

# Clockify Configuration (required)
CLOCKIFY_API_KEY=your_clockify_api_key
CLOCKIFY_WORKSPACE_ID=your_workspace_id
CLOCKIFY_DEFAULT_PROJECT_ID=  # Optional: default project for auto-tracked entries
```

### Configuration Parameters

#### Activity Tracker

| Parameter | Description | Default | Unit |
|-----------|-------------|---------|------|
| `ENABLE_ACTIVITY_TRACKER` | Enable/disable activity tracking | `false` | boolean |
| `ACTIVITY_TRACKER_INACTIVITY_LIMIT` | Time before considering user inactive | `300` | seconds |
| `ACTIVITY_TRACKER_CHECK_INTERVAL` | Frequency of activity checks | `5` | seconds |

#### GitHub Commit Tracker

| Parameter | Description | Default | Unit |
|-----------|-------------|---------|------|
| `ENABLE_GITHUB_TRACKER` | Enable/disable GitHub tracking | `false` | boolean |
| `COMMIT_TRACKER_MODE` | Tracking mode: user or org | `user` | string |
| `COMMIT_TRACKER_USERNAME` | GitHub username to monitor (user mode) | - | string |
| `COMMIT_TRACKER_ORG` | GitHub organization to monitor (org mode) | - | string |
| `COMMIT_TRACKER_TOKEN` | GitHub personal access token | - | string |
| `COMMIT_TRACKER_POLL_INTERVAL` | Time between GitHub API polls | `60` | seconds |
| `COMMIT_TRACKER_DURATION` | Duration per commit (legacy mode) | `10` | minutes |
| `COMMIT_TRACKER_USE_WORKED_HOURS` | Use cluster-based worked hours | `true` | boolean |
| `COMMIT_TRACKER_TIMEZONE` | Timezone for worked hours | `America/Asuncion` | string |

## Usage

### Programmatic Usage

```python
from src.infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from src.infrastructure.config import get_settings
from src.application.services.activity_tracker import ActivityTrackerService
from src.application.services.github_commit_tracker import GitHubCommitTrackerService

# Initialize settings
settings = get_settings()

# Create Clockify client
clockify_client = ClockifySyncAdapter(settings)

# Initialize Activity Tracker
activity_tracker = ActivityTrackerService(
    clockify_client=clockify_client,
    settings=settings,
    inactivity_limit=300,  # 5 minutes
    check_interval=5  # 5 seconds
)

# Initialize GitHub Commit Tracker
github_tracker = GitHubCommitTrackerService(
    clockify_client=clockify_client,
    settings=settings,
    github_username="your_username",
    github_token="your_token",  # Optional but recommended
    poll_interval=60,  # 1 minute
    commit_duration_minutes=10  # 10 minutes per commit
)

# Start both trackers
activity_tracker.start_monitoring()
github_tracker.start_tracking()

# Keep the application running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # Clean shutdown
    activity_tracker.stop_monitoring()
    github_tracker.stop_tracking()
```

### Standalone Script

Create a file `tracker.py`:

```python
#!/usr/bin/env python3
"""
Standalone Activity and Commit Tracker

Usage:
    python tracker.py
"""

import time
import os
from dotenv import load_dotenv

from src.infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter
from src.infrastructure.config import get_settings
from src.application.services.activity_tracker import ActivityTrackerService
from src.application.services.github_commit_tracker import GitHubCommitTrackerService

def main():
    # Load environment variables
    load_dotenv()
    settings = get_settings()

    # Initialize Clockify client
    clockify_client = ClockifySyncAdapter(settings)

    # Test connection
    print("Testing Clockify connection...")
    if not clockify_client.test_connection():
        print("Failed to connect to Clockify. Check your credentials.")
        return

    print("Connected to Clockify successfully!")

    # Initialize trackers
    trackers = []

    # Activity Tracker
    if os.getenv("ENABLE_ACTIVITY_TRACKER", "false").lower() == "true":
        activity_tracker = ActivityTrackerService(
            clockify_client=clockify_client,
            settings=settings,
            inactivity_limit=int(os.getenv("ACTIVITY_TRACKER_INACTIVITY_LIMIT", "300")),
            check_interval=int(os.getenv("ACTIVITY_TRACKER_CHECK_INTERVAL", "5"))
        )
        activity_tracker.start_monitoring()
        trackers.append(("Activity Tracker", activity_tracker))
        print("Activity Tracker started")

    # GitHub Commit Tracker
    if os.getenv("ENABLE_GITHUB_TRACKER", "false").lower() == "true":
        github_username = os.getenv("COMMIT_TRACKER_USERNAME")
        if github_username:
            github_tracker = GitHubCommitTrackerService(
                clockify_client=clockify_client,
                settings=settings,
                github_username=github_username,
                github_token=os.getenv("COMMIT_TRACKER_TOKEN"),
                poll_interval=int(os.getenv("COMMIT_TRACKER_POLL_INTERVAL", "60")),
                commit_duration_minutes=int(os.getenv("COMMIT_TRACKER_DURATION", "10"))
            )
            github_tracker.start_tracking()
            trackers.append(("GitHub Tracker", github_tracker))
            print("GitHub Commit Tracker started")
        else:
            print("COMMIT_TRACKER_USERNAME not configured, skipping GitHub tracker")

    if not trackers:
        print("No trackers enabled. Set ENABLE_ACTIVITY_TRACKER or ENABLE_GITHUB_TRACKER to true.")
        return

    print("\nTrackers running. Press Ctrl+C to stop.\n")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping trackers...")
        for name, tracker in trackers:
            if hasattr(tracker, 'stop_monitoring'):
                tracker.stop_monitoring()
            elif hasattr(tracker, 'stop_tracking'):
                tracker.stop_tracking()
            print(f"{name} stopped")
        print("All trackers stopped. Goodbye!")

if __name__ == "__main__":
    main()
```

Run the tracker:

```bash
python tracker.py
```

## How It Works

### Activity Monitoring Flow

1. **Input Detection**: Monitors mouse movements, clicks, and keyboard presses
2. **Activity Status**: Updates last activity timestamp on any input
3. **Timer Management**:
   - If active and no timer running → Start timer
   - If inactive and timer running → Stop timer
4. **Background Execution**: Runs in a separate thread, checking every N seconds

### GitHub Commit Tracking Flow

1. **API Polling**: Polls GitHub's endpoint based on mode:
   - User mode: `/users/:username/events`
   - Organization mode: `/orgs/:orgname/events`
2. **Event Processing**: Filters for `PushEvent` types
3. **Commit Detection**: Extracts commits from push events
4. **Duplicate Check**: Checks commit SHA against seen commits
5. **Clustering (Worked Hours Mode)**:
   - Collects commits in a buffer
   - Periodically runs cluster detection algorithm
   - Groups commits by author and repository
   - Calculates work session times using exponential decay
   - Merges nearby clusters
6. **Entry Creation**: Creates Clockify time entries:
   - **Worked Hours Mode** (recommended): One entry per work session cluster
     - Description: `{repo}: {count} commits ({start_time}–{end_time})`
     - Duration: Calculated from cluster timestamps
   - **Legacy Mode**: One entry per individual commit
     - Description: `Commit {sha} @ {repo}: {message}`
     - Duration: Fixed (default 10 minutes)
7. **State Persistence**: Saves seen commits to `clockify_github_state.json`

## State Files

The trackers maintain state files to prevent duplicate entries:

- **clockify_github_state.json**: Tracks seen commit SHAs
- Location: Current working directory (configurable)

**Note**: Do not delete these files while the tracker is running, as it will cause duplicate entries.

## Security Considerations

### API Keys

- **Never commit** `.env` files or expose API keys
- Use environment variables for all sensitive configuration
- Consider using a secrets manager for production deployments

### GitHub Token

A GitHub personal access token is optional but recommended:
- **Without token**: Limited to 60 requests/hour (rate limiting)
- **With token**: Up to 5,000 requests/hour

To create a token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `public_repo` or `repo` (for private repos)
4. Copy token and add to `.env` file

### Permissions

Activity tracking requires input monitoring permissions:
- **Windows**: Usually works without additional setup
- **macOS**: Grant accessibility permissions when prompted
- **Linux**: May require X11 or Wayland permissions

## Troubleshooting

### Activity Tracker Not Working

**Problem**: Timer doesn't start/stop automatically

**Solutions**:
1. Check if `pynput` is installed: `pip install pynput`
2. Verify permissions (especially on macOS/Linux)
3. Check logs for error messages
4. Ensure `ENABLE_ACTIVITY_TRACKER=true` in `.env`

### GitHub Tracker Not Detecting Commits

**Problem**: Commits not creating Clockify entries

**Solutions**:
1. Verify `COMMIT_TRACKER_USERNAME` is correct
2. Check if commits are public (or use token for private repos)
3. Verify API rate limits: Add `COMMIT_TRACKER_TOKEN` to `.env`
4. Check logs for API errors
5. Ensure state file isn't corrupted: Delete `clockify_github_state.json` and restart

### Duplicate Entries

**Problem**: Same commit creates multiple Clockify entries

**Solutions**:
1. Don't delete state files while tracker is running
2. Check if multiple tracker instances are running
3. Verify state file has write permissions

## Advanced Configuration

### Custom Callbacks

You can add custom callbacks for activity events:

```python
def on_activity():
    print("Activity detected!")

def on_inactivity():
    print("User became inactive")

activity_tracker = ActivityTrackerService(
    clockify_client=clockify_client,
    settings=settings,
    on_activity_callback=on_activity,
    on_inactivity_callback=on_inactivity
)
```

### Custom State File Location

```python
github_tracker = GitHubCommitTrackerService(
    clockify_client=clockify_client,
    settings=settings,
    github_username="username",
    state_file_path="/path/to/custom/state.json"
)
```

## Performance Considerations

- **Activity Tracker**: Minimal CPU usage (~0.1% idle, ~0.5% active)
- **GitHub Tracker**: Network usage depends on poll interval
  - Default (60s): ~1.5 KB per request, ~2.5 MB/day
  - Aggressive (10s): ~15 MB/day

## Integration with Existing Reports

The activity tracker creates standard Clockify time entries, so they automatically appear in:
- Generated reports
- Clockify web interface
- API queries

No special handling needed.

## Future Enhancements

Planned features:
- [ ] Application whitelist/blacklist for activity tracking
- [ ] Support for GitLab and Bitbucket
- [ ] Smart commit duration based on file changes
- [ ] Integration with IDE plugins
- [ ] Activity patterns and analytics
- [ ] Desktop notifications

## Support

For issues or questions:
1. Check this documentation
2. Review logs for error messages
3. Open an issue on GitHub with:
   - Error message
   - Configuration (without sensitive data)
   - Steps to reproduce
