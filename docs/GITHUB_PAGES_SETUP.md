# GitHub Pages Setup Guide

This guide explains how to enable and configure GitHub Pages for the Work Hours Dashboard.

## Quick Start

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (in left sidebar)
3. Under "Build and deployment":
   - **Source**: Deploy from a branch
   - **Branch**: Select `gh-pages` branch and `/ (root)` folder
   - Click **Save**

4. Wait 1-2 minutes for the site to deploy
5. Your dashboard will be available at:
   ```
   https://[your-org].github.io/[repo-name]/
   ```

### 2. Configure Required Secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

| Secret Name | Value | Required |
|------------|-------|----------|
| `GH_TOKEN` | GitHub Personal Access Token | ✅ Yes |
| `COMMIT_TRACKER_ORG` | Your GitHub organization name | ⚠️ If using org mode |

#### Creating a GitHub Personal Access Token

1. Go to GitHub → **Settings** (your profile, not repo)
2. Click **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token (classic)**
4. Name: "GitHub Pages Dashboard Token"
5. Expiration: Set as needed
6. Scopes required:
   - `repo` (Full control of private repositories)
   - `read:org` (Read org data, if using organization mode)
7. Click **Generate token**
8. Copy the token immediately (you won't see it again!)
9. Add as `GH_TOKEN` secret in your repository

### 3. Trigger First Deployment

Option A: **Wait for automatic schedule** (runs every 6 hours)

Option B: **Manual trigger** (immediate):
1. Go to **Actions** tab
2. Click "Deploy GitHub Pages Dashboard" workflow
3. Click **Run workflow** → **Run workflow**
4. Wait for completion (~1-2 minutes)

Option C: **Push to main branch**:
```bash
git add gh-pages-site/
git commit -m "Add GitHub Pages dashboard"
git push
```

### 4. Verify Deployment

1. Check **Actions** tab for workflow run status
2. Look for "pages build and deployment" workflow (auto-created by GitHub)
3. Once complete, visit your GitHub Pages URL
4. You should see the Work Hours Dashboard!

---

## Configuration Options

### Optional Environment Variables

Configure these in **Settings** → **Secrets and variables** → **Actions** → **Variables**:

| Variable | Default | Description |
|----------|---------|-------------|
| `COMMIT_HISTORY_DAYS` | 30 | Number of days of commit history to fetch |
| `COMMIT_TRACKER_MODE` | organization | 'organization' or 'user' |
| `COMMIT_TRACKER_TIMEZONE` | UTC | Timezone for time calculations |
| `SESSION_GAP_HOURS` | 3 | Gap between work sessions (hours) |
| `MIN_SESSION_HOURS` | 0.25 | Minimum session duration (hours) |

### Update Schedule

The dashboard auto-updates every 6 hours. To change this:

Edit `.github/workflows/gh-pages-deploy.yml`:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
    # Examples:
    # - cron: '0 */1 * * *'  # Every hour
    # - cron: '0 8,17 * * 1-5'  # 8 AM and 5 PM on weekdays
    # - cron: '0 0 * * *'  # Once daily at midnight
```

Cron syntax: `minute hour day month day-of-week`

---

## Restricting Access (Organization Members Only)

### Option 1: Private Repository (Requires GitHub Team/Enterprise)

If your repository is **private** and you have GitHub Team or Enterprise:

1. Your GitHub Pages site will automatically be private
2. Only organization members with repo access can view it
3. No additional configuration needed

### Option 2: Public Repository with Basic Auth (Manual)

For public repositories, you can add password protection using GitHub Pages + Cloudflare or similar:

**Using Cloudflare Access** (Free):

1. Set up Cloudflare for your domain
2. Configure Cloudflare Access
3. Add authentication rules for organization emails
4. Point custom domain to GitHub Pages

### Option 3: Keep Repository Private

The simplest approach:

1. Keep the repository private
2. Upgrade to GitHub Team ($4/user/month)
3. GitHub Pages will inherit repository privacy
4. Only organization members can access

---

## Troubleshooting

### "404 - Page Not Found"

**Causes:**
- GitHub Pages not enabled
- Wrong branch/folder selected
- gh-pages branch doesn't exist yet

**Solutions:**
1. Run workflow manually to create gh-pages branch
2. Check Settings → Pages → Source is set to "gh-pages" branch
3. Wait 1-2 minutes after workflow completes

### "Failed to Load Data" in Dashboard

**Causes:**
- `worked_hours.json` not generated
- Workflow failed
- No commits found in date range

**Solutions:**
1. Check Actions tab for workflow errors
2. Verify `GH_TOKEN` has correct permissions
3. Check workflow logs for "Processed X commits"
4. Ensure organization/username is correct

### Workflow Fails with "Resource not accessible by integration"

**Cause:** `GITHUB_TOKEN` doesn't have write permissions.

**Solution:**

Edit `.github/workflows/gh-pages-deploy.yml`, ensure these permissions are set:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

### Charts Not Rendering

**Causes:**
- Chart.js CDN blocked
- Browser console errors
- Data format incorrect

**Solutions:**
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify `worked_hours.json` format matches expected structure
4. Check network tab to see if Chart.js loaded

### Workflow Runs But No Data

**Causes:**
- No commits in date range
- Wrong organization/username
- API rate limit exceeded

**Solutions:**
1. Check workflow logs for "Total commits fetched: 0"
2. Verify `COMMIT_TRACKER_ORG` matches your organization name
3. Increase `COMMIT_HISTORY_DAYS` to fetch more history
4. Check GitHub API rate limit: https://api.github.com/rate_limit

---

## Advanced Configuration

### Custom Domain

1. Buy a domain (e.g., from Namecheap, Google Domains)
2. Add CNAME record pointing to `[your-org].github.io`
3. In repo Settings → Pages → Custom domain, enter your domain
4. Enable "Enforce HTTPS"
5. Wait for DNS propagation (~24 hours)

### Multiple Dashboards

To host multiple dashboards for different teams/projects:

1. Create separate repositories for each dashboard
2. Each gets its own GitHub Pages site at `[org].github.io/[repo-name]`
3. Or use subpaths: `dashboard.example.com/team-a`, `dashboard.example.com/team-b`

### Embedding in Other Sites

To embed the dashboard in another website:

```html
<iframe
  src="https://[your-org].github.io/[repo-name]/"
  width="100%"
  height="800px"
  frameborder="0"
></iframe>
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions Workflow (Every 6 hours)                    │
│  .github/workflows/gh-pages-deploy.yml                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
           ┌─────────────────────┐
           │  1. Checkout repo   │
           │  2. Setup Python    │
           │  3. Install deps    │
           └──────────┬──────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  Generate worked_hours.json            │
    │  (scripts/generate_worked_hours_json.py) │
    │                                        │
    │  - Fetch GitHub commits                │
    │  - Calculate work sessions             │
    │  - Aggregate statistics                │
    └──────────┬─────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────┐
    │  Copy static files:         │
    │  - index.html               │
    │  - styles.css               │
    │  - app.js                   │
    │  - worked_hours.json        │
    └──────────┬──────────────────┘
              │
              ▼
    ┌──────────────────────────────┐
    │  Deploy to gh-pages branch   │
    │  (peaceiris/actions-gh-pages) │
    └──────────┬───────────────────┘
              │
              ▼
    ┌──────────────────────────────────────┐
    │  GitHub Pages                        │
    │  https://[org].github.io/[repo]/     │
    │                                      │
    │  - Serves static files               │
    │  - Auto HTTPS                        │
    │  - Global CDN                        │
    └──────────────────────────────────────┘
```

---

## Security Considerations

### GitHub Token Permissions

The `GH_TOKEN` secret should have **minimal permissions**:

✅ **Required**:
- `repo` (if repositories are private)
- `read:org` (if using organization mode)

❌ **NOT Required**:
- `workflow`
- `admin`
- `delete_repo`

### Data Privacy

**What's public:**
- Commit messages
- Commit author names
- Repository names
- Commit timestamps
- Calculated worked hours

**What's NOT included:**
- Code content
- Commit diffs
- File paths
- Email addresses (not displayed in UI)
- Private repository contents

If your organization has strict privacy requirements:
- Keep repository private (requires GitHub Team/Enterprise)
- Review commit messages before enabling
- Consider filtering sensitive repository names in the code

---

## Monitoring

### Check Dashboard Health

```bash
# Test if dashboard is accessible
curl -I https://[your-org].github.io/[repo-name]/

# Check if data file exists
curl https://[your-org].github.io/[repo-name]/worked_hours.json

# View last update time
curl -s https://[your-org].github.io/[repo-name]/worked_hours.json | jq .generated_at
```

### GitHub Actions Monitoring

1. Enable notifications:
   - Go to repo **Settings** → **Notifications**
   - Check "Send notifications for failed workflows only"
2. Add status badge to README:
   ```markdown
   ![Deploy](https://github.com/[org]/[repo]/actions/workflows/gh-pages-deploy.yml/badge.svg)
   ```

---

## Cost

**Free Tier** (For most organizations):
- GitHub Pages: **Free** (public repos)
- GitHub Actions: **2,000 minutes/month free** (plenty for this workflow)
- Storage: **500 MB free** (dashboard is <1 MB)

**Paid Plans** (For private GitHub Pages):
- GitHub Team: **$4/user/month**
  - Includes private GitHub Pages
  - Increased Actions minutes
  - Organization management features

**Estimated Usage:**
- Workflow runs: ~120/month (every 6 hours = 4/day × 30 days)
- Minutes per run: ~2 minutes
- **Total: ~240 minutes/month** (well under 2,000 free limit)

---

## Support

- **GitHub Pages Docs**: https://docs.github.com/en/pages
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Chart.js Docs**: https://www.chartjs.org/docs/

For issues with this dashboard:
- Check existing issues: https://github.com/[org]/[repo]/issues
- Create new issue if needed

---

**You're all set! Your Work Hours Dashboard should now be live and auto-updating every 6 hours.** 🎉
