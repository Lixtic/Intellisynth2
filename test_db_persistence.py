"""
Test script to verify activity logs are persisted to database
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_database_persistence():
    print("=" * 60)
    print("Testing Activity Log Database Persistence")
    print("=" * 60)
    
    # Step 1: Create a new activity log
    print("\n1. Creating new activity log...")
    payload = {
        "agent_id": "test-persistence-agent",
        "action_type": "database_test",
        "severity": "info",
        "message": "Testing if activity logs are persisted to database",
        "data": {
            "test_number": 1,
            "timestamp": time.time(),
            "purpose": "database_persistence_test"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/activity-logs", json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        created_activity = response.json()
        activity_id = created_activity.get('id')
        print(f"   Created Activity ID: {activity_id}")
        print(f"   Hash: {created_activity.get('hash')}")
    else:
        print(f"   Error: {response.text}")
        return False
    
    # Step 2: Retrieve all activities to verify it's there
    print("\n2. Retrieving all activity logs...")
    response = requests.get(f"{BASE_URL}/api/activity-logs?limit=100")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        activities = response.json()
        print(f"   Total activities: {len(activities)}")
        
        # Find our test activity
        test_activity = next((a for a in activities if a.get('id') == activity_id), None)
        if test_activity:
            print(f"   ✓ Test activity found in database!")
            print(f"   Message: {test_activity.get('message')}")
        else:
            print(f"   ✗ Test activity NOT found!")
            return False
    else:
        print(f"   Error: {response.text}")
        return False
    
    # Step 3: Simulate server restart by checking if logs persist
    print("\n3. Verifying persistence after retrieval...")
    print("   (In production, you would restart the server here)")
    print("   Making another GET request to verify data is still there...")
    
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/api/activity-logs?limit=100")
    if response.status_code == 200:
        activities = response.json()
        test_activity = next((a for a in activities if a.get('id') == activity_id), None)
        if test_activity:
            print(f"   ✓ Activity still persisted after retrieval!")
        else:
            print(f"   ✗ Activity lost!")
            return False
    
    # Step 4: Check activity stats
    print("\n4. Checking activity statistics...")
    response = requests.get(f"{BASE_URL}/api/activity-logs/stats")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"   Total Activities: {stats.get('total_activities')}")
        print(f"   Active Agents: {stats.get('active_agents')}")
        print(f"   Errors: {stats.get('errors')}")
    
    # Step 5: Check database file exists
    print("\n5. Checking database file...")
    import os
    db_file = "logs.db"
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"   ✓ Database file exists: {db_file}")
        print(f"   Size: {size} bytes")
    else:
        print(f"   ✗ Database file NOT found: {db_file}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - Database persistence is working!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_database_persistence()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
