#!/usr/bin/env python3
"""
Simple script to list Clockify projects without dependencies.

Usage:
    CLOCKIFY_API_KEY=xxx CLOCKIFY_WORKSPACE_ID=yyy python scripts/get_project_id_simple.py
"""

import os
import sys
import httpx


def main():
    # Get credentials from environment
    api_key = os.getenv('CLOCKIFY_API_KEY')
    workspace_id = os.getenv('CLOCKIFY_WORKSPACE_ID')

    if not api_key:
        print("❌ Error: CLOCKIFY_API_KEY environment variable not set", file=sys.stderr)
        return 1

    if not workspace_id:
        print("❌ Error: CLOCKIFY_WORKSPACE_ID environment variable not set", file=sys.stderr)
        return 1

    # Setup API client
    base_url = "https://api.clockify.me/api/v1"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    print("=" * 70)
    print("  Clockify Projects Listing")
    print("=" * 70)
    print()
    print(f"Workspace ID: {workspace_id}")
    print()

    try:
        # Test connection
        print("Testing connection...")
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{base_url}/user", headers=headers)
            response.raise_for_status()
            user = response.json()
            print(f"✓ Connected as: {user.get('name', 'Unknown')}")
            print()

            # Fetch active projects
            print("Fetching projects...")
            response = client.get(
                f"{base_url}/workspaces/{workspace_id}/projects",
                headers=headers,
                params={"archived": "false"}
            )
            response.raise_for_status()
            projects = response.json()

            # Display projects
            if projects:
                print("─" * 70)
                print("ACTIVE PROJECTS")
                print("─" * 70)
                print()

                for idx, project in enumerate(projects, 1):
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

            # Summary
            print("=" * 70)
            print(f"Total active projects: {len(projects)}")
            print("=" * 70)
            print()

            # Instructions
            if projects:
                print("To use a project for GitHub commit tracking:")
                print("1. Copy the project ID from above")
                print("2. Set as environment variable:")
                print("   CLOCKIFY_DEFAULT_PROJECT_ID=<project-id>")
                print()
                print("Or for GitHub Actions, add as a secret:")
                print("   Repository Settings → Secrets → New secret")
                print("   Name: CLOCKIFY_DEFAULT_PROJECT_ID")
                print("   Value: <project-id>")
            else:
                print("No projects found. Create one first:")
                print("1. Go to https://app.clockify.me")
                print("2. Click 'Projects' in the sidebar")
                print("3. Click '+ New Project'")
                print("4. Name it 'GitHub Commits'")
                print("5. Save and run this script again")

            print()
            return 0

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
