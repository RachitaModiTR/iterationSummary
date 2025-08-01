# Azure DevOps Sprint Dashboard - Complete Implementation Prompt
**Date Created:** August 1, 2025  
**Version:** 2.0 - Enhanced with UX Categories, Tags Integration, and Burndown Fixes

## 🎯 Project Overview

Create a comprehensive Azure DevOps Sprint Dashboard using Streamlit that fetches work items from Azure DevOps API, analyzes sprint data, and provides detailed insights with interactive visualizations.

## 📋 Core Requirements

### 1. **Data Fetching & Processing**
- Fetch work items from Azure DevOps using WIQL queries
- Support multiple teams: ADGE-Prep, ADGE-Deliver, ADGE-Gather, reviewready-agentic-ai-workflow
- Include all essential fields: ID, Title, Type, State, Assignee, Story Points, Dates, **Tags**
- Process and categorize work items with enhanced logic
- Calculate cycle times and performance metrics

### 2. **Enhanced Work Item Categorization**
**Priority-Based Classification System:**
1. **🎨 UX Category (Highest Priority)**
   - **Tags-Based Detection**: Check `System.Tags` field for "UXE" tag first
   - **Title Keywords**: ux, user experience, usability, wireframe, mockup, prototype
   - **Rule**: If UXE tag exists, categorize as UX regardless of other keywords

2. **🧪 SQA Category (Second Priority)**
   - **Keywords**: sqa, software quality, quality assurance, qa engineer, qa lead

3. **🖥️ Frontend Category**
   - **Keywords**: frontend, fe, ui, button, screen, angular, saffron, component

4. **⚙️ Backend Category**
   - **Keywords**: backend, api, service, endpoint, database, deprecate, workflow

5. ** Bug Category**
   - **Work Item Type**: Bug

### 3. **Dashboard Tabs Structure**

#### **Tab 1: 📊 Overview**
1. **Sprint Success Metrics** - Performance indicators
2. **Key Metrics** - Essential sprint data with cards
3. **Sprint Configuration** - Team and project settings
4. **Sprint Summary** - Complete analysis including:
   - Sprint Overview (period, team, completion rate, story points)
   - Cycle Time Analysis (average, long-running items)
   - **Work Breakdown by Category** (proper Streamlit table format)
   - Key Highlights (dynamic content generation)
   - Items That Took Longer to Resolve
   - Sprint Success Metrics
5. **Sprint Hero** - Top performer analysis
6. **Azure DevOps Board** - Board URL and data source

#### **Tab 2: 📉 Burndown/Burnup**
- **Fixed Burndown Logic**: Count ALL completed items (Closed + Resolved states)
- Sprint timeline: July 16-29, 2025 (2025_S15_Jul16-Jul29)
- Burndown charts for both story count and story points
- Burnup charts showing completed work progression
- **Critical Fix**: Items without completion dates counted on last day
- Trend analysis and velocity projections

#### **Tab 3: 🔄 Cycle Time**
- Performance categorization (Fast ≤7 days, Normal 8-14 days, Slow >14 days)
- Cycle time statistics and distribution
- Long-running items analysis with thresholds

#### **Tab 4: 📋 Work Categories**
- Category breakdown with percentages
- Interactive pie charts for items and story points
- Detailed category view with item listings

#### **Tab 5: 📈 Charts**
- Status distribution charts
- Team workload analysis
- Cycle time by category
- Story points distribution

#### **Tab 6: 🔍 Detailed View**
- Filterable work items table
- Search functionality
- Export to CSV capability
- Column selection options

#### **Tab 7: 👁️ Data Monitor**
- Real-time file monitoring
- Statistics and change tracking
- File type analysis
- Data source detection

#### **Tab 8: 🔄 Recent Changes**
- **Top 5 Recently Changed Items**: Most recently modified work items
- **Enhanced History Column**: Detailed change summaries with specific values
- **Change Analysis**: Comprehensive revision history analysis
- **Smart Change Detection**: State, assignee, story points, title, iteration changes
- **Detailed Change Summaries**: Natural language descriptions of modifications
- **Revision Timeline**: Complete audit trail with user attribution

## 🔧 Technical Implementation Details

### **Azure DevOps API Integration**
```python
# Enhanced WIQL Query with Tags
wiql_query = {
    "query": f"""
    SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], 
           [System.AssignedTo], [Microsoft.VSTS.Scheduling.StoryPoints], 
           [System.CreatedDate], [Microsoft.VSTS.Common.StateChangeDate],
           [System.IterationPath], [System.AreaPath], [Microsoft.VSTS.Common.ActivatedDate],
           [Microsoft.VSTS.Common.ResolvedDate], [Microsoft.VSTS.Common.ClosedDate],
           [System.Tags]
    FROM WorkItems 
    WHERE [System.IterationPath] = '{iteration_path}'
    AND [System.AreaPath] UNDER '{area_path}'
    AND [System.WorkItemType] IN ('{work_item_types_filter}')
    ORDER BY [System.Id]
    """
}
```

### **Enhanced Categorization Logic**
```python
def categorize_work_item(self, title, work_type, tags=""):
    title_lower = title.lower()
    tags_lower = tags.lower() if tags else ""
    
    if work_type == 'Bug':
        return 'Bug'
    
    # Check tags first for UXE priority
    if 'uxe' in tags_lower:
        return 'UX'
    
    # Then check title keywords in priority order
    # UX keywords, SQA keywords, Frontend, Backend, Testing/QA
    # Return 'Other' if no matches
```

### **Fixed Burndown Chart Logic**
```python
# Count all completed items properly
if item['state'] in COMPLETED_STATES:
    completion_date = get_completion_date(item)
    
    if completion_date and completion_date <= current_date:
        completed_by_date_items += 1
        completed_by_date_points += item['story_points']
    elif not completion_date and current_date == end_date:
        # Count items without dates on last day
        completed_by_date_items += 1
        completed_by_date_points += item['story_points']
```

### **Work Breakdown Table Format**
```python
# Use Streamlit table instead of markdown
table_data = []
for _, row in category_breakdown.iterrows():
    points_pct = (row['Story Points'] / total_category_points * 100) if total_category_points > 0 else 0
    table_data.append({
        'Category': row['Category'],
        'Items': row['Items'],
        'Percentage': f"{row['Item %']:.1f}%",
        'Story Points': row['Story Points'],
        'Points %': f"{points_pct:.1f}%"
    })

table_df = pd.DataFrame(table_data)
st.table(table_df)
```

### **Recent Changes Implementation**
```python
# Fetch work item revision history
def fetch_work_item_revisions(work_item_id, pat_token):
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}/revisions?api-version=6.0"
    response = requests.get(url, headers=headers)
    return response.json().get('value', [])

# Enhanced History Column with specific change details
def get_brief_change_summary(revision_history):
    changes = []
    change_details = {}
    
    # Compare consecutive revisions
    for i in range(1, len(revision_history)):
        prev_fields = revision_history[i-1].get('fields', {})
        curr_fields = revision_history[i].get('fields', {})
        
        # State changes: "State: Active→Resolved"
        if prev_fields.get('System.State') != curr_fields.get('System.State'):
            change_details['State'] = f"{prev_fields.get('System.State', '')}→{curr_fields.get('System.State', '')}"
        
        # Story points: "Points: 3→5"
        if prev_fields.get('Microsoft.VSTS.Scheduling.StoryPoints') != curr_fields.get('Microsoft.VSTS.Scheduling.StoryPoints'):
            change_details['Points'] = f"{prev_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0)}→{curr_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0)}"
        
        # Assignee changes: "Assignee: John→Jane"
        prev_assignee = prev_fields.get('System.AssignedTo', {}).get('displayName', '').split()[0] if prev_fields.get('System.AssignedTo') else 'None'
        curr_assignee = curr_fields.get('System.AssignedTo', {}).get('displayName', '').split()[0] if curr_fields.get('System.AssignedTo') else 'None'
        if prev_assignee != curr_assignee:
            change_details['Assignee'] = f"{prev_assignee}→{curr_assignee}"
    
    # Format output: "State: Active→Resolved, Points: 3→5"
    if len(change_details) == 1:
        key, value = list(change_details.items())[0]
        return f"{key}: {value}"
    elif len(change_details) <= 3:
        return ", ".join([f"{k}: {v}" for k, v in change_details.items()])
    else:
        first_two = list(change_details.items())[:2]
        return f"{first_two[0][0]}: {first_two[0][1]}, {first_two[1][0]}: {first_two[1][1]}, +{len(change_details)-2} more"
```

## 🎨 UI/UX Design Requirements

### **Color Scheme - Pastel Colors**
```python
PASTEL_COLORS = {
    'primary': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFD1BA', '#E1BAFF'],
    'performance': ['#98FB98', '#F0E68C', '#FFB6C1'],
    'categories': ['#E6E6FA', '#F0F8FF', '#F5FFFA', '#FFF8DC', '#FFE4E1', '#F0FFFF'],
    'success': ['#90EE90', '#98FB98', '#AFEEEE'],
    'warning': ['#FFFFE0', '#F0E68C', '#DDA0DD'],
    'hero': ['#FFE4B5', '#FFDAB9', '#FFE4E1']
}
```

### **Custom CSS Styling**
- Gradient backgrounds for cards
- Professional metric displays
- Responsive layout design
- Clean typography and spacing

## 📊 Key Features & Enhancements

### **1. UX Category Integration**
- **Priority Detection**: UXE tags override all other categorization
- **Comprehensive Keywords**: Full UX terminology coverage
- **Proper Recognition**: UX specialists get dedicated category

### **2. Enhanced Sprint Analysis**
- **Dynamic Content**: Team-specific analysis and highlights
- **Intelligent Patterns**: Automatic detection of sprint focus areas
- **Contextual Insights**: Category-based highlight generation

### **3. Fixed Burndown Charts**
- **Complete Item Counting**: All 31 completed items (20 Closed + 11 Resolved)
- **Accurate Metrics**: Proper completion rates and velocity
- **Realistic Projections**: Trend analysis based on actual data

### **4. Professional Table Display**
- **Streamlit Tables**: Clean, aligned table formatting
- **Complete Data**: No truncation of categories or values
- **Percentage Calculations**: Both item and story point percentages

### **5. Sprint Hero Analysis**
- **Multi-Factor Scoring**: Story points, efficiency, complexity, volume
- **Performance Metrics**: Hero score and efficiency calculations
- **Category Specialization**: Primary work area identification

### **6. Recent Changes Analysis**
- **Top 5 Recently Changed Items**: Identifies most recently modified work items
- **Enhanced History Column**: Shows specific change details with before/after values
- **Revision History Integration**: Fetches complete change history from Azure DevOps API
- **Smart Change Detection**: Analyzes state, assignee, story points, title, and iteration changes
- **Natural Language Summaries**: Generates readable descriptions of work item evolution
- **Change Pattern Recognition**: Identifies workflow patterns and collaboration dynamics

## 🔍 Data Monitoring & Real-time Updates

### **File Monitoring System**
- **Watchdog Integration**: Real-time file change detection
- **Smart Analysis**: Automatic Azure DevOps data file identification
- **Statistics Tracking**: File types, data sources, activity patterns
- **Change History**: Recent modifications with metadata

## 📈 Sprint Configuration

### **Current Sprint Details**
- **Sprint Period**: July 16-29, 2025 (2025_S15_Jul16-Jul29)
- **Iteration Path**: TaxProf\2025\Q3\2025_S15_Jul16-Jul29
- **Teams Supported**: ADGE-Prep, ADGE-Deliver, ADGE-Gather, reviewready-agentic-ai-workflow
- **Work Item Types**: User Story, Task, Bug, Investigate

### **Team-Specific Area Paths**
- **ADGE-Prep**: ADGE\Prep
- **ADGE-Deliver**: ADGE\Deliver  
- **ADGE-Gather**: ADGE\Gather
- **reviewready-agentic-ai-workflow**: TaxProf\us\taxAuto\agenticaiworkflow

### **Team-Specific Tag Filters**
- **ADGE Teams**: No tag filtering applied
- **reviewready-agentic-ai-workflow**: Dynamic pod selection with dropdown (Pod 1, Pod 2, Pod 3, Pod 4, Pod 5)

### **Dynamic Pod Selection**
- **Pod Dropdown**: Appears only when reviewready-agentic-ai-workflow team is selected
- **Pod Options**: Pod 1, Pod 2, Pod 3, Pod 4, Pod 5
- **Tag Filtering**: Work items filtered by selected pod tag (e.g., "Pod 1", "Pod 2", etc.)
- **Default Selection**: Pod 1 is selected by default

## 🚀 Deployment & Usage

### **Required Dependencies**
```python
streamlit
pandas
plotly
requests
base64
datetime
watchdog  # For file monitoring
```

### **Configuration Files**
- **config.py**: Azure DevOps settings, completed states, work item types
- **azure_data_monitor.py**: File monitoring and change detection
- **requirements.txt**: All Python dependencies

### **Authentication**
- **PAT Token**: Azure DevOps Personal Access Token with Work Items (Read) scope
- **Secure Input**: Password-masked token input in sidebar
- **Token Instructions**: Built-in guidance for token creation

## 📋 Quality Assurance & Testing

### **Data Validation**
- **API Response Handling**: Proper error handling and user feedback
- **Data Processing**: Robust handling of missing or null values
- **Date Parsing**: Safe datetime conversion with fallbacks

### **Performance Optimization**
- **Caching**: Session state for work items data
- **Efficient Queries**: Optimized WIQL queries with necessary fields only
- **Responsive UI**: Fast loading with progress indicators

## 🎯 Success Metrics

### **Dashboard Effectiveness**
- **Complete Data Coverage**: All work items properly categorized
- **Accurate Metrics**: Correct completion rates and burndown charts
- **User Experience**: Intuitive navigation and professional presentation
- **Real-time Insights**: Dynamic content generation and monitoring

### **Sprint Analysis Quality**
- **Category Accuracy**: UX items properly identified via tags
- **Performance Tracking**: Comprehensive cycle time and velocity analysis
- **Team Recognition**: Sprint Hero identification and performance metrics
- **Actionable Insights**: Clear highlights and recommendations

## 📝 Implementation Notes

### **Critical Requirements**
1. **UXE Tag Priority**: Must check tags field before title keywords
2. **Complete Item Counting**: All Closed/Resolved items in burndown
3. **Table Format**: Use st.table() for Work Breakdown by Category
4. **Team Dynamics**: Support all four teams with proper area paths
5. **Date Handling**: Robust completion date parsing and fallbacks

### **Enhancement Opportunities**
- **Export Functionality**: PowerPoint generation for sprint reviews
- **Advanced Analytics**: Predictive modeling for sprint completion
- **Integration Options**: Slack/Teams notifications for sprint updates
- **Historical Tracking**: Multi-sprint comparison and trend analysis

---

**This prompt represents the complete implementation requirements for the Azure DevOps Sprint Dashboard with all enhancements, fixes, and optimizations implemented as of August 1, 2025.**
