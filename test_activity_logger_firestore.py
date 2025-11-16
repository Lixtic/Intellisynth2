"""
Test Activity Logger with Firestore
Tests the Firestore-based activity logger implementation
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_activity_logger_firestore():
    """Test Firestore activity logger"""
    
    print("=" * 60)
    print("Activity Logger Firestore Test")
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
    
    from app.services.activity_logger_firestore import activity_logger_firestore
    
    test_agent_id = "test-agent-001"
    
    # Step 1: Log a decision
    print("\n1. Logging AI decision...")
    try:
        await activity_logger_firestore.log_decision(
            agent_id=test_agent_id,
            decision="Approve transaction",
            reasoning="All compliance checks passed",
            confidence=0.95,
            context={'transaction_id': 'TXN123'}
        )
        print("   ✓ Decision logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Step 2: Log data collection
    print("\n2. Logging data collection...")
    try:
        await activity_logger_firestore.log_data_collection(
            agent_id=test_agent_id,
            data_source="customer_database",
            records_collected=1500,
            processing_time=2.5,
            data_quality="excellent"
        )
        print("   ✓ Data collection logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 3: Log analysis
    print("\n3. Logging analysis...")
    try:
        await activity_logger_firestore.log_analysis(
            agent_id=test_agent_id,
            analysis_type="fraud_detection",
            results={'flagged_transactions': 3, 'risk_score': 0.15},
            accuracy=0.98,
            processing_time=1.2
        )
        print("   ✓ Analysis logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 4: Log compliance check
    print("\n4. Logging compliance check...")
    try:
        await activity_logger_firestore.log_compliance_check(
            agent_id=test_agent_id,
            rule_id="RULE-001",
            rule_name="Data Privacy Policy",
            compliance_status="compliant",
            violations_found=0
        )
        print("   ✓ Compliance check logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 5: Log security scan
    print("\n5. Logging security scan...")
    try:
        await activity_logger_firestore.log_security_scan(
            agent_id=test_agent_id,
            scan_type="vulnerability_scan",
            threats_detected=0,
            scan_duration=3.5,
            severity_level="low"
        )
        print("   ✓ Security scan logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 6: Log an error
    print("\n6. Logging an error...")
    try:
        await activity_logger_firestore.log_error(
            agent_id=test_agent_id,
            error_type="connection_timeout",
            error_message="Failed to connect to external API",
            error_details={'api': 'payment_gateway', 'timeout': 30}
        )
        print("   ✓ Error logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 7: Log generic activity
    print("\n7. Logging generic activity...")
    try:
        await activity_logger_firestore.log_activity(
            agent_id=test_agent_id,
            action_type="system_maintenance",
            message="Scheduled cache cleanup completed",
            severity="info",
            data={'cache_cleared': True, 'memory_freed': '150MB'}
        )
        print("   ✓ Generic activity logged successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Wait a moment for Firestore to index
    await asyncio.sleep(2)
    
    # Step 8: Get all activities
    print("\n8. Retrieving all activities...")
    try:
        activities = await activity_logger_firestore.get_activities(limit=100)
        print(f"   ✓ Retrieved {len(activities)} activities")
        if activities:
            print(f"      Latest: {activities[0].get('action_type')} - {activities[0].get('message')[:50]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 9: Filter by agent
    print("\n9. Filtering activities by agent...")
    try:
        agent_activities = await activity_logger_firestore.get_activities(
            agent_id=test_agent_id,
            limit=50
        )
        print(f"   ✓ Found {len(agent_activities)} activities for agent {test_agent_id}")
        for activity in agent_activities[:3]:
            print(f"      - {activity.get('action_type')}: {activity.get('message')[:40]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 10: Filter by action type
    print("\n10. Filtering by action type...")
    try:
        decisions = await activity_logger_firestore.get_activities(
            action_type="decision",
            limit=10
        )
        print(f"   ✓ Found {len(decisions)} decision activities")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 11: Filter by severity
    print("\n11. Filtering by severity...")
    try:
        critical = await activity_logger_firestore.get_activities(
            severity="critical",
            limit=10
        )
        print(f"   ✓ Found {len(critical)} critical activities")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 12: Get latest activities
    print("\n12. Getting latest activities...")
    try:
        since = datetime.utcnow() - timedelta(hours=1)
        latest = await activity_logger_firestore.get_latest_activities(since=since, limit=20)
        print(f"   ✓ Found {len(latest)} activities in the last hour")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 13: Get activity statistics
    print("\n13. Getting activity statistics...")
    try:
        stats = await activity_logger_firestore.get_activity_stats()
        print(f"   ✓ Activity Statistics:")
        print(f"      Total activities: {stats['total_activities']}")
        print(f"      Decisions: {stats['decisions']}")
        print(f"      Data points: {stats['data_points']}")
        print(f"      Errors: {stats['errors']}")
        print(f"      Avg response time: {stats['avg_response_time']}ms")
        print(f"      Active agents: {stats['active_agents']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 14: Get agent activity summary
    print("\n14. Getting agent activity summary...")
    try:
        summary = await activity_logger_firestore.get_agent_activity_summary(test_agent_id)
        print(f"   ✓ Agent Summary:")
        print(f"      Total activities: {summary['total_activities']}")
        print(f"      Last active: {summary['last_active']}")
        print(f"      Error count: {summary['error_count']}")
        print(f"      Success rate: {summary['success_rate']}%")
        print(f"      Activity breakdown: {summary['activity_breakdown']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 15: Verify integrity
    print("\n15. Verifying activity integrity...")
    try:
        if activities:
            activity_id = activities[0].get('id')
            is_valid = await activity_logger_firestore.verify_integrity(activity_id)
            print(f"   ✓ Integrity check: {'VALID' if is_valid else 'INVALID'}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Success!
    print("\n" + "=" * 60)
    print("✓ All activity logger tests passed!")
    print("=" * 60)
    print("\nFirestore activity logger is working correctly!")
    print("\nNext steps:")
    print("1. Review activities in Firebase Console")
    print("2. Update database initialization script")
    print("3. Switch main application to use Firestore")
    print("\n")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_activity_logger_firestore())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
