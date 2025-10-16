#!/usr/bin/env python3
"""
Quick debug script to test Clockify API and verify time entries are being created.

Usage:
    export CLOCKIFY_API_KEY=your_key
    export CLOCKIFY_WORKSPACE_ID=your_workspace_id
    python debug_clockify.py
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set minimal required env vars for Settings to load
os.environ.setdefault('ADO_ORG', 'test')
os.environ.setdefault('ADO_PROJECT', 'test')
os.environ.setdefault('ADO_PAT', 'test')

from src.infrastructure.config import get_settings
from src.infrastructure.api_clients.clockify_sync_adapter import ClockifySyncAdapter


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def main():
    """Main debug function."""
    print_section("CLOCKIFY API DEBUG TOOL")

    # Check environment variables
    print("\n📋 Checking environment variables...")
    api_key = os.getenv('CLOCKIFY_API_KEY')
    workspace_id = os.getenv('CLOCKIFY_WORKSPACE_ID')
    project_id = os.getenv('CLOCKIFY_DEFAULT_PROJECT_ID')

    if not api_key:
        print("❌ CLOCKIFY_API_KEY not set!")
        print("   Run: export CLOCKIFY_API_KEY='your-api-key'")
        return 1

    if not workspace_id:
        print("❌ CLOCKIFY_WORKSPACE_ID not set!")
        print("   Run: export CLOCKIFY_WORKSPACE_ID='your-workspace-id'")
        return 1

    print(f"✓ CLOCKIFY_API_KEY: {api_key[:10]}..." + "*" * 20)
    print(f"✓ CLOCKIFY_WORKSPACE_ID: {workspace_id}")
    print(f"✓ CLOCKIFY_DEFAULT_PROJECT_ID: {project_id or 'NOT SET (optional)'}")

    # Load settings
    print("\n🔧 Loading settings...")
    try:
        settings = get_settings()
        print("✓ Settings loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return 1

    # Initialize client
    print("\n🔌 Initializing Clockify client...")
    try:
        client = ClockifySyncAdapter(settings)
        print("✓ Client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1

    # Test connection
    print("\n🌐 Testing connection to Clockify...")
    try:
        if client.test_connection():
            print("✓ Connection successful!")
        else:
            print("❌ Connection failed!")
            return 1
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return 1

    # Get user info
    print("\n👤 Fetching user information...")
    try:
        user = client.get_current_user()
        print(f"✓ Authenticated as: {user.get('name', 'Unknown')}")
        print(f"  Email: {user.get('email', 'N/A')}")
        print(f"  User ID: {user.get('id', 'N/A')}")
        print(f"  Status: {user.get('status', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to get user info: {e}")
        return 1

    # Create test entry
    print("\n📝 Creating test time entry...")
    print("   Description: 'DEBUG TEST - Please delete me'")

    now = datetime.utcnow()
    start_time = now - timedelta(hours=1)
    end_time = now

    print(f"   Start: {start_time.isoformat()}Z")
    print(f"   End: {end_time.isoformat()}Z")
    print(f"   Project: {project_id or 'None (no project)'}")

    try:
        response = client.create_time_entry_with_range(
            start=start_time,
            end=end_time,
            description="🔍 DEBUG TEST - Please delete me",
            project_id=project_id,
        )

        if response and isinstance(response, dict):
            print("\n✅ TIME ENTRY CREATED SUCCESSFULLY!")
            print("\n📊 Response Details:")
            print(f"   Entry ID: {response.get('id', 'N/A')}")
            print(f"   Description: {response.get('description', 'N/A')}")

            time_interval = response.get('timeInterval', {})
            print(f"   Start: {time_interval.get('start', 'N/A')}")
            print(f"   End: {time_interval.get('end', 'N/A')}")
            print(f"   Duration: {time_interval.get('duration', 'N/A')}")

            if 'projectId' in response:
                print(f"   Project ID: {response['projectId']}")
            else:
                print(f"   Project ID: None (no project assigned)")

            if 'workspaceId' in response:
                print(f"   Workspace ID: {response['workspaceId']}")

            print_section("✅ SUCCESS - CHECK CLOCKIFY UI NOW")
            print("\n🔍 Where to look:")
            print("   1. Go to https://app.clockify.me")
            print("   2. Make sure you're in the correct workspace")
            print("   3. Click 'Time Tracker' or 'Timesheet' in left sidebar")
            print("   4. Look for entry: '🔍 DEBUG TEST - Please delete me'")
            print("   5. Check today's date (or last hour)")
            print("\n   If you DON'T see it:")
            print("   - Try 'Reports' → 'Detailed' with date range 'Today'")
            print("   - Clear all filters")
            print(f"   - Make sure workspace ID matches: {workspace_id}")
            print("\n   📌 Entry ID for reference: " + response.get('id', 'N/A'))

            return 0
        else:
            print(f"\n⚠️ Unexpected response format: {response}")
            return 1

    except Exception as e:
        print(f"\n❌ Failed to create time entry!")
        print(f"   Error: {e}")
        print(f"   Type: {type(e).__name__}")

        if hasattr(e, 'response'):
            print(f"   HTTP Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"   Response: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    print("\n" + "=" * 70)
    sys.exit(exit_code)
