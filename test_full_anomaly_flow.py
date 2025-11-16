#!/usr/bin/env python3
"""
Generate test anomaly data and immediately test anomaly detection
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append('app')

from app.services.activity_logger import activity_logger
from app.services.anomaly_detection import AnomalyDetectionService

async def test_full_anomaly_flow():
    """Generate test data and immediately run anomaly detection"""
    print("🔧 Generating test anomaly data...")
    
    # 1. Generate some error-prone activities  
    for i in range(5):
        await activity_logger.log_activity(
            agent_id="error_prone_agent",
            action_type="error",
            message=f"Critical database error #{i}",
            severity="high",
            data={
                "error_code": f"DB_ERR_{i:03d}",
                "execution_time": 15000 + (i * 2000),
                "failure_reason": "Connection timeout",
                "retry_count": i + 1
            }
        )
        
    # 2. Generate hyperactive agent behavior
    for i in range(15):
        await activity_logger.log_activity(
            agent_id="hyperactive_agent", 
            action_type="decision",
            message=f"Rapid decision #{i}",
            severity="info",
            data={
                "execution_time": 100 + (i * 5),
                "confidence": 0.4,
                "decision_type": "trade"
            }
        )
    
    # 3. Generate slow performance
    await activity_logger.log_activity(
        agent_id="slow_agent",
        action_type="computation", 
        message="Very slow computation",
        severity="medium",
        data={
            "execution_time": 50000,  # 50 seconds!
            "cpu_usage": 95.0,
            "memory_usage": 89.2
        }
    )
    
    # 4. Generate low confidence decisions
    for i in range(4):
        await activity_logger.log_activity(
            agent_id="uncertain_agent",
            action_type="decision",
            message=f"Low confidence decision #{i}",
            severity="warning",
            data={
                "execution_time": 2000,
                "confidence": 0.2 + (i * 0.05),  # Very low confidence
                "uncertainty_factors": ["insufficient_data", "conflicting_signals"]
            }
        )
    
    print(f"✅ Generated test anomaly data")
    
    # Verify activities were stored
    activities = activity_logger.get_activities(limit=10)
    print(f"📋 Total activities in log: {len(activities)}")
    
    for activity in activities:
        agent_id = activity.get('agent_id')
        message = activity.get('message', 'No message')
        severity = activity.get('severity', 'unknown')
        print(f"  - {agent_id} [{severity}]: {message}")
    
    print(f"\n🔍 Running anomaly detection...")
    
    # Test anomaly detection
    anomaly_service = AnomalyDetectionService()
    result = await anomaly_service.detect_anomalies()
    
    print(f"🎯 Anomaly Detection Results:")
    print(f"  Total anomalies: {result['total_anomalies']}")
    print(f"  Severity breakdown: {result['severity_breakdown']}")
    print(f"  Methods used: {result['methods_used']}")
    print(f"  Average confidence: {result['avg_confidence']:.2f}")
    
    if result['anomalies']:
        print(f"\n📊 Detected Anomalies:")
        for i, anomaly in enumerate(result['anomalies'][:5]):  # Show first 5
            print(f"  {i+1}. [{anomaly.get('severity', 'unknown')}] {anomaly.get('type', 'unknown')}")
            print(f"     Description: {anomaly.get('description', 'No description')}")
            print(f"     Confidence: {anomaly.get('confidence', 0):.2f}")
    else:
        print("  No anomalies detected")
        
    if 'error' in result:
        print(f"❌ Error in anomaly detection: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_full_anomaly_flow())
