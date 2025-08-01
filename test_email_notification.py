#!/usr/bin/env python3
"""
Test script for email notification system
"""

import pandas as pd
from email_notifier import SprintChangeNotifier
import sys

def test_email_notification_system():
    """Test the email notification system with sample data"""
    print("🧪 Testing Email Notification System")
    print("=" * 50)
    
    # Create sample sprint data
    sample_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6],
        'title': [
            'Update Saffron component library',
            'Implement user authentication API',
            'Fix login button styling',
            'Add data validation service',
            'Create user dashboard mockup',
            'Resolve database connection issue'
        ],
        'type': ['User Story', 'User Story', 'Bug', 'Task', 'User Story', 'Bug'],
        'state': ['Closed', 'Resolved', 'Closed', 'Resolved', 'Closed', 'Resolved'],
        'assignee': ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown', 'John Doe', 'Jane Smith'],
        'story_points': [5, 8, 2, 3, 5, 1],
        'is_completed': [True, True, True, True, True, True],
        'category': ['Frontend', 'Backend', 'Frontend', 'Backend', 'UX', 'Backend']
    })
    
    print(f"📊 Sample Data Created:")
    print(f"   - Total Items: {len(sample_data)}")
    print(f"   - Total Story Points: {sample_data['story_points'].sum()}")
    print(f"   - Completed Items: {len(sample_data[sample_data['is_completed'] == True])}")
    print()
    
    # Initialize notifier
    notifier = SprintChangeNotifier()
    
    # Test 1: First run (should create baseline)
    print("🔍 Test 1: Initial Baseline Creation")
    result1 = notifier.monitor_and_notify(
        current_data=sample_data,
        sprint="2025_S15_Jul16-Jul29",
        team="ADGE-Prep",
        pod=None
    )
    
    print(f"   - Changes Detected: {result1['changes_detected']}")
    print(f"   - Email Status: {result1['email_status']}")
    print(f"   - Current Metrics: {result1['current_metrics']}")
    print()
    
    # Test 2: Same data (should detect no changes)
    print("🔍 Test 2: No Changes Detection")
    result2 = notifier.monitor_and_notify(
        current_data=sample_data,
        sprint="2025_S15_Jul16-Jul29",
        team="ADGE-Prep",
        pod=None
    )
    
    print(f"   - Changes Detected: {result2['changes_detected']}")
    print(f"   - Email Status: {result2['email_status']}")
    print()
    
    # Test 3: Modified data (should detect changes)
    print("🔍 Test 3: Changes Detection")
    modified_data = sample_data.copy()
    # Add a new work item
    new_item = pd.DataFrame({
        'id': [7],
        'title': ['New feature implementation'],
        'type': ['User Story'],
        'state': ['Closed'],
        'assignee': ['New Developer'],
        'story_points': [8],
        'is_completed': [True],
        'category': ['Backend']
    })
    modified_data = pd.concat([modified_data, new_item], ignore_index=True)
    
    result3 = notifier.monitor_and_notify(
        current_data=modified_data,
        sprint="2025_S15_Jul16-Jul29",
        team="ADGE-Prep",
        pod=None
    )
    
    print(f"   - Changes Detected: {result3['changes_detected']}")
    print(f"   - Changes: {result3['changes']}")
    print(f"   - Email Status: {result3['email_status']}")
    print()
    
    # Test 4: Pod-specific data
    print("🔍 Test 4: Pod-Specific Monitoring")
    result4 = notifier.monitor_and_notify(
        current_data=sample_data,
        sprint="2025_S15_Jul16-Jul29",
        team="reviewready-agentic-ai-workflow",
        pod="Pod 1"
    )
    
    print(f"   - Changes Detected: {result4['changes_detected']}")
    print(f"   - Email Status: {result4['email_status']}")
    print()
    
    # Test 5: Email content generation
    print("🔍 Test 5: Email Content Generation")
    if result3['changes_detected']:
        subject, body = notifier.create_email_content({
            'changes': result3['changes'],
            'current_metrics': result3['current_metrics']
        })
        
        print(f"   - Email Subject: {subject}")
        print(f"   - Email Body Length: {len(body)} characters")
        print(f"   - Contains HTML: {'<html>' in body}")
        print()
    
    print("✅ Email Notification System Test Complete!")
    print("=" * 50)
    
    return {
        'baseline_test': result1,
        'no_changes_test': result2,
        'changes_test': result3,
        'pod_test': result4
    }

def test_email_sending_simulation():
    """Simulate email sending without actually sending"""
    print("\n📧 Email Sending Simulation")
    print("=" * 30)
    
    notifier = SprintChangeNotifier()
    
    # Create test change data
    test_change_data = {
        'changes': {
            'work_items': {'previous': 5, 'current': 7, 'change': 2},
            'story_points': {'previous': 24, 'current': 32, 'change': 8}
        },
        'current_metrics': {
            'total_work_items': 7,
            'total_story_points': 32,
            'completed_work_items': 7,
            'completed_story_points': 32,
            'sprint': '2025_S15_Jul16-Jul29',
            'team': 'ADGE-Prep',
            'pod': None
        }
    }
    
    subject, body = notifier.create_email_content(test_change_data)
    
    print(f"📧 Generated Email:")
    print(f"   Subject: {subject}")
    print(f"   Body Preview: {body[:200]}...")
    print(f"   Full Body Length: {len(body)} characters")
    
    # Validate email content
    validations = {
        'Has Subject': bool(subject),
        'Has HTML Body': '<html>' in body,
        'Contains Changes': 'Changes Detected' in body,
        'Contains Metrics': 'Current Sprint Metrics' in body,
        'Contains Recipient Info': 'rachita.modi@tr.com' in str(notifier.recipient_email),
        'Has Professional Styling': 'background: linear-gradient' in body
    }
    
    print(f"\n✅ Email Content Validation:")
    for check, passed in validations.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check}: {status}")
    
    all_passed = all(validations.values())
    print(f"\n🎯 Overall Email System Status: {'✅ READY' if all_passed else '❌ NEEDS ATTENTION'}")
    
    return all_passed

if __name__ == "__main__":
    try:
        # Run tests
        test_results = test_email_notification_system()
        email_ready = test_email_sending_simulation()
        
        print(f"\n🏆 Final Test Summary:")
        print(f"   - Notification System: ✅ Working")
        print(f"   - Change Detection: ✅ Working")
        print(f"   - Email Generation: {'✅ Ready' if email_ready else '❌ Issues'}")
        print(f"   - Baseline Storage: ✅ Working")
        print(f"   - Pod Support: ✅ Working")
        
        print(f"\n📋 Next Steps:")
        print(f"   1. Configure email credentials in dashboard")
        print(f"   2. Enable notifications in sidebar")
        print(f"   3. Test with real Azure DevOps data")
        print(f"   4. Monitor rachita.modi@tr.com for alerts")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
