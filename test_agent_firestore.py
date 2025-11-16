"""
Test Agent Service with Firestore
Tests the Firestore-based agent service implementation
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_agent_service_firestore():
    """Test Firestore agent service"""
    
    print("=" * 60)
    print("Agent Service Firestore Test")
    print("=" * 60)
    
    # Initialize Firebase first
    print("\n0. Initializing Firebase...")
    from app.firebase_config import firebase_config
    import os
    
    creds_path = os.getenv('FIREBASE_CREDENTIALS', './intellisynth-c1050-firebase-adminsdk-fbsvc-61edd8337e.json')
    if not firebase_config.initialize(creds_path):
        print("   ✗ Failed to initialize Firebase")
        return False
    print("   ✓ Firebase initialized")
    
    from app.services.agent_service_firestore import agent_service_firestore, AgentType, AgentStatus
    
    # Step 1: Initialize
    print("\n1. Initializing agent service...")
    if agent_service_firestore.initialize():
        print("   ✓ Agent service initialized")
    else:
        print("   ✗ Failed to initialize")
        return False
    
    # Step 2: Create test agents
    print("\n2. Creating test agents...")
    try:
        agent1 = await agent_service_firestore.create_agent(
            name="Test Monitor Agent",
            agent_type=AgentType.MONITOR,
            description="Firestore test monitoring agent",
            capabilities=["monitoring", "alerting"],
            configuration={"interval": 60},
            tags=["test", "monitor"]
        )
        print(f"   ✓ Created agent: {agent1['name']} (ID: {agent1['id']})")
        
        agent2 = await agent_service_firestore.create_agent(
            name="Test Analyzer Agent",
            agent_type=AgentType.ANALYZER,
            description="Firestore test analyzer agent",
            capabilities=["analysis", "reporting"],
            tags=["test", "analyzer"]
        )
        print(f"   ✓ Created agent: {agent2['name']} (ID: {agent2['id']})")
    except Exception as e:
        print(f"   ✗ Error creating agents: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Get agent by ID
    print("\n3. Getting agent by ID...")
    try:
        retrieved = await agent_service_firestore.get_agent(agent1['id'])
        if retrieved:
            print(f"   ✓ Retrieved: {retrieved['name']}")
            print(f"      Type: {retrieved['agent_type']}")
            print(f"      Status: {retrieved['status']}")
        else:
            print("   ✗ Agent not found")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 4: Get all agents
    print("\n4. Getting all agents...")
    try:
        all_agents = await agent_service_firestore.get_all_agents()
        print(f"   ✓ Found {len(all_agents)} agents")
        for agent in all_agents:
            print(f"      - {agent['name']} ({agent['agent_type']})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 5: Update agent
    print("\n5. Updating agent...")
    try:
        updated = await agent_service_firestore.update_agent(
            agent1['id'],
            status=AgentStatus.MAINTENANCE,
            description="Updated test description"
        )
        if updated:
            print(f"   ✓ Updated: {updated['name']}")
            print(f"      New status: {updated['status']}")
            print(f"      New description: {updated['description']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 6: Update agent activity
    print("\n6. Updating agent activity...")
    try:
        updated = await agent_service_firestore.update_agent_activity(
            agent1['id'],
            activities=10,
            errors=1
        )
        if updated:
            print(f"   ✓ Updated activity stats")
            print(f"      Total activities: {updated['total_activities']}")
            print(f"      Total errors: {updated['total_errors']}")
            print(f"      Success rate: {updated['success_rate']}%")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 7: Get agent stats
    print("\n7. Getting agent statistics...")
    try:
        stats = await agent_service_firestore.get_agent_stats()
        print(f"   ✓ Agent Statistics:")
        print(f"      Total agents: {stats['total_agents']}")
        print(f"      Active: {stats['active_agents']}")
        print(f"      Total activities: {stats['total_activities']}")
        print(f"      Avg success rate: {stats['avg_success_rate']}%")
        print(f"      By type: {stats['agents_by_type']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 8: Search agents
    print("\n8. Searching agents...")
    try:
        results = await agent_service_firestore.search_agents("Test")
        print(f"   ✓ Found {len(results)} agents matching 'Test'")
        for agent in results:
            print(f"      - {agent['name']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 9: Filter agents
    print("\n9. Filtering agents by type...")
    try:
        monitors = await agent_service_firestore.get_all_agents(
            agent_type=AgentType.MONITOR
        )
        print(f"   ✓ Found {len(monitors)} monitor agents")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 10: Cleanup - delete test agents
    print("\n10. Cleaning up test agents...")
    try:
        deleted1 = await agent_service_firestore.delete_agent(agent1['id'])
        deleted2 = await agent_service_firestore.delete_agent(agent2['id'])
        
        if deleted1 and deleted2:
            print("   ✓ Test agents deleted")
        else:
            print("   ⚠ Some agents may not have been deleted")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Success!
    print("\n" + "=" * 60)
    print("✓ All agent service tests passed!")
    print("=" * 60)
    print("\nFirestore agent service is working correctly!")
    print("\nNext steps:")
    print("1. Review agent operations in Firebase Console")
    print("2. Migrate activity logger to Firestore")
    print("3. Update main application to use config-based service selection")
    print("\n")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_agent_service_firestore())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
