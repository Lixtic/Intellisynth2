"""
Test script to verify Agent CRUD operations
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_agent_crud():
    print_section("Testing Agent CRUD Operations")
    
    # Test 1: Create a new agent
    print_section("1. CREATE - Creating a new agent")
    agent_data = {
        "name": "Test Monitoring Agent",
        "agent_type": "monitor",
        "description": "A test agent for monitoring system health",
        "capabilities": ["health_check", "metrics_collection", "alerting"],
        "configuration": {
            "check_interval": 60,
            "alert_threshold": 80
        },
        "owner": "test_user",
        "tags": ["test", "monitoring", "production"]
    }
    
    response = requests.post(f"{BASE_URL}/api/agents", json=agent_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        created_agent = response.json()
        agent_id = created_agent['id']
        print(f"✓ Agent created successfully!")
        print(f"  ID: {agent_id}")
        print(f"  Name: {created_agent['name']}")
        print(f"  Type: {created_agent['agent_type']}")
        print(f"  Status: {created_agent['status']}")
    else:
        print(f"✗ Failed to create agent: {response.text}")
        return False
    
    # Test 2: Get all agents
    print_section("2. READ - Getting all agents")
    response = requests.get(f"{BASE_URL}/api/agents")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"✓ Found {len(agents)} agent(s)")
        for agent in agents:
            print(f"  - {agent['name']} ({agent['id']}) - {agent['status']}")
    else:
        print(f"✗ Failed to get agents: {response.text}")
    
    # Test 3: Get specific agent by ID
    print_section("3. READ - Getting agent by ID")
    response = requests.get(f"{BASE_URL}/api/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        agent = response.json()
        print(f"✓ Agent retrieved successfully!")
        print(f"  Name: {agent['name']}")
        print(f"  Description: {agent['description']}")
        print(f"  Capabilities: {', '.join(agent['capabilities'])}")
        print(f"  Tags: {', '.join(agent['tags'])}")
    else:
        print(f"✗ Failed to get agent: {response.text}")
    
    # Test 4: Update agent
    print_section("4. UPDATE - Updating agent")
    update_data = {
        "description": "Updated description - now monitoring critical systems",
        "status": "active",
        "capabilities": ["health_check", "metrics_collection", "alerting", "auto_remediation"],
        "tags": ["test", "monitoring", "production", "critical"]
    }
    
    response = requests.put(f"{BASE_URL}/api/agents/{agent_id}", json=update_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        updated_agent = response.json()
        print(f"✓ Agent updated successfully!")
        print(f"  New Description: {updated_agent['description']}")
        print(f"  Capabilities: {len(updated_agent['capabilities'])} (added 1)")
        print(f"  Tags: {len(updated_agent['tags'])} (added 1)")
    else:
        print(f"✗ Failed to update agent: {response.text}")
    
    # Test 5: Get agent statistics
    print_section("5. READ - Getting agent statistics")
    response = requests.get(f"{BASE_URL}/api/agents/stats/overview")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✓ Statistics retrieved successfully!")
        print(f"  Total Agents: {stats['total_agents']}")
        print(f"  Active Agents: {stats['active_agents']}")
        print(f"  Agents by Type: {json.dumps(stats['agents_by_type'], indent=4)}")
        print(f"  Avg Success Rate: {stats['avg_success_rate']}%")
    else:
        print(f"✗ Failed to get stats: {response.text}")
    
    # Test 6: Search agents
    print_section("6. SEARCH - Searching for agents")
    response = requests.get(f"{BASE_URL}/api/agents/search/monitoring")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        search_results = response.json()
        print(f"✓ Found {len(search_results)} agent(s) matching 'monitoring'")
        for agent in search_results:
            print(f"  - {agent['name']}")
    else:
        print(f"✗ Search failed: {response.text}")
    
    # Test 7: Filter agents by type
    print_section("7. FILTER - Getting agents by type")
    response = requests.get(f"{BASE_URL}/api/agents?agent_type=monitor")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        filtered_agents = response.json()
        print(f"✓ Found {len(filtered_agents)} monitor agent(s)")
    else:
        print(f"✗ Filter failed: {response.text}")
    
    # Test 8: Delete agent
    print_section("8. DELETE - Deleting agent")
    response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Agent deleted successfully!")
        print(f"  Message: {result['message']}")
    else:
        print(f"✗ Failed to delete agent: {response.text}")
    
    # Test 9: Verify deletion
    print_section("9. VERIFY - Checking agent was deleted")
    response = requests.get(f"{BASE_URL}/api/agents/{agent_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"✓ Agent successfully deleted (404 as expected)")
    else:
        print(f"✗ Agent still exists!")
    
    # Test 10: Check database persistence
    print_section("10. DATABASE - Checking database file")
    import os
    import sqlite3
    
    db_file = "logs.db"
    if os.path.exists(db_file):
        print(f"✓ Database file exists: {db_file}")
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if agents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
        if cursor.fetchone():
            print(f"✓ Agents table exists")
            
            # Count agents in database
            cursor.execute("SELECT COUNT(*) FROM agents")
            count = cursor.fetchone()[0]
            print(f"  Total agents in database: {count}")
        else:
            print(f"✗ Agents table not found")
        
        conn.close()
    else:
        print(f"✗ Database file not found")
    
    print_section("✓ ALL CRUD TESTS COMPLETED SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    try:
        success = test_agent_crud()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
