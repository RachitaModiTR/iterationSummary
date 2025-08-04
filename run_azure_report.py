#!/usr/bin/env python3
"""
Azure DevOps Sprint Report Runner
This script runs the Azure DevOps sprint report generator with the updated configuration.
"""

import os
import sys
from azure_devops_sprint_report import main
from config import AZURE_DEVOPS_CONFIG, SPRINT_CONFIG, WORK_ITEM_TYPES, COMPLETED_STATES

def run_report():
    print("Azure DevOps Sprint Report Generator")
    print("=" * 50)
    
    # Display configuration
    print("Configuration:")
    print(f"  Organization: {AZURE_DEVOPS_CONFIG['organization']}")
    print(f"  Project: {AZURE_DEVOPS_CONFIG['project']}")
    print(f"  Team: {AZURE_DEVOPS_CONFIG['team']}")
    print(f"  Sprint: {SPRINT_CONFIG['iteration_path']}")
    print(f"  Area Path: {SPRINT_CONFIG['area_path']}")
    print(f"  Work Item Types: {', '.join(WORK_ITEM_TYPES)}")
    print(f"  Completed States: {', '.join(COMPLETED_STATES)}")
    print()
    
    # Check for Personal Access Token
    pat = os.environ.get('AZURE_DEVOPS_PAT')
    if not pat:
        print("Personal Access Token Setup:")
        print("You can either:")
        print("1. Set the AZURE_DEVOPS_PAT environment variable")
        print("2. Enter it when prompted below")
        print()
        print("To create a PAT:")
        print("- Go to https://dev.azure.com/tr-tax/_usersSettings/tokens")
        print("- Click 'New Token'")
        print("- Give it a name and select 'Work Items (Read)' scope")
        print("- Copy the generated token")
        print()
        
        pat = input("Enter your Personal Access Token: ").strip()
        if not pat:
            print("Error: Personal Access Token is required!")
            sys.exit(1)
        
        # Set environment variable for the main script
        os.environ['AZURE_DEVOPS_PAT'] = pat
    
    print("Starting report generation...")
    print()
    
    try:
        # Run the main report generation
        main()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your Personal Access Token is valid")
        print("2. Check that you have access to the specified project/team")
        print("3. Ensure the organization, project, and team names are correct")
        print("4. Make sure your PAT has 'Work Items (Read)' permissions")
        print("5. Verify the iteration path and area path are correct")
        sys.exit(1)

if __name__ == "__main__":
    run_report()
