# Clockify Time Entries Not Showing - Troubleshooting Guide

## Issue: Time Entries Created via API Don't Appear in Clockify UI

If your GitHub Actions workflow completes successfully but you don't see time entries in Clockify, follow this diagnostic checklist.

---

## ✅ Step 1: Verify Workflow Actually Creates Entries

### Check GitHub Actions Logs

1. Go to your repository → **Actions** tab
2. Click on the latest "GitHub Commit Tracker - Scheduled Sync" run
3. Expand the "Run commit tracker (one-time sync)" step
4. Look for output like:
   ```
   [Sync] ✓ Sync complete! Processed X commits
   ```

**If you see "Processed 0 commits":**
- No commits were found in the date range
- Check `COMMIT_HISTORY_DAYS` or date range settings
- Verify commits exist in your repositories during that time

**If you see "Processed 5 commits":**
- The tracker found and processed commits
- Continue to Step 2

---

## ✅ Step 2: Check Clockify API Response

### Add Debug Logging

Add temporary logging to see the API response:

**Edit `.github/workflows/commit-tracker-scheduled.yml`** line 170:

```python
# Before
tracker.start_tracking(skip_historical=False)

# After - ADD THIS LINE
import logging
logging.basicConfig(level=logging.DEBUG)
tracker.start_tracking(skip_historical=False)
```

**Or modify `src/application/services/github_commit_tracker.py` line 424:**

```python
response = self.clockify_client.create_time_entry_with_range(
    start=cluster.start,
    end=cluster.end,
    description=cluster.detailed_description,
    project_id=self.settings.get("CLOCKIFY_DEFAULT_PROJECT_ID"),
)

# ADD THESE LINES:
print(f"[DEBUG] Created entry response: {response}")
if response and "id" in response:
    print(f"[DEBUG] Entry ID: {response['id']}")
    print(f"[DEBUG] Entry details: {response}")
```

Re-run the workflow and check logs for the API response.

---

## ✅ Step 3: Verify Entry Actually Exists in Clockify

### Method A: Check via Clockify Web UI

1. Go to https://app.clockify.me
2. Select your workspace
3. Click **"Time Tracker"** or **"Timesheet"** in sidebar
4. **Check different views:**
   - **Calendar View**: Click on the dates
   - **List View**: Scroll through entries
   - **Filter by Project**: Select your "GitHub Commits" project
   - **Check Week/Month View**: Entries might be in different time periods

### Method B: Check via Clockify Reports

1. Go to **Reports** → **Detailed**
2. Set date range to **last 30 days**
3. Group by: **Project**
4. Look for your project entries

### Method C: Verify via API

Run this script to manually check if entries exist:

```python
import os
import asyncio
from src.infrastructure.config import get_settings
from src.infrastructure.api_clients.clockify_client import ClockifyClient
from datetime import datetime, timedelta

async def check_entries():
    settings = get_settings()
    client = ClockifyClient(settings)

    # Get current user
    user = await client.get_current_user()
    user_id = user['id']
    print(f"User: {user['name']} (ID: {user_id})")

    # Get time entries for last 7 days
    from src.domain.value_objects import DateRange
    date_range = DateRange(
        start=datetime.now() - timedelta(days=7),
        end=datetime.now()
    )

    entries = await client.get_time_entries(user_id, date_range)

    print(f"\nFound {len(entries)} time entries in last 7 days:")
    for entry in entries:
        print(f"  - {entry.description[:50]}... | {entry.start} to {entry.end}")

asyncio.run(check_entries())
```

---

## ✅ Step 4: Common Causes & Solutions

### Cause 1: Wrong Workspace

**Symptom**: Entries created in different workspace

**Solution**:
1. Check `CLOCKIFY_WORKSPACE_ID` secret in GitHub
2. Verify it matches the workspace you're viewing
3. Get workspace ID:
   - Go to Clockify → Settings → Workspace settings
   - Or run: `python -c "from src.infrastructure.config import get_settings; s=get_settings(); print(f'Workspace: {s.clockify_workspace_id}')"`

### Cause 2: Wrong User

**Symptom**: Entries created for different user

**Solution**:
- Clockify API key authentication automatically creates entries for the authenticated user
- Verify you're logged into Clockify with the same account as the API key
- Check API key owner:
  ```python
  curl -H "X-Api-Key: YOUR_API_KEY" https://api.clockify.me/api/v1/user
  ```

### Cause 3: Wrong Date/Time

**Symptom**: Entries created but in wrong time period

**Solution**:
1. **Check Timezone**: Verify `COMMIT_TRACKER_TIMEZONE` matches your Clockify profile timezone
2. **Check Date Range**: Entries might be created for commits from weeks ago
3. **UTC vs Local**: Clockify stores times in UTC but displays in your profile timezone

### Cause 4: Invisible Due to Filters

**Symptom**: Entries exist but hidden by UI filters

**Solution**:
1. Clear all filters in Clockify Time Tracker
2. Check "Show entries from all projects"
3. Disable "Billable only" filter
4. Check calendar doesn't have date range limitations

### Cause 5: API Returned Error (Silent Failure)

**Symptom**: No error in logs but entries not created

**Check API Response**:

Modify `src/infrastructure/api_clients/base_client.py` to log all responses:

```python
async def post(self, endpoint: str, json_data: Dict[str, Any] = None, **kwargs) -> Any:
    """Make a POST request."""
    response = await self._request("POST", endpoint, json=json_data, **kwargs)

    # ADD THIS:
    print(f"[API] POST {endpoint}")
    print(f"[API] Request: {json_data}")
    print(f"[API] Response: {response}")

    return response
```

**Look for error responses:**
- `400 Bad Request`: Invalid data format
- `401 Unauthorized`: Invalid API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Invalid workspace/project ID
- `422 Unprocessable Entity`: Validation error

### Cause 6: Project ID Invalid

**Symptom**: Entries might be created without project assignment

**Solution**:
1. Verify project ID is correct:
   ```bash
   python scripts/get_project_id_simple.py
   ```
2. Check project exists and isn't archived
3. Try creating entry WITHOUT project ID to test if that's the issue

---

## ✅ Step 5: Manual API Test

Test the exact API call manually to isolate the issue:

```bash
# Test creating a time entry directly
curl -X POST "https://api.clockify.me/api/v1/workspaces/YOUR_WORKSPACE_ID/time-entries" \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "start": "2025-01-16T10:00:00Z",
    "end": "2025-01-16T11:00:00Z",
    "description": "Test entry from API",
    "projectId": "YOUR_PROJECT_ID"
  }'
```

**Expected Response:**
```json
{
  "id": "entry-id-here",
  "description": "Test entry from API",
  "start": "2025-01-16T10:00:00Z",
  "end": "2025-01-16T11:00:00Z",
  ...
}
```

**If this works**, the issue is in the Python code.
**If this fails**, the issue is with Clockify API key/permissions.

---

## ✅ Step 6: Check Clockify Account Permissions

### Workspace Role Requirements

Time entry creation requires:
- **Regular User** or higher permissions
- **Not a Guest** (guests can't create entries)
- **Not locked** (account must be active)

**To check:**
1. Go to Clockify → Settings → Workspace settings → Members
2. Find your user → Check role
3. Must be: Admin, Project Manager, or Team Member

### API Key Validity

Test API key:
```bash
curl -H "X-Api-Key: YOUR_API_KEY" https://api.clockify.me/api/v1/user
```

Should return your user info. If it fails, regenerate API key.

---

## ✅ Step 7: Enable Detailed Logging in Workflow

Add comprehensive logging to the workflow:

**In `.github/workflows/commit-tracker-scheduled.yml`**, modify the sync script:

```python
def main():
    # Load settings
    settings = get_settings()

    # ADD LOGGING
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Workspace ID: {settings.clockify_workspace_id}")
    logger.info(f"Project ID: {settings.get('CLOCKIFY_DEFAULT_PROJECT_ID')}")

    # Rest of code...
```

---

## 📊 Quick Diagnostic Checklist

- [ ] Workflow runs successfully (no errors in logs)
- [ ] Workflow logs show "Processed X commits" (X > 0)
- [ ] Correct workspace ID configured
- [ ] Logged into Clockify with same user as API key
- [ ] Checked all Clockify views (Time Tracker, Timesheet, Reports)
- [ ] Checked correct date range in Clockify UI
- [ ] No UI filters hiding entries
- [ ] Project exists and isn't archived
- [ ] API key has correct permissions
- [ ] Manual API test works
- [ ] Timezone configured correctly

---

## 🔧 Emergency Debug Script

Save this as `debug_clockify.py` and run it:

```python
#!/usr/bin/env python3
import os
import sys
import asyncio
from datetime import datetime, timedelta

# Set minimal env vars
os.environ.setdefault('ADO_ORG', 'test')
os.environ.setdefault('ADO_PROJECT', 'test')
os.environ.setdefault('ADO_PAT', 'test')

from src.infrastructure.config import get_settings
from src.infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter

async def debug():
    settings = get_settings()
    client = ClockifySyncAdapter(settings)

    print("=" * 70)
    print("CLOCKIFY DEBUG INFORMATION")
    print("=" * 70)

    # Test connection
    print("\n1. Testing connection...")
    if client.test_connection():
        print("   ✓ Connection successful")
    else:
        print("   ✗ Connection failed")
        return

    # Get user info
    print("\n2. Getting user info...")
    user = client.get_current_user()
    print(f"   User: {user.get('name')} ({user.get('email')})")
    print(f"   User ID: {user.get('id')}")

    # Get workspace
    print(f"\n3. Workspace ID: {settings.clockify_workspace_id}")

    # Get project
    project_id = settings.get("CLOCKIFY_DEFAULT_PROJECT_ID")
    print(f"\n4. Project ID: {project_id or 'NOT SET'}")

    # Try creating a test entry
    print("\n5. Creating test time entry...")
    try:
        now = datetime.utcnow()
        response = client.create_time_entry_with_range(
            start=now - timedelta(hours=1),
            end=now,
            description="DEBUG TEST ENTRY - DELETE ME",
            project_id=project_id,
        )

        if response and "id" in response:
            print(f"   ✓ Entry created successfully!")
            print(f"   Entry ID: {response['id']}")
            print(f"   Description: {response.get('description')}")
            print(f"   Start: {response.get('timeInterval', {}).get('start')}")
            print(f"   End: {response.get('timeInterval', {}).get('end')}")
            print(f"\n   → Check Clockify UI now! Entry should be visible.")
        else:
            print(f"   ✗ Entry creation returned unexpected response: {response}")

    except Exception as e:
        print(f"   ✗ Failed to create entry: {e}")

    print("\n" + "=" * 70)

if __name__ == '__main__':
    asyncio.run(debug())
```

Run it:
```bash
python debug_clockify.py
```

This will create a test entry and tell you if it worked.

---

## 📞 Still Not Working?

If you've tried everything and entries still don't show:

1. **Check Clockify Status**: https://status.clockify.me/
2. **Contact Clockify Support**: support@clockify.me
   - Include: Workspace ID, User email, Time entry IDs (from API responses)
3. **Check for Known Issues**: https://forum.clockify.me/

---

**Most Common Solution**: Entries ARE being created, but you're looking in the wrong place or wrong date range in Clockify UI. Always check Reports → Detailed with a wide date range first!
