# Clockify Projects Guide

## What Are Projects in Clockify?

**Projects** are organizational units within Clockify that help you categorize and group time entries. They exist at the **workspace level** and provide several benefits:

### Benefits of Using Projects

1. **Organization** - Group related time entries together
2. **Reporting** - Filter reports by project to analyze time spent
3. **Budgeting** - Set time and cost budgets per project
4. **Team Collaboration** - Assign team members to specific projects
5. **Client Management** - Link projects to clients for billing
6. **Visual Grouping** - Color-code projects for easy identification

## Projects vs. Time Entries

```
Workspace (your company/org)
  └── Projects (GitHub Commits, Web Development, etc.)
       └── Time Entries (individual tracked time blocks)
```

- **Workspace**: Top-level container (you have one or more)
- **Project**: Category within workspace (optional but recommended)
- **Time Entry**: Individual time block with start/end times

## How Projects Appear in Clockify UI

### In the Web Interface

Projects appear in several places:

1. **Projects Page** (`Projects` in sidebar)
   - Lists all your projects
   - Shows project name, color, client, and status
   - **Note**: Project IDs are NOT visible here directly

2. **Time Tracker Page** (main dashboard)
   - Dropdown menu to select project when starting timer
   - Shows project name and color dot

3. **Reports Page**
   - Filter time entries by project
   - Group reports by project
   - View time/cost per project

4. **Time Entry Details**
   - Each time entry shows its associated project (if any)
   - Project name appears with colored indicator

### Why Project IDs Are Hidden in UI

Clockify hides technical IDs (like project IDs) from the UI to keep it user-friendly. Project IDs are **internal identifiers** used by the API, but users interact with **project names** in the interface.

**This is normal and by design.**

## How to Get Project IDs

Since project IDs aren't visible in the Clockify web UI, you need to use the API or our helper script:

### Method 1: Use Our Helper Script (Easiest)

```bash
# Make sure your .env file has CLOCKIFY_API_KEY and CLOCKIFY_WORKSPACE_ID
python scripts/get_clockify_project_id.py
```

This will output:
```
======================================================================
  Clockify Projects Listing
======================================================================

Workspace ID: 5f9c8b7a6d5e4f3g2h1j0k9l

✓ Connected as: John Doe

──────────────────────────────────────────────────────────────────────
ACTIVE PROJECTS
──────────────────────────────────────────────────────────────────────

1. GitHub Commits
   ID: 64c777ddd3fcab07cfbb210c
   Color: #2196F3
   Client: No client

2. Web Development
   ID: 64c888eed4fdbc18dgcc321d
   Color: #4CAF50
   Client: Acme Corp

======================================================================
Total active projects: 2
Total archived projects: 0
======================================================================
```

### Method 2: Use Browser Developer Tools

1. Open Clockify web interface (https://app.clockify.me)
2. Go to the Projects page
3. Open browser DevTools (F12)
4. Go to Network tab
5. Refresh the page
6. Look for API requests to `/workspaces/.../projects`
7. Inspect the response - you'll see project IDs in the JSON

### Method 3: Direct API Call

```bash
curl -X GET "https://api.clockify.me/api/v1/workspaces/{workspaceId}/projects" \
  -H "X-Api-Key: YOUR_API_KEY"
```

Replace `{workspaceId}` with your workspace ID.

## Creating a Project for GitHub Commits

### Via Web UI (Recommended for First-Time Setup)

1. **Go to Clockify**
   - Open https://app.clockify.me
   - Log in to your workspace

2. **Navigate to Projects**
   - Click `Projects` in the left sidebar
   - Click `+ New Project` button (top right)

3. **Configure Project**
   - **Name**: `GitHub Commits` (or `Automated Tracking`)
   - **Client**: Leave empty or select existing client
   - **Color**: Choose blue (#2196F3) to indicate automation
   - **Public**: Enable (so team can see these entries)
   - **Billable**: Set based on your needs
   - **Template**: Leave as "Blank project"

4. **Save Project**
   - Click `Create`

5. **Get Project ID**
   - Run our helper script: `python scripts/get_clockify_project_id.py`
   - Copy the ID for your new "GitHub Commits" project

6. **Configure Environment Variable**
   - Add to `.env` file:
     ```bash
     CLOCKIFY_DEFAULT_PROJECT_ID=64c777ddd3fcab07cfbb210c
     ```
   - Or add as GitHub Actions secret

### Via API (For Automation)

If you want to programmatically create projects:

```python
import asyncio
from src.infrastructure.config import get_settings
from src.infrastructure.api_clients.clockify_client import ClockifyClient

async def create_github_project():
    settings = get_settings()
    client = ClockifyClient(settings)

    # Note: You'll need to add this method to clockify_client.py
    endpoint = f"/workspaces/{client.workspace_id}/projects"
    body = {
        "name": "GitHub Commits",
        "color": "#2196F3",  # Blue
        "isPublic": True,
        "billable": False
    }

    project = await client.post(endpoint, json_data=body)
    print(f"Created project: {project['name']}")
    print(f"Project ID: {project['id']}")

    return project['id']

# Run it
project_id = asyncio.run(create_github_project())
```

## Using Projects with GitHub Commit Tracker

### Configuration

Once you have a project ID, configure it in your environment:

**Local Development (.env file):**
```bash
CLOCKIFY_DEFAULT_PROJECT_ID=64c777ddd3fcab07cfbb210c
```

**GitHub Actions (Repository Secrets):**
1. Go to repository Settings
2. Click Secrets → Actions
3. Click "New repository secret"
4. Name: `CLOCKIFY_DEFAULT_PROJECT_ID`
5. Value: `64c777ddd3fcab07cfbb210c`
6. Click "Add secret"

### How It Works

When configured, every time entry created by the commit tracker will be associated with this project:

```python
# In github_commit_tracker.py
response = self.clockify_client.create_time_entry_with_range(
    start=cluster.start,
    end=cluster.end,
    description=cluster.detailed_description,
    project_id=self.settings.get("CLOCKIFY_DEFAULT_PROJECT_ID"),  # ← Uses your project
)
```

### Benefits for Commit Tracking

With a dedicated project:

1. **Clear Separation**
   - Manual time entries vs automated commit entries
   - Easy to identify which entries are from GitHub

2. **Better Reports**
   - Filter reports to show only commit-based time
   - Compare automated vs manual tracking
   - Analyze time spent per repository

3. **Team Visibility**
   - Team members see "GitHub Commits" project
   - Clear indication of automated tracking
   - Transparent time allocation

4. **Easier Management**
   - Archive or delete all commit entries together
   - Change project settings without affecting other entries
   - Set project-specific permissions

## Verifying Project Usage

After configuring `CLOCKIFY_DEFAULT_PROJECT_ID`, verify it's working:

1. **Run the tracker** (manually or via GitHub Actions)
2. **Check Clockify web UI**
   - Go to time tracker page
   - Look for your new time entries
   - They should show "GitHub Commits" project with blue color
3. **Run a report**
   - Go to Reports → Summary
   - Group by Project
   - You should see "GitHub Commits" with tracked time

## Troubleshooting

### "Project ID not found" Error

**Cause**: The project ID is invalid or doesn't exist in your workspace.

**Solution**:
1. Run `python scripts/get_clockify_project_id.py` to list valid IDs
2. Verify the project exists in Clockify web UI
3. Check you're using the correct workspace ID

### Time Entries Created Without Project

**Cause**: `CLOCKIFY_DEFAULT_PROJECT_ID` is not set or is empty.

**Solution**:
1. Set the environment variable in your .env file
2. For GitHub Actions, add it as a repository secret
3. Restart the tracker after setting the variable

### Can't Find Projects in Clockify UI

**Cause**: You might not have any projects created yet.

**Solution**:
1. Projects are optional in Clockify - you might not have created any
2. Create your first project via Projects → + New Project
3. Some workspaces hide projects if you're on a free plan (check Clockify limits)

## API Endpoints Reference

### Get All Projects
```
GET /v1/workspaces/{workspaceId}/projects
```

### Get Specific Project
```
GET /v1/workspaces/{workspaceId}/projects/{projectId}
```

### Create Project
```
POST /v1/workspaces/{workspaceId}/projects
Body: { "name": "Project Name", "color": "#2196F3", "isPublic": true }
```

### Create Time Entry with Project
```
POST /v1/workspaces/{workspaceId}/time-entries
Body: {
  "start": "2025-01-15T09:00:00Z",
  "end": "2025-01-15T17:00:00Z",
  "description": "Work description",
  "projectId": "64c777ddd3fcab07cfbb210c"
}
```

## Frequently Asked Questions

### Q: Are projects required?

**A:** No, projects are optional. You can create time entries without a project. However, we **strongly recommend** using a dedicated project for GitHub commit tracking for better organization.

### Q: Can I change the project after creating time entries?

**A:** Yes, you can update existing time entries to change their project assignment. Our tracker supports this via the `update_time_entry()` method.

### Q: Can I use different projects for different repositories?

**A:** Yes! You could create separate projects for each repository and use logic to determine which project ID to use based on the repository name. This would require customizing the tracker code.

### Q: Why can't I see project IDs in the Clockify UI?

**A:** Clockify intentionally hides technical IDs to keep the UI user-friendly. Users work with project names, while the API uses IDs internally. This is standard practice for many SaaS applications.

### Q: Do I need a paid Clockify plan to use projects?

**A:** No, projects are available on Clockify's free plan. All users can create and use projects.

## Conclusion

**The Truth Confirmed:**

✅ **Projects DO exist** in Clockify
✅ **Project IDs are real** and used by the API
✅ **Project IDs are hidden in the UI** by design (normal behavior)
✅ **You can use `projectId` parameter** when creating time entries
✅ **Our implementation is correct** and follows Clockify best practices

**Recommendation:**

Create a dedicated "GitHub Commits" project in your Clockify workspace and configure `CLOCKIFY_DEFAULT_PROJECT_ID` to improve organization and reporting of your automated time tracking.
