#!/usr/bin/env python3
"""
Direct test of activity logger to verify it's working
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('app')

from app.services.activity_logger import activity_logger

async def test_activity_logger():
    """Test if activity logger is working"""
    print("🧪 Testing activity logger...")
    
    try:
        # Test logging an activity
        result = await activity_logger.log_activity(
            agent_id="test_agent",
            action_type="test",
            message="Direct test activity",
            severity="info",
            data={"test": True}
        )
        
        print(f"✅ Activity logged successfully: {result.get('id', 'unknown')}")
        
        # Test retrieving activities
        activities = activity_logger.get_activities(limit=5)
        print(f"📋 Retrieved {len(activities)} activities:")
        
        for activity in activities:
            print(f"  - {activity.get('agent_id')}: {activity.get('message')}")
        
        if len(activities) == 0:
            print("❌ No activities found - there might be a database issue")
        
    except Exception as e:
        print(f"❌ Error testing activity logger: {e}")

if __name__ == "__main__":
    asyncio.run(test_activity_logger())
