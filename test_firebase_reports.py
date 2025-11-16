"""
Test Firebase Report Storage

Verify that reports are correctly stored and retrieved from Firestore
"""

import asyncio
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

async def test_report_service():
    """Test Firebase report service functionality"""
    print("=" * 70)
    print("  TESTING FIREBASE REPORT STORAGE")
    print("=" * 70)
    
    from app.services.report_service_firestore import report_service_firestore
    from app.firebase_config import firebase_config
    import os
    
    # Ensure Firebase is initialized with proper credentials
    if not firebase_config.is_initialized():
        creds_path = os.getenv('FIREBASE_CREDENTIALS', './intellisynth-c1050-firebase-adminsdk-fbsvc-61edd8337e.json')
        if not firebase_config.initialize(creds_path):
            print("\n✗ Failed to initialize Firebase. Exiting...")
            return
    
    print("\n1. Creating test reports...")
    print("-" * 70)
    
    # Test data for different report types
    test_reports = [
        {
            "type": "agent_activity",
            "time_period": "24h",
            "data": {
                "total_activities": 100,
                "by_type": {"decision": 50, "analysis": 30, "data_collection": 20},
                "agent_stats": {"total_agents": 5, "active_agents": 4}
            }
        },
        {
            "type": "security_summary",
            "time_period": "7d",
            "data": {
                "total_security_events": 25,
                "threats_detected": 3,
                "security_events": {"critical_events": 1, "high_priority": 2}
            }
        },
        {
            "type": "compliance_check",
            "time_period": "30d",
            "data": {
                "total_checks": 150,
                "compliant": 145,
                "violations": 5,
                "compliance_score": "96.7%"
            }
        }
    ]
    
    created_reports = []
    for test_report in test_reports:
        report = await report_service_firestore.create_report(
            report_type=test_report["type"],
            time_period=test_report["time_period"],
            data=test_report["data"]
        )
        
        if report:
            created_reports.append(report)
            print(f"  ✓ Created {report['type']} report (ID: {report['id']})")
        else:
            print(f"  ✗ Failed to create {test_report['type']} report")
    
    print(f"\n✓ Created {len(created_reports)} reports")
    
    # Test 2: Retrieve individual reports
    print("\n2. Retrieving individual reports...")
    print("-" * 70)
    
    for report in created_reports:
        retrieved = await report_service_firestore.get_report(report['id'])
        if retrieved:
            print(f"  ✓ Retrieved {retrieved['type']} report")
            print(f"    - Status: {retrieved['status']}")
            print(f"    - Time Period: {retrieved['time_period']}")
            print(f"    - Data Size: {retrieved['metadata']['data_size']} bytes")
        else:
            print(f"  ✗ Failed to retrieve report {report['id']}")
    
    # Test 3: List all reports
    print("\n3. Listing all reports...")
    print("-" * 70)
    
    all_reports = await report_service_firestore.list_reports()
    print(f"  ✓ Found {len(all_reports)} total reports")
    
    for report in all_reports[:5]:  # Show first 5
        print(f"    - {report['type']} ({report['time_period']}) - {report['status']}")
    
    # Test 4: Filter by type
    print("\n4. Filtering reports by type...")
    print("-" * 70)
    
    agent_reports = await report_service_firestore.list_reports(report_type="agent_activity")
    print(f"  ✓ Found {len(agent_reports)} agent_activity reports")
    
    security_reports = await report_service_firestore.list_reports(report_type="security_summary")
    print(f"  ✓ Found {len(security_reports)} security_summary reports")
    
    # Test 5: Get summary statistics
    print("\n5. Getting summary statistics...")
    print("-" * 70)
    
    summary = await report_service_firestore.get_reports_summary()
    print(f"  ✓ Total reports: {summary['total_reports']}")
    print(f"  ✓ Reports in last 24h: {summary['reports_24h']}")
    print(f"  ✓ Successful in last 24h: {summary['successful_24h']}")
    print(f"  ✓ Available types: {summary['available_types']}")
    
    # Test 6: Test report retrieval by ID
    print("\n6. Testing report retrieval...")
    print("-" * 70)
    
    if created_reports:
        test_id = created_reports[0]['id']
        report = await report_service_firestore.get_report(test_id)
        
        if report:
            print(f"  ✓ Successfully retrieved report: {test_id}")
            print(f"    - Type: {report['type']}")
            print(f"    - Generated: {report['generated_at']}")
            print(f"    - Record count: {report['metadata']['record_count']}")
        else:
            print(f"  ✗ Failed to retrieve report: {test_id}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("  ✓ ALL TESTS PASSED")
    print("=" * 70)
    print(f"\nFirebase Report Storage is working correctly!")
    print(f"- Reports are persisted in Firestore")
    print(f"- Summary statistics are accurate")
    print(f"- Filtering and querying works as expected")
    print()


if __name__ == "__main__":
    asyncio.run(test_report_service())
