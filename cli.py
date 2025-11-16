#!/usr/bin/env python3
"""
AI Flight Recorder CLI
Command-line interface for interacting with the AI Flight Recorder system.
"""

import click
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_TIMEOUT = 30

class AIFlightRecorderCLI:
    """Main CLI class for AI Flight Recorder"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.token = None
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=API_TIMEOUT)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, params=params, timeout=API_TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            click.echo(click.style("❌ Error: Cannot connect to AI Flight Recorder server", fg="red"))
            click.echo(f"   Make sure the server is running at {self.base_url}")
            sys.exit(1)
        except requests.exceptions.Timeout:
            click.echo(click.style("⏰ Error: Request timeout", fg="red"))
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            click.echo(click.style(f"❌ HTTP Error: {e.response.status_code}", fg="red"))
            sys.exit(1)
        except Exception as e:
            click.echo(click.style(f"❌ Error: {str(e)}", fg="red"))
            sys.exit(1)

cli_instance = AIFlightRecorderCLI()

@click.group()
@click.version_option(version="1.0.0", prog_name="AI Flight Recorder CLI")
def cli():
    """🚀 AI Flight Recorder Command Line Interface
    
    Interact with your AI Flight Recorder system from the command line.
    """
    pass

@cli.command()
def status():
    """📊 Show system status and health"""
    click.echo(click.style("🔍 Checking AI Flight Recorder status...", fg="blue"))
    
    try:
        # Try the new comprehensive dashboard endpoint first
        dashboard = cli_instance.make_request("GET", "/api/monitoring/dashboard")
        system = dashboard['system_status']
        metrics = dashboard['metrics']
        agents = dashboard['agents']
        
        click.echo(click.style(f"✅ System Status: {system['status'].upper()}", fg="green"))
        click.echo(f"   Version: {system['version']}")
        click.echo(f"   Uptime: {system['uptime']}")
        click.echo(f"   Timestamp: {system['last_update']}")
        
        click.echo(f"\n📈 Quick Metrics:")
        click.echo(f"   CPU Usage: {metrics['cpu_usage']}%")
        click.echo(f"   Memory Usage: {metrics['memory_usage']}%")
        click.echo(f"   Active Agents: {agents['active']}/{agents['total']}")
        click.echo(f"   Response Time: {metrics['response_time']}ms")
        
        click.echo(f"\n📊 API Statistics:")
        click.echo(f"   Total Endpoints: 18")
        click.echo(f"   Categories: 7")
        click.echo(f"   Status: operational")
        
    except:
        # Fallback to basic health check
        health = cli_instance.make_request("GET", "/health")
        click.echo(click.style(f"✅ System Status: {health['status'].upper()}", fg="green"))
        click.echo(f"   Version: {health['version']}")
        click.echo(f"   Uptime: {health['uptime']}")
        click.echo(f"   Timestamp: {health['timestamp']}")
        
        # Get API info
        api_info = cli_instance.make_request("GET", "/api/info")
        click.echo(f"\n📈 API Statistics:")
        click.echo(f"   Total Endpoints: {api_info['endpoints']['total']}")
        click.echo(f"   Categories: {api_info['endpoints']['categories']}")
        click.echo(f"   Status: {api_info['status']}")

@cli.command()
def agents():
    """🤖 List all connected agents"""
    click.echo(click.style("🤖 Fetching connected agents...", fg="blue"))
    
    agents_data = cli_instance.make_request("GET", "/api/monitoring/agents")
    agents_list = agents_data["agents"]
    
    click.echo(f"\n📊 Connected Agents Summary:")
    click.echo(f"   Total Agents: {agents_data['total_count']}")
    click.echo(f"   Active Agents: {agents_data['active_count']}")
    click.echo(f"   API Integrated: {agents_data['api_integrated_count']}")
    
    click.echo(f"\n🔍 Agent Details:")
    for agent in agents_list:
        status_color = "green" if agent["status"] == "active" else "yellow" if agent["status"] == "idle" else "red"
        click.echo(f"   • {agent['name']} ({agent['id']})")
        click.echo(f"     Status: " + click.style(agent['status'].upper(), fg=status_color))
        click.echo(f"     Type: {agent['type']} | Version: {agent['version']}")
        click.echo(f"     CPU: {agent['cpu_usage']}% | Memory: {agent['memory']}")
        click.echo(f"     Tasks: {agent['tasks_completed']} | Uptime: {agent['uptime']}")
        if 'curl_command' in agent:
            click.echo(f"     API: {click.style('Available', fg='green')}")
        click.echo()

@cli.command()
def metrics():
    """📈 Show current system metrics"""
    click.echo(click.style("📈 Fetching system metrics...", fg="blue"))
    
    metrics_data = cli_instance.make_request("GET", "/api/monitoring/metrics")
    system_data = cli_instance.make_request("GET", "/api/monitoring/system")
    
    click.echo(f"\n🖥️  System Metrics:")
    click.echo(f"   CPU Usage: {metrics_data['cpu_usage']}%")
    click.echo(f"   Memory Usage: {metrics_data['memory_usage']}%")
    click.echo(f"   Response Time: {metrics_data['response_time']}ms")
    click.echo(f"   Error Rate: {metrics_data['error_rate']}%")
    
    click.echo(f"\n🤖 Agent Metrics:")
    click.echo(f"   Active Agents: {metrics_data['active_agents']}")
    click.echo(f"   Completed Tasks: {metrics_data['completed_tasks']}")
    
    click.echo(f"\n💾 System Resources:")
    sys_metrics = system_data["system"]
    click.echo(f"   CPU Cores: {sys_metrics['cpu']['cores']} | Load: {sys_metrics['cpu']['load_avg']}")
    click.echo(f"   Memory: {sys_metrics['memory']['used']}% of {sys_metrics['memory']['total']}")
    click.echo(f"   Disk: {sys_metrics['disk']['used']}% of {sys_metrics['disk']['total']}")

@cli.command()
def activity():
    """📋 Show recent system activity"""
    click.echo(click.style("📋 Fetching recent activity...", fg="blue"))
    
    activity_data = cli_instance.make_request("GET", "/api/monitoring/activity")
    activities = activity_data["activities"]
    
    click.echo(f"\n🔄 Recent Activity (Total today: {activity_data['total_today']}):")
    for activity in activities:
        status_color = "green" if activity["status"] == "success" else "red"
        click.echo(f"   • {activity['time']} - {activity['agent']}")
        click.echo(f"     Action: {activity['action']}")
        click.echo(f"     Status: " + click.style(activity['status'].upper(), fg=status_color))
        click.echo()

@cli.command()
def compliance():
    """🔍 Show compliance status and violations"""
    click.echo(click.style("🔍 Checking compliance status...", fg="blue"))
    
    try:
        violations_data = cli_instance.make_request("GET", "/api/monitoring/compliance/violations")
        violations = violations_data["violations"]
        
        click.echo(f"\n⚖️  Compliance Overview:")
        click.echo(f"   Total Violations: {violations_data['total_count']}")
        click.echo(f"   Resolution Rate: {violations_data['resolution_rate']}")
        
        severity_counts = violations_data.get("by_severity", {})
        click.echo(f"   By Severity: High({severity_counts.get('high', 0)}) | Medium({severity_counts.get('medium', 0)}) | Low({severity_counts.get('low', 0)})")
        
        if violations:
            click.echo(f"\n🚨 Active Violations:")
            for violation in violations:
                severity_color = "red" if violation["severity"] == "high" else "yellow" if violation["severity"] == "medium" else "green"
                click.echo(f"   • {violation['id']} - " + click.style(violation['severity'].upper(), fg=severity_color))
                click.echo(f"     Type: {violation['type']}")
                click.echo(f"     Description: {violation['description']}")
                click.echo(f"     Agent: {violation['affected_agent']}")
                click.echo(f"     Detected: {violation['detected']} | Status: {violation['status']}")
                click.echo()
        else:
            click.echo(click.style("   ✅ No active violations found!", fg="green"))
    
    except Exception as e:
        click.echo(click.style(f"   ⚠️  Could not fetch compliance data: {str(e)}", fg="yellow"))

@cli.command()
def security():
    """🔒 Show security status and anomalies"""
    click.echo(click.style("🔒 Checking security status...", fg="blue"))
    
    anomalies_data = cli_instance.make_request("GET", "/api/monitoring/anomalies")
    anomalies = anomalies_data["anomalies"]
    
    click.echo(f"\n🛡️  Security Overview:")
    click.echo(f"   Total Anomalies: {anomalies_data['total_count']}")
    click.echo(f"   Detection Accuracy: {anomalies_data['detection_accuracy']}")
    
    severity_counts = anomalies_data.get("by_severity", {})
    click.echo(f"   By Severity: High({severity_counts.get('high', 0)}) | Medium({severity_counts.get('medium', 0)}) | Low({severity_counts.get('low', 0)})")
    
    if anomalies:
        click.echo(f"\n🚨 Detected Anomalies:")
        for anomaly in anomalies:
            severity_color = "red" if anomaly["severity"] == "high" else "yellow" if anomaly["severity"] == "medium" else "green"
            click.echo(f"   • {anomaly['id']} - " + click.style(anomaly['severity'].upper(), fg=severity_color))
            click.echo(f"     Type: {anomaly['type']} | Metric: {anomaly['metric']}")
            click.echo(f"     Current: {anomaly['current_value']} | Expected: {anomaly['expected_range']}")
            click.echo(f"     Detected: {anomaly['detected']} | Status: {anomaly['status']}")
            click.echo()
    else:
        click.echo(click.style("   ✅ No anomalies detected!", fg="green"))

@cli.command()
@click.option('--rules', is_flag=True, help='Show compliance rules')
@click.option('--violations', is_flag=True, help='Show only violations')
@click.option('--severity', type=click.Choice(['HIGH', 'MEDIUM', 'LOW']), help='Filter by severity')
def compliance(rules, violations, severity):
    """🔍 Compliance status and violations"""
    try:
        client = AIFlightRecorderCLI()
        
        if rules:
            # Show compliance rules
            rules_data = client.make_request("GET", "/api/compliance/rules")
            if not rules_data:
                return
                
            click.echo(click.style("📋 Compliance Rules:", fg="blue", bold=True))
            click.echo(f"   Total Rules: {rules_data['total_count']}")
            click.echo(f"   Active Rules: {rules_data['active_count']}")
            click.echo(f"   Coverage: {rules_data['coverage_percentage']}%")
            
            if rules_data.get("rules"):
                click.echo("\n📝 Rules Details:")
                for rule in rules_data["rules"]:
                    status_color = "green" if rule["status"] == "ACTIVE" else "red"
                    severity_color = "red" if rule["severity"] == "HIGH" else "yellow" if rule["severity"] == "MEDIUM" else "green"
                    
                    click.echo(f"   • {rule['name']} ({rule['id']})")
                    click.echo(f"     Type: {rule['type']} | Severity: " + click.style(rule['severity'], fg=severity_color))
                    click.echo(f"     Status: " + click.style(rule['status'], fg=status_color) + f" | Violations: {rule['violations_count']}")
                    click.echo(f"     Description: {rule['description']}")
                    click.echo(f"     Last Check: {rule['last_check']}")
                    click.echo()
        else:
            # Show compliance violations (default)
            compliance_data = client.make_request("GET", "/api/monitoring/compliance/violations")
            if not compliance_data:
                return
                
            violations_list = compliance_data.get("violations", [])
            
            # Filter by severity if specified
            if severity:
                violations_list = [v for v in violations_list if v.get("severity", "").upper() == severity]
            
            click.echo(click.style("⚖️ Compliance Overview:", fg="yellow", bold=True))
            click.echo(f"   Total Violations: {compliance_data['total_count']}")
            click.echo(f"   Resolution Rate: {compliance_data['resolution_rate']}")
            
            severity_counts = compliance_data.get("by_severity", {})
            click.echo(f"   By Severity: High({severity_counts.get('high', 0)}) | Medium({severity_counts.get('medium', 0)}) | Low({severity_counts.get('low', 0)})")
            
            if violations_list:
                click.echo(f"\n🚨 Active Violations:")
                for violation in violations_list:
                    severity_color = "red" if violation["severity"] == "high" else "yellow" if violation["severity"] == "medium" else "green"
                    status_color = "green" if violation["status"] == "resolved" else "yellow" if violation["status"] == "investigating" else "blue"
                    
                    click.echo(f"   • {violation['id']} - " + click.style(violation['severity'].upper(), fg=severity_color))
                    click.echo(f"     Type: {violation['type']} | Agent: {violation['affected_agent']}")
                    click.echo(f"     Description: {violation['description']}")
                    click.echo(f"     Detected: {violation['detected']} | Status: " + click.style(violation['status'].upper(), fg=status_color))
                    click.echo()
            else:
                click.echo(click.style("   ✅ No violations found!" + (f" (Severity: {severity})" if severity else ""), fg="green"))
                
    except Exception as e:
        click.echo(click.style(f"❌ Error fetching compliance data: {str(e)}", fg="red"))

@cli.command()
def approvals():
    """✅ Show pending approvals"""
    click.echo(click.style("✅ Checking pending approvals...", fg="blue"))
    
    approvals_data = cli_instance.make_request("GET", "/api/monitoring/approvals/pending")
    pending_approvals = approvals_data["pending_approvals"]
    
    click.echo(f"\n📋 Approval Summary:")
    click.echo(f"   Total Pending: {approvals_data['total_count']}")
    click.echo(f"   Average Response Time: {approvals_data['avg_response_time']}")
    
    priority_counts = approvals_data.get("by_priority", {})
    click.echo(f"   By Priority: High({priority_counts.get('high', 0)}) | Medium({priority_counts.get('medium', 0)}) | Low({priority_counts.get('low', 0)})")
    
    if pending_approvals:
        click.echo(f"\n⏳ Pending Approvals:")
        for approval in pending_approvals:
            priority_color = "red" if approval["priority"] == "high" else "yellow" if approval["priority"] == "medium" else "green"
            click.echo(f"   • {approval['id']} - " + click.style(approval['priority'].upper(), fg=priority_color))
            click.echo(f"     Type: {approval['type']}")
            click.echo(f"     Description: {approval['description']}")
            click.echo(f"     Requested by: {approval['requested_by']}")
            click.echo(f"     Submitted: {approval['submitted']} | Expires: {approval['expires']}")
            click.echo(f"     Impact: {approval['estimated_impact']}")
            click.echo()
    else:
        click.echo(click.style("   ✅ No pending approvals!", fg="green"))

@cli.command()
@click.option("--username", prompt=True, help="Username for authentication")
@click.option("--password", prompt=True, hide_input=True, help="Password for authentication")
def login(username, password):
    """🔐 Login to the system"""
    click.echo(click.style("🔐 Authenticating...", fg="blue"))
    
    credentials = {"username": username, "password": password}
    auth_result = cli_instance.make_request("POST", "/api/auth/login", credentials)
    
    if auth_result.get("success"):
        cli_instance.token = auth_result.get("token")
        user_info = auth_result.get("user", {})
        
        click.echo(click.style("✅ Login successful!", fg="green"))
        click.echo(f"   Welcome, {user_info.get('username', 'User')}!")
        click.echo(f"   Role: {user_info.get('role', 'Unknown')}")
        click.echo(f"   Permissions: {', '.join(user_info.get('permissions', []))}")
    else:
        click.echo(click.style("❌ Login failed!", fg="red"))
        click.echo(f"   {auth_result.get('message', 'Invalid credentials')}")

@cli.command()
@click.option("--follow", "-f", is_flag=True, help="Follow logs in real-time")
@click.option("--interval", default=5, help="Update interval in seconds (for --follow)")
def monitor(follow, interval):
    """👀 Monitor system in real-time"""
    if follow:
        click.echo(click.style("👀 Real-time monitoring started (Ctrl+C to stop)", fg="blue"))
        try:
            while True:
                click.clear()
                click.echo(click.style(f"🚀 AI Flight Recorder - Real-time Monitor", fg="cyan"))
                click.echo(click.style(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fg="yellow"))
                click.echo("=" * 60)
                
                # Show key metrics
                metrics_data = cli_instance.make_request("GET", "/api/monitoring/metrics")
                click.echo(f"CPU: {metrics_data['cpu_usage']}% | Memory: {metrics_data['memory_usage']}% | Agents: {metrics_data['active_agents']}")
                click.echo(f"Tasks: {metrics_data['completed_tasks']} | Response: {metrics_data['response_time']}ms | Errors: {metrics_data['error_rate']}%")
                
                # Show recent activity
                activity_data = cli_instance.make_request("GET", "/api/monitoring/activity")
                click.echo(f"\n📋 Recent Activity:")
                for activity in activity_data["activities"][:3]:  # Show only last 3
                    status_icon = "✅" if activity["status"] == "success" else "❌"
                    click.echo(f"   {status_icon} {activity['time']} - {activity['agent']}: {activity['action']}")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo(click.style("\n👋 Monitoring stopped", fg="yellow"))
    else:
        # Single snapshot
        click.echo(click.style("📊 System Snapshot", fg="blue"))
        ctx = click.get_current_context()
        ctx.invoke(metrics)

@cli.command()
def dashboard():
    """🌐 Open web dashboard"""
    import webbrowser
    dashboard_url = f"{BASE_URL}/"
    click.echo(click.style(f"🌐 Opening dashboard: {dashboard_url}", fg="blue"))
    webbrowser.open(dashboard_url)

@cli.command()
def docs():
    """📚 Open API documentation"""
    import webbrowser
    docs_url = f"{BASE_URL}/docs"
    click.echo(click.style(f"📚 Opening API documentation: {docs_url}", fg="blue"))
    webbrowser.open(docs_url)

@cli.command()
def test():
    """🧪 Test API connectivity"""
    click.echo(click.style("🧪 Testing API connectivity...", fg="blue"))
    
    test_result = cli_instance.make_request("GET", "/test")
    click.echo(click.style("✅ API test successful!", fg="green"))
    click.echo(f"   Message: {test_result['message']}")
    click.echo(f"   Status: {test_result['status']}")
    click.echo(f"   Timestamp: {test_result['timestamp']}")

@cli.command()
@click.option('--limit', default=20, help='Number of activities to display')
@click.option('--agent', help='Filter by agent ID')
@click.option('--action', help='Filter by action type')
@click.option('--severity', help='Filter by severity level')
@click.option('--since', help='Show activities since timestamp (ISO format)')
@click.option('--follow', '-f', is_flag=True, help='Follow live activity stream')
@click.option('--export', help='Export activities to JSON file')
def activity_log(limit, agent, action, severity, since, follow, export):
    """📋 View real-time activity log - transparent immutable record of AI agent interactions"""
    
    if follow:
        click.echo(click.style("📋 Following live activity stream... (Press Ctrl+C to exit)", fg="green"))
        click.echo()
        
        try:
            last_timestamp = datetime.utcnow().isoformat()
            while True:
                # Get latest activities
                params = {"since": last_timestamp, "limit": 10}
                
                activities = cli_instance.make_request("GET", "/api/activity-logs/latest", params)
                
                if activities:
                    for activity in reversed(activities):  # Show in chronological order
                        timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
                        formatted_time = timestamp.strftime('%H:%M:%S')
                        
                        # Color code by severity
                        severity_colors = {
                            'critical': 'red',
                            'high': 'magenta',
                            'medium': 'yellow',
                            'low': 'cyan',
                            'info': 'white'
                        }
                        severity_color = severity_colors.get(activity['severity'], 'white')
                        
                        agent_name = activity['agent_id'].replace('-', ' ').replace('_', ' ').title()
                        
                        click.echo(click.style(
                            f"[{formatted_time}] {agent_name} → {activity['action_type']} ",
                            fg='blue'
                        ) + click.style(
                            f"({activity['severity']}) ",
                            fg=severity_color
                        ) + click.style(
                            activity['message'][:80] + ('...' if len(activity['message']) > 80 else ''),
                            fg='white'
                        ))
                        
                        last_timestamp = activity['timestamp']
                
                time.sleep(2)  # Poll every 2 seconds
                
        except KeyboardInterrupt:
            click.echo(click.style("\n📋 Activity stream stopped.", fg="yellow"))
            return
    
    else:
        # Build query parameters
        params = {"limit": limit}
        if agent:
            params["agent_id"] = agent
        if action:
            params["action_type"] = action
        if severity:
            params["severity"] = severity
        if since:
            params["since"] = since
        
        click.echo(click.style(f"📋 Fetching {limit} activity log entries...", fg="blue"))
        
        activities = cli_instance.make_request("GET", "/api/activity-logs", params)
        
        if export:
            # Export to JSON file
            with open(export, 'w') as f:
                json.dump(activities, f, indent=2, default=str)
            click.echo(click.style(f"📁 Exported {len(activities)} activities to {export}", fg="green"))
        
        if not activities:
            click.echo(click.style("📋 No activities found matching the criteria.", fg="yellow"))
            return
        
        # Display activities
        click.echo(click.style(f"\n📋 Activity Log ({len(activities)} entries)", fg="green", bold=True))
        click.echo("=" * 80)
        
        for activity in activities:
            timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Color code by severity
            severity_colors = {
                'critical': 'red',
                'high': 'magenta', 
                'medium': 'yellow',
                'low': 'cyan',
                'info': 'white'
            }
            severity_color = severity_colors.get(activity['severity'], 'white')
            
            agent_name = activity['agent_id'].replace('-', ' ').replace('_', ' ').title()
            
            # Header line
            click.echo(click.style(f"[{formatted_time}] ", fg='cyan') + 
                      click.style(f"{agent_name} ", fg='blue', bold=True) +
                      click.style(f"→ {activity['action_type']} ", fg='green') +
                      click.style(f"({activity['severity']})", fg=severity_color, bold=True))
            
            # Message
            click.echo(f"  📝 {activity['message']}")
            
            # Additional info
            if activity.get('data', {}).get('execution_time'):
                exec_time = activity['data']['execution_time']
                click.echo(f"  ⏱️  Execution: {exec_time}ms")
            
            if activity.get('data', {}).get('user_id'):
                click.echo(f"  👤 User: {activity['data']['user_id']}")
            
            if activity.get('hash'):
                click.echo(f"  🔐 Hash: {activity['hash']}")
            
            click.echo()

@cli.command()
@click.option('--since', help='Calculate stats since timestamp (ISO format)')
def activity_stats(since):
    """📊 Get activity log statistics and metrics"""
    click.echo(click.style("📊 Fetching activity statistics...", fg="blue"))
    
    params = {}
    if since:
        params["since"] = since
    
    stats = cli_instance.make_request("GET", "/api/activity-logs/stats", params)
    
    click.echo(click.style("\n📊 Activity Statistics", fg="green", bold=True))
    click.echo("=" * 50)
    
    # Main stats
    click.echo(click.style("📈 Activity Counts:", fg="cyan", bold=True))
    click.echo(f"  Total Activities: {stats['total_activities']}")
    click.echo(f"  Decisions Made:   {stats['decisions']}")
    click.echo(f"  Data Points:      {stats['data_points']}")
    click.echo(f"  Errors:           {stats['errors']}")
    
    # Performance
    click.echo(click.style("\n⚡ Performance:", fg="yellow", bold=True))
    click.echo(f"  Avg Response Time: {stats['avg_response_time']}ms")
    click.echo(f"  Active Agents:     {stats['active_agents']}")
    
    # Agent distribution
    if 'agent_distribution' in stats:
        click.echo(click.style("\n🤖 Agent Activity Distribution:", fg="magenta", bold=True))
        for agent, count in stats['agent_distribution'].items():
            agent_name = agent.replace('-', ' ').replace('_', ' ').title()
            click.echo(f"  {agent_name}: {count} activities")
    
    click.echo(f"\n🕐 Last Updated: {stats['timestamp']}")

@cli.command()
def verify_integrity():
    """🔐 Verify integrity of immutable activity log records"""
    click.echo(click.style("🔐 Verifying activity log integrity...", fg="blue"))
    
    result = cli_instance.make_request("GET", "/api/activity-logs/verify-integrity")
    
    # Status
    status_color = 'green' if result['status'] == 'verified' else 'yellow'
    click.echo(click.style(f"\n🔐 Integrity Status: {result['status'].upper()}", fg=status_color, bold=True))
    
    # Results
    click.echo(f"📊 Total Records:    {result['total_records']}")
    click.echo(f"✅ Verified Records: {result['verified_records']}")
    click.echo(f"❌ Invalid Records:  {result['invalid_records']}")
    click.echo(f"📈 Integrity:        {result['integrity_percentage']}%")
    
    # System hash
    click.echo(f"\n🔐 System Hash: {result['system_hash']}")
    click.echo(f"🕐 Verified:    {result['verification_timestamp']}")
    
    if result['status'] != 'verified':
        click.echo(click.style("\n⚠️  Some records may have integrity issues!", fg="yellow"))

@cli.command()
def list_agents():
    """🤖 List active AI agents and their status"""
    click.echo(click.style("🤖 Fetching active agents...", fg="blue"))
    
    agents = cli_instance.make_request("GET", "/api/agents")
    
    click.echo(click.style(f"\n🤖 Active AI Agents ({len(agents)} total)", fg="green", bold=True))
    click.echo("=" * 70)
    
    for agent in agents:
        status_color = 'green' if agent['status'] == 'active' else 'red'
        
        click.echo(click.style(f"🤖 {agent['name']}", fg="blue", bold=True))
        click.echo(f"   ID:            {agent['id']}")
        click.echo(f"   Status:        " + click.style(agent['status'].upper(), fg=status_color))
        click.echo(f"   Activity Count: {agent['activity_count']}")
        click.echo(f"   Last Activity:  {agent['last_activity']}")
        click.echo()

if __name__ == "__main__":
    cli()
