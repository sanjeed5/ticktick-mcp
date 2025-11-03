#!/usr/bin/env python3
"""
Functional test for TickTick MCP server tools.
Tests filter_tasks and other tools with actual API calls.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env
from ticktick_mcp.src.server import (
    initialize_client, filter_tasks, get_projects, 
    get_project_tasks, create_task, engaged, next_actions
)

async def test_tools():
    """Test the actual tool functions."""
    
    print("=" * 70)
    print("Functional Test: TickTick MCP Server Tools")
    print("=" * 70)
    
    # Initialize client
    print("\n1. Initializing TickTick client...")
    if not initialize_client():
        print("❌ Failed to initialize client. Check your .env file.")
        return False
    print("✅ Client initialized successfully")
    
    # Test get_projects
    print("\n2. Testing get_projects tool...")
    try:
        result = await get_projects()
        if "Error" in result or "Failed" in result:
            print(f"❌ Error: {result}")
            return False
        print("✅ get_projects working")
        print(f"   Result preview: {result[:100]}...")
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    # Test filter_tasks with different parameters
    print("\n3. Testing filter_tasks tool...")
    
    test_cases = [
        ("all tasks", {}),
        ("overdue tasks", {"date_filter": "overdue"}),
        ("today tasks", {"date_filter": "today"}),
        ("high priority", {"priority": 5}),
        ("all tasks (default)", {"date_filter": "all"}),
    ]
    
    for test_name, params in test_cases:
        try:
            print(f"   Testing: {test_name}")
            result = await filter_tasks(**params)
            if "Error" in result or "Failed" in result:
                print(f"      ⚠️  Warning: {result[:100]}")
            else:
                print(f"      ✅ Success - returned {len(result)} characters")
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            return False
    
    # Test filter_tasks with invalid parameters
    print("\n4. Testing filter_tasks validation...")
    try:
        result = await filter_tasks(date_filter="invalid")
        if "Invalid date_filter" in result:
            print("   ✅ Invalid date_filter properly rejected")
        else:
            print(f"   ⚠️  Unexpected response: {result[:100]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    try:
        result = await filter_tasks(priority=99)
        if "Invalid priority" in result:
            print("   ✅ Invalid priority properly rejected")
        else:
            print(f"   ⚠️  Unexpected response: {result[:100]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test prompts
    print("\n5. Testing prompts...")
    try:
        result = await engaged()
        if isinstance(result, list) and len(result) > 0:
            print("   ✅ engaged prompt returns valid format")
            if 'role' in result[0] and 'content' in result[0]:
                print("   ✅ Prompt message structure correct")
        else:
            print(f"   ❌ Invalid format: {type(result)}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    try:
        result = await next_actions()
        if isinstance(result, list) and len(result) > 0:
            print("   ✅ next_actions prompt returns valid format")
            if 'role' in result[0] and 'content' in result[0]:
                print("   ✅ Prompt message structure correct")
        else:
            print(f"   ❌ Invalid format: {type(result)}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test get_project_tasks if we have projects
    print("\n6. Testing get_project_tasks...")
    try:
        projects_result = await get_projects()
        if "inbox" in projects_result.lower() or "project" in projects_result.lower():
            # Try to get inbox tasks
            result = await get_project_tasks("inbox")
            if "Error" not in result and "Failed" not in result:
                print("   ✅ get_project_tasks('inbox') working")
            else:
                print(f"   ⚠️  Note: {result[:100]}")
        else:
            print("   ⚠️  Could not determine project structure")
    except Exception as e:
        print(f"   ⚠️  Exception (non-critical): {e}")
    
    print("\n" + "=" * 70)
    print("✅ All functional tests completed!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_tools())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
