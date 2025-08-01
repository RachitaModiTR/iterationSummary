import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional

class SprintChangeNotifier:
    """Email notification system for sprint data changes"""
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.recipient_email = "rachita.modi@tr.com"
        self.baseline_file = "sprint_baseline.json"
        
    def load_baseline_data(self) -> Dict[str, Any]:
        """Load baseline sprint data from file"""
        if os.path.exists(self.baseline_file):
            try:
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading baseline data: {e}")
                return {}
        return {}
    
    def save_baseline_data(self, data: Dict[str, Any]):
        """Save baseline sprint data to file"""
        try:
            with open(self.baseline_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving baseline data: {e}")
    
    def generate_sprint_key(self, sprint: str, team: str, pod: Optional[str] = None) -> str:
        """Generate unique key for sprint/team/pod combination"""
        key = f"{sprint}_{team}"
        if pod:
            key += f"_{pod}"
        return key
    
    def check_for_changes(self, current_data: pd.DataFrame, sprint: str, team: str, pod: Optional[str] = None) -> Dict[str, Any]:
        """Check for changes in work items and story points"""
        sprint_key = self.generate_sprint_key(sprint, team, pod)
        baseline_data = self.load_baseline_data()
        
        # Calculate current metrics
        current_metrics = {
            'total_work_items': len(current_data),
            'total_story_points': int(current_data['story_points'].sum()),
            'completed_work_items': len(current_data[current_data['is_completed'] == True]),
            'completed_story_points': int(current_data[current_data['is_completed'] == True]['story_points'].sum()),
            'last_updated': datetime.now().isoformat(),
            'sprint': sprint,
            'team': team,
            'pod': pod
        }
        
        # Get baseline metrics for this sprint/team/pod
        baseline_metrics = baseline_data.get(sprint_key, {})
        
        changes_detected = {}
        
        # Check for changes in total work items
        if baseline_metrics.get('total_work_items') is not None:
            baseline_items = baseline_metrics['total_work_items']
            current_items = current_metrics['total_work_items']
            if baseline_items != current_items:
                changes_detected['work_items'] = {
                    'previous': baseline_items,
                    'current': current_items,
                    'change': current_items - baseline_items
                }
        
        # Check for changes in total story points
        if baseline_metrics.get('total_story_points') is not None:
            baseline_points = baseline_metrics['total_story_points']
            current_points = current_metrics['total_story_points']
            if baseline_points != current_points:
                changes_detected['story_points'] = {
                    'previous': baseline_points,
                    'current': current_points,
                    'change': current_points - baseline_points
                }
        
        # Update baseline data
        baseline_data[sprint_key] = current_metrics
        self.save_baseline_data(baseline_data)
        
        return {
            'changes_detected': len(changes_detected) > 0,
            'changes': changes_detected,
            'current_metrics': current_metrics,
            'baseline_metrics': baseline_metrics
        }
    
    def create_email_content(self, change_data: Dict[str, Any]) -> tuple:
        """Create email subject and body for sprint changes"""
        current_metrics = change_data['current_metrics']
        changes = change_data['changes']
        
        # Create subject
        sprint = current_metrics['sprint']
        team = current_metrics['team']
        pod = current_metrics['pod']
        
        subject_parts = []
        if 'work_items' in changes:
            change = changes['work_items']['change']
            subject_parts.append(f"Work Items: {change:+d}")
        if 'story_points' in changes:
            change = changes['story_points']['change']
            subject_parts.append(f"Story Points: {change:+d}")
        
        subject = f"🚨 Sprint Data Change Alert - {sprint} ({team}"
        if pod:
            subject += f" - {pod}"
        subject += f"): {', '.join(subject_parts)}"
        
        # Create email body
        body = f"""
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .content {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .change-item {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
        .metrics-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .metrics-table th, .metrics-table td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        .metrics-table th {{ background-color: #667eea; color: white; }}
        .increase {{ color: #28a745; font-weight: bold; }}
        .decrease {{ color: #dc3545; font-weight: bold; }}
        .footer {{ background: #e9ecef; padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 12px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 Sprint Data Change Alert</h1>
        <p>Changes detected in Azure DevOps sprint data</p>
    </div>
    
    <div class="content">
        <h2>📊 Sprint Information</h2>
        <ul>
            <li><strong>Sprint:</strong> {sprint}</li>
            <li><strong>Team:</strong> {team}</li>
            {"<li><strong>Pod:</strong> " + pod + "</li>" if pod else ""}
            <li><strong>Detection Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        </ul>
        
        <h2>🔄 Changes Detected</h2>
"""
        
        # Add work items changes
        if 'work_items' in changes:
            change_data_items = changes['work_items']
            change_class = "increase" if change_data_items['change'] > 0 else "decrease"
            change_symbol = "📈" if change_data_items['change'] > 0 else "📉"
            
            body += f"""
        <div class="change-item">
            <h3>{change_symbol} Work Items Changed</h3>
            <p><strong>Previous Count:</strong> {change_data_items['previous']}</p>
            <p><strong>Current Count:</strong> {change_data_items['current']}</p>
            <p><strong>Change:</strong> <span class="{change_class}">{change_data_items['change']:+d} items</span></p>
        </div>
"""
        
        # Add story points changes
        if 'story_points' in changes:
            change_data_points = changes['story_points']
            change_class = "increase" if change_data_points['change'] > 0 else "decrease"
            change_symbol = "📈" if change_data_points['change'] > 0 else "📉"
            
            body += f"""
        <div class="change-item">
            <h3>{change_symbol} Story Points Changed</h3>
            <p><strong>Previous Total:</strong> {change_data_points['previous']}</p>
            <p><strong>Current Total:</strong> {change_data_points['current']}</p>
            <p><strong>Change:</strong> <span class="{change_class}">{change_data_points['change']:+d} points</span></p>
        </div>
"""
        
        # Add current sprint metrics table
        body += f"""
        <h2>📈 Current Sprint Metrics</h2>
        <table class="metrics-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Work Items</td>
                <td>{current_metrics['total_work_items']}</td>
            </tr>
            <tr>
                <td>Total Story Points</td>
                <td>{current_metrics['total_story_points']}</td>
            </tr>
            <tr>
                <td>Completed Work Items</td>
                <td>{current_metrics['completed_work_items']}</td>
            </tr>
            <tr>
                <td>Completed Story Points</td>
                <td>{current_metrics['completed_story_points']}</td>
            </tr>
            <tr>
                <td>Completion Rate (Items)</td>
                <td>{(current_metrics['completed_work_items'] / current_metrics['total_work_items'] * 100):.1f}%</td>
            </tr>
            <tr>
                <td>Completion Rate (Points)</td>
                <td>{(current_metrics['completed_story_points'] / current_metrics['total_story_points'] * 100):.1f}%</td>
            </tr>
        </table>
    </div>
    
    <div class="footer">
        <p><strong>Azure DevOps Sprint Dashboard</strong> - Automated Change Detection</p>
        <p>This email was automatically generated when changes were detected in sprint data.</p>
        <p>Dashboard URL: <a href="http://localhost:8501">http://localhost:8501</a></p>
        <p>Generated by: Technology Manager (Tax Evolution)</p>
    </div>
</body>
</html>
"""
        
        return subject, body
    
    def send_email(self, subject: str, body: str, sender_email: str, sender_password: str):
        """Send email notification"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, self.recipient_email, text)
            server.quit()
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def monitor_and_notify(self, current_data: pd.DataFrame, sprint: str, team: str, pod: Optional[str] = None, 
                          sender_email: Optional[str] = None, sender_password: Optional[str] = None) -> Dict[str, Any]:
        """Monitor sprint data and send notifications if changes detected"""
        
        # Check for changes
        change_result = self.check_for_changes(current_data, sprint, team, pod)
        
        result = {
            'changes_detected': change_result['changes_detected'],
            'changes': change_result['changes'],
            'current_metrics': change_result['current_metrics'],
            'email_sent': False,
            'email_status': 'No changes detected'
        }
        
        # Send email if changes detected and email credentials provided
        if change_result['changes_detected'] and sender_email and sender_password:
            subject, body = self.create_email_content(change_result)
            email_success, email_message = self.send_email(subject, body, sender_email, sender_password)
            
            result['email_sent'] = email_success
            result['email_status'] = email_message
            result['email_subject'] = subject
        elif change_result['changes_detected']:
            result['email_status'] = 'Changes detected but email credentials not provided'
        
        return result

# Example usage and testing functions
def test_email_notification():
    """Test function to demonstrate email notification"""
    import pandas as pd
    
    # Create sample data
    sample_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'title': ['Task 1', 'Task 2', 'Task 3', 'Task 4', 'Task 5'],
        'story_points': [3, 5, 2, 8, 1],
        'is_completed': [True, True, False, True, False]
    })
    
    notifier = SprintChangeNotifier()
    
    # Test monitoring (this will create baseline on first run)
    result = notifier.monitor_and_notify(
        current_data=sample_data,
        sprint="2025_S15_Jul16-Jul29",
        team="ADGE-Prep",
        pod=None
    )
    
    print("Monitoring Result:")
    print(f"Changes Detected: {result['changes_detected']}")
    print(f"Email Status: {result['email_status']}")
    print(f"Current Metrics: {result['current_metrics']}")
    
    return result

if __name__ == "__main__":
    # Run test
    test_result = test_email_notification()
    print("\nTest completed successfully!")
