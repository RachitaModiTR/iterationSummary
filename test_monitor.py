#!/usr/bin/env python3
"""
Test script for Azure Data Monitor
Demonstrates the watchdog file monitoring functionality
"""

import time
import json
import csv
from pathlib import Path
from azure_data_monitor import start_monitoring, stop_monitoring

def create_test_files():
    """Create test files to demonstrate monitoring"""
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    print("📁 Creating test files...")
    
    # Create a sample Azure DevOps JSON file
    azure_data = [
        {
            "id": 12345,
            "fields": {
                "System.Id": 12345,
                "System.Title": "Test work item",
                "System.WorkItemType": "User Story",
                "System.State": "Active",
                "System.AssignedTo": {"displayName": "Test User"},
                "Microsoft.VSTS.Scheduling.StoryPoints": 5
            }
        },
        {
            "id": 12346,
            "fields": {
                "System.Id": 12346,
                "System.Title": "Another test item",
                "System.WorkItemType": "Bug",
                "System.State": "Resolved",
                "System.AssignedTo": {"displayName": "Another User"},
                "Microsoft.VSTS.Scheduling.StoryPoints": 3
            }
        }
    ]
    
    with open(data_dir / "azure_work_items.json", "w") as f:
        json.dump(azure_data, f, indent=2)
    print("✅ Created azure_work_items.json")
    
    # Create a sample CSV file
    csv_data = [
        ["id", "title", "state", "assignee", "story_points"],
        [12345, "Test work item", "Active", "Test User", 5],
        [12346, "Another test item", "Resolved", "Another User", 3]
    ]
    
    with open(data_dir / "work_items.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print("✅ Created work_items.csv")
    
    # Create a text log file
    with open(data_dir / "sprint_log.txt", "w") as f:
        f.write("Sprint Log\n")
        f.write("==========\n")
        f.write("Sprint started: 2025-07-16\n")
        f.write("Team: ADGE-Prep\n")
        f.write("Total items: 33\n")
    print("✅ Created sprint_log.txt")

def modify_test_files():
    """Modify test files to trigger monitoring events"""
    data_dir = Path("./data")
    
    print("\n🔄 Modifying test files...")
    
    # Modify JSON file
    time.sleep(1)
    azure_file = data_dir / "azure_work_items.json"
    if azure_file.exists():
        with open(azure_file, "r") as f:
            data = json.load(f)
        
        # Add a new work item
        data.append({
            "id": 12347,
            "fields": {
                "System.Id": 12347,
                "System.Title": "New work item added",
                "System.WorkItemType": "Task",
                "System.State": "New",
                "System.AssignedTo": {"displayName": "New User"},
                "Microsoft.VSTS.Scheduling.StoryPoints": 2
            }
        })
        
        with open(azure_file, "w") as f:
            json.dump(data, f, indent=2)
        print("✅ Modified azure_work_items.json (added new item)")
    
    # Modify text file
    time.sleep(1)
    log_file = data_dir / "sprint_log.txt"
    if log_file.exists():
        with open(log_file, "a") as f:
            f.write(f"Update: {time.strftime('%Y-%m-%d %H:%M:%S')} - File monitoring test\n")
        print("✅ Modified sprint_log.txt (added log entry)")
    
    # Create a new file
    time.sleep(1)
    new_file = data_dir / "new_data.json"
    with open(new_file, "w") as f:
        json.dump({"test": "new file created", "timestamp": time.time()}, f, indent=2)
    print("✅ Created new_data.json")

def cleanup_test_files():
    """Clean up test files"""
    data_dir = Path("./data")
    
    print("\n🧹 Cleaning up test files...")
    
    test_files = [
        "azure_work_items.json",
        "work_items.csv", 
        "sprint_log.txt",
        "new_data.json",
        "monitoring_log.json"
    ]
    
    for filename in test_files:
        file_path = data_dir / filename
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️ Deleted {filename}")

def main():
    """Main test function"""
    print("🔍 Azure Data Monitor Test")
    print("=" * 50)
    
    def data_change_callback(file_info):
        """Callback function to handle file changes"""
        print(f"\n🔔 DETECTED: {file_info['event_type'].upper()} - {file_info['file_name']}")
        print(f"   📁 Size: {file_info['file_size']} bytes")
        print(f"   📅 Time: {file_info['timestamp'][:19]}")
        
        if 'record_count' in file_info:
            print(f"   📊 Records: {file_info['record_count']}")
        if 'data_source' in file_info:
            print(f"   🎯 Source: {file_info['data_source']}")
        if 'work_items' in file_info:
            print(f"   📋 Work Items: {file_info['work_items']}")
    
    try:
        # Start monitoring
        print("🚀 Starting file monitor...")
        observer, monitor = start_monitoring("./data", data_change_callback)
        
        print("✅ Monitor started successfully!")
        print("📁 Monitoring directory: ./data")
        print("\n" + "=" * 50)
        
        # Create initial test files
        create_test_files()
        
        print("\n⏳ Waiting 3 seconds for initial file events...")
        time.sleep(3)
        
        # Modify files to trigger more events
        modify_test_files()
        
        print("\n⏳ Waiting 3 seconds for modification events...")
        time.sleep(3)
        
        # Show monitoring statistics
        print("\n📊 Monitoring Statistics:")
        print("-" * 30)
        stats = monitor.get_monitoring_stats()
        
        if 'error' not in stats:
            print(f"Total Events: {stats['total_events']}")
            print(f"File Types: {list(stats['file_types'].keys())}")
            if stats['data_sources']:
                print(f"Data Sources: {list(stats['data_sources'].keys())}")
            
            print(f"\nRecent Events ({len(stats['recent_events'])}):")
            for event in stats['recent_events'][-5:]:  # Show last 5
                print(f"  • {event['event']}")
        else:
            print(f"Error: {stats['error']}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed successfully!")
        print("💡 You can now use the Data Monitor tab in the dashboard")
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
    finally:
        # Stop monitoring
        if 'observer' in locals():
            print("\n🛑 Stopping monitor...")
            stop_monitoring(observer)
        
        # Ask user if they want to clean up
        try:
            cleanup = input("\n🧹 Clean up test files? (y/N): ").lower().strip()
            if cleanup in ['y', 'yes']:
                cleanup_test_files()
                print("✅ Cleanup completed")
            else:
                print("📁 Test files kept in ./data directory")
        except (EOFError, KeyboardInterrupt):
            print("\n📁 Test files kept in ./data directory")

if __name__ == "__main__":
    main()
