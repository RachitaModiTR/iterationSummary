"""
Configuration file for Azure DevOps Sprint Report Generator

Modify these settings according to your Azure DevOps setup.
"""

# Azure DevOps Configuration
AZURE_DEVOPS_CONFIG = {
    # Organization name from your Azure DevOps URL
    # Example: https://dev.azure.com/YOUR_ORGANIZATION/
    "organization": "tr-tax",
    
    # Project name
    "project": "TaxProf",
    
    # Team name
    "team": "ADGE-Prep",
    
    # API version (usually doesn't need to be changed)
    "api_version": "6.0"
}

# Work Item States Configuration
# Define which states should be considered as "completed"
COMPLETED_STATES = [
    "Done",
    "Completed", 
    "Closed",
    "Resolved"  # Add more states as needed
]

# Work Item Types Configuration
# Define which work item types to include in the report
WORK_ITEM_TYPES = [
    "Bug",
    "User Story", 
    "Investigate"
]

# Sprint Configuration
SPRINT_CONFIG = {
    "iteration_path": "TaxProf\\2025\\Q3\\2025_S15_Jul16-Jul29",
    "area_path": "TaxProf\\us\\taxAuto\\ADGE\\Prep"
}

# Report Configuration
REPORT_CONFIG = {
    # Output file names
    "powerpoint_filename": "Sprint_Summary_Report.pptx",
    "burndown_chart_filename": "burndown_chart.png",
    
    # Chart settings
    "chart_width": 12,
    "chart_height": 8,
    "chart_dpi": 300,
    
    # PowerPoint settings
    "slide_title_font_size": 18,
    "slide_content_font_size": 14,
    "table_max_title_length": 50
}

# Iteration Path Configuration
# If you need to specify a custom iteration path, uncomment and modify:
# CUSTOM_ITERATION_PATH = "TaxProf\\ADGE-Prep\\Sprint 1"

# Field Mappings (Azure DevOps field names)
FIELD_MAPPINGS = {
    "id": "System.Id",
    "title": "System.Title",
    "work_item_type": "System.WorkItemType",
    "state": "System.State",
    "assigned_to": "System.AssignedTo",
    "story_points": "Microsoft.VSTS.Scheduling.StoryPoints",
    "created_date": "System.CreatedDate",
    "state_change_date": "Microsoft.VSTS.Common.StateChangeDate",
    "iteration_path": "System.IterationPath"
}
