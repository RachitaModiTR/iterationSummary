# Azure DevOps Sprint Report Generator

This tool automatically fetches work items from your Azure DevOps board, analyzes completed work, and generates a comprehensive PowerPoint presentation for sprint reviews.

## Features

- ✅ Fetches work items from Azure DevOps for the current sprint
- ✅ Filters for 'Resolved' and 'Closed' work items
- ✅ Calculates total story points completed
- ✅ Identifies important work items for review meetings
- ✅ Generates burndown chart visualization
- ✅ Creates professional PowerPoint presentation
- ✅ Exports as .pptx file

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Azure DevOps Personal Access Token** with Work Items (Read) permissions
3. **Access** to the Azure DevOps project and team

## Installation

1. Install required Python packages:
```bash
pip install -r requirements.txt
```

The requirements include:
- `requests` - For Azure DevOps API calls
- `pandas` - For data analysis
- `matplotlib` - For burndown chart generation
- `python-pptx` - For PowerPoint presentation creation

## Configuration

The system is now configured for the specific sprint:
- **Organization**: tr-tax
- **Project**: TaxProf
- **Team**: ADGE-Prep
- **Sprint**: 2025_S15_Jul16-Jul29
- **Area Path**: TaxProf\us\taxAuto\ADGE\Prep
- **Work Item Types**: Bug, User Story, Investigate
- **Completed States**: Done, Completed, Closed, Resolved

If you need to change these settings, edit the configuration in `config.py`.

## Getting Your Personal Access Token

1. Go to [Azure DevOps Personal Access Tokens](https://dev.azure.com/tr-tax/_usersSettings/tokens)
2. Click "New Token"
3. Give it a descriptive name (e.g., "Sprint Report Generator")
4. Set expiration as needed
5. Under "Scopes", select "Work Items (Read)"
6. Click "Create"
7. **Important**: Copy the token immediately - you won't be able to see it again!

## Usage

### Method 1: Run the simplified script
```bash
python run_azure_report.py
```

### Method 2: Run the main script directly
```bash
python azure_devops_sprint_report.py
```

### Method 3: Set environment variable (recommended for automation)
```bash
export AZURE_DEVOPS_PAT="your_personal_access_token_here"
python run_azure_report.py
```

## Output Files

The tool generates two main files:

1. **Azure_DevOps_Sprint_Report.pptx** - Complete PowerPoint presentation
2. **burndown_chart.png** - Burndown chart image

## PowerPoint Presentation Structure

### Slide 1: Sprint Summary
- Sprint name and dates
- Team information
- Total completed work items
- Total story points completed

### Slide 2: Completed Work Items
- Table format with ID, Title, Type, and Assignee
- All work items marked as 'Resolved' or 'Closed'

### Slide 3: Burndown Chart
- Visual representation of remaining work over time
- Ideal vs. actual burndown lines

### Slide 4: Important Work Items for Review
- Automatically identified high-priority items based on:
  - High story points (≥5 points)
  - Important work item types (Feature, User Story, Epic)
  - Keywords in title (critical, important, major, feature, integration, security, performance)

### Slide 5: Key Highlights & Blockers
- Template slide for manual input during review meetings

## Work Item Analysis

The tool automatically identifies important work items using these criteria:

1. **High Story Points**: Items with 5 or more story points
2. **Important Types**: Features, User Stories, Epics
3. **Keywords**: Items containing words like:
   - critical, important, major
   - feature, integration
   - security, performance

## Troubleshooting

### Common Issues

1. **"Could not find current iteration"**
   - Check that you have access to the specified team
   - Verify the organization, project, and team names are correct
   - Ensure there's an active sprint/iteration

2. **"No completed work items found"**
   - Verify work items are marked as 'Resolved' or 'Closed'
   - Check that work items are assigned to the current iteration
   - Confirm you have permission to view work items

3. **Authentication errors**
   - Verify your Personal Access Token is valid and not expired
   - Ensure the PAT has 'Work Items (Read)' permissions
   - Check that you have access to the specified project

4. **API errors**
   - Check your internet connection
   - Verify the Azure DevOps service is accessible
   - Try regenerating your Personal Access Token

### Debug Information

The script provides detailed output including:
- Connection status
- Iteration information
- Work item counts
- Error messages with troubleshooting tips

## Customization

### Modifying Important Item Criteria

Edit the `identify_important_work_items` method in `azure_devops_sprint_report.py`:

```python
# Change story point threshold
if item['story_points'] >= 3:  # Changed from 5 to 3

# Add more work item types
if item['type'].lower() in ['feature', 'user story', 'epic', 'bug']:

# Add more keywords
important_keywords = ['critical', 'important', 'major', 'urgent', 'blocker']
```

### Changing Output Filenames

Modify the file paths in `run_azure_report.py`:

```python
pptx_path = "My_Sprint_Report.pptx"
chart_path = "my_burndown_chart.png"
```

### Customizing PowerPoint Slides

The presentation layout can be modified in the `create_powerpoint_presentation` method. You can:
- Change slide layouts
- Modify fonts and colors
- Add company branding
- Adjust table columns
- Add more slides

## API Limitations

- The burndown chart uses simulated data since historical state changes require additional API calls
- For real burndown data, you would need to track work item state changes over time
- The tool fetches data for the current iteration only

## Security Notes

- Never commit your Personal Access Token to version control
- Use environment variables for automation
- Regularly rotate your access tokens
- Follow your organization's security policies

## Support

For issues related to:
- **Azure DevOps API**: Check Microsoft's Azure DevOps REST API documentation
- **Python dependencies**: Refer to individual package documentation
- **Script functionality**: Review the error messages and troubleshooting section

## File Structure

```
├── azure_devops_sprint_report.py  # Main report generator class
├── run_azure_report.py           # Simplified runner script
├── config.py                     # Configuration settings
├── requirements.txt              # Python dependencies
├── AZURE_DEVOPS_README.md       # This documentation
├── Azure_DevOps_Sprint_Report.pptx  # Generated presentation
└── burndown_chart.png           # Generated chart
```

## Version History

- **v1.0**: Initial release with basic functionality
- **v1.1**: Added important work items identification
- **v1.2**: Enhanced PowerPoint presentation with 5 slides
- **v1.3**: Added comprehensive error handling and documentation
