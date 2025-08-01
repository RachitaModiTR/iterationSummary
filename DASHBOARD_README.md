# 🚀 Azure DevOps Sprint Dashboard

An interactive web-based dashboard for analyzing Azure DevOps sprint data with comprehensive cycle time analysis, work categorization, and visual analytics.

## 📊 Features

### 🎯 Overview Tab
- **Key Metrics**: Total work items, completion rate, story points delivered, average cycle time
- **Sprint Configuration**: Organization, project, team, and iteration details
- **Real-time Data**: Live connection to Azure DevOps API

### 🔄 Cycle Time Analysis
- **Statistical Analysis**: Average, median, and maximum cycle times
- **Distribution Charts**: Histogram showing cycle time patterns
- **Bottleneck Identification**: Items taking longer than expected (Average + 1 Standard Deviation)
- **Detailed Drill-down**: Click on items to see activation and completion dates

### 📋 Work Categories
- **Intelligent Categorization**: Automatic classification into:
  - **Frontend**: UI/UX, buttons, screens, Angular components
  - **Backend**: APIs, services, databases, AWS Lambda
  - **Testing/QA**: Automated testing, validation, deployment checks
  - **Bug Fixes**: Bug resolution and fixes
  - **Investigate**: Research and investigation tasks
- **Interactive Pie Charts**: Visual breakdown by items and story points
- **Category Deep-dive**: Select categories to view detailed work items

### 📈 Visual Analytics
- **Status Distribution**: Work items by current status
- **Team Workload**: Items and story points by assignee
- **Cycle Time by Category**: Performance comparison across work types
- **Story Points Distribution**: Complexity analysis

### 🔍 Detailed View
- **Advanced Filtering**: Filter by status, type, category, and assignee
- **Search Functionality**: Find specific work items by title
- **Customizable Columns**: Choose which data to display
- **CSV Export**: Download filtered data for external analysis

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- Azure DevOps Personal Access Token (PAT)

### Quick Start
1. **Clone or download the files**:
   - `azure_devops_dashboard.py`
   - `config.py`
   - `run_dashboard.py`

2. **Install dependencies**:
   ```bash
   pip install streamlit plotly pandas requests
   ```

3. **Run the dashboard**:
   ```bash
   python run_dashboard.py
   ```
   Or directly:
   ```bash
   streamlit run azure_devops_dashboard.py
   ```

4. **Access the dashboard**:
   - Open your browser to `http://localhost:8501`
   - Enter your Azure DevOps PAT token in the sidebar
   - Click "Fetch Data" to load your sprint information

## 🔑 Azure DevOps Setup

### Creating a Personal Access Token (PAT)
1. Go to `https://dev.azure.com/[your-org]/_usersSettings/tokens`
2. Click "New Token"
3. Give it a descriptive name (e.g., "Sprint Dashboard")
4. Select scope: **Work Items (Read)**
5. Set expiration as needed
6. Copy the generated token (save it securely!)

### Configuration
Update `config.py` with your Azure DevOps details:
```python
AZURE_DEVOPS_CONFIG = {
    "organization": "your-org",
    "project": "your-project", 
    "team": "your-team"
}

SPRINT_CONFIG = {
    "iteration_path": "your-iteration-path",
    "area_path": "your-area-path"
}
```

## 📱 Dashboard Navigation

### Sidebar Controls
- **PAT Token Input**: Secure token entry (password field)
- **Fetch Data Button**: Retrieves latest data from Azure DevOps
- **Data Caching**: Fetched data is cached in session for performance

### Tab Structure
1. **📊 Overview**: High-level sprint metrics and configuration
2. **🔄 Cycle Time**: Detailed cycle time analysis and bottlenecks
3. **📋 Work Categories**: Work breakdown and category analysis
4. **📈 Charts**: Visual analytics and team performance
5. **🔍 Detailed View**: Advanced filtering and data export

## 🎨 Interactive Features

### Click-to-Explore
- **Category Selection**: Click categories to see detailed work items
- **Expandable Items**: Click work items to see full details
- **Chart Interactions**: Hover over charts for detailed information

### Filtering & Search
- **Multi-select Filters**: Filter by multiple criteria simultaneously
- **Real-time Search**: Search work item titles as you type
- **Dynamic Updates**: Filters update counts and displays instantly

### Data Export
- **CSV Download**: Export filtered data with timestamp
- **Custom Columns**: Choose which fields to include in export
- **Formatted Data**: Clean, readable format for external analysis

## 🔧 Customization

### Adding New Categories
Modify the `categorize_work_item` method in `azure_devops_dashboard.py`:
```python
# Add new keywords for categorization
new_category_keywords = ['keyword1', 'keyword2', 'keyword3']
```

### Changing Metrics
Update the metrics calculation in the overview tab:
```python
# Add custom metrics
custom_metric = df['custom_field'].sum()
st.metric("Custom Metric", custom_metric)
```

### Styling
Streamlit supports custom CSS through `st.markdown()`:
```python
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)
```

## 🚨 Troubleshooting

### Common Issues

**"Failed to fetch data"**
- Check your PAT token has correct permissions
- Verify organization/project names in config.py
- Ensure network connectivity to Azure DevOps

**"No work items found"**
- Verify iteration path and area path are correct
- Check if work items exist in the specified sprint
- Confirm work item types match your project setup

**Dashboard won't start**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.9+ required)
- Verify port 8501 is available

**Slow performance**
- Use "Fetch Data" button sparingly (data is cached)
- Filter data before exporting large datasets
- Close unused browser tabs

### Performance Tips
- **Data Caching**: Fetched data persists in session
- **Selective Loading**: Only fetch when needed
- **Efficient Filtering**: Use multiple filters to narrow results
- **Browser Resources**: Close other tabs for better performance

## 📊 Data Analysis Tips

### Cycle Time Analysis
- **Look for Patterns**: Items consistently taking longer may indicate process issues
- **Category Comparison**: Compare cycle times across work types
- **Team Performance**: Identify if specific assignees need support

### Work Distribution
- **Balance Check**: Ensure work is distributed across categories
- **Capacity Planning**: Use story points for future sprint planning
- **Skill Gaps**: Identify areas where team needs more expertise

### Sprint Health
- **Completion Rate**: Target 85%+ completion for healthy sprints
- **Scope Creep**: Monitor if work items are added mid-sprint
- **Blockers**: Use cycle time data to identify bottlenecks

## 🔄 Updates & Maintenance

### Regular Updates
- **Refresh Data**: Click "Fetch Data" for latest information
- **Token Renewal**: Update PAT tokens before expiration
- **Configuration**: Update sprint paths for new iterations

### Version Control
- Keep `config.py` in version control (without sensitive data)
- Use environment variables for PAT tokens in production
- Document configuration changes for team members

## 🤝 Contributing

### Adding Features
1. Fork the repository
2. Create feature branch
3. Add new functionality to appropriate tab
4. Test with real Azure DevOps data
5. Submit pull request

### Reporting Issues
- Include error messages and screenshots
- Provide Azure DevOps configuration (without sensitive data)
- Describe expected vs actual behavior

## 📄 License

This project is open source. Feel free to modify and distribute according to your organization's needs.

---

**Happy Sprint Analysis! 🎉**

For questions or support, please refer to the troubleshooting section or create an issue in the repository.
