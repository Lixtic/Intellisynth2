#!/usr/bin/env python3
"""
Generate test activities that will trigger anomalies for demonstration purposes.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append('app')

from app.services.activity_logger import activity_logger

async def generate_test_anomalies():
    """Generate various types of activities that should trigger anomaly detection"""
    print("🔧 Generating test anomalies for demonstration...")
    
    # 1. Generate high error rate activities
    print("1️⃣ Generating high error rate activities...")
    for i in range(8):
        await activity_logger.log_activity(
            agent_id="error_prone_agent",
            action_type="error", 
            message=f"critical_error_{i}",
            severity="high",
            data={
                "error_code": f"E00{i}",
                "execution_time": 15000 + (i * 1000),  # Increasingly slow
                "failure_reason": "Database connection timeout",
                "retry_count": i + 1
            }
        )
    
    # 2. Generate unusually high activity from one agent
    print("2️⃣ Generating suspicious high-activity pattern...")
    for i in range(25):
        await activity_logger.log_activity(
            agent_id="hyperactive_agent",
            action_type="decision",
            message=f"rapid_decision_{i}",
            severity="info",
            data={
                "execution_time": 50 + (i * 2),  # Fast but frequent
                "confidence": 0.3 + (i * 0.01),  # Low confidence initially
                "decision_type": "automated_trade" if i % 3 == 0 else "data_analysis"
            }
        )
    
    # 3. Generate slow execution anomalies
    print("3️⃣ Generating performance anomalies...")
    for i in range(3):
        await activity_logger.log_activity(
            agent_id="slow_processor",
            action_type="computation",
            message=f"heavy_computation_{i}",
            severity="medium",
            data={
                "execution_time": 45000 + (i * 5000),  # Very slow
                "cpu_usage": 95.5,
                "memory_usage": 87.2,
                "processing_complexity": "high"
            }
        )
    
    # 4. Generate behavioral anomalies (low confidence decisions)
    print("4️⃣ Generating behavioral anomalies...")
    for i in range(6):
        await activity_logger.log_activity(
            agent_id="uncertain_agent",
            action_type="decision",
            message=f"low_confidence_decision_{i}",
            severity="warning",
            data={
                "execution_time": 2000,
                "confidence": 0.15 + (i * 0.02),  # Very low confidence
                "decision_factors": ["insufficient_data", "conflicting_signals"],
                "fallback_used": True
            }
        )
    
    # 5. Generate correlation anomalies (isolated agent activity)
    print("5️⃣ Generating correlation anomalies...")
    base_time = datetime.utcnow()
    for minute_offset in range(10):
        # This agent works alone in 5-minute windows
        await activity_logger.log_activity(
            agent_id="isolated_agent",
            action_type="analysis",
            message=f"solo_analysis_{minute_offset}",
            severity="info",
            data={
                "execution_time": 1500,
                "analysis_type": "market_trend",
                "working_alone": True,
                "isolation_score": 0.95
            }
        )
        
        # Small delay to simulate time passage
        await asyncio.sleep(0.1)
    
    print("✅ Test anomalies generated successfully!")
    print("🔍 Now run the anomaly detection to see the results...")

if __name__ == "__main__":
    asyncio.run(generate_test_anomalies())
