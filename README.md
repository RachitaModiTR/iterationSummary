# Azure DevOps Sprint Report Generator

This Python script fetches work items from Azure DevOps, analyzes completed work, generates a burndown chart, and creates a comprehensive PowerPoint presentation for sprint reporting.

## Features

- Fetches work items from Azure DevOps for the current sprint
- Filters work items by completion status ('Done', 'Completed', 'Closed')
- Analyzes total work items and story points completed
- Generates a burndown chart visualization
- Creates a PowerPoint presentation with:
  - Sprint Summary slide
  - Completed Work Items table
  - Burndown Chart
  - Key Highlights & Blockers (template)

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Azure DevOps Personal Access Token** with appropriate permissions
3. Access to the Azure DevOps project: `tr-tax/TaxProf`

## Setup Instructions

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

### 2. Create Azure DevOps Personal Access Token

1. Go to Azure DevOps: https://dev.azure.com/tr-tax
2. Click on your profile picture → Personal access tokens
3. Click "New Token"
4. Set the following permissions:
   - **Work Items**: Read
   - **Project and Team**: Read
5. Copy the generated token (you'll need this when running the script)

### 3. Run the Script

```bash
cd "/Users/rachitamodi/Downloads/Iteration summary"
python azure_devops_sprint_report.py
```

When prompted, enter your Personal Access Token.

## Configuration

The script is pre-configured for:
- **Organization**: tr-tax
- **Project**: TaxProf  
- **Team**: ADGE-Prep
- **Board URL**: https://dev.azure.com/tr-tax/TaxProf/_boards/board/t/ADGE-Prep/Stories

If you need to modify these settings, edit the variables in the `main()` function.

## Output Files

The script generates:
1. **Sprint_Summary_Report.pptx** - Complete PowerPoint presentation
2. **burndown_chart.png** - Burndown chart image

## Troubleshooting

### Common Issues:

1. **Authentication Error (401)**
   - Verify your Personal Access Token is correct
   - Ensure the token has proper permissions (Work Items: Read, Project and Team: Read)

2. **No Current Iteration Found**
   - Check if there's an active sprint/iteration
   - Verify team configuration in Azure DevOps

3. **No Work Items Found**
   - Confirm the iteration path is correct
   - Check if work items exist in the current sprint

4. **Import Errors**
   - Run `pip install -r requirements.txt` to install dependencies
   - Ensure you're using Python 3.7+

### API Limitations:

- The burndown chart uses simulated data based on current work item states
- For accurate historical burndown data, you would need to track daily work item state changes
- The script fetches the current active iteration automatically

## Customization

You can modify the script to:
- Change the completed work item states (currently: 'Done', 'Completed', 'Closed')
- Adjust the PowerPoint slide layouts and formatting
- Add additional work item fields to the analysis
- Customize the burndown chart appearance

## Security Note

Never commit your Personal Access Token to version control. The script prompts for the token at runtime for security.
