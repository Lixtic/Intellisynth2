"""
Database Initialization Script
Creates all tables and optionally seeds sample data
"""

import argparse
import sys
from datetime import datetime, timedelta
from app.database import Base, engine, SessionLocal
from app.models.activity_log import ActivityLog
from app.models.agent import Agent, AgentStatus, AgentType

def create_tables():
    """Create all database tables"""
    print("=" * 70)
    print("  Creating Database Tables")
    print("=" * 70)
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def seed_sample_agents():
    """Seed database with sample AI agents"""
    print("\n" + "=" * 70)
    print("  Seeding Sample Agents")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        sample_agents = [
            {
                "name": "AI Monitor Agent",
                "agent_type": AgentType.MONITOR.value,
                "description": "Monitors system health and performance metrics in real-time",
                "capabilities": ["health_check", "metrics_collection", "alerting", "uptime_monitoring"],
                "configuration": {
                    "check_interval": 60,
                    "alert_threshold": 80,
                    "metrics": ["cpu", "memory", "disk", "network"]
                },
                "status": AgentStatus.ACTIVE.value,
                "owner": "system",
                "tags": ["monitoring", "production", "critical"]
            },
            {
                "name": "Compliance Agent",
                "agent_type": AgentType.COMPLIANCE.value,
                "description": "Ensures all AI operations comply with regulations and policies",
                "capabilities": ["compliance_checking", "audit_trail", "policy_enforcement", "reporting"],
                "configuration": {
                    "check_frequency": "hourly",
                    "policies": ["GDPR", "HIPAA", "SOC2"],
                    "auto_remediate": False
                },
                "status": AgentStatus.ACTIVE.value,
                "owner": "compliance_team",
                "tags": ["compliance", "audit", "governance"]
            },
            {
                "name": "Security Scanner",
                "agent_type": AgentType.SECURITY.value,
                "description": "Scans for security threats and vulnerabilities",
                "capabilities": ["threat_detection", "vulnerability_scanning", "incident_response", "penetration_testing"],
                "configuration": {
                    "scan_frequency": "daily",
                    "scan_depth": "deep",
                    "auto_patch": False
                },
                "status": AgentStatus.ACTIVE.value,
                "owner": "security_team",
                "tags": ["security", "scanning", "protection"]
            },
            {
                "name": "Data Analyst",
                "agent_type": AgentType.ANALYZER.value,
                "description": "Analyzes data patterns and provides insights",
                "capabilities": ["pattern_analysis", "anomaly_detection", "report_generation", "data_visualization"],
                "configuration": {
                    "analysis_type": "statistical",
                    "confidence_threshold": 0.85,
                    "output_format": "json"
                },
                "status": AgentStatus.ACTIVE.value,
                "owner": "data_team",
                "tags": ["analytics", "insights", "reporting"]
            },
            {
                "name": "Anomaly Detector",
                "agent_type": AgentType.ANALYZER.value,
                "description": "Detects anomalies in system behavior and data patterns",
                "capabilities": ["statistical_analysis", "pattern_recognition", "behavioral_analysis", "correlation_detection"],
                "configuration": {
                    "detection_methods": ["statistical", "pattern", "behavioral", "correlation"],
                    "sensitivity": "medium",
                    "auto_alert": True
                },
                "status": AgentStatus.ACTIVE.value,
                "owner": "ops_team",
                "tags": ["anomaly", "detection", "monitoring"]
            },
            {
                "name": "Data Collector",
                "agent_type": AgentType.COLLECTOR.value,
                "description": "Collects data from various sources and systems",
                "capabilities": ["data_mining", "log_parsing", "metric_collection", "api_integration"],
                "configuration": {
                    "sources": ["logs", "metrics", "apis", "databases"],
                    "collection_interval": 300,
                    "batch_size": 1000
                },
                "status": AgentStatus.ACTIVE.value,
                "owner": "data_team",
                "tags": ["collection", "ingestion", "etl"]
            },
            {
                "name": "Decision Maker",
                "agent_type": AgentType.DECISION_MAKER.value,
                "description": "Makes automated decisions based on rules and ML models",
                "capabilities": ["rule_engine", "ml_inference", "automated_response", "decision_logging"],
                "configuration": {
                    "decision_model": "hybrid",
                    "confidence_required": 0.9,
                    "human_approval_required": True
                },
                "status": AgentStatus.INACTIVE.value,
                "owner": "ai_team",
                "tags": ["decision", "automation", "ai"]
            }
        ]
        
        created_count = 0
        for agent_data in sample_agents:
            # Check if agent already exists
            existing = db.query(Agent).filter(Agent.name == agent_data["name"]).first()
            if existing:
                print(f"  ⊙ Agent already exists: {agent_data['name']}")
                continue
            
            # Create new agent
            agent = Agent(**agent_data)
            db.add(agent)
            created_count += 1
            print(f"  ✓ Created agent: {agent_data['name']}")
        
        db.commit()
        print(f"\n✓ Created {created_count} new agents")
        print(f"  Total agents in database: {db.query(Agent).count()}")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding agents: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def seed_sample_activity_logs():
    """Seed database with sample activity logs"""
    print("\n" + "=" * 70)
    print("  Seeding Sample Activity Logs")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # Check if we have agents to reference
        agents = db.query(Agent).all()
        if not agents:
            print("  ⚠ No agents found. Skipping activity log seeding.")
            print("    Run with --seed-agents first")
            return True
        
        import hashlib
        
        sample_activities = []
        agent_names = [a.name for a in agents[:5]]  # Use first 5 agents
        
        # Generate sample activities for the past 7 days
        for days_ago in range(7, 0, -1):
            timestamp = datetime.utcnow() - timedelta(days=days_ago)
            
            for i in range(5):  # 5 activities per day
                agent_name = agent_names[i % len(agent_names)]
                action_types = ["decision", "data_collection", "analysis", "compliance_check", "security_scan"]
                action_type = action_types[i % len(action_types)]
                
                message = f"Sample {action_type} performed by {agent_name}"
                hash_input = f"{agent_name}-{action_type}-{timestamp.isoformat()}-{message}"
                activity_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
                
                activity = ActivityLog(
                    id=f"activity-{timestamp.timestamp()}-{activity_hash[:8]}",
                    timestamp=timestamp,
                    agent_id=agent_name.lower().replace(" ", "-"),
                    action_type=action_type,
                    severity="info",
                    message=message,
                    data={
                        "execution_time": 100 + (i * 50),
                        "success": True,
                        "metadata": {
                            "confidence": 0.95,
                            "impact_score": 7.5
                        }
                    },
                    hash=activity_hash
                )
                sample_activities.append(activity)
        
        # Check how many already exist
        existing_count = db.query(ActivityLog).count()
        
        # Add new activities
        for activity in sample_activities:
            existing = db.query(ActivityLog).filter(ActivityLog.id == activity.id).first()
            if not existing:
                db.add(activity)
        
        db.commit()
        
        new_count = db.query(ActivityLog).count()
        created_count = new_count - existing_count
        
        print(f"✓ Created {created_count} new activity logs")
        print(f"  Total activity logs in database: {new_count}")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding activity logs: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def check_database_status():
    """Check current database status"""
    print("\n" + "=" * 70)
    print("  Database Status")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # Check agents
        agent_count = db.query(Agent).count()
        active_agents = db.query(Agent).filter(Agent.status == AgentStatus.ACTIVE.value).count()
        
        print(f"\nAgents:")
        print(f"  Total: {agent_count}")
        print(f"  Active: {active_agents}")
        
        if agent_count > 0:
            print(f"\n  Sample agents:")
            for agent in db.query(Agent).limit(5).all():
                print(f"    - {agent.name} ({agent.agent_type}) - {agent.status}")
        
        # Check activity logs
        activity_count = db.query(ActivityLog).count()
        print(f"\nActivity Logs:")
        print(f"  Total: {activity_count}")
        
        if activity_count > 0:
            recent = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(3).all()
            print(f"\n  Recent activities:")
            for log in recent:
                print(f"    - {log.timestamp.strftime('%Y-%m-%d %H:%M')} | {log.agent_id} | {log.action_type}")
        
        return True
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return False
    finally:
        db.close()

def main():
    """Main initialization function"""
    parser = argparse.ArgumentParser(
        description="Initialize and seed the AI Flight Recorder database"
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create all database tables"
    )
    parser.add_argument(
        "--seed-agents",
        action="store_true",
        help="Seed sample AI agents"
    )
    parser.add_argument(
        "--seed-logs",
        action="store_true",
        help="Seed sample activity logs"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Create tables and seed all sample data"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check database status"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("\n" + "=" * 70)
    print("  AI FLIGHT RECORDER - DATABASE INITIALIZATION")
    print("=" * 70)
    
    success = True
    
    # Handle --all flag
    if args.all:
        args.create_tables = True
        args.seed_agents = True
        args.seed_logs = True
    
    # Create tables
    if args.create_tables:
        if not create_tables():
            success = False
    
    # Seed agents
    if args.seed_agents and success:
        if not seed_sample_agents():
            success = False
    
    # Seed logs
    if args.seed_logs and success:
        if not seed_sample_activity_logs():
            success = False
    
    # Check status
    if args.status:
        check_database_status()
    
    # Final summary
    if success:
        print("\n" + "=" * 70)
        print("  ✓ DATABASE INITIALIZATION COMPLETE!")
        print("=" * 70)
        check_database_status()
    else:
        print("\n" + "=" * 70)
        print("  ✗ DATABASE INITIALIZATION FAILED")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
