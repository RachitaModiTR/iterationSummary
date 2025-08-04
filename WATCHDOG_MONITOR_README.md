# 👁️ Azure DevOps Data Monitor with Watchdog

## Overview

The Azure DevOps Sprint Dashboard now includes a powerful **Data Monitor** feature powered by the Python `watchdog` library. This feature provides real-time file system monitoring capabilities to track changes to Azure DevOps data files and other project-related documents.

## 🚀 Features

### Real-Time File Monitoring
- **Live Detection**: Automatically detects file creation, modification, and deletion events
- **Smart Filtering**: Monitors specific file types (JSON, CSV, Excel, TXT)
- **Azure DevOps Recognition**: Automatically identifies Azure DevOps data files
- **Content Analysis**: Extracts metadata like record counts and data types

### Dashboard Integration
- **New Tab**: Dedicated "👁️ Data Monitor" tab in the dashboard
- **Visual Statistics**: Charts showing file types and data sources
- **Recent Changes**: Real-time display of file modifications
- **Control Panel**: Start/stop monitoring with simple buttons

### Intelligent Analysis
- **Content Detection**: Recognizes Azure DevOps JSON structures
- **Record Counting**: Counts work items and data records
- **File Classification**: Categorizes files by content type
- **Change History**: Maintains log of all file system events

## 📦 Installation

The watchdog module has been added to the project requirements:

```bash
# Install all dependencies including watchdog
pip install -r requirements.txt

# Or install watchdog separately
pip install watchdog==3.0.0
```

## 🔧 Usage

### 1. Dashboard Integration

Access the Data Monitor through the dashboard:

1. Start the dashboard: `python3 run_dashboard.py`
2. Navigate to the "👁️ Data Monitor" tab
3. Set the directory to monitor (default: `./data`)
4. Click "🚀 Start Monitor" to begin watching
5. View real-time statistics and file changes
6. Click "🛑 Stop Monitor" when done

### 2. Standalone Testing

Test the monitoring functionality independently:

```bash
# Run the test script
python3 test_monitor.py
```

This will:
- Create sample Azure DevOps data files
- Start monitoring the `./data` directory
- Demonstrate file creation, modification, and deletion events
- Show monitoring statistics
- Clean up test files (optional)

### 3. Programmatic Usage

Use the monitor in your own scripts:

```python
from azure_data_monitor import start_monitoring, stop_monitoring

def file_change_callback(file_info):
    print(f"File changed: {file_info['file_name']}")
    if 'work_items' in file_info:
        print(f"Azure DevOps work items: {file_info['work_items']}")

# Start monitoring
observer, handler = start_monitoring("./data", file_change_callback)

# Your code here...

# Stop monitoring
stop_monitoring(observer)
```

## 📁 Monitored File Types

The monitor tracks the following file types:

| Extension | Description | Analysis Features |
|-----------|-------------|-------------------|
| `.json` | JSON data files | Record counting, Azure DevOps detection |
| `.csv` | CSV data exports | Column analysis, record counting |
| `.xlsx`, `.xls` | Excel spreadsheets | Sheet analysis, data structure |
| `.txt` | Text files and logs | Line counting, content analysis |

## 🎯 Azure DevOps Detection

The monitor automatically identifies Azure DevOps data files by looking for:

### JSON Files
- `fields` property in work item objects
- `System.Id` fields
- Azure DevOps API response structures

### CSV Files
- Common Azure DevOps column names:
  - `id`, `title`, `state`, `assignee`, `story_points`
  - Case-insensitive matching

## 📊 Dashboard Features

### Control Panel
- **Directory Input**: Specify which directory to monitor
- **Start/Stop Buttons**: Control monitoring state
- **Status Indicator**: Shows active/inactive monitoring status

### Statistics Display
- **Total Events**: Count of all file system events
- **File Types**: Breakdown of monitored file extensions
- **Data Sources**: Identified data source types
- **Recent Events**: Last 10 file system events

### Visual Analytics
- **File Types Chart**: Pie chart showing file type distribution
- **Data Sources Chart**: Bar chart of detected data sources
- **Recent Changes**: Expandable list with detailed file information

### Change History
- **Event Details**: File name, size, timestamp, event type
- **Content Analysis**: Record counts, data source identification
- **Azure DevOps Info**: Work item counts for recognized files
- **Clear History**: Button to reset change log

## 🔍 Use Cases

### Development Workflow
- **Data Pipeline Monitoring**: Track Azure DevOps data exports and imports
- **File Change Detection**: Monitor when sprint data files are updated
- **Automated Processing**: Trigger actions when new data arrives
- **Quality Assurance**: Verify data file integrity and structure

### Sprint Management
- **Data Freshness**: Know when Azure DevOps data was last updated
- **Export Tracking**: Monitor CSV exports from Azure DevOps
- **Report Generation**: Detect when new reports are available
- **Backup Monitoring**: Track data backup and archival processes

### Team Collaboration
- **Shared Data**: Monitor shared data directories for team updates
- **Version Control**: Track changes to data files outside Git
- **Integration Points**: Monitor API response caches and data stores
- **Workflow Automation**: Trigger dashboard refreshes on data changes

## 🛠️ Technical Implementation

### Core Components

#### `AzureDataMonitor` Class
- Extends `FileSystemEventHandler` from watchdog
- Implements event handlers for file creation, modification, deletion
- Provides content analysis and metadata extraction
- Maintains change history and statistics

#### Key Methods
- `on_modified()`: Handles file modification events
- `on_created()`: Handles file creation events  
- `on_deleted()`: Handles file deletion events
- `analyze_file_content()`: Extracts file metadata
- `get_monitoring_stats()`: Returns monitoring statistics

#### Dashboard Integration
- `render_data_monitor_tab()`: Dashboard tab implementation
- Session state management for monitoring status
- Real-time statistics display and visualization
- Interactive controls for start/stop functionality

### File Analysis Features

#### JSON Analysis
```python
# Detects Azure DevOps structures
if 'fields' in first_item or 'System.Id' in str(first_item):
    analysis['data_source'] = 'azure_devops'
    analysis['work_items'] = len(data)
```

#### CSV Analysis
```python
# Identifies Azure DevOps columns
azure_columns = ['id', 'title', 'state', 'assignee', 'story_points']
if any(col.lower() in [c.lower() for c in df.columns] for col in azure_columns):
    analysis['data_source'] = 'azure_devops'
```

## 📝 Configuration

### Monitoring Settings
- **Directory**: Default `./data`, configurable via dashboard
- **File Types**: JSON, CSV, Excel, TXT (configurable in code)
- **Cooldown**: 2-second cooldown to prevent duplicate events
- **History Limit**: Keeps last 1000 events, last 50 in session state

### Performance Considerations
- **Event Throttling**: Prevents excessive processing of rapid file changes
- **Memory Management**: Limits stored events to prevent memory leaks
- **Background Processing**: Monitoring runs in separate thread
- **Resource Cleanup**: Proper observer shutdown and resource cleanup

## 🚨 Error Handling

### Common Issues and Solutions

#### Permission Errors
```python
# Monitor handles permission errors gracefully
try:
    file_info = analyze_file_content(file_path)
except PermissionError:
    logging.warning(f"Permission denied: {file_path}")
```

#### File Lock Issues
```python
# Cooldown prevents processing locked files
if current_time - self.last_processed[file_path] < 2:
    return  # Skip if processed recently
```

#### Invalid File Formats
```python
# Graceful handling of corrupted files
try:
    data = json.load(f)
except json.JSONDecodeError:
    analysis['analysis_error'] = "Invalid JSON format"
```

## 🔮 Future Enhancements

### Planned Features
- **Email Notifications**: Send alerts when important files change
- **Webhook Integration**: Trigger external systems on file changes
- **Advanced Filtering**: Custom file patterns and exclusion rules
- **Cloud Storage**: Monitor cloud storage directories (S3, Azure Blob)
- **Database Integration**: Store monitoring events in database
- **Performance Metrics**: Track file processing times and system load

### Integration Opportunities
- **CI/CD Pipelines**: Trigger builds when data files change
- **Slack/Teams**: Send notifications to team channels
- **Azure DevOps**: Create work items when issues detected
- **Power BI**: Refresh reports when data sources update
- **Automated Testing**: Run data validation when files change

## 📚 Examples

### Basic Monitoring
```python
from azure_data_monitor import start_monitoring, stop_monitoring

# Simple callback
def on_change(file_info):
    print(f"Changed: {file_info['file_name']}")

observer, handler = start_monitoring("./data", on_change)
# ... do work ...
stop_monitoring(observer)
```

### Advanced Analysis
```python
def detailed_callback(file_info):
    if file_info['event_type'] == 'created':
        print(f"New file: {file_info['file_name']}")
        
    if 'data_source' in file_info:
        if file_info['data_source'] == 'azure_devops':
            print(f"Azure DevOps data detected!")
            if 'work_items' in file_info:
                print(f"Work items: {file_info['work_items']}")
    
    if 'record_count' in file_info:
        print(f"Records: {file_info['record_count']}")
```

### Dashboard Integration
```python
# In Streamlit dashboard
if st.button("Start Monitor"):
    observer, handler = start_monitoring(directory, callback)
    st.session_state.monitor_active = True
    st.success("Monitor started!")
```

## 🤝 Contributing

To contribute to the Data Monitor functionality:

1. **Test Changes**: Run `python3 test_monitor.py` to verify functionality
2. **Update Documentation**: Keep this README current with new features
3. **Add Tests**: Include test cases for new monitoring capabilities
4. **Performance**: Consider impact on dashboard performance
5. **Error Handling**: Ensure graceful handling of edge cases

## 📄 License

This monitoring functionality is part of the Azure DevOps Sprint Dashboard project and follows the same licensing terms.

---

**Happy Monitoring! 👁️📊**

*The Data Monitor feature enhances your Azure DevOps workflow by providing real-time visibility into data file changes, ensuring you always have the most current information for sprint analysis and reporting.*
