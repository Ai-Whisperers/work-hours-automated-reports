#!/usr/bin/env python3
"""
Script to list all projects in your Clockify workspace and get their IDs.

This helps you find the project ID to use for CLOCKIFY_DEFAULT_PROJECT_ID.

Usage:
    python scripts/get_clockify_project_id.py

Requirements:
    - CLOCKIFY_API_KEY environment variable
    - CLOCKIFY_WORKSPACE_ID environment variable
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config import get_settings
from src.infrastructure.api_clients.clockify_client import ClockifyClient


async def list_projects():
    """List all projects in the workspace with their IDs."""
    try:
        # Load settings
        settings = get_settings()

        print("=" * 70)
        print("  Clockify Projects Listing")
        print("=" * 70)
        print()
        print(f"Workspace ID: {settings.clockify_workspace_id}")
        print()

        # Initialize client
        client = ClockifyClient(settings)

        # Test connection
        print("Testing connection...")
        user = await client.get_current_user()
        print(f"✓ Connected as: {user.get('name', 'Unknown')}")
        print()

        # Fetch all projects (including archived)
        print("Fetching projects...")
        active_projects = await client.get_projects(archived=False)
        archived_projects = await client.get_projects(archived=True)

        # Display active projects
        if active_projects:
            print("─" * 70)
            print("ACTIVE PROJECTS")
            print("─" * 70)
            print()

            for idx, project in enumerate(active_projects, 1):
                project_id = project.get('id', 'N/A')
                project_name = project.get('name', 'Unnamed')
                color = project.get('color', '#000000')
                client_name = project.get('clientName', 'No client')

                print(f"{idx}. {project_name}")
                print(f"   ID: {project_id}")
                print(f"   Color: {color}")
                print(f"   Client: {client_name}")
                print()
        else:
            print("No active projects found.")
            print()

        # Display archived projects
        if archived_projects:
            print("─" * 70)
            print("ARCHIVED PROJECTS")
            print("─" * 70)
            print()

            for idx, project in enumerate(archived_projects, 1):
                project_id = project.get('id', 'N/A')
                project_name = project.get('name', 'Unnamed')

                print(f"{idx}. {project_name}")
                print(f"   ID: {project_id}")
                print()

        # Summary
        print("=" * 70)
        print(f"Total active projects: {len(active_projects)}")
        print(f"Total archived projects: {len(archived_projects)}")
        print("=" * 70)
        print()

        # Instructions
        if active_projects:
            print("To use a project for GitHub commit tracking:")
            print("1. Copy the project ID from above")
            print("2. Add to your .env file:")
            print("   CLOCKIFY_DEFAULT_PROJECT_ID=<project-id>")
            print()
            print("Or for GitHub Actions, add as a secret:")
            print("   Repository Settings → Secrets → New secret")
            print("   Name: CLOCKIFY_DEFAULT_PROJECT_ID")
            print("   Value: <project-id>")
        else:
            print("No projects found. You should create one first:")
            print("1. Go to https://app.clockify.me")
            print("2. Click 'Projects' in the sidebar")
            print("3. Click '+ New Project'")
            print("4. Name it 'GitHub Commits' (or similar)")
            print("5. Save and run this script again")

        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print()
        print("Make sure you have set:")
        print("  - CLOCKIFY_API_KEY")
        print("  - CLOCKIFY_WORKSPACE_ID")
        print()
        return 1


def main():
    """Main entry point."""
    # Check required environment variables
    required_vars = ['CLOCKIFY_API_KEY', 'CLOCKIFY_WORKSPACE_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:", file=sys.stderr)
        for var in missing_vars:
            print(f"  - {var}", file=sys.stderr)
        print()
        print("Set them in your .env file or export them:", file=sys.stderr)
        print(f"  export CLOCKIFY_API_KEY='your-api-key'", file=sys.stderr)
        print(f"  export CLOCKIFY_WORKSPACE_ID='your-workspace-id'", file=sys.stderr)
        return 1

    # Run async function
    return asyncio.run(list_projects())


if __name__ == '__main__':
    sys.exit(main())
