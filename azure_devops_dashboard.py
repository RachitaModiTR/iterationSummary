# Page configuration - MUST be first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="Azure DevOps Sprint Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import requests
import json
import base64
import os
import threading
from datetime import datetime, timedelta

# Plotly imports with error handling
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Plotly import failed: {e}")
    print (f"❌ Plotly import failed: {e}")
    st.error("Please install plotly: pip install plotly")
    PLOTLY_AVAILABLE = False
    # Create dummy functions to prevent errors
    class DummyPlotly:
        def __init__(self):
            pass
        def pie(self, *args, **kwargs):
            return None
        def bar(self, *args, **kwargs):
            return None
        def histogram(self, *args, **kwargs):
            return None
        def scatter(self, *args, **kwargs):
            return None
    
    class DummyGO:
        def __init__(self):
            pass
        def Figure(self, *args, **kwargs):
            return None
        def Pie(self, *args, **kwargs):
            return None
        def Bar(self, *args, **kwargs):
            return None
        def Scatter(self, *args, **kwargs):
            return None
    
    px = DummyPlotly()
    go = DummyGO()

# Config imports with error handling
try:
    from config import AZURE_DEVOPS_CONFIG, COMPLETED_STATES, WORK_ITEM_TYPES, SPRINT_CONFIG
except ImportError as e:
    st.error(f"❌ Config import failed: {e}")
    # Provide default config
    AZURE_DEVOPS_CONFIG = {
        "organization": "tr-tax",
        "project": "TaxProf"
    }
    COMPLETED_STATES = ['Closed', 'Resolved']
    WORK_ITEM_TYPES = ['User Story', 'Bug', 'Task']
    SPRINT_CONFIG = {
        "area_path": "TaxProf\\ADGE\\Prep",
        "iteration_path": "TaxProf\\2025\\Q3\\2025_S15_Jul16-Jul29"
    }

# Email notifier import with error handling
try:
    from email_notifier import SprintChangeNotifier
    EMAIL_NOTIFIER_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Email notifier not available: {e}")
    EMAIL_NOTIFIER_AVAILABLE = False
    class DummyNotifier:
        def monitor_and_notify(self, *args, **kwargs):
            return {'changes_detected': False, 'email_sent': False, 'email_status': 'Email notifier not available'}
    SprintChangeNotifier = DummyNotifier

# Centralized date parsing functions - all return datetime objects for consistency
def parse_azure_date_to_datetime(date_str):
    """Parse Azure DevOps date string and return datetime object normalized to date only"""
    if not date_str:
        return None
    
    try:
        # First, try to extract YYYY-MM-DD format directly from the string
        if len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
            date_part = date_str[:10]  # Extract YYYY-MM-DD
            return datetime.strptime(date_part, '%Y-%m-%d')
        
        # Handle various Azure DevOps date formats with full ISO parsing
        clean_date_str = date_str
        
        # Handle fractional seconds by removing them entirely
        if '.' in clean_date_str and ('Z' in clean_date_str or '+' in clean_date_str):
            date_part = clean_date_str.split('.')[0]
            if 'Z' in clean_date_str:
                clean_date_str = date_part + 'Z'
            elif '+' in clean_date_str:
                tz_part = clean_date_str.split('+')[1] if '+' in clean_date_str else '00:00'
                clean_date_str = date_part + '+' + tz_part
        
        # Replace Z with timezone offset for consistent parsing
        if clean_date_str.endswith('Z'):
            clean_date_str = clean_date_str.replace('Z', '+00:00')
        
        # Parse the datetime and return date part only
        dt = datetime.fromisoformat(clean_date_str)
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)  # Normalize to date only
        
    except Exception:
        # Final fallback: try various common date formats
        try:
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str[:19], fmt).replace(hour=0, minute=0, second=0, microsecond=0)
                except:
                    continue
        except Exception:
            pass
        return None

def format_date_for_display(date_obj):
    """Format datetime object for display as YYYY-MM-DD string"""
    if date_obj is None:
        return 'Missing'
    
    # Handle pandas NaT (Not a Time) values
    if pd.isna(date_obj):
        return 'Missing'
    
    if isinstance(date_obj, str):
        # If it's still a string, parse it first
        date_obj = parse_azure_date_to_datetime(date_obj)
        if date_obj is None:
            return 'Invalid Date'
    
    try:
        return date_obj.strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return 'Invalid Date'

def date_to_string(date_obj):
    """Convert datetime object to YYYY-MM-DD string for compatibility"""
    if date_obj is None:
        return None
    
    if isinstance(date_obj, str):
        # If it's already a string, try to parse and reformat
        parsed = parse_azure_date_to_datetime(date_obj)
        return parsed.strftime('%Y-%m-%d') if parsed else None
    
    return date_obj.strftime('%Y-%m-%d')

# Optional imports for monitoring features
try:
    from azure_data_monitor import AzureDataMonitor, start_monitoring, stop_monitoring
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    # Create dummy functions if monitoring is not available
    def start_monitoring(*args, **kwargs):
        return None, None
    def stop_monitoring(*args, **kwargs):
        pass

# Enhanced CSS for beautiful, professional dashboard styling with full width
st.markdown("""
<style>
    /* AGGRESSIVE FULL WIDTH OVERRIDES */
    .main .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Target all possible Streamlit container classes */
    .css-1d391kg, .css-1lcbmhc, .css-18e3th9, .css-1y4p8pa, .css-12oz5g7 {
        max-width: none !important;
        width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* Main app container */
    .stApp > div {
        max-width: none !important;
        width: 100% !important;
        padding: 0 !important;
    }
    
    /* Main content area */
    .main > div {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Streamlit's main container */
    section.main > div {
        max-width: none !important;
        width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    /* Additional container overrides */
    .css-k1vhr4, .css-1kyxreq, .css-17eq0hr {
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Remove any margin auto that centers content */
    .main .block-container, .css-1d391kg, .css-1lcbmhc {
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    
    /* Ensure tabs and content use full width */
    .stTabs [data-baseweb="tab-list"], .stTabs [data-baseweb="tab-panel"] {
        width: 100% !important;
        max-width: none !important;
    }
    
    /* Full width for all content elements */
    .element-container, .stMarkdown, .stDataFrame, .stPlotlyChart {
        width: 100% !important;
        max-width: none !important;
    }
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Enhanced Metric Cards */
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin: 0.5rem 0;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    
    /* Beautiful Card Styles */
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(240, 147, 251, 0.3);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .hero-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(252, 182, 159, 0.4);
        border: 1px solid rgba(255,255,255,0.3);
        position: relative;
        overflow: hidden;
    }
    
    .hero-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%);
        pointer-events: none;
    }
    
    .success-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 2rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 6px 24px rgba(168, 237, 234, 0.3);
        border-left: 4px solid #4ecdc4;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 2rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 6px 24px rgba(255, 234, 167, 0.3);
        border-left: 4px solid #fdcb6e;
    }
    
    .info-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 6px 24px rgba(116, 185, 255, 0.3);
        border-left: 4px solid #0984e3;
    }
    
    /* Enhanced Section Headers */
    .section-header {
        color: #2d3436;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 2.5rem 0 1.5rem 0;
        padding: 1rem 0;
        border-bottom: 3px solid transparent;
        background: linear-gradient(90deg, #667eea, #764ba2) padding-box,
                    linear-gradient(90deg, #667eea, #764ba2) border-box;
        border-image: linear-gradient(90deg, #667eea, #764ba2) 1;
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    /* Beautiful Highlight Text */
    .highlight-text {
        background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-weight: 600;
        color: #2d3436;
        display: inline-block;
        margin: 0.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Enhanced Tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(90deg, #f8f9fa, #ffffff);
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background: transparent;
        border-radius: 8px;
        color: #636e72;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        border-right: 1px solid #e9ecef;
    }
    
    /* Button Enhancements */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 10px;
        border: 1px solid #e9ecef;
        padding: 1rem;
        margin: 0.5rem 0;
        font-weight: 600;
        color: #2d3436;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Alert Boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Success Alert */
    .stAlert[data-baseweb="notification"] [data-testid="stNotificationContentSuccess"] {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
    }
    
    /* Warning Alert */
    .stAlert[data-baseweb="notification"] [data-testid="stNotificationContentWarning"] {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
    }
    
    /* Info Alert */
    .stAlert[data-baseweb="notification"] [data-testid="stNotificationContentInfo"] {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
    }
    
    /* Plotly Chart Containers */
    .js-plotly-plot {
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        overflow: hidden;
        margin: 1rem 0;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem;
        }
        
        .hero-card, .metric-card {
            padding: 1.5rem;
        }
        
        .section-header {
            font-size: 1.4rem;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .stMetric {
            background: linear-gradient(135deg, #2d3436 0%, #636e72 100%);
            color: white;
        }
        
        .section-header {
            color: #ddd;
        }
    }
</style>
""", unsafe_allow_html=True)

# Pastel color palettes for charts
PASTEL_COLORS = {
    'primary': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFD1BA', '#E1BAFF'],
    'performance': ['#98FB98', '#F0E68C', '#FFB6C1'],  # Light green, khaki, light pink
    'categories': ['#E6E6FA', '#F0F8FF', '#F5FFFA', '#FFF8DC', '#FFE4E1', '#F0FFFF'],
    'success': ['#90EE90', '#98FB98', '#AFEEEE'],  # Light greens and cyan
    'warning': ['#FFFFE0', '#F0E68C', '#DDA0DD'],  # Light yellows and plum
    'hero': ['#FFE4B5', '#FFDAB9', '#FFE4E1']  # Moccasin, peach puff, misty rose
}

class AzureDevOpsDashboard:
    def __init__(self):
        self.data = None
        self.work_items = None
        
    def get_azure_devops_data(self, pat_token, selected_team="ADGE-Prep", selected_pod=None, selected_sprint="2025_S15_Jul16-Jul29"):
        """Fetch data from Azure DevOps API"""
        organization = AZURE_DEVOPS_CONFIG["organization"]
        project = AZURE_DEVOPS_CONFIG["project"]
        base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f":{pat_token}".encode()).decode()}',
            'Content-Type': 'application/json'
        }
        
        # Construct dynamic iteration path based on selected sprint
        iteration_path = f"TaxProf\\2025\\Q3\\{selected_sprint}"
        
        # Handle different team path structures
        if selected_team.startswith("ADGE-"):
            # For ADGE teams, use the pattern ADGE\{team_suffix}
            team_suffix = selected_team.split('-')[1]  # Get "Prep", "Deliver", "Gather"
            area_path = SPRINT_CONFIG["area_path"].replace("ADGE\\Prep", f"ADGE\\{team_suffix}")
        elif selected_team == "reviewready-agentic-ai-workflow":
            # For the agentic AI workflow team, use the correct area path
            area_path = "TaxProf\\us\\taxAuto\\agenticaiworkflow"
        else:
            # For other teams, use the team name directly
            area_path = selected_team
        
        # WIQL query - include Tags field and pod1 filter for reviewready-agentic-ai-workflow team
        work_item_types_filter = "', '".join(WORK_ITEM_TYPES)
        
        # Add dynamic pod tag filter for reviewready-agentic-ai-workflow team
        tag_filter = ""
        if selected_team == "reviewready-agentic-ai-workflow" and selected_pod:
            tag_filter = f"AND [System.Tags] CONTAINS '{selected_pod}'"
        
        wiql_query = {
            "query": f"""
            SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State], 
                   [System.AssignedTo], [Microsoft.VSTS.Scheduling.StoryPoints], 
                   [System.CreatedDate], [System.ChangedDate], [Microsoft.VSTS.Common.StateChangeDate],
                   [System.IterationPath], [System.AreaPath], [Microsoft.VSTS.Common.ActivatedDate],
                   [Microsoft.VSTS.Common.ResolvedDate], [Microsoft.VSTS.Common.ClosedDate],
                   [System.Tags], [Microsoft.VSTS.Common.ActivatedBy], [Microsoft.VSTS.Common.ResolvedBy],
                   [Microsoft.VSTS.Common.ClosedBy], [System.Reason]
            FROM WorkItems 
            WHERE [System.IterationPath] = '{iteration_path}'
            AND [System.AreaPath] UNDER '{area_path}'
            AND [System.WorkItemType] IN ('{work_item_types_filter}')
            {tag_filter}
            ORDER BY [System.Id]
            """
        }
        
        try:
            # Execute WIQL query
            url = f"{base_url}/wit/wiql?api-version=6.0"
            response = requests.post(url, headers=headers, json=wiql_query)
            
            if response.status_code == 200:
                work_item_ids = [item['id'] for item in response.json().get('workItems', [])]
                
                if work_item_ids:
                    # Get detailed work item information
                    ids_string = ','.join(map(str, work_item_ids))
                    details_url = f"{base_url}/wit/workitems?ids={ids_string}&api-version=6.0"
                    details_response = requests.get(details_url, headers=headers)
                    
                    if details_response.status_code == 200:
                        return details_response.json()['value']
            
            return []
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return []
    
    def process_work_items(self, raw_data):
        """Process raw Azure DevOps data into structured format"""
        processed_items = []
        
        for item in raw_data:
            fields = item['fields']
            
            # Extract assignee
            assignee = fields.get('System.AssignedTo', {})
            assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
            
            # Calculate cycle time with fallback approach
            cycle_time_days = None
            activated_date = fields.get('Microsoft.VSTS.Common.ActivatedDate', '')
            resolved_date = fields.get('Microsoft.VSTS.Common.ResolvedDate', '')
            closed_date = fields.get('Microsoft.VSTS.Common.ClosedDate', '')
            created_date = fields.get('System.CreatedDate', '')
            state_change_date = fields.get('Microsoft.VSTS.Common.StateChangeDate', '')
            
            # Convert all dates to datetime objects using the centralized function
            activated_date_dt = parse_azure_date_to_datetime(activated_date)
            resolved_date_dt = parse_azure_date_to_datetime(resolved_date)
            closed_date_dt = parse_azure_date_to_datetime(closed_date)
            created_date_dt = parse_azure_date_to_datetime(created_date)
            
            # Calculate cycle time using datetime objects (more reliable)
            cycle_time_days = None
            
            # Primary approach: ActivatedDate to ResolvedDate/ClosedDate
            if activated_date_dt and (resolved_date_dt or closed_date_dt):
                try:
                    completion_dt = resolved_date_dt if resolved_date_dt else closed_date_dt
                    
                    if completion_dt and completion_dt >= activated_date_dt:
                        cycle_time_days = (completion_dt - activated_date_dt).days
                except Exception:
                    pass  # Skip if date parsing fails
            
            # Fallback approach: CreatedDate to completion if no ActivatedDate
            if cycle_time_days is None and created_date_dt and (resolved_date_dt or closed_date_dt):
                try:
                    completion_dt = resolved_date_dt if resolved_date_dt else closed_date_dt
                    
                    if completion_dt and completion_dt >= created_date_dt:
                        cycle_time_days = (completion_dt - created_date_dt).days
                except Exception:
                    pass  # Skip if date parsing fails
            
            
            # Extract tags
            tags = fields.get('System.Tags', '') or ''
            
            # Categorize work item using title, type, and tags
            category = self.categorize_work_item(fields.get('System.Title', ''), fields.get('System.WorkItemType', ''), tags)
            
            processed_items.append({
                'id': item['id'],
                'title': fields.get('System.Title', ''),
                'type': fields.get('System.WorkItemType', ''),
                'state': fields.get('System.State', ''),
                'assignee': assignee_name,
                'story_points': fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0,
                'created_date': parse_azure_date_to_datetime(fields.get('System.CreatedDate', '')),
                'activated_date': activated_date_dt,
                'resolved_date': resolved_date_dt,
                'closed_date': closed_date_dt,
                'cycle_time_days': cycle_time_days,
                'category': category,
                'tags': tags,
                'is_completed': fields.get('System.State', '') in COMPLETED_STATES
            })
        
        return pd.DataFrame(processed_items)
    
    def categorize_work_item(self, title, work_type, tags=""):
        """Categorize work item based on title, type, and tags into 5 main categories: Frontend, Backend, UX, Bug, QA"""
        title_lower = title.lower()
        tags_lower = tags.lower() if tags else ""
        
        # Bug category - highest priority
        if work_type == 'Bug':
            return 'Bug'
        
        # UX category - check UXE tags first (highest priority for UX), then analyze title
        if 'uxe' in tags_lower:
            return 'UX'
        
        # Enhanced UX keywords - comprehensive list for UX work identification
        ux_keywords = [
            'ux ', 'user experience', 'usability', 'user interface design', 
            'interaction design', 'user research', 'wireframe', 'mockup', 'prototype',
            'user journey', 'persona', 'accessibility', 'user testing', 'design system',
            'visual design', 'information architecture', 'user flow', 'design pattern',
            'user story mapping', 'design thinking', 'user-centered', 'human-computer interaction'
        ]
        
        # Check UX keywords in title
        for keyword in ux_keywords:
            if keyword in title_lower:
                return 'UX'
        
        # QA category - comprehensive quality assurance keywords
        qa_keywords = [
            'qa', 'quality assurance', 'testing', 'test', 'sqa', 'software quality',
            'qa engineer', 'qa lead', 'test case', 'test plan', 'automation test',
            'regression test', 'integration test', 'unit test', 'performance test',
            'load test', 'security test', 'acceptance test', 'validation', 'verification'
        ]
        
        # Check QA keywords
        for keyword in qa_keywords:
            if keyword in title_lower:
                return 'QA'
        
        # Frontend keywords - comprehensive list for frontend work
        frontend_keywords = [
            'frontend', 'front-end', 'fe ', 'ui', 'user interface', 'button', 'screen', 
            'window', 'tab', 'grid', 'upload', 'branding', 'text', 'alert', 'breadcrumb', 
            'scroll', 'menu', 'welcome', 'settings', 'angular', 'saffron', 'component',
            'react', 'vue', 'javascript', 'typescript', 'css', 'html', 'scss', 'sass',
            'bootstrap', 'material-ui', 'responsive', 'mobile', 'web app', 'spa',
            'client-side', 'browser', 'dom', 'jquery', 'ajax', 'form', 'modal',
            'dropdown', 'navigation', 'header', 'footer', 'sidebar', 'layout'
        ]
        
        # Backend keywords - comprehensive list for backend work
        backend_keywords = [
            'backend', 'back-end', 'api', 'service', 'endpoint', 'lambda', 'aws', 
            'database', 'postgres', 'server', 'deprecate', 'ultratax', 'taxassistant', 
            'workflow', 'metric', 'email', 'microservice', 'rest', 'graphql', 'sql',
            'nosql', 'mongodb', 'redis', 'cache', 'queue', 'job', 'cron', 'batch',
            'authentication', 'authorization', 'security', 'encryption', 'token',
            'middleware', 'framework', 'spring', 'node.js', 'python', 'java',
            'docker', 'kubernetes', 'deployment', 'infrastructure', 'cloud',
            'integration', 'webhook', 'message', 'event', 'stream'
        ]
        
        # Check Frontend keywords
        for keyword in frontend_keywords:
            if keyword in title_lower:
                return 'Frontend'
        
        # Check Backend keywords
        for keyword in backend_keywords:
            if keyword in title_lower:
                return 'Backend'
        
        # Default to Frontend if no specific category is identified
        # This assumes most unclassified work items are likely frontend-related
        return 'Frontend'

def main():
    st.title("🚀 Azure DevOps Sprint Dashboard")
    st.markdown("---")
    
    # Initialize dashboard
    dashboard = AzureDevOpsDashboard()
    
    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # PAT Token input - moved to the top
    pat_token = st.sidebar.text_input(
        "Azure DevOps Personal Access Token",
        type="password",
        help="Enter your Azure DevOps PAT token"
    )
    
    # Sprint selection dropdown - above team dropdown
    sprint_options = [
        "2025_S14_Jul02-Jul15",
        "2025_S15_Jul16-Jul29", 
        "2025_S16_Jul30-Aug12",
        "2025_S17_Aug13-Aug26"
    ]
    selected_sprint = st.sidebar.selectbox(
        "Select Sprint:",
        options=sprint_options,
        index=1,  # Default to 2025_S15_Jul16-Jul29
        help="Select the sprint to analyze"
    )
    
    # Team selection dropdown - moved below sprint selection
    team_options = ["ADGE-Prep", "ADGE-Deliver", "ADGE-Gather", "reviewready-agentic-ai-workflow"]
    selected_team = st.sidebar.selectbox(
        "Select Team:",
        options=team_options,
        index=0,  # Default to ADGE-Prep
        help="Select the team to analyze"
    )
    
    # Pod selection dropdown - only show for reviewready-agentic-ai-workflow team
    selected_pod = None
    if selected_team == "reviewready-agentic-ai-workflow":
        pod_options = ["Pod 1", "Pod 2", "Pod 3", "Pod 4", "Pod 5"]
        selected_pod = st.sidebar.selectbox(
            "Pod:",
            options=pod_options,
            index=0,  # Default to Pod 1
            help="Select the pod to analyze"
        )
    
    # Fetch data button - moved above email notifications
    if st.sidebar.button("🔄 Fetch Data", type="primary"):
        if not pat_token:
            st.sidebar.error("Please enter your PAT token first!")
        else:
            with st.spinner(f"Fetching data from Azure DevOps for {selected_team}..."):
                raw_data = dashboard.get_azure_devops_data(pat_token, selected_team, selected_pod, selected_sprint)
                if raw_data:
                    dashboard.work_items = dashboard.process_work_items(raw_data)
                    st.session_state['work_items'] = dashboard.work_items
                    st.session_state['selected_team'] = selected_team  # Store selected team
                    st.session_state['selected_sprint'] = selected_sprint  # Store selected sprint
                    st.success(f"Successfully fetched {len(dashboard.work_items)} work items for {selected_team}!")
                    
                    # Check for changes and send notifications if enabled (after data fetch)
                    if 'enable_notifications' in locals() and enable_notifications and 'sender_email' in locals() and 'sender_password' in locals() and sender_email and sender_password:
                        with st.spinner("Checking for changes and sending notifications..."):
                            notifier = SprintChangeNotifier()
                            notification_result = notifier.monitor_and_notify(
                                current_data=dashboard.work_items,
                                sprint=selected_sprint,
                                team=selected_team,
                                pod=selected_pod,
                                sender_email=sender_email,
                                sender_password=sender_password
                            )
                            
                            if notification_result['changes_detected']:
                                if notification_result['email_sent']:
                                    st.success(f"📧 Email notification sent to rachita.modi@tr.com")
                                    st.info(f"Changes detected: {', '.join(notification_result['changes'].keys())}")
                                else:
                                    st.warning(f"⚠️ Changes detected but email failed: {notification_result['email_status']}")
                            else:
                                st.info("ℹ️ No changes detected since last check")
                    
                else:
                    st.error("Failed to fetch data. Please check your PAT token and configuration.")
    
    # Email notification settings
    st.sidebar.markdown("---")
    st.sidebar.subheader("📧 Email Notifications")
    
    enable_notifications = st.sidebar.checkbox(
        "Enable change notifications",
        value=False,
        help="Send email alerts when work items or story points change"
    )
    
    sender_email = None
    sender_password = None
    
    if enable_notifications:
        sender_email = st.sidebar.text_input(
            "Sender Email:",
            placeholder="your-email@gmail.com",
            help="Gmail address to send notifications from"
        )
        sender_password = st.sidebar.text_input(
            "App Password:",
            type="password",
            help="Gmail app password (not your regular password)"
        )
        
        if sender_email and sender_password:
            st.sidebar.success("✅ Email notifications configured")
        else:
            st.sidebar.warning("⚠️ Email credentials required for notifications")
    
    # Note: Fetch data button moved above - email notifications are checked during data fetch
    if False:  # Placeholder to maintain code structure
        if not pat_token:
            st.sidebar.error("Please enter your PAT token first!")
        else:
            with st.spinner(f"Fetching data from Azure DevOps for {selected_team}..."):
                raw_data = dashboard.get_azure_devops_data(pat_token, selected_team, selected_pod, selected_sprint)
                if raw_data:
                    dashboard.work_items = dashboard.process_work_items(raw_data)
                    st.session_state['work_items'] = dashboard.work_items
                    st.session_state['selected_team'] = selected_team  # Store selected team
                    st.success(f"Successfully fetched {len(dashboard.work_items)} work items for {selected_team}!")
                    
                    # Check for changes and send notifications if enabled
                    if enable_notifications and sender_email and sender_password:
                        with st.spinner("Checking for changes and sending notifications..."):
                            notifier = SprintChangeNotifier()
                            notification_result = notifier.monitor_and_notify(
                                current_data=dashboard.work_items,
                                sprint=selected_sprint,
                                team=selected_team,
                                pod=selected_pod,
                                sender_email=sender_email,
                                sender_password=sender_password
                            )
                            
                            if notification_result['changes_detected']:
                                if notification_result['email_sent']:
                                    st.success(f"📧 Email notification sent to rachita.modi@tr.com")
                                    st.info(f"Changes detected: {', '.join(notification_result['changes'].keys())}")
                                else:
                                    st.warning(f"⚠️ Changes detected but email failed: {notification_result['email_status']}")
                            else:
                                st.info("ℹ️ No changes detected since last check")
                    
                else:
                    st.error("Failed to fetch data. Please check your PAT token and configuration.")
    
    # Show PAT token instructions if not provided
    if not pat_token:
        st.warning("Please enter your Azure DevOps Personal Access Token in the sidebar to continue.")
        st.info("""
        To create a PAT token:
        1. Go to https://dev.azure.com/tr-tax/_usersSettings/tokens
        2. Click 'New Token'
        3. Give it a name and select 'Work Items (Read)' scope
        4. Copy the generated token
        """)
        # Add prepared by information at the bottom of sidebar when no data
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        **Prepared by:**  
        Rachita Modi  
        Technology Manager (Tax Evolution)
        """)
        return
    
    # Use cached data if available
    if 'work_items' in st.session_state:
        dashboard.work_items = st.session_state['work_items']
    
    if dashboard.work_items is None or dashboard.work_items.empty:
        st.info("Click 'Fetch Data' to load Azure DevOps work items.")
        # Add prepared by information at the bottom of sidebar when no data
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        **Prepared by:**  
        Rachita Modi  
        Technology Manager (Tax Evolution)
        """)
        return
    
    # Main dashboard content
    df = dashboard.work_items
    completed_df = df[df['is_completed'] == True]
    
    # Add prepared by information at the bottom of sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Prepared by:**  
    Rachita Modi  
    Technology Manager (Tax Evolution)
    """)
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Overview", 
        "📉 Burndown/Burnup", 
        "🔄 Cycle Time", 
        "📋 Work Categories", 
        "📈 Charts", 
        "🔍 Detailed View",
        "🔄 Recent Changes",
        "🤖 AI Assistant"
    ])
    
    with tab1:
        render_overview_tab(df, completed_df)
    
    with tab2:
        render_burndown_tab(df, completed_df)
    
    with tab3:
        render_cycle_time_tab(completed_df)
    
    with tab4:
        render_categories_tab(completed_df)
    
    with tab5:
        render_charts_tab(df, completed_df)
    
    with tab6:
        render_detailed_view_tab(df)
    
    with tab7:
        render_recent_changes_tab(df, pat_token)
    
    with tab8:
        render_ai_assistant_tab(df, completed_df)

def render_overview_tab(df, completed_df):
    """Render the overview tab"""
    st.header("Sprint Overview")
    
    # Calculate common metrics
    completion_rate = (len(completed_df) / len(df)) * 100 if len(df) > 0 else 0
    total_points = completed_df['story_points'].sum()
    cycle_time_items = completed_df[completed_df['cycle_time_days'].notna()]
    avg_cycle_time = cycle_time_items['cycle_time_days'].mean() if len(cycle_time_items) > 0 else 0
    
    # Work breakdown by category for success metrics
    category_breakdown = completed_df.groupby('category').agg({
        'id': 'count',
        'story_points': 'sum'
    }).reset_index()
    category_breakdown.columns = ['Category', 'Items', 'Story Points']
    
    # Calculate percentages
    total_items = category_breakdown['Items'].sum()
    category_breakdown['Item %'] = (category_breakdown['Items'] / total_items * 100).round(1) if total_items > 0 else 0
    
    # 1. Sprint Success Metrics - first
    st.subheader("📈 Sprint Success Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if completion_rate >= 85:
            st.success(f"✅ **{completion_rate:.1f}% completion rate** - Strong delivery performance")
        else:
            st.warning(f"⚠️ **{completion_rate:.1f}% completion rate** - Below target")
    
    with col2:
        if total_points > 0:
            st.success(f"✅ **{int(total_points)} story points delivered** - Met sprint capacity")
        else:
            st.warning("⚠️ **No story points delivered** - Review sprint planning")
    
    with col3:
        if not category_breakdown.empty:
            top_category = category_breakdown.loc[category_breakdown['Items'].idxmax()]
            if top_category['Item %'] > 50:
                st.info(f"🎯 **{top_category['Category']}-heavy sprint** - {top_category['Item %']:.1f}% of work")
            else:
                st.success("✅ **Balanced work distribution** - Good variety")
        else:
            st.info("ℹ️ **No categorized work** - Review work classification")
    
    # 2. Key metrics - second
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Work Items",
            len(df),
            delta=f"{len(completed_df)} completed"
        )
    
    with col2:
        # Calculate total story points targeted for the sprint (all items in scope)
        total_targeted_points = df['story_points'].sum()
        st.metric(
            "Total Story Points Targeted",
            int(total_targeted_points),
            delta=f"{len(df)} items in scope"
        )
    
    with col3:
        st.metric(
            "Completion Rate",
            f"{completion_rate:.1f}%",
            delta=f"{len(df) - len(completed_df)} remaining"
        )
    
    with col4:
        st.metric(
            "Story Points Delivered",
            int(total_points),
            delta=f"Avg: {total_points/len(completed_df):.1f}" if len(completed_df) > 0 else "0"
        )
    
    with col5:
        st.metric(
            "Avg Cycle Time",
            f"{avg_cycle_time:.1f} days",
            delta=f"{len(cycle_time_items)} items tracked"
        )
    
    # 3. Sprint Configuration - third
    st.subheader("⚙️ Sprint Configuration")
    col1, col2 = st.columns(2)
    
    # Get the current team and selected sprint dynamically
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    current_sprint = st.session_state.get('selected_sprint', '2025_S15_Jul16-Jul29')
    
    # Calculate area path based on selected team (same logic as in data fetching)
    if current_team.startswith("ADGE-"):
        team_suffix = current_team.split('-')[1]  # Get "Prep", "Deliver", "Gather"
        calculated_area_path = SPRINT_CONFIG["area_path"].replace("ADGE\\Prep", f"ADGE\\{team_suffix}")
    elif current_team == "reviewready-agentic-ai-workflow":
        calculated_area_path = "TaxProf\\us\\taxAuto\\agenticaiworkflow"
    else:
        calculated_area_path = current_team
    
    # Calculate dynamic iteration path based on selected sprint
    dynamic_iteration_path = f"TaxProf\\2025\\Q3\\{current_sprint}"
    
    with col1:
        st.info(f"""
        **Organization:** {AZURE_DEVOPS_CONFIG['organization']}  
        **Project:** {AZURE_DEVOPS_CONFIG['project']}  
        **Team:** {current_team}
        """)
    
    with col2:
        st.info(f"""
        **Iteration:** {dynamic_iteration_path}  
        **Area Path:** {calculated_area_path}  
        **Work Item Types:** {', '.join(WORK_ITEM_TYPES)}
        """)
    
    # 4. Sprint Summary - fourth (matching Sprint_Summary_Markdown.md format exactly)
    
    # Get current team and sprint for dynamic summary
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    current_sprint = st.session_state.get('selected_sprint', '2025_S15_Jul16-Jul29')
    
    # Map sprint to human-readable dates
    sprint_date_mapping = {
        "2025_S14_Jul02-Jul15": "July 2-15, 2025",
        "2025_S15_Jul16-Jul29": "July 16-29, 2025",
        "2025_S16_Jul30-Aug12": "July 30 - August 12, 2025",
        "2025_S17_Aug13-Aug26": "August 13-26, 2025"
    }
    
    sprint_period = sprint_date_mapping.get(current_sprint, "Unknown Sprint Period")
    
    # Sprint Overview Section (exact format from markdown)
    st.markdown("## 📊 Sprint Overview")
    st.markdown(f"""
- **Sprint Period**: {sprint_period}
- **Team**: {current_team}
- **Completion Rate**: {completion_rate:.1f}% ({len(completed_df)} of {len(df)} items)
- **Story Points Delivered**: {int(total_points)} points
""")
    
    # Cycle Time Analysis Section (exact format from markdown)
    st.markdown("## 🔄 Cycle Time Analysis")
    if len(cycle_time_items) > 0:
        long_cycle_threshold = avg_cycle_time + cycle_time_items['cycle_time_days'].std() if len(cycle_time_items) > 1 else avg_cycle_time + 5
        long_cycle_items = cycle_time_items[cycle_time_items['cycle_time_days'] > long_cycle_threshold]
        
        # Get categories of long cycle items for description
        long_cycle_categories = []
        if len(long_cycle_items) > 0:
            category_counts = long_cycle_items['category'].value_counts()
            for cat, count in category_counts.items():
                if cat.lower() == 'backend':
                    long_cycle_categories.append(f"{count} backend items")
                elif cat.lower() == 'frontend':
                    long_cycle_categories.append(f"{count} frontend items")
                else:
                    long_cycle_categories.append(f"{count} {cat.lower()} items")
        
        category_desc = ", ".join(long_cycle_categories) if long_cycle_categories else "various items"
        
        st.markdown(f"""
- **Average Cycle Time**: {avg_cycle_time:.1f} days
- **Items Taking Longer**: {len(long_cycle_items)} - {category_desc} ({long_cycle_threshold:.0f}-{long_cycle_items['cycle_time_days'].max():.0f} days each)
""")
        
        # Add specific descriptions based on long cycle items
        if len(long_cycle_items) > 0:
            # Analyze the types of work that took longer
            long_titles = long_cycle_items['title'].tolist()
            descriptions = []
            
            # Check for common patterns in long cycle items
            if any('saffron' in title.lower() or 'component' in title.lower() for title in long_titles):
                descriptions.append("  - Major Saffron component update")
            if any('deprecate' in title.lower() or 'api' in title.lower() for title in long_titles):
                descriptions.append("  - API deprecation tasks")
            if any('migration' in title.lower() or 'angular' in title.lower() for title in long_titles):
                descriptions.append("  - Framework migration work")
            if any('test' in title.lower() or 'qa' in title.lower() for title in long_titles):
                descriptions.append("  - Complex testing scenarios")
            
            if descriptions:
                st.markdown("\n".join(descriptions))
    else:
        st.markdown("""
- **Average Cycle Time**: No cycle time data available
- **Items Taking Longer**: Unable to analyze without cycle time data
""")
    
    # Work Breakdown by Category Section (proper table format)
    st.markdown("## 📋 Work Breakdown by Category")
    st.markdown("")  # Empty line for spacing
    
    if not category_breakdown.empty:
        # Prepare data for proper table display
        table_data = []
        total_category_points = category_breakdown['Story Points'].sum()
        
        for _, row in category_breakdown.iterrows():
            points_pct = (row['Story Points'] / total_category_points * 100) if total_category_points > 0 else 0
            table_data.append({
                'Category': row['Category'],
                'Items': row['Items'],
                'Percentage': f"{row['Item %']:.1f}%",
                'Story Points': row['Story Points'],
                'Points %': f"{points_pct:.1f}%"
            })
        
        # Create and display the table using Streamlit's table
        table_df = pd.DataFrame(table_data)
        st.table(table_df)
    else:
        st.markdown("*No completed work items available for category analysis*")
    
    # Key Highlights Section (exact format from markdown)
    st.markdown("## 🎯 Key Highlights")
    
    # Generate dynamic key highlights based on actual data
    highlights = []
    
    if not category_breakdown.empty:
        top_category = category_breakdown.loc[category_breakdown['Items'].idxmax()]
        
        # Category-specific highlights
        if top_category['Category'] == 'Frontend' and top_category['Item %'] > 50:
            highlights.append("- **Frontend Focus**: Major UI/UX improvements, component updates, user experience enhancements")
        elif top_category['Category'] == 'Backend' and top_category['Item %'] > 50:
            highlights.append("- **Backend Modernization**: API cleanup, service updates, technical debt reduction")
        elif top_category['Category'] == 'Testing/QA' and top_category['Item %'] > 30:
            highlights.append("- **Quality Assurance**: Comprehensive testing, validation, and quality improvements")
        else:
            highlights.append(f"- **{top_category['Category']} Focus**: Primary work area with {top_category['Item %']:.1f}% of completed items")
        
        # Additional highlights based on other categories
        for _, row in category_breakdown.iterrows():
            if row['Category'] == 'Backend' and row['Item %'] > 15 and top_category['Category'] != 'Backend':
                highlights.append("- **Backend Modernization**: API cleanup, service deprecation, technical debt reduction")
            elif row['Category'] == 'Testing/QA' and row['Item %'] > 10 and top_category['Category'] != 'Testing/QA':
                highlights.append("- **Quality Assurance**: Comprehensive testing post-development")
        
        # Bug analysis
        bug_items = category_breakdown[category_breakdown['Category'].str.contains('Bug', case=False, na=False)]
        if not bug_items.empty and bug_items.iloc[0]['Items'] <= 2:
            highlights.append(f"- **Low Bug Count**: Only {bug_items.iloc[0]['Items']} bug(s) resolved, indicating good code quality")
        elif bug_items.empty:
            highlights.append("- **Excellent Code Quality**: No bugs reported, indicating strong development practices")
    
    # Display highlights
    for highlight in highlights:
        st.markdown(highlight)
    
    # Items That Took Longer to Resolve Section (exact format from markdown)
    st.markdown("## ⚠️ Items That Took Longer to Resolve")
    
    if len(cycle_time_items) > 0:
        long_cycle_threshold = avg_cycle_time + cycle_time_items['cycle_time_days'].std() if len(cycle_time_items) > 1 else avg_cycle_time + 5
        long_items = cycle_time_items[cycle_time_items['cycle_time_days'] > long_cycle_threshold].sort_values('cycle_time_days', ascending=False)
        
        if len(long_items) > 0:
            for i, (_, item) in enumerate(long_items.head(3).iterrows(), 1):  # Show top 3 like in markdown
                st.markdown(f"{i}. **{item['title']}** - {item['cycle_time_days']} days")
        else:
            st.markdown("✅ **All Items Completed Within Expected Time**")
    else:
        st.markdown("*No cycle time data available for analysis*")
    
    # Sprint Success Metrics Section (exact format from markdown)
    st.markdown("## 📈 Sprint Success Metrics")
    
    # Generate success metrics in the exact format
    success_metrics = []
    
    # Completion rate metric
    if completion_rate >= 90:
        success_metrics.append(f"- ✅ **{completion_rate:.1f}% completion rate** - Strong delivery performance")
    elif completion_rate >= 80:
        success_metrics.append(f"- ✅ **{completion_rate:.1f}% completion rate** - Good delivery performance")
    elif completion_rate >= 70:
        success_metrics.append(f"- ⚠️ **{completion_rate:.1f}% completion rate** - Moderate performance")
    else:
        success_metrics.append(f"- ❌ **{completion_rate:.1f}% completion rate** - Below target performance")
    
    # Story points metric
    if total_points > 0:
        success_metrics.append(f"- ✅ **{int(total_points)} story points delivered** - Met sprint capacity")
    else:
        success_metrics.append("- ⚠️ **No story points delivered** - Review sprint planning")
    
    # Category focus metric
    if not category_breakdown.empty:
        top_category = category_breakdown.loc[category_breakdown['Items'].idxmax()]
        if top_category['Category'] == 'Frontend' and top_category['Item %'] > 50:
            success_metrics.append(f"- ✅ **Frontend-heavy sprint** - Significant user experience improvements")
        elif top_category['Category'] == 'Backend' and top_category['Item %'] > 50:
            success_metrics.append(f"- ✅ **Backend-heavy sprint** - Significant infrastructure improvements")
        else:
            success_metrics.append(f"- ✅ **{top_category['Category']}-focused sprint** - Balanced work distribution")
    
    # Cycle time / complexity metric
    if len(cycle_time_items) > 0:
        long_cycle_threshold = avg_cycle_time + cycle_time_items['cycle_time_days'].std() if len(cycle_time_items) > 1 else avg_cycle_time + 5
        long_cycle_items = cycle_time_items[cycle_time_items['cycle_time_days'] > long_cycle_threshold]
        
        if len(long_cycle_items) > 0:
            # Check if backend items took longer
            backend_long_items = long_cycle_items[long_cycle_items['category'] == 'Backend']
            if len(backend_long_items) > 0:
                success_metrics.append("- ⚠️ **Backend tasks took longer** - Complex API deprecation work")
            else:
                success_metrics.append(f"- ⚠️ **Some tasks took longer** - Complex {long_cycle_items.iloc[0]['category'].lower()} work")
        else:
            success_metrics.append("- ✅ **All tasks completed efficiently** - Good sprint planning")
    
    # Display all success metrics
    for metric in success_metrics:
        st.markdown(metric)
    
    # 5. Sprint Hero - fifth (moved down after restoring Sprint Summary)
    st.subheader("🏆 Sprint Hero")
    
    # Calculate Sprint Hero based on story points, complexity, and performance
    hero_data = calculate_sprint_hero(completed_df)
    
    if hero_data:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.success(f"""
            🏆 **{hero_data['name']}** - Sprint Champion!
            
            **Why they're the hero:**
            - 📊 **{hero_data['story_points']} story points** delivered ({hero_data['points_percentage']:.1f}% of total)
            - 🎯 **{hero_data['items_completed']} work items** completed
            - ⚡ **{hero_data['avg_cycle_time']:.1f} days** average cycle time
            - 🔥 **{hero_data['complexity_score']:.1f}** complexity score
            - 🎨 **{hero_data['category_focus']}** specialist
            """)
        
        with col2:
            # Hero performance metrics
            st.metric("Hero Score", f"{hero_data['hero_score']:.1f}", delta="🏆 Top Performer")
            st.metric("Efficiency", f"{hero_data['efficiency']:.1f}", delta="Points/Day")
    else:
        st.info("🏆 Sprint Hero analysis requires completed work items with assignees")
    
    # Azure DevOps Board URL - at the bottom of overview
    st.subheader("🔗 Azure DevOps Board")
    
    # Get the current team from session state or use selected team
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    organization = AZURE_DEVOPS_CONFIG["organization"]
    project = AZURE_DEVOPS_CONFIG["project"]
    
    # Construct the board URL based on team
    if current_team.startswith("ADGE-"):
        team_suffix = current_team.split('-')[1]  # Get "Prep", "Deliver", "Gather"
        board_url = f"https://dev.azure.com/{organization}/{project}/_boards/board/t/ADGE-{team_suffix}/Stories"
    elif current_team == "reviewready-agentic-ai-workflow":
        board_url = "https://dev.azure.com/tr-tax/TaxProf/_boards/board/t/reviewready-agentic-ai-workflow/Stories"
    else:
        board_url = f"https://dev.azure.com/{organization}/{project}/_boards/board/t/{current_team}/Stories"
    
    st.info(f"""
    **Data Source**: This dashboard fetches data from the Azure DevOps board below:  
    🔗 **Board URL**: [{board_url}]({board_url})  
    📊 **Team**: {current_team}  
    🎯 **Iteration**: {SPRINT_CONFIG['iteration_path']}
    """)

def calculate_sprint_hero(completed_df):
    """Calculate the Sprint Hero based on multiple performance factors"""
    if completed_df.empty:
        return None
    
    # Group by assignee and calculate metrics
    assignee_stats = completed_df.groupby('assignee').agg({
        'story_points': ['sum', 'mean'],
        'id': 'count',
        'cycle_time_days': 'mean',
        'category': lambda x: x.mode().iloc[0] if not x.empty else 'Other'
    }).reset_index()
    
    # Flatten column names
    assignee_stats.columns = ['assignee', 'total_points', 'avg_points', 'items_count', 'avg_cycle_time', 'primary_category']
    
    # Remove unassigned entries
    assignee_stats = assignee_stats[assignee_stats['assignee'] != 'Unassigned']
    
    if assignee_stats.empty:
        return None
    
    # Calculate complexity score (higher story points + variety of work)
    assignee_stats['complexity_score'] = (
        assignee_stats['total_points'] * 0.6 +  # Story points weight
        assignee_stats['avg_points'] * 0.4      # Average complexity weight
    )
    
    # Calculate efficiency (points per day, handling NaN cycle times)
    assignee_stats['efficiency'] = assignee_stats.apply(
        lambda row: row['total_points'] / row['avg_cycle_time'] if pd.notna(row['avg_cycle_time']) and row['avg_cycle_time'] > 0 else row['total_points'],
        axis=1
    )
    
    # Calculate hero score (combination of all factors)
    # Normalize each metric to 0-100 scale
    max_points = assignee_stats['total_points'].max()
    max_efficiency = assignee_stats['efficiency'].max()
    max_complexity = assignee_stats['complexity_score'].max()
    
    assignee_stats['hero_score'] = (
        (assignee_stats['total_points'] / max_points * 40) +      # 40% story points
        (assignee_stats['efficiency'] / max_efficiency * 30) +    # 30% efficiency
        (assignee_stats['complexity_score'] / max_complexity * 20) + # 20% complexity
        (assignee_stats['items_count'] / assignee_stats['items_count'].max() * 10) # 10% volume
    )
    
    # Get the top performer
    hero = assignee_stats.loc[assignee_stats['hero_score'].idxmax()]
    
    # Calculate percentage of total points
    total_sprint_points = completed_df['story_points'].sum()
    points_percentage = (hero['total_points'] / total_sprint_points * 100) if total_sprint_points > 0 else 0
    
    return {
        'name': hero['assignee'],
        'story_points': int(hero['total_points']),
        'points_percentage': points_percentage,
        'items_completed': int(hero['items_count']),
        'avg_cycle_time': hero['avg_cycle_time'] if pd.notna(hero['avg_cycle_time']) else 0,
        'complexity_score': hero['complexity_score'],
        'category_focus': hero['primary_category'],
        'hero_score': hero['hero_score'],
        'efficiency': hero['efficiency']
    }

def render_cycle_time_tab(completed_df):
    """Render the cycle time analysis tab"""
    st.header("Cycle Time Analysis")
    
    # Get current sprint context
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    current_sprint = st.session_state.get('selected_sprint', '2025_S15_Jul16-Jul29')
    
    # Sprint date mapping for context
    sprint_date_mapping = {
        "2025_S14_Jul02-Jul15": "July 2-15, 2025",
        "2025_S15_Jul16-Jul29": "July 16-29, 2025",
        "2025_S16_Jul30-Aug12": "July 30 - August 12, 2025",
        "2025_S17_Aug13-Aug26": "August 13-26, 2025"
    }
    sprint_period = sprint_date_mapping.get(current_sprint, "Unknown Sprint Period")
    
    # Display sprint context
    st.info(f"""
    **Sprint Context**: {sprint_period} ({current_sprint})  
    **Team**: {current_team}  
    **Analysis**: Cycle time for work items completed in this sprint
    """)
    
    # Filter for items with cycle time data
    cycle_time_df = completed_df[completed_df['cycle_time_days'].notna()].copy()
    
    if cycle_time_df.empty:
        st.warning("No cycle time data available for completed work items in this sprint.")
        st.info("""
        **Why no cycle time data?**
        - Work items need both activation date and completion date
        - Items may have been completed outside the sprint period
        - Some items might be missing required date fields
        """)
        
        # Show debug information
        with st.expander("🔍 Debug: Check work item dates"):
            st.write("**Completed items with date information:**")
            debug_df = completed_df[['id', 'title', 'activated_date', 'resolved_date', 'closed_date', 'cycle_time_days']].copy()
            debug_df['has_activated'] = debug_df['activated_date'].notna()
            debug_df['has_resolved'] = debug_df['resolved_date'].notna()
            debug_df['has_closed'] = debug_df['closed_date'].notna()
            st.dataframe(debug_df)
        return
    
    # Sprint-specific insights and recommendations - moved to top
    st.subheader("💡 Sprint-Specific Insights & Recommendations")
    
    avg_time = cycle_time_df['cycle_time_days'].mean()
    
    if not cycle_time_df.empty:
        # Performance insights
        insights = []
        
        # Overall performance assessment
        if avg_time <= 7:
            insights.append("🏆 **Excellent cycle time performance** - Team is delivering work very efficiently")
        elif avg_time <= 10:
            insights.append("✅ **Good cycle time performance** - Team maintains solid delivery pace")
        else:
            insights.append("⚠️ **Cycle time needs attention** - Consider breaking down work or addressing blockers")
        
        # Category-specific insights
        if 'category' in cycle_time_df.columns:
            category_cycle_times = cycle_time_df.groupby('category')['cycle_time_days'].mean()
            slowest_category = category_cycle_times.idxmax()
            fastest_category = category_cycle_times.idxmin()
            
            if len(category_cycle_times) > 1:
                insights.append(f"📊 **{slowest_category} work takes longest** ({category_cycle_times[slowest_category]:.1f} days avg)")
                insights.append(f"⚡ **{fastest_category} work is fastest** ({category_cycle_times[fastest_category]:.1f} days avg)")
        
        # Team performance insights
        assignee_cycle_time = cycle_time_df.groupby('assignee').agg({
            'cycle_time_days': ['mean', 'count', 'std']
        }).round(1)
        assignee_cycle_time.columns = ['Avg Cycle Time', 'Items Count', 'Std Dev']
        assignee_cycle_time = assignee_cycle_time[assignee_cycle_time.index != 'Unassigned']
        assignee_cycle_time = assignee_cycle_time.sort_values('Avg Cycle Time', ascending=True)
        
        if not assignee_cycle_time.empty and len(assignee_cycle_time) > 1:
            fastest_member = assignee_cycle_time.index[0]  # Already sorted by avg cycle time ascending
            insights.append(f"🌟 **{fastest_member} has the fastest cycle time** - Consider knowledge sharing")
        
        # Display insights
        for insight in insights:
            st.info(insight)
        
        # Recommendations based on data
        st.markdown("### 🎯 Recommendations for Next Sprint:")
        recommendations = []
        
        if avg_time > 10:
            recommendations.append("- **Break down large work items** into smaller, manageable pieces")
            recommendations.append("- **Identify and address common blockers** that slow down delivery")
        
        # Long cycle items analysis for recommendations
        if len(cycle_time_df) > 1:
            std_dev = cycle_time_df['cycle_time_days'].std()
            threshold = avg_time + std_dev
            long_cycle_items = cycle_time_df[cycle_time_df['cycle_time_days'] > threshold]
            
            if len(long_cycle_items) > 0:
                recommendations.append(f"- **Review the {len(long_cycle_items)} items that took longer** to identify improvement opportunities")
        
        if not assignee_cycle_time.empty and len(assignee_cycle_time) > 1:
            cycle_time_range = assignee_cycle_time['Avg Cycle Time'].max() - assignee_cycle_time['Avg Cycle Time'].min()
            if cycle_time_range > 5:
                recommendations.append("- **Balance workload distribution** - significant variation in team member cycle times")
                recommendations.append("- **Implement pair programming** for knowledge sharing and skill development")
        
        recommendations.append("- **Continue tracking cycle time** to monitor improvement trends")
        
        for rec in recommendations:
            st.markdown(rec)
    else:
        st.warning("**No cycle time data available for analysis**")
        st.info("""
        **To improve cycle time tracking:**
        - Ensure work items are properly activated when work begins
        - Set resolved/closed dates when work is completed
        - Use consistent workflow states across the team
        - Track activation and completion dates for all work items
        """)
    
    st.markdown("---")  # Add separator after recommendations
    
    # Cycle time statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Items with Cycle Time", len(cycle_time_df), delta=f"of {len(completed_df)} completed")
    
    with col2:
        st.metric("Average Cycle Time", f"{avg_time:.1f} days")
    
    with col3:
        median_time = cycle_time_df['cycle_time_days'].median()
        st.metric("Median Cycle Time", f"{median_time:.1f} days")
    
    with col4:
        max_time = cycle_time_df['cycle_time_days'].max()
        min_time = cycle_time_df['cycle_time_days'].min()
        st.metric("Range", f"{min_time}-{max_time} days")
    
    # Enhanced Cycle Time Analysis
    st.subheader("📊 Cycle Time Performance Analysis")
    
    # Create performance categories
    cycle_time_df['performance_category'] = cycle_time_df['cycle_time_days'].apply(
        lambda x: 'Fast (≤7 days)' if x <= 7 
        else 'Normal (8-14 days)' if x <= 14 
        else 'Slow (>14 days)'
    )
    
    # Performance summary
    performance_summary = cycle_time_df['performance_category'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # COMPREHENSIVE DEBUG SECTION FOR CYCLE TIME PERFORMANCE CHART
        st.markdown("### 🔍 DEBUG: Cycle Time Performance Chart Data Analysis")
        
        # Debug 1: Show raw completed_df info
        st.write(f"**Total completed items**: {len(completed_df)}")
        if not completed_df.empty:
            st.write(f"**Completed items columns**: {list(completed_df.columns)}")
            
            # Debug 2: Check cycle_time_days column
            if 'cycle_time_days' in completed_df.columns:
                cycle_time_stats = completed_df['cycle_time_days'].describe()
                st.write(f"**Cycle time stats**: {cycle_time_stats}")
                
                # Show items with and without cycle time data
                items_with_cycle_time = completed_df[completed_df['cycle_time_days'].notna()]
                items_without_cycle_time = completed_df[completed_df['cycle_time_days'].isna()]
                
                st.write(f"**Items WITH cycle time data**: {len(items_with_cycle_time)}")
                st.write(f"**Items WITHOUT cycle time data**: {len(items_without_cycle_time)}")
                
                # Debug 3: Show sample items with cycle time data
                if not items_with_cycle_time.empty:
                    st.write("**Sample items WITH cycle time:**")
                    sample_with = items_with_cycle_time[['id', 'title', 'activated_date', 'resolved_date', 'closed_date', 'cycle_time_days']].head(3)
                    st.dataframe(sample_with)
                    
                    # Debug 4: Show the actual cycle time values
                    cycle_times = items_with_cycle_time['cycle_time_days'].tolist()
                    st.write(f"**Actual cycle time values**: {cycle_times}")
                    
                    # Debug 5: Performance categorization
                    fast_items = len(items_with_cycle_time[items_with_cycle_time['cycle_time_days'] <= 7])
                    normal_items = len(items_with_cycle_time[(items_with_cycle_time['cycle_time_days'] > 7) & (items_with_cycle_time['cycle_time_days'] <= 14)])
                    slow_items = len(items_with_cycle_time[items_with_cycle_time['cycle_time_days'] > 14])
                    
                    st.write(f"**Performance breakdown**: Fast={fast_items}, Normal={normal_items}, Slow={slow_items}")
                    
                    # Debug 6: Show items in each category
                    if fast_items > 0:
                        fast_list = items_with_cycle_time[items_with_cycle_time['cycle_time_days'] <= 7]['cycle_time_days'].tolist()
                        st.write(f"**Fast items cycle times**: {fast_list}")
                    
                    if normal_items > 0:
                        normal_list = items_with_cycle_time[(items_with_cycle_time['cycle_time_days'] > 7) & (items_with_cycle_time['cycle_time_days'] <= 14)]['cycle_time_days'].tolist()
                        st.write(f"**Normal items cycle times**: {normal_list}")
                    
                    if slow_items > 0:
                        slow_list = items_with_cycle_time[items_with_cycle_time['cycle_time_days'] > 14]['cycle_time_days'].tolist()
                        st.write(f"**Slow items cycle times**: {slow_list}")
                
                # Debug 7: Show sample items WITHOUT cycle time data
                if not items_without_cycle_time.empty:
                    st.write("**Sample items WITHOUT cycle time (missing dates):**")
                    sample_without = items_without_cycle_time[['id', 'title', 'activated_date', 'resolved_date', 'closed_date', 'cycle_time_days']].head(5)
                    st.dataframe(sample_without)
            else:
                st.error("❌ 'cycle_time_days' column not found in completed_df!")
        
        # Performance distribution chart - use the same data as performance breakdown
        if not cycle_time_df.empty:
            # Create performance categories using the same logic as the breakdown
            fast_items = len(cycle_time_df[cycle_time_df['cycle_time_days'] <= 7])
            normal_items = len(cycle_time_df[(cycle_time_df['cycle_time_days'] > 7) & (cycle_time_df['cycle_time_days'] <= 14)])
            slow_items = len(cycle_time_df[cycle_time_df['cycle_time_days'] > 14])
            
            # Debug information
            st.write(f"**CHART DEBUG**: Fast={fast_items}, Normal={normal_items}, Slow={slow_items}, Total cycle_time_df={len(cycle_time_df)}")
            
            # Check if we have any data to plot
            total_performance_items = fast_items + normal_items + slow_items
            
            if total_performance_items > 0:
                # Always include all categories for proper chart display
                categories = ['Fast (≤7 days)', 'Normal (8-14 days)', 'Slow (>14 days)']
                counts = [fast_items, normal_items, slow_items]
                
                st.write(f"**CHART DATA**: Categories={categories}, Counts={counts}")
                
                # Create the chart data
                performance_data = pd.DataFrame({
                    'Performance Category': categories,
                    'Number of Items': counts
                })
                
                st.write("**Chart DataFrame:**")
                st.dataframe(performance_data)
                
                # Create the chart
                fig_performance = px.bar(
                    performance_data,
                    x='Performance Category',
                    y='Number of Items',
                    title="Work Items by Cycle Time Performance",
                    color='Performance Category',
                    color_discrete_map={
                        'Fast (≤7 days)': PASTEL_COLORS['performance'][0],  # Light green
                        'Normal (8-14 days)': PASTEL_COLORS['performance'][1],  # Khaki
                        'Slow (>14 days)': PASTEL_COLORS['performance'][2]  # Light pink
                    }
                )
                fig_performance.update_layout(
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    title_font_size=16,
                    xaxis_title="Performance Category",
                    yaxis_title="Number of Items",
                    yaxis=dict(range=[0, max(counts) + 1])
                )
                st.plotly_chart(fig_performance, use_container_width=True)
            else:
                st.warning("❌ No items with valid cycle time data to display in performance chart")
                st.info("**Possible reasons:**")
                st.info("- Work items are missing activation dates")
                st.info("- Work items are missing completion dates (resolved/closed)")
                st.info("- Items were completed outside the sprint period")
                st.info("- Date parsing failed for the available dates")
        else:
            st.warning("❌ cycle_time_df is empty - No cycle time data available for performance analysis")
            st.info("**This means**: No completed items have both activation date and completion date")
            
            # Show all completed items for reference
            if not completed_df.empty:
                st.markdown("**All completed items (for debugging):**")
                reference_df = completed_df[['id', 'title', 'type', 'assignee', 'state', 'activated_date', 'resolved_date', 'closed_date', 'cycle_time_days']].copy()
                reference_df['title'] = reference_df['title'].apply(lambda x: x[:50] + "..." if len(x) > 50 else x)
                reference_df['activated_date'] = reference_df['activated_date'].apply(format_date_for_display)
                reference_df['resolved_date'] = reference_df['resolved_date'].apply(format_date_for_display)
                reference_df['closed_date'] = reference_df['closed_date'].apply(format_date_for_display)
                
                # Rename columns for display
                reference_df.columns = ['ID', 'Title', 'Type', 'Assignee', 'State', 'Activated Date', 'Resolved Date', 'Closed Date', 'Cycle Time']
                
                st.dataframe(reference_df, use_container_width=True, hide_index=True)
                st.info("💡 **Key Point**: Items need both activation date and completion date (resolved/closed) to calculate cycle time")
                
                # Additional debugging: Check date field availability
                activated_count = completed_df['activated_date'].notna().sum()
                resolved_count = completed_df['resolved_date'].notna().sum()
                closed_count = completed_df['closed_date'].notna().sum()
                
                st.write(f"**Date field availability:**")
                st.write(f"- Items with activated_date: {activated_count}/{len(completed_df)}")
                st.write(f"- Items with resolved_date: {resolved_count}/{len(completed_df)}")
                st.write(f"- Items with closed_date: {closed_count}/{len(completed_df)}")
    
    with col2:
        # Performance metrics
        fast_items = len(cycle_time_df[cycle_time_df['cycle_time_days'] <= 7])
        normal_items = len(cycle_time_df[(cycle_time_df['cycle_time_days'] > 7) & (cycle_time_df['cycle_time_days'] <= 14)])
        slow_items = len(cycle_time_df[cycle_time_df['cycle_time_days'] > 14])
        
        st.markdown("### Performance Breakdown")
        st.markdown(f"""
        - 🟢 **Fast (≤7 days)**: {fast_items} items ({fast_items/len(cycle_time_df)*100:.1f}%)
        - 🟡 **Normal (8-14 days)**: {normal_items} items ({normal_items/len(cycle_time_df)*100:.1f}%)
        - 🔴 **Slow (>14 days)**: {slow_items} items ({slow_items/len(cycle_time_df)*100:.1f}%)
        """)
        
        # Performance score
        performance_score = (fast_items * 3 + normal_items * 2 + slow_items * 1) / len(cycle_time_df)
        if performance_score >= 2.5:
            st.success(f"🏆 **Excellent Performance** - Score: {performance_score:.1f}/3.0")
        elif performance_score >= 2.0:
            st.info(f"✅ **Good Performance** - Score: {performance_score:.1f}/3.0")
        else:
            st.warning(f"⚠️ **Needs Improvement** - Score: {performance_score:.1f}/3.0")
    
    # Cycle Time Distribution Chart
    st.subheader("📈 Cycle Time Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram of cycle times
        fig_hist = px.histogram(
            cycle_time_df,
            x='cycle_time_days',
            nbins=10,
            title="Cycle Time Distribution",
            labels={'cycle_time_days': 'Cycle Time (Days)', 'count': 'Number of Items'},
            color_discrete_sequence=[PASTEL_COLORS['primary'][0]]
        )
        fig_hist.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            showlegend=False
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Cycle time by category
        if 'category' in cycle_time_df.columns:
            cycle_by_category = cycle_time_df.groupby('category')['cycle_time_days'].mean().sort_values(ascending=False)
            
            fig_category = px.bar(
                x=cycle_by_category.index,
                y=cycle_by_category.values,
                title="Average Cycle Time by Category",
                labels={'x': 'Category', 'y': 'Average Cycle Time (Days)'},
                color=cycle_by_category.values,
                color_continuous_scale=PASTEL_COLORS['warning']
            )
            fig_category.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                title_font_size=16,
                showlegend=False
            )
            st.plotly_chart(fig_category, use_container_width=True)
    
    # Cycle Time by Assignee
    st.subheader("👥 Cycle Time by Team Member")
    
    assignee_cycle_time = cycle_time_df.groupby('assignee').agg({
        'cycle_time_days': ['mean', 'count', 'std']
    }).round(1)
    assignee_cycle_time.columns = ['Avg Cycle Time', 'Items Count', 'Std Dev']
    assignee_cycle_time = assignee_cycle_time[assignee_cycle_time.index != 'Unassigned']
    assignee_cycle_time = assignee_cycle_time.sort_values('Avg Cycle Time', ascending=True)
    
    if not assignee_cycle_time.empty:
        # Display as a nice table
        st.dataframe(assignee_cycle_time, use_container_width=True)
        
        # Chart showing cycle time by assignee
        assignee_chart_data = assignee_cycle_time.reset_index()
        assignee_chart_data = assignee_chart_data.sort_values('Avg Cycle Time', ascending=True)
        
        fig_assignee_cycle = px.bar(
            assignee_chart_data,
            x='Avg Cycle Time',
            y='assignee',
            orientation='h',
            title="Average Cycle Time by Team Member",
            labels={'Avg Cycle Time': 'Average Cycle Time (Days)', 'assignee': 'Team Member'},
            color='Avg Cycle Time',
            color_continuous_scale=PASTEL_COLORS['warning']
        )
        fig_assignee_cycle.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            showlegend=False,
            height=max(300, len(assignee_chart_data) * 40)  # Dynamic height based on team size
        )
        st.plotly_chart(fig_assignee_cycle, use_container_width=True)
    else:
        st.info("No team member cycle time data available - items may be unassigned or missing dates")
    
    # Long cycle items analysis
    if len(cycle_time_df) > 1:
        std_dev = cycle_time_df['cycle_time_days'].std()
        threshold = avg_time + std_dev
        long_cycle_items = cycle_time_df[cycle_time_df['cycle_time_days'] > threshold]
        
        if not long_cycle_items.empty:
            st.subheader(f"⚠️ Items Taking Longer Than Expected ({len(long_cycle_items)} items)")
            st.caption(f"Threshold: {threshold:.1f} days (Average + 1 Standard Deviation)")
            
            # Show detailed analysis of long cycle items
            for _, item in long_cycle_items.sort_values('cycle_time_days', ascending=False).iterrows():
                with st.expander(f"#{item['id']}: {item['title'][:60]}... ({item['cycle_time_days']} days)", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        **Work Item Details:**
                        - **Type**: {item['type']}
                        - **Category**: {item['category']}
                        - **Story Points**: {item['story_points']}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Assignment & Timeline:**
                        - **Assignee**: {item['assignee']}
                        - **State**: {item['state']}
                        - **Cycle Time**: {item['cycle_time_days']} days
                        """)
                    
                    with col3:
                        if item['activated_date'] and (item['resolved_date'] or item['closed_date']):
                            activated = format_date_for_display(item['activated_date'])
                            completed = format_date_for_display(item['resolved_date'] or item['closed_date'])
                            st.markdown(f"""
                            **Date Timeline:**
                            - **Activated**: {activated}
                            - **Completed**: {completed}
                            - **Duration**: {item['cycle_time_days']} days
                            """)
                        else:
                            st.markdown("**Date Timeline:**\n- Date information incomplete")
        else:
            st.success("✅ **All Items Completed Within Expected Time**")
            st.info("No items exceeded the expected cycle time threshold - great team performance!")

def get_category_insight(category, items, story_points, item_pct, points_pct):
    """Generate insight text for a category based on its metrics"""
    avg_points_per_item = story_points / items if items > 0 else 0
    
    insights = []
    
    # Complexity insight
    if avg_points_per_item > 3:
        insights.append("High complexity work")
    elif avg_points_per_item > 1:
        insights.append("Medium complexity")
    else:
        insights.append("Low complexity tasks")
    
    # Volume insight
    if item_pct > 40:
        insights.append("Sprint focus area")
    elif item_pct > 20:
        insights.append("Significant portion")
    else:
        insights.append("Supporting work")
    
    # Category-specific insights
    if category.lower() == 'backend':
        if story_points > 15:
            insights.append("Major infrastructure work")
        else:
            insights.append("API/service updates")
    elif category.lower() == 'frontend':
        if story_points > 15:
            insights.append("Major UI overhaul")
        else:
            insights.append("UI improvements")
    elif category.lower() == 'bug':
        if items <= 2:
            insights.append("Good code quality")
        else:
            insights.append("Quality review needed")
    elif category.lower() == 'ux':
        insights.append("User experience focus")
    
    return " • ".join(insights)

def render_categories_tab(completed_df):
    """Render the work categories tab"""
    st.header("Work Categories Analysis")
    
    # Add comprehensive completed_df table at the top
    st.subheader("📋 All Completed Work Items - Detailed View")
    
    if not completed_df.empty:
        # Create a comprehensive display version of completed_df
        display_completed_df = completed_df.copy()
        
        # Format dates for better display
        date_columns = ['created_date', 'activated_date', 'resolved_date', 'closed_date']
        for col in date_columns:
            if col in display_completed_df.columns:
                display_completed_df[col] = display_completed_df[col].apply(format_date_for_display)
        
        # Format cycle time
        if 'cycle_time_days' in display_completed_df.columns:
            display_completed_df['cycle_time_days'] = display_completed_df['cycle_time_days'].apply(
                lambda x: f"{x:.1f} days" if pd.notna(x) else "N/A"
            )
        
        # Truncate long titles for better display
        if 'title' in display_completed_df.columns:
            display_completed_df['title'] = display_completed_df['title'].apply(
                lambda x: x[:50] + "..." if len(x) > 50 else x
            )
        
        # Format tags
        if 'tags' in display_completed_df.columns:
            display_completed_df['tags'] = display_completed_df['tags'].apply(
                lambda x: x[:30] + "..." if x and len(x) > 30 else (x if x else "None")
            )
        
        # Format completion status
        if 'is_completed' in display_completed_df.columns:
            display_completed_df['is_completed'] = display_completed_df['is_completed'].apply(
                lambda x: "✅ Yes" if x else "⏳ No"
            )
        
        # Select and reorder columns for optimal display
        display_columns = [
            'id', 'title', 'type', 'state', 'assignee', 'story_points', 
            'category', 'cycle_time_days', 'created_date', 'activated_date', 
            'resolved_date', 'closed_date', 'tags'
        ]
        
        # Only include columns that exist in the dataframe
        available_columns = [col for col in display_columns if col in display_completed_df.columns]
        display_table = display_completed_df[available_columns].copy()
        
        # Rename columns for better readability
        column_renames = {
            'id': 'ID',
            'title': 'Title',
            'type': 'Type',
            'state': 'State',
            'assignee': 'Assignee',
            'story_points': 'Story Points',
            'category': 'Category',
            'cycle_time_days': 'Cycle Time',
            'created_date': 'Created Date',
            'activated_date': 'Activated Date',
            'resolved_date': 'Resolved Date',
            'closed_date': 'Closed Date',
            'tags': 'Tags'
        }
        
        # Apply renames only for columns that exist
        display_table = display_table.rename(columns={k: v for k, v in column_renames.items() if k in display_table.columns})
        
        # Display summary metrics above the table
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Completed Items", len(completed_df))
        
        with col2:
            total_points = completed_df['story_points'].sum()
            st.metric("Total Story Points", int(total_points))
        
        with col3:
            avg_cycle_time = completed_df[completed_df['cycle_time_days'].notna()]['cycle_time_days'].mean()
            cycle_time_text = f"{avg_cycle_time:.1f} days" if pd.notna(avg_cycle_time) else "N/A"
            st.metric("Avg Cycle Time", cycle_time_text)
        
        with col4:
            unique_assignees = len(completed_df['assignee'].unique()) - (1 if 'Unassigned' in completed_df['assignee'].unique() else 0)
            st.metric("Active Contributors", unique_assignees)
        
        # Display the comprehensive table
        st.dataframe(
            display_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "State": st.column_config.TextColumn("State", width="small"),
                "Assignee": st.column_config.TextColumn("Assignee", width="medium"),
                "Story Points": st.column_config.NumberColumn("Story Points", width="small"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Cycle Time": st.column_config.TextColumn("Cycle Time", width="small"),
                "Created Date": st.column_config.TextColumn("Created Date", width="small"),
                "Activated Date": st.column_config.TextColumn("Activated Date", width="small"),
                "Resolved Date": st.column_config.TextColumn("Resolved Date", width="small"),
                "Closed Date": st.column_config.TextColumn("Closed Date", width="small"),
                "Tags": st.column_config.TextColumn("Tags", width="medium")
            }
        )
        
        # Add export functionality for completed items
        if st.button("📥 Export Completed Items to CSV"):
            # Use original data with proper formatting for export
            export_df = completed_df.copy()
            
            # Format dates for export
            for col in date_columns:
                if col in export_df.columns:
                    export_df[col] = export_df[col].apply(format_date_for_display)
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download Completed Items CSV",
                data=csv,
                file_name=f"completed_work_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        st.markdown("---")  # Add separator before category analysis
    else:
        st.warning("No completed work items available for analysis.")
        return
    
    # Category summary
    category_summary = completed_df.groupby('category').agg({
        'id': 'count',
        'story_points': 'sum'
    }).reset_index()
    category_summary.columns = ['Category', 'Items', 'Story Points']
    
    # Calculate percentages
    total_items = category_summary['Items'].sum()
    total_points = category_summary['Story Points'].sum()
    category_summary['Item %'] = (category_summary['Items'] / total_items * 100).round(1)
    category_summary['Points %'] = (category_summary['Story Points'] / total_points * 100).round(1)
    
    # Display comprehensive category summary table
    st.subheader("📊 Category Summary - Chart Data Analysis")
    
    if not category_summary.empty:
        # Add summary metrics above the table
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Categories", len(category_summary))
        
        with col2:
            st.metric("Total Items", int(total_items))
        
        with col3:
            st.metric("Total Story Points", int(total_points))
        
        with col4:
            dominant_category = category_summary.loc[category_summary['Story Points'].idxmax()]
            st.metric("Dominant Category", dominant_category['Category'], 
                     delta=f"{dominant_category['Points %']:.1f}% of points")
        
        # Create enhanced display version of category_summary
        display_category_summary = category_summary.copy()
        
        # Sort by story points descending for better visualization
        display_category_summary = display_category_summary.sort_values('Story Points', ascending=False)
        
        # Add ranking column
        display_category_summary['Rank'] = range(1, len(display_category_summary) + 1)
        
        # Add visual indicators for percentages
        display_category_summary['Item % Visual'] = display_category_summary['Item %'].apply(
            lambda x: f"{x:.1f}% {'🟢' if x >= 30 else '🟡' if x >= 15 else '🔴'}"
        )
        
        display_category_summary['Points % Visual'] = display_category_summary['Points %'].apply(
            lambda x: f"{x:.1f}% {'🟢' if x >= 30 else '🟡' if x >= 15 else '🔴'}"
        )
        
        # Add category insights
        display_category_summary['Category Insight'] = display_category_summary.apply(
            lambda row: get_category_insight(row['Category'], row['Items'], row['Story Points'], row['Item %'], row['Points %']),
            axis=1
        )
        
        # Reorder columns for optimal display
        display_columns = [
            'Rank', 'Category', 'Items', 'Item % Visual', 
            'Story Points', 'Points % Visual', 'Category Insight'
        ]
        
        display_table = display_category_summary[display_columns].copy()
        
        # Rename columns for better readability
        display_table.columns = [
            'Rank', 'Category', 'Items Count', 'Item Distribution', 
            'Story Points', 'Points Distribution', 'Insight'
        ]
        
        st.write("**Category Summary Data (Used for Chart Generation):**")
        st.dataframe(
            display_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "Category": st.column_config.TextColumn("Category", width="medium"),
                "Items Count": st.column_config.NumberColumn("Items Count", width="small"),
                "Item Distribution": st.column_config.TextColumn("Item Distribution", width="medium"),
                "Story Points": st.column_config.NumberColumn("Story Points", width="small"),
                "Points Distribution": st.column_config.TextColumn("Points Distribution", width="medium"),
                "Insight": st.column_config.TextColumn("Insight", width="large")
            }
        )
        
        # Add detailed breakdown section
        st.write("**Detailed Category Breakdown:**")
        
        # Create detailed analysis for each category
        for _, row in display_category_summary.iterrows():
            with st.expander(f"📋 {row['Category']} - Detailed Analysis", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    **Basic Metrics:**
                    - **Rank**: #{row['Rank']} by story points
                    - **Items**: {row['Items']} work items
                    - **Story Points**: {row['Story Points']} points
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Distribution:**
                    - **Item Share**: {row['Item %']:.1f}% of total items
                    - **Points Share**: {row['Points %']:.1f}% of total points
                    - **Avg Points/Item**: {(row['Story Points']/row['Items']):.1f}
                    """)
                
                with col3:
                    # Get items in this category for additional insights
                    category_items = completed_df[completed_df['category'] == row['Category']]
                    avg_cycle_time = category_items[category_items['cycle_time_days'].notna()]['cycle_time_days'].mean()
                    unique_assignees = len(category_items['assignee'].unique())
                    
                    st.markdown(f"""
                    **Performance:**
                    - **Avg Cycle Time**: {avg_cycle_time:.1f} days if pd.notna(avg_cycle_time) else 'N/A'
                    - **Contributors**: {unique_assignees} team members
                    - **Complexity**: {'High' if (row['Story Points']/row['Items']) > 3 else 'Medium' if (row['Story Points']/row['Items']) > 1 else 'Low'}
                    """)
                
                # Show sample items from this category
                sample_items = category_items.head(3)
                if not sample_items.empty:
                    st.markdown("**Sample Items:**")
                    for _, item in sample_items.iterrows():
                        st.markdown(f"- **#{item['id']}**: {item['title'][:60]}{'...' if len(item['title']) > 60 else ''} ({item['story_points']} pts)")
        
        # Add export functionality for category summary
        if st.button("📥 Export Category Summary to CSV"):
            # Use original category_summary data for export
            csv = category_summary.to_csv(index=False)
            st.download_button(
                label="Download Category Summary CSV",
                data=csv,
                file_name=f"category_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        st.markdown("---")  # Add separator before charts
    else:
        st.warning("No category data available for analysis.")
        return
    
    # Category breakdown charts - using the actual category_summary data
    col1, col2 = st.columns(2)
    
    with col1:
        # COMPREHENSIVE DEBUG: Show the data being used for the chart
        st.write("**🔍 COMPREHENSIVE DEBUG: Work Items Chart Data Analysis**")
        st.write(f"**category_summary DataFrame info:**")
        st.write(f"- Shape: {category_summary.shape}")
        st.write(f"- Columns: {list(category_summary.columns)}")
        st.write(f"- Data types: {category_summary.dtypes.to_dict()}")
        
        st.write("**Complete category_summary DataFrame:**")
        st.dataframe(category_summary)
        
        # Check for data issues
        if category_summary.empty:
            st.error("❌ category_summary is EMPTY!")
        elif 'Category' not in category_summary.columns:
            st.error("❌ 'Category' column missing from category_summary!")
        elif 'Items' not in category_summary.columns:
            st.error("❌ 'Items' column missing from category_summary!")
        else:
            # Show the exact data that will be used for the chart
            chart_data_items = category_summary[['Category', 'Items']].copy()
            st.write("**Exact chart data for pie chart:**")
            st.dataframe(chart_data_items)
            
            # Show individual values
            st.write("**Individual values for pie chart:**")
            for _, row in chart_data_items.iterrows():
                st.write(f"- {row['Category']}: {row['Items']} items")
            
            # Check for zero or negative values
            zero_items = chart_data_items[chart_data_items['Items'] <= 0]
            if not zero_items.empty:
                st.warning(f"⚠️ Found {len(zero_items)} categories with zero or negative items!")
                st.dataframe(zero_items)
            
            # Try alternative chart creation method
            st.write("**Creating chart with explicit data...**")
            
            try:
                # Method 1: Direct data approach
                categories = chart_data_items['Category'].tolist()
                values = chart_data_items['Items'].tolist()
                
                st.write(f"**Chart input data:**")
                st.write(f"- Categories: {categories}")
                st.write(f"- Values: {values}")
                
                # Create chart using go.Pie instead of px.pie
                fig_items = go.Figure(data=[go.Pie(
                    labels=categories,
                    values=values,
                    name="Work Items"
                )])
                
                fig_items.update_layout(
                    title="Work Items by Category",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    title_font_size=16,
                    showlegend=True
                )
                
                fig_items.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Items: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                
                st.plotly_chart(fig_items, use_container_width=True)
                st.success("✅ Chart created successfully using go.Pie!")
                
            except Exception as e:
                st.error(f"❌ Error creating chart: {str(e)}")
                
                # Fallback: Try px.pie with explicit parameters
                try:
                    st.write("**Trying fallback method with px.pie...**")
                    fig_items_fallback = px.pie(
                        values=values,
                        names=categories,
                        title="Work Items by Category (Fallback)",
                        color_discrete_sequence=PASTEL_COLORS['categories']
                    )
                    fig_items_fallback.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        title_font_size=16,
                        showlegend=True
                    )
                    st.plotly_chart(fig_items_fallback, use_container_width=True)
                    st.success("✅ Fallback chart created successfully!")
                except Exception as e2:
                    st.error(f"❌ Fallback method also failed: {str(e2)}")
    
    with col2:
        # COMPREHENSIVE DEBUG: Show the data being used for the chart
        st.write("**🔍 COMPREHENSIVE DEBUG: Story Points Chart Data Analysis**")
        st.write("**Complete category_summary DataFrame for Story Points:**")
        st.dataframe(category_summary[['Category', 'Story Points']])
        
        # Check for data issues
        if 'Story Points' not in category_summary.columns:
            st.error("❌ 'Story Points' column missing from category_summary!")
        else:
            # Show the exact data that will be used for the chart
            chart_data_points = category_summary[['Category', 'Story Points']].copy()
            st.write("**Exact chart data for story points pie chart:**")
            st.dataframe(chart_data_points)
            
            # Show individual values
            st.write("**Individual values for story points pie chart:**")
            for _, row in chart_data_points.iterrows():
                st.write(f"- {row['Category']}: {row['Story Points']} points")
            
            # Check for zero or negative values
            zero_points = chart_data_points[chart_data_points['Story Points'] <= 0]
            if not zero_points.empty:
                st.warning(f"⚠️ Found {len(zero_points)} categories with zero or negative story points!")
                st.dataframe(zero_points)
            
            try:
                # Method 1: Direct data approach for story points
                categories = chart_data_points['Category'].tolist()
                values = chart_data_points['Story Points'].tolist()
                
                st.write(f"**Story Points Chart input data:**")
                st.write(f"- Categories: {categories}")
                st.write(f"- Values: {values}")
                
                # Create chart using go.Pie instead of px.pie
                fig_points = go.Figure(data=[go.Pie(
                    labels=categories,
                    values=values,
                    name="Story Points"
                )])
                
                fig_points.update_layout(
                    title="Story Points by Category",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    title_font_size=16,
                    showlegend=True
                )
                
                fig_points.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Story Points: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                
                st.plotly_chart(fig_points, use_container_width=True)
                st.success("✅ Story Points chart created successfully using go.Pie!")
                
            except Exception as e:
                st.error(f"❌ Error creating story points chart: {str(e)}")
                
                # Fallback: Try px.pie with explicit parameters
                try:
                    st.write("**Trying fallback method for story points with px.pie...**")
                    fig_points_fallback = px.pie(
                        values=values,
                        names=categories,
                        title="Story Points by Category (Fallback)",
                        color_discrete_sequence=PASTEL_COLORS['categories']
                    )
                    fig_points_fallback.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        title_font_size=16,
                        showlegend=True
                    )
                    st.plotly_chart(fig_points_fallback, use_container_width=True)
                    st.success("✅ Story Points fallback chart created successfully!")
                except Exception as e2:
                    st.error(f"❌ Story Points fallback method also failed: {str(e2)}")
    
    # Detailed category view
    st.subheader("Category Details")
    selected_category = st.selectbox("Select a category to view details:", category_summary['Category'].tolist())
    
    if selected_category:
        category_items = completed_df[completed_df['category'] == selected_category]
        
        st.write(f"**{selected_category}** - {len(category_items)} items, {category_items['story_points'].sum()} story points")
        
        # Show items in selected category
        for _, item in category_items.iterrows():
            with st.expander(f"#{item['id']}: {item['title'][:80]}..."):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Type:** {item['type']}")
                    st.write(f"**State:** {item['state']}")
                with col2:
                    st.write(f"**Assignee:** {item['assignee']}")
                    st.write(f"**Story Points:** {item['story_points']}")
                with col3:
                    if item['cycle_time_days']:
                        st.write(f"**Cycle Time:** {item['cycle_time_days']} days")
                    else:
                        st.write("**Cycle Time:** N/A")

def render_charts_tab(df, completed_df):
    """Render the charts tab"""
    st.header("Visual Analytics")
    
    # Completion status chart
    st.subheader("Work Item Status Distribution")
    status_counts = df['state'].value_counts()
    fig_status = px.bar(
        x=status_counts.index,
        y=status_counts.values,
        title="Work Items by Status",
        labels={'x': 'Status', 'y': 'Count'},
        color=status_counts.index,
        color_discrete_sequence=PASTEL_COLORS['primary']
    )
    fig_status.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        title_font_size=16
    )
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Assignee workload
    st.subheader("Team Workload Analysis")
    assignee_summary = completed_df.groupby('assignee').agg({
        'id': 'count',
        'story_points': 'sum',
        'cycle_time_days': 'mean'
    }).reset_index()
    assignee_summary.columns = ['Assignee', 'Items Completed', 'Story Points', 'Avg Cycle Time']
    assignee_summary = assignee_summary.sort_values('Story Points', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_assignee_items = px.bar(
            assignee_summary.head(10),
            x='Assignee',
            y='Items Completed',
            title="Items Completed by Assignee (Top 10)",
            color='Items Completed',
            color_continuous_scale=PASTEL_COLORS['primary']
        )
        fig_assignee_items.update_layout(
            xaxis_tickangle=45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            showlegend=False
        )
        st.plotly_chart(fig_assignee_items, use_container_width=True)
    
    with col2:
        fig_assignee_points = px.bar(
            assignee_summary.head(10),
            x='Assignee',
            y='Story Points',
            title="Story Points by Assignee (Top 10)",
            color='Story Points',
            color_continuous_scale=PASTEL_COLORS['primary']
        )
        fig_assignee_points.update_layout(
            xaxis_tickangle=45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            showlegend=False
        )
        st.plotly_chart(fig_assignee_points, use_container_width=True)
    
    # Cycle time by category
    st.subheader("Cycle Time by Category")
    cycle_time_by_category = completed_df[completed_df['cycle_time_days'].notna()].groupby('category')['cycle_time_days'].mean().reset_index()
    cycle_time_by_category = cycle_time_by_category.sort_values('cycle_time_days', ascending=False)
    
    fig_cycle_category = px.bar(
        cycle_time_by_category,
        x='category',
        y='cycle_time_days',
        title="Average Cycle Time by Category",
        labels={'cycle_time_days': 'Average Cycle Time (Days)', 'category': 'Category'},
        color='cycle_time_days',
        color_continuous_scale=PASTEL_COLORS['warning']
    )
    fig_cycle_category.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        title_font_size=16,
        showlegend=False
    )
    st.plotly_chart(fig_cycle_category, use_container_width=True)
    
    # Story points distribution
    st.subheader("Story Points Distribution")
    story_points_dist = completed_df[completed_df['story_points'] > 0]['story_points'].value_counts().sort_index()
    
    # Create DataFrame for plotly
    points_dist_df = pd.DataFrame({
        'Story Points': story_points_dist.index,
        'Number of Items': story_points_dist.values
    })
    
    fig_points_dist = px.bar(
        points_dist_df,
        x='Story Points',
        y='Number of Items',
        title="Distribution of Story Points",
        color='Number of Items',
        color_continuous_scale=PASTEL_COLORS['success']
    )
    fig_points_dist.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        title_font_size=16,
        showlegend=False
    )
    st.plotly_chart(fig_points_dist, use_container_width=True)

def render_burndown_tab(df, completed_df):
    """Render the burndown/burnup charts tab"""
    st.header("Burndown & Burnup Charts")
    
    # Check if we have date information
    if df.empty:
        st.warning("No data available for burndown analysis.")
        return
    
    # Get selected sprint from session state or default
    current_sprint = st.session_state.get('selected_sprint', '2025_S15_Jul16-Jul29')
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    
    # Define sprint dates based on selected sprint
    sprint_date_mapping = {
        "2025_S14_Jul02-Jul15": (datetime(2025, 7, 2).date(), datetime(2025, 7, 15).date()),
        "2025_S15_Jul16-Jul29": (datetime(2025, 7, 16).date(), datetime(2025, 7, 29).date()),
        "2025_S16_Jul30-Aug12": (datetime(2025, 7, 30).date(), datetime(2025, 8, 12).date()),
        "2025_S17_Aug13-Aug26": (datetime(2025, 8, 13).date(), datetime(2025, 8, 26).date())
    }
    
    sprint_start_date, sprint_end_date = sprint_date_mapping.get(current_sprint, 
        (datetime(2025, 7, 16).date(), datetime(2025, 7, 29).date()))
    
    # Human-readable sprint period mapping
    sprint_period_mapping = {
        "2025_S14_Jul02-Jul15": "July 2-15, 2025",
        "2025_S15_Jul16-Jul29": "July 16-29, 2025",
        "2025_S16_Jul30-Aug12": "July 30 - August 12, 2025",
        "2025_S17_Aug13-Aug26": "August 13-26, 2025"
    }
    
    sprint_period = sprint_period_mapping.get(current_sprint, "Unknown Sprint Period")
    
    # Display sprint information
    st.info(f"""
    **Sprint Period**: {sprint_period} ({current_sprint})  
    **Duration**: {(sprint_end_date - sprint_start_date).days + 1} days  
    **Team**: {current_team}
    """)
    
    # Show burndown scope information
    REMAINING_STATES = ['Active', 'Ready', 'New']
    remaining_states_in_data = df[df['state'].isin(REMAINING_STATES)]['state'].value_counts()
    completed_states_in_data = df[df['state'].isin(COMPLETED_STATES)]['state'].value_counts()
    
    st.info(f"""
    **Burndown Scope**: Only tracking Active, Ready, New → Closed/Resolved transitions  
    **Remaining States**: {len(df[df['state'].isin(REMAINING_STATES)])} items (Active: {remaining_states_in_data.get('Active', 0)}, Ready: {remaining_states_in_data.get('Ready', 0)}, New: {remaining_states_in_data.get('New', 0)})  
    **Completed States**: {len(df[df['state'].isin(COMPLETED_STATES)])} items (Closed: {completed_states_in_data.get('Closed', 0)}, Resolved: {completed_states_in_data.get('Resolved', 0)})
    """)
    
    
    
    # Use sprint dates for analysis
    start_date = sprint_start_date
    end_date = sprint_end_date
    
    # Generate daily data points
    current_date = start_date
    burndown_data = []
    
    # Define remaining work states (Active, Ready, New) and completed states (Closed, Resolved)
    REMAINING_STATES = ['Active', 'Ready', 'New']
    
    # Calculate total scope based on remaining + completed states only (proper workflow tracking)
    scope_items = df[df['state'].isin(REMAINING_STATES + COMPLETED_STATES)]
    total_items = len(scope_items)
    total_story_points = scope_items['story_points'].sum()
    
    # Create a more realistic burndown by simulating daily progress
    # This tracks the transition from Active/Ready/New → Closed/Resolved
    
    while current_date <= end_date:
        # Count items that have transitioned from remaining states to completed states by this date
        completed_by_date_items = 0
        completed_by_date_points = 0
        
        # DEBUG TABLE: Show all data being processed in the scope_items loop
        if current_date == start_date:  # Only show on first iteration to avoid repetition
            st.markdown("### 🔍 DEBUG: scope_items Loop Data (Line 2145)")
            st.write(f"**Processing {len(scope_items)} items in scope_items.iterrows() loop**")
            st.write(f"**Current date being processed**: {current_date}")
            st.write(f"**Sprint date range**: {start_date} to {end_date}")
            
            # Create comprehensive debug table for the loop
            loop_debug_data = []
            for idx, (_, item) in enumerate(scope_items.iterrows()):
                # Extract all the data that will be processed in the loop
                resolved_date_raw = item.get('resolved_date', None)
                closed_date_raw = item.get('closed_date', None)
                
                # Parse dates using the same logic as in the loop
                resolved_date_parsed = None
                closed_date_parsed = None
                completion_date = None
                
                if resolved_date_raw:
                    resolved_date_parsed = parse_azure_date_to_datetime(resolved_date_raw)
                    completion_date = resolved_date_parsed.date() if resolved_date_parsed else None
                elif closed_date_raw:
                    closed_date_parsed = parse_azure_date_to_datetime(closed_date_raw)
                    completion_date = closed_date_parsed.date() if closed_date_parsed else None
                
                # Determine if item will be counted as completed
                will_be_counted = False
                completion_logic = "Not completed"
                
                if item['state'] in COMPLETED_STATES:
                    if completion_date and sprint_start_date <= completion_date <= current_date:
                        will_be_counted = True
                        completion_logic = f"Completed on {completion_date} (within sprint)"
                    elif not completion_date:
                        # Check sprint progress logic
                        sprint_progress = (current_date - start_date).days / (end_date - start_date).days
                        if sprint_progress >= 0.5:
                            will_be_counted = True
                            completion_logic = f"Completed (no date, sprint progress {sprint_progress:.1f})"
                        else:
                            completion_logic = f"Completed (no date, sprint progress {sprint_progress:.1f} < 0.5)"
                    else:
                        completion_logic = f"Completed but date {completion_date} outside range"
                
                loop_debug_data.append({
                    'Index': idx,
                    'ID': item['id'],
                    'Title': item['title'][:40] + "..." if len(item['title']) > 40 else item['title'],
                    'State': item['state'],
                    'Story Points': item['story_points'],
                    'Is Completed': item['is_completed'],
                    'Resolved Date Raw': str(resolved_date_raw)[:19] if resolved_date_raw else "None",
                    'Closed Date Raw': str(closed_date_raw)[:19] if closed_date_raw else "None",
                    'Resolved Date Parsed': resolved_date_parsed.strftime('%Y-%m-%d') if resolved_date_parsed and pd.notna(resolved_date_parsed) else "None",
                    'Closed Date Parsed': closed_date_parsed.strftime('%Y-%m-%d') if closed_date_parsed and pd.notna(closed_date_parsed) else "None",
                    'Completion Date': str(completion_date) if completion_date else "None",
                    'Will Be Counted': "✅ Yes" if will_be_counted else "❌ No",
                    'Logic': completion_logic
                })
            
            # Display the comprehensive debug table
            loop_debug_df = pd.DataFrame(loop_debug_data)
            st.dataframe(loop_debug_df, use_container_width=True, hide_index=True)
            
            # Show summary of what will be processed
            items_to_be_counted = sum(1 for item in loop_debug_data if item['Will Be Counted'] == "✅ Yes")
            points_to_be_counted = sum(item['Story Points'] for item in loop_debug_data if item['Will Be Counted'] == "✅ Yes")
            
            st.write(f"**Loop Processing Summary for {current_date}:**")
            st.write(f"- Items that will be counted as completed: {items_to_be_counted}")
            st.write(f"- Story points that will be counted: {points_to_be_counted}")
            st.write(f"- Items in COMPLETED_STATES: {len([item for item in loop_debug_data if item['State'] in COMPLETED_STATES])}")
            st.write(f"- Items with completion dates: {len([item for item in loop_debug_data if item['Completion Date'] != 'None'])}")
            
            st.markdown("---")
        
        for _, item in scope_items.iterrows():
            # Check if item has transitioned to completed state
            if item['state'] in COMPLETED_STATES:
                completion_date = None
                
                # Get the actual completion date from resolved_date or closed_date using enhanced parsing logic
                if pd.notna(item['resolved_date']):
                    # Handle both datetime objects and strings for resolved_date
                    if isinstance(item['resolved_date'], datetime):
                        parsed_date = item['resolved_date']
                    else:
                        parsed_date = parse_azure_date_to_datetime(item['resolved_date'])
                    completion_date = parsed_date.date() if parsed_date else None
                elif pd.notna(item['closed_date']):
                    # Handle both datetime objects and strings for closed_date
                    if isinstance(item['closed_date'], datetime):
                        parsed_date = item['closed_date']
                    else:
                        parsed_date = parse_azure_date_to_datetime(item['closed_date'])
                    completion_date = parsed_date.date() if parsed_date else None
                
                # If we have a completion date within sprint, use it
                if completion_date and sprint_start_date <= completion_date <= current_date:
                    completed_by_date_items += 1
                    completed_by_date_points += item['story_points']
                # If no completion date but item is completed, distribute completion across sprint
                elif not completion_date and item['state'] in COMPLETED_STATES:
                    # For items without completion dates, assume they were completed by the current date
                    # if we're at or past the sprint midpoint (realistic assumption)
                    sprint_progress = (current_date - start_date).days / (end_date - start_date).days
                    if sprint_progress >= 0.5:  # After sprint midpoint
                        completed_by_date_items += 1
                        completed_by_date_points += item['story_points']
        
        # Calculate remaining work (items that haven't transitioned to Closed/Resolved)
        remaining_items = total_items - completed_by_date_items
        remaining_points = total_story_points - completed_by_date_points
        
        # Ensure remaining counts don't go negative
        remaining_items = max(0, remaining_items)
        remaining_points = max(0, remaining_points)
        
        # DEBUG: Show calculation for first few days
        if current_date <= start_date + timedelta(days=3):
            st.write(f"**DEBUG {current_date}**: total_items={total_items}, completed_by_date_items={completed_by_date_items}, remaining_items={remaining_items}")
        
        burndown_data.append({
            'date': current_date,
            'remaining_items': remaining_items,
            'remaining_points': remaining_points,
            'completed_items': completed_by_date_items,
            'completed_points': completed_by_date_points,
            'total_scope_items': total_items,
            'total_scope_points': total_story_points
        })
        
        current_date += timedelta(days=1)
    
    # DEBUG TABLE: Show scope_items data AFTER processing the complete for loop
    st.markdown("### 🔍 DEBUG: scope_items Data AFTER Complete Loop Processing")
    st.write(f"**Loop processing completed for all dates from {start_date} to {end_date}**")
    st.write(f"**Total burndown data points generated**: {len(burndown_data)}")
    
    # Create comprehensive debug table showing final state of scope_items after all processing
    final_scope_debug_data = []
    for idx, (_, item) in enumerate(scope_items.iterrows()):
        # Extract all the data that was processed throughout the loop
        resolved_date_raw = item.get('resolved_date', None)
        closed_date_raw = item.get('closed_date', None)
        
        # Parse dates using the same logic as in the loop
        resolved_date_parsed = None
        closed_date_parsed = None
        completion_date = None
        
        # Handle both datetime objects and strings for date parsing
        if resolved_date_raw:
            st.write(f"**DEBUG - Processing resolved_date_raw**: '{resolved_date_raw}' (type: {type(resolved_date_raw)})")
            try:
                # Check if it's already a datetime object
                if isinstance(resolved_date_raw, datetime):
                    resolved_date_parsed = resolved_date_raw
                    st.write(f"**DEBUG - Already datetime object, using directly**: {resolved_date_parsed}")
                elif pd.notna(resolved_date_raw):
                    # Try to parse as string
                    resolved_date_parsed = parse_azure_date_to_datetime(resolved_date_raw)
                    st.write(f"**DEBUG - Parsed from string**: {resolved_date_parsed}")
                else:
                    resolved_date_parsed = None
                    st.write(f"**DEBUG - resolved_date_raw is NaN/None**")
                
                completion_date = resolved_date_parsed.date() if resolved_date_parsed else None
                st.write(f"**DEBUG - Final completion_date from resolved**: {completion_date}")
            except Exception as e:
                st.error(f"**DEBUG - Error processing resolved_date**: {e}")
                resolved_date_parsed = None
                completion_date = None
        elif closed_date_raw:
            st.write(f"**DEBUG - Processing closed_date_raw**: '{closed_date_raw}' (type: {type(closed_date_raw)})")
            try:
                # Check if it's already a datetime object
                if isinstance(closed_date_raw, datetime):
                    closed_date_parsed = closed_date_raw
                    st.write(f"**DEBUG - Already datetime object, using directly**: {closed_date_parsed}")
                elif pd.notna(closed_date_raw):
                    # Try to parse as string
                    closed_date_parsed = parse_azure_date_to_datetime(closed_date_raw)
                    st.write(f"**DEBUG - Parsed from string**: {closed_date_parsed}")
                else:
                    closed_date_parsed = None
                    st.write(f"**DEBUG - closed_date_raw is NaN/None**")
                
                completion_date = closed_date_parsed.date() if closed_date_parsed else None
                st.write(f"**DEBUG - Final completion_date from closed**: {completion_date}")
            except Exception as e:
                st.error(f"**DEBUG - Error processing closed_date**: {e}")
                closed_date_parsed = None
                completion_date = None
        
        # Determine final completion status based on loop logic
        was_counted_as_completed = False
        final_completion_logic = "Not completed"
        
        if item['state'] in COMPLETED_STATES:
            if completion_date and sprint_start_date <= completion_date <= end_date:
                was_counted_as_completed = True
                final_completion_logic = f"Completed on {completion_date} (within sprint period)"
            elif not completion_date:
                # This item would have been counted after sprint midpoint
                was_counted_as_completed = True
                final_completion_logic = f"Completed (no date, counted after sprint midpoint)"
            else:
                final_completion_logic = f"Completed but date {completion_date} outside sprint range"
        
        # Calculate which day this item would have been counted (if applicable)
        counted_on_day = "N/A"
        if was_counted_as_completed:
            if completion_date and sprint_start_date <= completion_date <= end_date:
                counted_on_day = str(completion_date)
            else:
                # Would be counted after midpoint
                midpoint_date = start_date + timedelta(days=(end_date - start_date).days // 2)
                counted_on_day = f"After {midpoint_date} (no completion date)"
        
        final_scope_debug_data.append({
            'Index': idx,
            'ID': item['id'],
            'Title': item['title'][:50] + "..." if len(item['title']) > 50 else item['title'],
            'Type': item['type'],
            'State': item['state'],
            'Assignee': item['assignee'],
            'Story Points': item['story_points'],
            'Category': item['category'],
            'Is Completed': item['is_completed'],
            'Resolved Date Raw': str(resolved_date_raw)[:19] if resolved_date_raw else "None",
            'Closed Date Raw': str(closed_date_raw)[:19] if closed_date_raw else "None",
            'Resolved Date Parsed': resolved_date_parsed.strftime('%Y-%m-%d') if resolved_date_parsed and pd.notna(resolved_date_parsed) else "None",
            'Closed Date Parsed': closed_date_parsed.strftime('%Y-%m-%d') if closed_date_parsed and pd.notna(closed_date_parsed) else "None",
            'Final Completion Date': str(completion_date) if completion_date else "None",
            'Was Counted in Burndown': "✅ Yes" if was_counted_as_completed else "❌ No",
            'Counted On Day': counted_on_day,
            'Final Logic': final_completion_logic,
            'Created Date': format_date_for_display(item['created_date']),
            'Activated Date': format_date_for_display(item['activated_date']),
            'Cycle Time': f"{item['cycle_time_days']:.1f} days" if pd.notna(item['cycle_time_days']) else "N/A",
            'Tags': item['tags'][:30] + "..." if item['tags'] and len(item['tags']) > 30 else (item['tags'] if item['tags'] else "None")
        })
    
    # Display the comprehensive debug table
    final_scope_debug_df = pd.DataFrame(final_scope_debug_data)
    st.dataframe(final_scope_debug_df, use_container_width=True, hide_index=True)
    
    # Show final processing summary
    items_counted_in_burndown = sum(1 for item in final_scope_debug_data if item['Was Counted in Burndown'] == "✅ Yes")
    points_counted_in_burndown = sum(item['Story Points'] for item in final_scope_debug_data if item['Was Counted in Burndown'] == "✅ Yes")
    items_not_counted = sum(1 for item in final_scope_debug_data if item['Was Counted in Burndown'] == "❌ No")
    
    st.write(f"**Final Loop Processing Summary:**")
    st.write(f"- Total scope_items processed: {len(final_scope_debug_data)}")
    st.write(f"- Items counted in burndown: {items_counted_in_burndown}")
    st.write(f"- Story points counted in burndown: {points_counted_in_burndown}")
    st.write(f"- Items NOT counted in burndown: {items_not_counted}")
    st.write(f"- Items in COMPLETED_STATES: {len([item for item in final_scope_debug_data if item['State'] in COMPLETED_STATES])}")
    st.write(f"- Items with valid completion dates: {len([item for item in final_scope_debug_data if item['Final Completion Date'] != 'None'])}")
    
    # Show breakdown by completion status
    completed_items = [item for item in final_scope_debug_data if item['State'] in COMPLETED_STATES]
    if completed_items:
        st.write(f"**Completed Items Breakdown:**")
        counted_completed = [item for item in completed_items if item['Was Counted in Burndown'] == "✅ Yes"]
        not_counted_completed = [item for item in completed_items if item['Was Counted in Burndown'] == "❌ No"]
        
        st.write(f"- Completed items counted in burndown: {len(counted_completed)}")
        st.write(f"- Completed items NOT counted in burndown: {len(not_counted_completed)}")
        
        if not_counted_completed:
            st.write(f"**Reasons for completed items not being counted:**")
            reasons = {}
            for item in not_counted_completed:
                reason = item['Final Logic']
                if reason not in reasons:
                    reasons[reason] = 0
                reasons[reason] += 1
            
            for reason, count in reasons.items():
                st.write(f"  - {reason}: {count} items")
    
    st.markdown("---")
    
    burndown_df = pd.DataFrame(burndown_data)
    
    # Add burndown data table
    st.subheader("📊 Burndown Data Table")
    st.write("**Complete burndown dataset showing daily progress throughout the sprint:**")
    
    # Create a formatted version of burndown_df for display
    display_burndown_df = burndown_df.copy()
    
    # Format the date column for better display
    display_burndown_df['date'] = display_burndown_df['date'].apply(lambda x: x.strftime('%Y-%m-%d (%a)'))
    
    # Rename columns for better readability
    display_burndown_df = display_burndown_df.rename(columns={
        'date': 'Date',
        'remaining_items': 'Remaining Items',
        'remaining_points': 'Remaining Points',
        'completed_items': 'Completed Items',
        'completed_points': 'Completed Points',
        'total_scope_items': 'Total Scope Items',
        'total_scope_points': 'Total Scope Points'
    })
    
    # Display the burndown data table
    st.dataframe(
        display_burndown_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.TextColumn("Date", width="medium"),
            "Remaining Items": st.column_config.NumberColumn("Remaining Items", width="small"),
            "Remaining Points": st.column_config.NumberColumn("Remaining Points", width="small"),
            "Completed Items": st.column_config.NumberColumn("Completed Items", width="small"),
            "Completed Points": st.column_config.NumberColumn("Completed Points", width="small"),
            "Total Scope Items": st.column_config.NumberColumn("Total Scope Items", width="small"),
            "Total Scope Points": st.column_config.NumberColumn("Total Scope Points", width="small")
        }
    )
    
    # Add summary information about the burndown data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sprint Days", len(burndown_df), delta=f"{start_date} to {end_date}")
    
    with col2:
        final_remaining_items = burndown_df.iloc[-1]['remaining_items']
        st.metric("Final Remaining Items", int(final_remaining_items))
    
    with col3:
        final_remaining_points = burndown_df.iloc[-1]['remaining_points']
        st.metric("Final Remaining Points", int(final_remaining_points))
    
    with col4:
        total_completed_items = burndown_df.iloc[-1]['completed_items']
        completion_pct = (total_completed_items / total_items * 100) if total_items > 0 else 0
        st.metric("Items Completed", int(total_completed_items), delta=f"{completion_pct:.1f}%")
    
    # Add export functionality for the burndown data
    if st.button("📥 Export Burndown Data to CSV"):
        csv = burndown_df.to_csv(index=False)
        st.download_button(
            label="Download Burndown Data CSV",
            data=csv,
            file_name=f"sprint_burndown_data_{current_sprint}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    st.markdown("---")  # Add separator before charts
    
    # Calculate key metrics for the burndown header
    current_remaining = burndown_df.iloc[-1]['remaining_items']
    completion_percentage = ((total_items - current_remaining) / total_items * 100) if total_items > 0 else 0
    
    # Calculate average burndown (items completed per day)
    total_completed = total_items - current_remaining
    sprint_days_elapsed = len(burndown_df)
    avg_burndown = total_completed / sprint_days_elapsed if sprint_days_elapsed > 0 else 0
    
    # Calculate scope changes (assuming scope started at total_items)
    initial_scope = total_items
    current_scope = total_items  # In this case, scope hasn't changed
    scope_change = current_scope - initial_scope
    
    # Calculate projected completion
    if avg_burndown > 0 and current_remaining > 0:
        days_to_complete = current_remaining / avg_burndown
        projected_completion = end_date + timedelta(days=int(days_to_complete))
        days_beyond_sprint = (projected_completion - end_date).days
    else:
        projected_completion = end_date
        days_beyond_sprint = 0
    
    # Work Items Breakdown Table - show all items considered in the current iteration
    st.subheader("📋 Work Items in Current Iteration - Detailed Breakdown")
    
    # Create comprehensive table with all relevant fields
    breakdown_df = scope_items.copy()
    
    # Format the data for display
    display_breakdown = breakdown_df[[
        'id', 'title', 'type', 'state', 'assignee', 'story_points', 
        'category', 'created_date', 'activated_date', 'resolved_date', 
        'closed_date', 'cycle_time_days', 'tags', 'is_completed'
    ]].copy()
    
    # Format dates for display
    display_breakdown['created_date'] = display_breakdown['created_date'].apply(format_date_for_display)
    display_breakdown['activated_date'] = display_breakdown['activated_date'].apply(format_date_for_display)
    display_breakdown['resolved_date'] = display_breakdown['resolved_date'].apply(format_date_for_display)
    display_breakdown['closed_date'] = display_breakdown['closed_date'].apply(format_date_for_display)
    
    # Format cycle time
    display_breakdown['cycle_time_days'] = display_breakdown['cycle_time_days'].apply(
        lambda x: f"{x:.1f} days" if pd.notna(x) else "N/A"
    )
    
    # Truncate long titles for better display
    display_breakdown['title'] = display_breakdown['title'].apply(
        lambda x: x[:60] + "..." if len(x) > 60 else x
    )
    
    # Format tags
    display_breakdown['tags'] = display_breakdown['tags'].apply(
        lambda x: x[:30] + "..." if x and len(x) > 30 else (x if x else "None")
    )
    
    # Format completion status
    display_breakdown['is_completed'] = display_breakdown['is_completed'].apply(
        lambda x: "✅ Yes" if x else "⏳ No"
    )
    
    # Rename columns for better display
    display_breakdown.columns = [
        'ID', 'Title', 'Type', 'State', 'Assignee', 'Story Points',
        'Category', 'Created Date', 'Activated Date', 'Resolved Date',
        'Closed Date', 'Cycle Time', 'Tags', 'Completed'
    ]
    
    # Add summary information above the table
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items in Scope", len(scope_items))
    
    with col2:
        completed_count = len(scope_items[scope_items['is_completed'] == True])
        st.metric("Completed Items", completed_count, delta=f"{(completed_count/len(scope_items)*100):.1f}%")
    
    with col3:
        remaining_count = len(scope_items[scope_items['is_completed'] == False])
        st.metric("Remaining Items", remaining_count)
    
    with col4:
        total_scope_points = scope_items['story_points'].sum()
        st.metric("Total Story Points", int(total_scope_points))
    
    # Display the comprehensive table
    st.dataframe(
        display_breakdown,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "State": st.column_config.TextColumn("State", width="small"),
            "Assignee": st.column_config.TextColumn("Assignee", width="medium"),
            "Story Points": st.column_config.NumberColumn("Story Points", width="small"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "Created Date": st.column_config.TextColumn("Created Date", width="small"),
            "Activated Date": st.column_config.TextColumn("Activated Date", width="small"),
            "Resolved Date": st.column_config.TextColumn("Resolved Date", width="small"),
            "Closed Date": st.column_config.TextColumn("Closed Date", width="small"),
            "Cycle Time": st.column_config.TextColumn("Cycle Time", width="small"),
            "Tags": st.column_config.TextColumn("Tags", width="medium"),
            "Completed": st.column_config.TextColumn("Completed", width="small")
        }
    )
    
    # Add export functionality for the breakdown table
    if st.button("📥 Export Work Items Breakdown to CSV"):
        # Use original data with proper formatting for export
        export_df = scope_items.copy()
        export_df['created_date'] = export_df['created_date'].apply(format_date_for_display)
        export_df['activated_date'] = export_df['activated_date'].apply(format_date_for_display)
        export_df['resolved_date'] = export_df['resolved_date'].apply(format_date_for_display)
        export_df['closed_date'] = export_df['closed_date'].apply(format_date_for_display)
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download Work Items Breakdown CSV",
            data=csv,
            file_name=f"sprint_work_items_breakdown_{current_sprint}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    st.markdown("---")  # Add separator before burndown charts
    
    # COMPREHENSIVE DEBUG SECTION FOR fig_burndown CHART DATA ANALYSIS
    st.markdown("### 🔍 DEBUG: fig_burndown Chart Data Analysis")
    
    # Debug 1: Show burndown_df structure and data for work items chart
    st.write(f"**fig_burndown chart data source**: burndown_df")
    st.write(f"**burndown_df shape**: {burndown_df.shape}")
    st.write(f"**burndown_df columns**: {list(burndown_df.columns)}")
    
    # Debug 2: Show complete data from burndown_df for work items
    st.write("**Complete burndown_df data for fig_burndown (work items chart):**")
    st.dataframe(burndown_df)
    
    # Debug 3: Show remaining_items specific data
    if 'remaining_items' in burndown_df.columns:
        st.write(f"**remaining_items data**: {burndown_df['remaining_items'].tolist()}")
        st.write(f"**remaining_items stats**: min={burndown_df['remaining_items'].min()}, max={burndown_df['remaining_items'].max()}, mean={burndown_df['remaining_items'].mean():.2f}")
        
        # Check for the specific date mentioned in the issue (07/16)
        july_16_data = burndown_df[burndown_df['date'] == datetime(2025, 7, 16).date()]
        if not july_16_data.empty:
            july_16_remaining = july_16_data['remaining_items'].iloc[0]
            st.write(f"**07/16 remaining_items value**: {july_16_remaining} (should be 32 according to user)")
        else:
            st.write("**07/16 data**: Not found in burndown_df")
    else:
        st.error("❌ 'remaining_items' column not found in burndown_df!")
    
    # Debug 4: Show total_items variable used in chart
    st.write(f"**total_items variable**: {total_items}")
    st.write(f"**total_story_points variable**: {total_story_points}")
    
    # Debug 5: Show date column for work items chart
    if 'date' in burndown_df.columns:
        st.write(f"**date data**: {burndown_df['date'].tolist()}")
        st.write(f"**date range**: {burndown_df['date'].min()} to {burndown_df['date'].max()}")
        st.write(f"**date data types**: {[type(d) for d in burndown_df['date'].tolist()]}")
    else:
        st.error("❌ 'date' column not found in burndown_df!")
    
    # Debug 6: Check for any NaN or invalid values in work items data
    if 'remaining_items' in burndown_df.columns:
        nan_count = burndown_df['remaining_items'].isna().sum()
        st.write(f"**remaining_items NaN count**: {nan_count}")
        if nan_count > 0:
            st.warning(f"⚠️ Found {nan_count} NaN values in remaining_items!")
            st.write("**Rows with NaN remaining_items:**")
            nan_rows = burndown_df[burndown_df['remaining_items'].isna()]
            st.dataframe(nan_rows)
    
    # Debug 7: Show chart data preparation for fig_burndown
    if all(col in burndown_df.columns for col in ['date', 'remaining_items']):
        chart_data_items = {
            'x_data': burndown_df['date'].tolist(),
            'y_data_remaining_items': burndown_df['remaining_items'].tolist(),
            'chart_type': 'Work Items Burndown (fig_burndown)'
        }
        st.write("**Chart data for fig_burndown (work items):**")
        st.json(chart_data_items)
        
        # Show specific data points that will be plotted
        st.write("**Key data points for fig_burndown:**")
        for i, (date, remaining) in enumerate(zip(burndown_df['date'], burndown_df['remaining_items'])):
            if i < 5 or date == datetime(2025, 7, 16).date():  # Show first 5 and July 16th
                st.write(f"  - {date}: {remaining} remaining items")
    else:
        st.error("❌ Missing required columns for fig_burndown chart data!")
    
    # Debug 8: Show ideal burndown calculation for comparison
    if len(burndown_df) > 0:
        st.write("**Ideal burndown calculation for fig_burndown:**")
        ideal_burndown_debug = []
        for i, date in enumerate(burndown_df['date']):
            progress = i / (len(burndown_df) - 1) if len(burndown_df) > 1 else 0
            ideal_remaining = total_items * (1 - progress)
            ideal_burndown_debug.append({
                'date': date,
                'progress': f"{progress:.2f}",
                'ideal_remaining': f"{ideal_remaining:.1f}"
            })
        
        # Show first few and July 16th
        for item in ideal_burndown_debug[:5]:
            st.write(f"  - {item['date']}: progress={item['progress']}, ideal_remaining={item['ideal_remaining']}")
        
        # Find July 16th in ideal burndown
        july_16_ideal = next((item for item in ideal_burndown_debug if item['date'] == datetime(2025, 7, 16).date()), None)
        if july_16_ideal:
            st.write(f"  - **07/16 ideal**: progress={july_16_ideal['progress']}, ideal_remaining={july_16_ideal['ideal_remaining']}")
    
    # Debug 9: Compare actual vs expected for July 16th
    if 'remaining_items' in burndown_df.columns:
        july_16_data = burndown_df[burndown_df['date'] == datetime(2025, 7, 16).date()]
        if not july_16_data.empty:
            actual_remaining = july_16_data['remaining_items'].iloc[0]
            st.write(f"**07/16 COMPARISON:**")
            st.write(f"  - Actual remaining items: {actual_remaining}")
            st.write(f"  - Expected (user reported): 32")
            st.write(f"  - Match: {'✅ YES' if actual_remaining == 32 else '❌ NO'}")
            
            if actual_remaining != 32:
                st.error(f"❌ MISMATCH: Chart will show {actual_remaining} but should show 32")
            else:
                st.success(f"✅ CORRECT: Chart will show {actual_remaining} as expected")
    
    st.markdown("---")  # Add separator before chart
    
    # Create the main burndown chart as line chart with dynamic data
    fig_burndown = go.Figure()
    
    # Add actual burndown line (thick blue line showing remaining work items)
    fig_burndown.add_trace(go.Scatter(
        x=burndown_df['date'],
        y=burndown_df['remaining_items'],
        mode='lines+markers',
        name='Actual Burndown',
        line=dict(color='#4A90E2', width=4),  # Thick blue line
        marker=dict(size=8, color='#4A90E2', symbol='circle'),
        hovertemplate='<b>Date:</b> %{x}<br><b>Remaining Items:</b> %{y}<extra></extra>'
    ))
    
    # Add ideal burndown line (dashed gray line) for reference
    ideal_burndown = []
    for i, date in enumerate(burndown_df['date']):
        # Calculate ideal remaining items (linear burndown)
        progress = i / (len(burndown_df) - 1) if len(burndown_df) > 1 else 0
        ideal_remaining = total_items * (1 - progress)
        ideal_burndown.append(ideal_remaining)
    
    fig_burndown.add_trace(go.Scatter(
        x=burndown_df['date'],
        y=ideal_burndown,
        mode='lines',
        name='Ideal Burndown',
        line=dict(color='#95A5A6', width=3, dash='dash'),  # Gray dashed line
        hovertemplate='<b>Date:</b> %{x}<br><b>Ideal Remaining:</b> %{y:.0f}<extra></extra>'
    ))
    
    # Add total scope reference line (orange dashed line at the top)
    fig_burndown.add_trace(go.Scatter(
        x=burndown_df['date'],
        y=[total_items] * len(burndown_df),
        mode='lines',
        name='Total Scope',
        line=dict(color='#F39C12', width=2, dash='dot'),  # Orange dotted line
        hovertemplate='<b>Total Scope:</b> %{y} items<extra></extra>'
    ))
    
    # Add zero line for reference
    fig_burndown.add_trace(go.Scatter(
        x=burndown_df['date'],
        y=[0] * len(burndown_df),
        mode='lines',
        name='Sprint Goal',
        line=dict(color='#27AE60', width=2, dash='solid'),  # Green solid line
        hovertemplate='<b>Sprint Goal:</b> 0 items remaining<extra></extra>'
    ))
    
    # Update layout for enhanced line chart format
    fig_burndown.update_layout(
        title=dict(
            text="Sprint Burndown Chart - Work Items Progress",
            font=dict(size=18, color='#2c3e50'),
            x=0.5
        ),
        xaxis_title="Sprint Dates",
        yaxis_title="Remaining Work Items",
        plot_bgcolor='rgba(248, 249, 250, 0.8)',  # Light background
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12, family="Arial, sans-serif"),
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1
        ),
        xaxis=dict(
            tickangle=45,
            tickformat='%m/%d',
            title=dict(
                text=f"Sprint Dates ({start_date.strftime('%m/%d')} to {end_date.strftime('%m/%d')})",
                font=dict(size=12, color='#2c3e50')
            ),
            gridcolor='rgba(0,0,0,0.1)',
            showgrid=True
        ),
        yaxis=dict(
            title=dict(
                text="Remaining Work Items",
                font=dict(size=12, color='#2c3e50')
            ),
            side='left',
            range=[0, total_items + 2],  # Set range from 0 to slightly above total scope
            gridcolor='rgba(0,0,0,0.1)',
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(39, 174, 96, 0.5)',  # Green zero line
            zerolinewidth=2
        ),
        hovermode='x unified',
        margin=dict(t=60, b=100, l=60, r=60)  # Better margins
    )
    
    # COMPREHENSIVE DEBUG SECTION FOR BURNDOWN CHART DATA ANALYSIS - MOVED ABOVE CHARTS
    st.markdown("### 🔍 DEBUG: Burndown Chart Data Analysis")
    
    # Debug 1: Show burndown_df structure and data
    st.write(f"**burndown_df shape**: {burndown_df.shape}")
    st.write(f"**burndown_df columns**: {list(burndown_df.columns)}")
    
    # Debug 2: Show complete data from burndown_df
    st.write("**Complete burndown_df data (all rows):**")
    st.dataframe(burndown_df)
    
    # Debug 3: Show story points specific columns
    if 'remaining_points' in burndown_df.columns:
        st.write(f"**remaining_points data**: {burndown_df['remaining_points'].tolist()}")
        st.write(f"**remaining_points stats**: min={burndown_df['remaining_points'].min()}, max={burndown_df['remaining_points'].max()}, mean={burndown_df['remaining_points'].mean():.2f}")
    else:
        st.error("❌ 'remaining_points' column not found in burndown_df!")
    
    if 'total_scope_points' in burndown_df.columns:
        st.write(f"**total_scope_points data**: {burndown_df['total_scope_points'].tolist()}")
        st.write(f"**total_scope_points unique values**: {burndown_df['total_scope_points'].unique()}")
    else:
        st.error("❌ 'total_scope_points' column not found in burndown_df!")
    
    # Debug 4: Show date column
    if 'date' in burndown_df.columns:
        st.write(f"**date data**: {burndown_df['date'].tolist()}")
        st.write(f"**date range**: {burndown_df['date'].min()} to {burndown_df['date'].max()}")
    else:
        st.error("❌ 'date' column not found in burndown_df!")
    
    # Debug 5: Show total_story_points variable
    st.write(f"**total_story_points variable**: {total_story_points}")
    
    # Debug 6: Show scope_items analysis
    st.write(f"**scope_items shape**: {scope_items.shape}")
    st.write(f"**scope_items story_points sum**: {scope_items['story_points'].sum()}")
    st.write(f"**scope_items story_points breakdown**: {scope_items['story_points'].value_counts().sort_index().to_dict()}")
    
    # Debug 7: Check for any NaN or invalid values
    if 'remaining_points' in burndown_df.columns:
        nan_count = burndown_df['remaining_points'].isna().sum()
        st.write(f"**remaining_points NaN count**: {nan_count}")
        if nan_count > 0:
            st.warning(f"⚠️ Found {nan_count} NaN values in remaining_points!")
    
    # Debug 8: Show processed items table with ALL columns
    st.write("**Processed Items Table (scope_items) - ALL COLUMNS:**")
    if not scope_items.empty:
        # Show ALL columns from scope_items
        processed_display_full = scope_items.copy()
        
        # Format dates for better display
        date_columns = ['created_date', 'activated_date', 'resolved_date', 'closed_date']
        for col in date_columns:
            if col in processed_display_full.columns:
                processed_display_full[col] = processed_display_full[col].apply(format_date_for_display)
        
        # Format cycle time
        if 'cycle_time_days' in processed_display_full.columns:
            processed_display_full['cycle_time_days'] = processed_display_full['cycle_time_days'].apply(
                lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
            )
        
        # Truncate long titles for better display
        if 'title' in processed_display_full.columns:
            processed_display_full['title'] = processed_display_full['title'].apply(
                lambda x: x[:60] + "..." if len(x) > 60 else x
            )
        
        # Format tags
        if 'tags' in processed_display_full.columns:
            processed_display_full['tags'] = processed_display_full['tags'].apply(
                lambda x: x[:40] + "..." if x and len(x) > 40 else (x if x else "None")
            )
        
        # Format completion status
        if 'is_completed' in processed_display_full.columns:
            processed_display_full['is_completed'] = processed_display_full['is_completed'].apply(
                lambda x: "✅ Yes" if x else "⏳ No"
            )
        
        st.dataframe(processed_display_full, use_container_width=True, hide_index=True)
        
        # Show summary stats
        completed_count = len(scope_items[scope_items['is_completed'] == True])
        remaining_count = len(scope_items[scope_items['is_completed'] == False])
        total_points = scope_items['story_points'].sum()
        completed_points = scope_items[scope_items['is_completed'] == True]['story_points'].sum()
        
        st.write(f"**Processed Items Summary:**")
        st.write(f"- Total items processed: {len(scope_items)}")
        st.write(f"- Completed items: {completed_count}")
        st.write(f"- Remaining items: {remaining_count}")
        st.write(f"- Total story points: {total_points}")
        st.write(f"- Completed story points: {completed_points}")
        st.write(f"- Remaining story points: {total_points - completed_points}")
    else:
        st.error("❌ No processed items (scope_items is empty)!")
    
    # Debug 9: Show chart data preparation
    if all(col in burndown_df.columns for col in ['date', 'remaining_points', 'total_scope_points']):
        chart_data = {
            'x_data': burndown_df['date'].tolist(),
            'y_data_remaining': burndown_df['remaining_points'].tolist(),
            'y_data_total': burndown_df['total_scope_points'].tolist()
        }
        st.write("**Chart data for fig_burndown_points:**")
        st.json(chart_data)
    else:
        st.error("❌ Missing required columns for chart data!")
    
    st.markdown("---")  # Add separator before charts
    
    # Display burndown charts side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(fig_burndown, use_container_width=True)
    
    with col2:
        # Story Points Burndown Chart - Column Chart Format
        fig_burndown_points = go.Figure()
        
        # Add remaining points as blue column bars
        fig_burndown_points.add_trace(go.Bar(
            x=burndown_df['date'],
            y=burndown_df['remaining_points'],
            name='Remaining Story Points',
            marker_color='#4A90E2',  # Blue color matching work items chart
            opacity=0.8,
            width=0.6  # Make bars slightly narrower for better appearance
        ))
        
        # Add burndown line (gray) - showing trend of story points completion
        fig_burndown_points.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=burndown_df['remaining_points'],
            mode='lines+markers',
            name='Burndown Line',
            line=dict(color='#95A5A6', width=3),  # Gray color matching work items chart
            marker=dict(size=6, color='#95A5A6'),
            yaxis='y'
        ))
        
        # Add total scope line for points (orange)
        fig_burndown_points.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=burndown_df['total_scope_points'],
            mode='lines',
            name='Total Scope Line',
            line=dict(color='#F39C12', width=3, dash='dash'),  # Orange color matching work items chart
            yaxis='y'
        ))
        
        fig_burndown_points.update_layout(
            title="Sprint Burndown Chart - Story Points Progress",
            xaxis_title="Sprint Dates",
            yaxis_title="Count of Story Points",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            height=500,  # Match the height of the main burndown chart
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                tickangle=45,
                tickformat='%d/%m/%Y',
                title=f"Sprint Dates ({start_date} to {end_date})"
            ),
            yaxis=dict(
                title="Count of Story Points",
                side='left',
                range=[0, total_story_points + 2]  # Set range from 0 to slightly above total scope
            ),
            hovermode='x unified',
            bargap=0.2  # Add gap between bars for better visibility
        )
        
        st.plotly_chart(fig_burndown_points, use_container_width=True)
    
    # Burnup Charts
    st.subheader("📈 Sprint Burnup Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Burnup Chart - Story Count
        fig_burnup_items = go.Figure()
        
        # Completed work
        fig_burnup_items.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=burndown_df['completed_items'],
            mode='lines+markers',
            name='Completed Items',
            line=dict(color=PASTEL_COLORS['success'][0], width=3),
            marker=dict(size=6),
            fill='tonexty'
        ))
        
        # Total scope line
        fig_burnup_items.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=[total_items] * len(burndown_df),
            mode='lines',
            name='Total Scope',
            line=dict(color=PASTEL_COLORS['primary'][2], width=2, dash='dash')
        ))
        
        fig_burnup_items.update_layout(
            title="Burnup Chart - Story Count",
            xaxis_title="Date",
            yaxis_title="Completed Items",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_burnup_items, use_container_width=True)
    
    with col2:
        # Burnup Chart - Story Points
        fig_burnup_points = go.Figure()
        
        # Completed work
        fig_burnup_points.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=burndown_df['completed_points'],
            mode='lines+markers',
            name='Completed Points',
            line=dict(color=PASTEL_COLORS['success'][1], width=3),
            marker=dict(size=6),
            fill='tonexty'
        ))
        
        # Total scope line
        fig_burnup_points.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=[total_story_points] * len(burndown_df),
            mode='lines',
            name='Total Scope',
            line=dict(color=PASTEL_COLORS['primary'][3], width=2, dash='dash')
        ))
        
        fig_burnup_points.update_layout(
            title="Burnup Chart - Story Points",
            xaxis_title="Date",
            yaxis_title="Completed Story Points",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_burnup_points, use_container_width=True)
    
    # Sprint Progress Summary
    st.subheader("📊 Sprint Progress Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completion_rate_items = (len(completed_df) / total_items * 100) if total_items > 0 else 0
        st.metric(
            "Items Completion",
            f"{completion_rate_items:.1f}%",
            delta=f"{len(completed_df)}/{total_items}"
        )
    
    with col2:
        completed_points = completed_df['story_points'].sum()
        completion_rate_points = (completed_points / total_story_points * 100) if total_story_points > 0 else 0
        st.metric(
            "Points Completion",
            f"{completion_rate_points:.1f}%",
            delta=f"{int(completed_points)}/{int(total_story_points)}"
        )
    
    with col3:
        sprint_duration = (end_date - start_date).days + 1
        st.metric(
            "Sprint Duration",
            f"{sprint_duration} days",
            delta=f"{start_date} to {end_date}"
        )
    
    with col4:
        avg_velocity_items = len(completed_df) / sprint_duration if sprint_duration > 0 else 0
        st.metric(
            "Avg Velocity",
            f"{avg_velocity_items:.1f} items/day",
            delta=f"{completed_points/sprint_duration:.1f} pts/day" if sprint_duration > 0 else "0 pts/day"
        )
    
    # Trend Analysis
    if len(burndown_df) > 1:
        st.subheader("📈 Trend Analysis")
        
        # Calculate velocity trend
        recent_days = min(7, len(burndown_df) // 2)
        if recent_days > 1:
            recent_velocity = (burndown_df.iloc[-1]['completed_items'] - burndown_df.iloc[-recent_days]['completed_items']) / recent_days
            early_velocity = burndown_df.iloc[recent_days]['completed_items'] / recent_days if recent_days < len(burndown_df) else 0
            
            col1, col2 = st.columns(2)
            
            with col1:
                if recent_velocity > early_velocity:
                    st.success(f"📈 **Accelerating** - Recent velocity: {recent_velocity:.1f} items/day")
                elif recent_velocity < early_velocity * 0.8:
                    st.warning(f"📉 **Slowing down** - Recent velocity: {recent_velocity:.1f} items/day")
                else:
                    st.info(f"➡️ **Steady pace** - Recent velocity: {recent_velocity:.1f} items/day")
            
            with col2:
                # Projection based on current velocity
                if recent_velocity > 0:
                    remaining_items = burndown_df.iloc[-1]['remaining_items']
                    days_to_complete = remaining_items / recent_velocity
                    projected_end = burndown_df.iloc[-1]['date'] + timedelta(days=int(days_to_complete))
                    
                    if projected_end <= end_date:
                        st.success(f"🎯 **On track** - Projected completion: {projected_end}")
                    else:
                        st.warning(f"⚠️ **Behind schedule** - Projected completion: {projected_end}")
                else:
                    st.warning("⚠️ **No recent progress** - Review sprint blockers")

def render_detailed_view_tab(df):
    """Render the detailed view tab"""
    st.header("Detailed Work Items View")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status:",
            options=df['state'].unique(),
            default=df['state'].unique()
        )
    
    with col2:
        type_filter = st.multiselect(
            "Filter by Type:",
            options=df['type'].unique(),
            default=df['type'].unique()
        )
    
    with col3:
        category_filter = st.multiselect(
            "Filter by Category:",
            options=df['category'].unique(),
            default=df['category'].unique()
        )
    
    with col4:
        assignee_filter = st.multiselect(
            "Filter by Assignee:",
            options=df['assignee'].unique(),
            default=df['assignee'].unique()
        )
    
    # Apply filters
    filtered_df = df[
        (df['state'].isin(status_filter)) &
        (df['type'].isin(type_filter)) &
        (df['category'].isin(category_filter)) &
        (df['assignee'].isin(assignee_filter))
    ]
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} work items")
    
    # Search functionality
    search_term = st.text_input("Search in titles:", "")
    if search_term:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
        st.write(f"Found {len(filtered_df)} items matching '{search_term}'")
    
    # Display filtered data
    if not filtered_df.empty:
        # Select columns to display
        display_columns = st.multiselect(
            "Select columns to display:",
            options=['id', 'title', 'type', 'state', 'assignee', 'story_points', 'category', 'cycle_time_days'],
            default=['id', 'title', 'type', 'state', 'assignee', 'story_points', 'cycle_time_days']
        )
        
        if display_columns:
            # Format the dataframe for display with clickable work item links
            display_df = filtered_df[display_columns].copy()
            
            # Add clickable links for work item IDs
            if 'id' in display_columns:
                display_df['id'] = display_df['id'].apply(
                    lambda x: f'<a href="https://dev.azure.com/tr-tax/TaxProf/_workitems/edit/{x}" target="_blank">{x}</a>'
                )
            
            # Format cycle time
            if 'cycle_time_days' in display_columns:
                display_df['cycle_time_days'] = display_df['cycle_time_days'].apply(
                    lambda x: f"{x} days" if pd.notna(x) else "N/A"
                )
            
            # Truncate long titles
            if 'title' in display_columns:
                display_df['title'] = display_df['title'].apply(
                    lambda x: x[:80] + "..." if len(x) > 80 else x
                )
            
            # Display with HTML links enabled
            st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Export functionality
            if st.button("📥 Export to CSV"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"azure_devops_work_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    else:
        st.info("No work items match the current filters.")

def render_recent_changes_tab(df, pat_token):
    """Render the recent changes tab showing top 5 recently changed work items"""
    st.header("🔄 Recent Changes Analysis")
    st.markdown("Analysis of the top 5 most recently changed work items with detailed change history")
    
    if df.empty:
        st.warning("No work items data available. Please fetch data first.")
        return
    
    if not pat_token:
        st.warning("PAT token required to fetch work item revision history.")
        return
    
    # Get the 5 most recently changed items based on StateChangeDate
    recent_items = df.copy()
    
    # Convert StateChangeDate to datetime for sorting
    recent_items['state_change_datetime'] = pd.to_datetime(recent_items['created_date'], errors='coerce')
    
    # Sort by most recent changes and get top 5
    recent_items = recent_items.sort_values('state_change_datetime', ascending=False).head(5)
    
    if recent_items.empty:
        st.info("No recent changes found in the current work items.")
        return
    
    st.subheader("📊 Top 5 Recently Changed Work Items")
    
    # Display summary table with history
    summary_data = []
    
    # Fetch revision history for each item to generate brief change summary
    with st.spinner("Fetching change history for summary table..."):
        for _, item in recent_items.iterrows():
            # Get brief change summary
            revision_history = fetch_work_item_revisions(item['id'], pat_token)
            change_summary = get_brief_change_summary(revision_history)
            
            summary_data.append({
                'ID': f'<a href="https://dev.azure.com/tr-tax/TaxProf/_workitems/edit/{item["id"]}" target="_blank">{item["id"]}</a>',
                'Title': item['title'][:50] + "..." if len(item['title']) > 50 else item['title'],
                'Type': item['type'],
                'State': item['state'],
                'Assignee': item['assignee'],
                'Last Changed': item['state_change_datetime'].strftime('%Y-%m-%d %H:%M') if pd.notna(item['state_change_datetime']) else 'N/A',
                'History': change_summary
            })
    
    summary_df = pd.DataFrame(summary_data)
    st.markdown(summary_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    # Detailed analysis for each item
    st.subheader("🔍 Detailed Change Analysis")
    
    for idx, (_, item) in enumerate(recent_items.iterrows(), 1):
        with st.expander(f"#{item['id']}: {item['title'][:80]}..." if len(item['title']) > 80 else f"#{item['id']}: {item['title']}", expanded=(idx == 1)):
            
            # Basic item information
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **Work Item Details:**
                - **ID**: {item['id']}
                - **Type**: {item['type']}
                - **State**: {item['state']}
                """)
            
            with col2:
                st.markdown(f"""
                **Assignment & Points:**
                - **Assignee**: {item['assignee']}
                - **Story Points**: {item['story_points']}
                - **Category**: {item['category']}
                """)
            
            with col3:
                st.markdown(f"""
                **Timeline:**
                - **Created**: {format_date_for_display(item['created_date'])}
                - **Last Changed**: {item['state_change_datetime'].strftime('%Y-%m-%d') if pd.notna(item['state_change_datetime']) else 'N/A'}
                - **Cycle Time**: {item['cycle_time_days']} days if pd.notna(item['cycle_time_days']) else 'N/A'
                """)
            
            # Fetch and analyze revision history
            st.markdown("### 📋 Change History Analysis")
            
            with st.spinner(f"Fetching revision history for work item #{item['id']}..."):
                revision_history = fetch_work_item_revisions(item['id'], pat_token)
                
                if revision_history:
                    change_analysis = analyze_work_item_changes(revision_history)
                    
                    # Display change summary
                    st.markdown("**Change Summary:**")
                    st.markdown(change_analysis['summary'])
                    
                    # Display detailed changes
                    if change_analysis['detailed_changes']:
                        st.markdown("**Detailed Changes:**")
                        for change in change_analysis['detailed_changes']:
                            st.markdown(f"- **{change['date']}**: {change['description']}")
                    
                    # Display revision timeline
                    if len(revision_history) > 1:
                        st.markdown("**Revision Timeline:**")
                        timeline_data = []
                        for rev in revision_history[-5:]:  # Show last 5 revisions
                            timeline_data.append({
                                'Revision': rev.get('rev', 'N/A'),
                                'Date': rev.get('fields', {}).get('System.ChangedDate', 'N/A')[:10] if rev.get('fields', {}).get('System.ChangedDate') else 'N/A',
                                'Changed By': rev.get('fields', {}).get('System.ChangedBy', {}).get('displayName', 'Unknown') if rev.get('fields', {}).get('System.ChangedBy') else 'Unknown',
                                'State': rev.get('fields', {}).get('System.State', 'N/A')
                            })
                        
                        timeline_df = pd.DataFrame(timeline_data)
                        st.table(timeline_df)
                else:
                    st.warning(f"Could not fetch revision history for work item #{item['id']}")

def fetch_work_item_revisions(work_item_id, pat_token):
    """Fetch revision history for a specific work item"""
    try:
        organization = AZURE_DEVOPS_CONFIG["organization"]
        project = AZURE_DEVOPS_CONFIG["project"]
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f":{pat_token}".encode()).decode()}',
            'Content-Type': 'application/json'
        }
        
        # Get work item revisions
        url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}/revisions?api-version=6.0"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            st.error(f"Failed to fetch revisions for work item {work_item_id}: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Error fetching work item revisions: {str(e)}")
        return []

def get_brief_change_summary(revision_history):
    """Generate a brief summary of changes for the History column with specific details"""
    if not revision_history or len(revision_history) < 2:
        return "No changes"
    
    changes = []
    change_details = {}
    
    # Compare consecutive revisions to identify key changes
    for i in range(1, len(revision_history)):
        prev_rev = revision_history[i-1]
        curr_rev = revision_history[i]
        
        prev_fields = prev_rev.get('fields', {})
        curr_fields = curr_rev.get('fields', {})
        
        # Check for state changes
        prev_state = prev_fields.get('System.State', '')
        curr_state = curr_fields.get('System.State', '')
        if prev_state != curr_state:
            change_key = "State"
            if change_key not in change_details:
                change_details[change_key] = f"{prev_state}→{curr_state}"
                changes.append(change_key)
        
        # Check for assignee changes
        prev_assignee = prev_fields.get('System.AssignedTo', {}).get('displayName', '') if prev_fields.get('System.AssignedTo') else ''
        curr_assignee = curr_fields.get('System.AssignedTo', {}).get('displayName', '') if curr_fields.get('System.AssignedTo') else ''
        if prev_assignee != curr_assignee:
            change_key = "Assignee"
            if change_key not in change_details:
                # Shorten names for display
                prev_short = prev_assignee.split()[0] if prev_assignee else "None"
                curr_short = curr_assignee.split()[0] if curr_assignee else "None"
                change_details[change_key] = f"{prev_short}→{curr_short}"
                changes.append(change_key)
        
        # Check for story points changes
        prev_points = prev_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0
        curr_points = curr_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0
        if prev_points != curr_points:
            change_key = "Points"
            if change_key not in change_details:
                change_details[change_key] = f"{prev_points}→{curr_points}"
                changes.append(change_key)
        
        # Check for title changes
        prev_title = prev_fields.get('System.Title', '')
        curr_title = curr_fields.get('System.Title', '')
        if prev_title != curr_title and prev_title and curr_title:
            change_key = "Title"
            if change_key not in change_details:
                change_details[change_key] = "Updated"
                changes.append(change_key)
        
        # Check for iteration path changes
        prev_iteration = prev_fields.get('System.IterationPath', '')
        curr_iteration = curr_fields.get('System.IterationPath', '')
        if prev_iteration != curr_iteration:
            change_key = "Iteration"
            if change_key not in change_details:
                # Extract just the iteration name for brevity
                prev_iter = prev_iteration.split('\\')[-1] if prev_iteration else "None"
                curr_iter = curr_iteration.split('\\')[-1] if curr_iteration else "None"
                change_details[change_key] = f"{prev_iter}→{curr_iter}"
                changes.append(change_key)
    
    # Remove duplicates while preserving order
    unique_changes = list(dict.fromkeys(changes))
    
    if not unique_changes:
        return "Created"
    elif len(unique_changes) == 1:
        change = unique_changes[0]
        return f"{change}: {change_details[change]}"
    elif len(unique_changes) == 2:
        change1, change2 = unique_changes[0], unique_changes[1]
        return f"{change1}: {change_details[change1]}, {change2}: {change_details[change2]}"
    elif len(unique_changes) == 3:
        change1, change2, change3 = unique_changes[0], unique_changes[1], unique_changes[2]
        return f"{change1}: {change_details[change1]}, {change2}: {change_details[change2]}, {change3}: {change_details[change3]}"
    else:
        change1, change2 = unique_changes[0], unique_changes[1]
        return f"{change1}: {change_details[change1]}, {change2}: {change_details[change2]}, +{len(unique_changes)-2} more"

def analyze_work_item_changes(revision_history):
    """Analyze work item revision history and generate change summary"""
    if not revision_history or len(revision_history) < 2:
        return {
            'summary': "No significant changes detected or insufficient revision history.",
            'detailed_changes': []
        }
    
    changes = []
    detailed_changes = []
    
    # Compare consecutive revisions
    for i in range(1, len(revision_history)):
        prev_rev = revision_history[i-1]
        curr_rev = revision_history[i]
        
        prev_fields = prev_rev.get('fields', {})
        curr_fields = curr_rev.get('fields', {})
        
        change_date = curr_fields.get('System.ChangedDate', '')[:10] if curr_fields.get('System.ChangedDate') else 'Unknown'
        changed_by = curr_fields.get('System.ChangedBy', {}).get('displayName', 'Unknown') if curr_fields.get('System.ChangedBy') else 'Unknown'
        
        # Check for state changes
        prev_state = prev_fields.get('System.State', '')
        curr_state = curr_fields.get('System.State', '')
        if prev_state != curr_state:
            changes.append(f"State changed from '{prev_state}' to '{curr_state}'")
            detailed_changes.append({
                'date': change_date,
                'description': f"State changed from '{prev_state}' to '{curr_state}' by {changed_by}"
            })
        
        # Check for assignee changes
        prev_assignee = prev_fields.get('System.AssignedTo', {}).get('displayName', '') if prev_fields.get('System.AssignedTo') else ''
        curr_assignee = curr_fields.get('System.AssignedTo', {}).get('displayName', '') if curr_fields.get('System.AssignedTo') else ''
        if prev_assignee != curr_assignee:
            if not prev_assignee:
                changes.append(f"Assigned to {curr_assignee}")
                detailed_changes.append({
                    'date': change_date,
                    'description': f"Work item assigned to {curr_assignee}"
                })
            elif not curr_assignee:
                changes.append(f"Unassigned from {prev_assignee}")
                detailed_changes.append({
                    'date': change_date,
                    'description': f"Work item unassigned from {prev_assignee}"
                })
            else:
                changes.append(f"Reassigned from {prev_assignee} to {curr_assignee}")
                detailed_changes.append({
                    'date': change_date,
                    'description': f"Reassigned from {prev_assignee} to {curr_assignee}"
                })
        
        # Check for story points changes
        prev_points = prev_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0
        curr_points = curr_fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0
        if prev_points != curr_points:
            changes.append(f"Story points changed from {prev_points} to {curr_points}")
            detailed_changes.append({
                'date': change_date,
                'description': f"Story points updated from {prev_points} to {curr_points} by {changed_by}"
            })
        
        # Check for title changes
        prev_title = prev_fields.get('System.Title', '')
        curr_title = curr_fields.get('System.Title', '')
        if prev_title != curr_title and prev_title and curr_title:
            changes.append("Title was updated")
            detailed_changes.append({
                'date': change_date,
                'description': f"Title updated by {changed_by}"
            })
        
        # Check for iteration path changes
        prev_iteration = prev_fields.get('System.IterationPath', '')
        curr_iteration = curr_fields.get('System.IterationPath', '')
        if prev_iteration != curr_iteration:
            changes.append(f"Moved to different iteration")
            detailed_changes.append({
                'date': change_date,
                'description': f"Moved from '{prev_iteration}' to '{curr_iteration}' by {changed_by}"
            })
    
    # Generate summary
    if not changes:
        summary = "Work item was created but no significant field changes detected."
    else:
        summary = f"This work item has undergone {len(changes)} significant changes: "
        if len(changes) <= 3:
            summary += ", ".join(changes) + "."
        else:
            summary += ", ".join(changes[:2]) + f", and {len(changes)-2} other changes."
    
    # Add context based on change patterns
    state_changes = [c for c in changes if 'State changed' in c]
    assignment_changes = [c for c in changes if 'assigned' in c.lower()]
    
    if len(state_changes) > 2:
        summary += " This item has moved through multiple workflow states, indicating active development."
    elif len(assignment_changes) > 1:
        summary += " This item has been reassigned multiple times, possibly indicating workload balancing or expertise requirements."
    
    return {
        'summary': summary,
        'detailed_changes': detailed_changes[-10:]  # Keep last 10 changes
    }

def render_ai_assistant_tab(df, completed_df):
    """Render the AI Assistant chatbot tab with modern chat interface matching dashboard UI"""
    
    if df.empty:
        st.warning("No work items data available. Please fetch data first to enable AI assistance.")
        return
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Create modern chat interface matching the dashboard style
    st.markdown("""
    <style>
    /* Chat Interface Styles matching dashboard UI */
    .chat-widget {
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        overflow: hidden;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
        max-width: 800px;
        margin: 2rem auto;
    }
    
    .chat-header {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        padding: 1.5rem 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        font-weight: 600;
        font-size: 1.2rem;
    }
    
    .chat-header-icon {
        width: 40px;
        height: 40px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    
    .chat-messages {
        padding: 2rem;
        min-height: 400px;
        max-height: 500px;
        overflow-y: auto;
        background: #f8f9fa;
    }
    
    .bot-message {
        background: #f1f3f4;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 0;
        max-width: 85%;
        position: relative;
        color: #2d3436;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .bot-message::before {
        content: "🤖";
        position: absolute;
        left: -2.5rem;
        top: 0.5rem;
        width: 2rem;
        height: 2rem;
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin: 1rem 0 1rem auto;
        max-width: 85%;
        margin-left: auto;
        position: relative;
        line-height: 1.5;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .user-message::after {
        content: "👤";
        position: absolute;
        right: -2.5rem;
        top: 0.5rem;
        width: 2rem;
        height: 2rem;
        background: white;
        color: #2d3436;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .welcome-message {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: #2d3436;
        border-left: 4px solid #4ecdc4;
        box-shadow: 0 4px 16px rgba(168, 237, 234, 0.3);
    }
    
    .quick-actions {
        padding: 1.5rem 2rem;
        background: white;
        border-top: 1px solid #e9ecef;
    }
    
    .quick-action-btn {
        background: white;
        border: 2px solid #e74c3c;
        color: #e74c3c;
        padding: 0.75rem 1.5rem;
        border-radius: 25px;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
        display: inline-block;
    }
    
    .quick-action-btn:hover {
        background: #e74c3c;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
    }
    
    .chat-input-area {
        padding: 1.5rem 2rem;
        background: white;
        border-top: 1px solid #e9ecef;
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .chat-input {
        flex: 1;
        padding: 1rem 1.5rem;
        border: 1px solid #ddd;
        border-radius: 25px;
        font-size: 1rem;
        outline: none;
        transition: border-color 0.2s ease;
    }
    
    .chat-input:focus {
        border-color: #e74c3c;
        box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
    }
    
    .chat-send-btn {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        border: none;
        padding: 1rem 1.5rem;
        border-radius: 25px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .chat-send-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(231, 76, 60, 0.3);
    }
    
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #666;
        font-style: italic;
        margin: 1rem 0;
    }
    
    .typing-dots {
        display: flex;
        gap: 0.25rem;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background: #e74c3c;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    /* Scrollbar styling */
    .chat-messages::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: #e74c3c;
        border-radius: 3px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: #c0392b;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize chat history if empty
    if not st.session_state.chat_history:
        welcome_msg = """👋 **Welcome back! What can we help you with?**

I'm your AI Sprint Assistant, ready to analyze your team's performance and provide insights on:

• **Sprint Progress** - Completion rates, velocity, and timeline analysis
• **Team Performance** - Top performers, workload distribution, and efficiency  
• **Work Analysis** - Category breakdowns, cycle times, and complexity
• **Issue Detection** - Potential blockers, risks, and recommendations
• **Goal Tracking** - Sprint objectives and target achievement

What would you like to know about your sprint?"""
        
        st.session_state.chat_history.append(("system", welcome_msg))
    
    # Create the chat widget
    st.markdown('<div class="chat-widget">', unsafe_allow_html=True)
    
    # Chat header
    st.markdown('''
    <div class="chat-header">
        <div class="chat-header-icon">🤖</div>
        <div>AI Sprint Assistant</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Chat messages area
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    
    # Display chat history
    for message_type, content in st.session_state.chat_history:
        if message_type == "system":
            st.markdown(f'<div class="welcome-message">{content}</div>', unsafe_allow_html=True)
        elif message_type == "user":
            st.markdown(f'<div class="user-message">{content}</div>', unsafe_allow_html=True)
        elif message_type == "ai":
            st.markdown(f'<div class="bot-message">{content}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick actions section
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    
    # Create quick action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Sprint Overview", key="qa_overview"):
            question = "Give me a comprehensive sprint overview with key metrics"
            st.session_state.chat_history.append(("user", question))
            ai_response = process_ai_question(question, df, completed_df)
            st.session_state.chat_history.append(("ai", ai_response))
            st.rerun()
    
    with col2:
        if st.button("🏆 Top Performers", key="qa_performers"):
            question = "Who are the top performers this sprint and why?"
            st.session_state.chat_history.append(("user", question))
            ai_response = process_ai_question(question, df, completed_df)
            st.session_state.chat_history.append(("ai", ai_response))
            st.rerun()
    
    with col3:
        if st.button("⚠️ Issues & Blockers", key="qa_issues"):
            question = "What potential issues or blockers should I be aware of?"
            st.session_state.chat_history.append(("user", question))
            ai_response = process_ai_question(question, df, completed_df)
            st.session_state.chat_history.append(("ai", ai_response))
            st.rerun()
    
    # Second row of quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏱️ Cycle Time Analysis", key="qa_cycle"):
            question = "Analyze our cycle times and identify improvement areas"
            st.session_state.chat_history.append(("user", question))
            ai_response = process_ai_question(question, df, completed_df)
            st.session_state.chat_history.append(("ai", ai_response))
            st.rerun()
    
    with col2:
        if st.button("📋 Work Categories", key="qa_categories"):
            question = "Break down our work by categories and types"
            st.session_state.chat_history.append(("user", question))
            ai_response = process_ai_question(question, df, completed_df)
            st.session_state.chat_history.append(("ai", ai_response))
            st.rerun()
    
    with col3:
        if st.button("🚀 Team Velocity", key="qa_velocity"):
            question = "What's our team velocity and how does it compare?"
            st.session_state.chat_history.append(("user", question))
            ai_response = process_ai_question(question, df, completed_df)
            st.session_state.chat_history.append(("ai", ai_response))
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input area
    st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
    
    # Input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Reply to AI Sprint Assistant",
                placeholder="Ask me anything about your sprint data...",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.form_submit_button("Send", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process user input
    if send_button and user_input.strip():
        # Add user message to chat
        st.session_state.chat_history.append(("user", user_input))
        
        # Generate AI response
        with st.spinner("🤖 AI is analyzing your data..."):
            ai_response = process_ai_question(user_input, df, completed_df)
        
        # Add AI response to chat
        st.session_state.chat_history.append(("ai", ai_response))
        
        # Rerun to show new messages
        st.rerun()
    
    # Chat management
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**💬 Chat Management**")
    
    with col2:
        if st.session_state.chat_history and len(st.session_state.chat_history) > 1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                # Keep only the welcome message
                welcome_msg = st.session_state.chat_history[0]
                st.session_state.chat_history = [welcome_msg]

def generate_top_performers_response(completed_df):
    """Generate top performers analysis response"""
    
    if completed_df.empty:
        return "❌ No completed work items available to analyze top performers."
    
    # Analyze performance by assignee
    assignee_stats = completed_df.groupby('assignee').agg({
        'story_points': ['sum', 'mean'],
        'id': 'count',
        'cycle_time_days': 'mean'
    }).reset_index()
    
    assignee_stats.columns = ['assignee', 'total_points', 'avg_points', 'items_count', 'avg_cycle_time']
    assignee_stats = assignee_stats[assignee_stats['assignee'] != 'Unassigned']
    
    if assignee_stats.empty:
        return "❌ No assigned work items available to analyze top performers."
    
    # Sort by total story points
    top_performers = assignee_stats.sort_values('total_points', ascending=False).head(3)
    
    response = "🏆 **Top Performers This Sprint:**\n\n"
    
    for i, (_, performer) in enumerate(top_performers.iterrows(), 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        cycle_time_text = f"{performer['avg_cycle_time']:.1f} days avg cycle time" if pd.notna(performer['avg_cycle_time']) else "No cycle time data"
        
        response += f"{medal} **{performer['assignee']}**\n"
        response += f"   - {int(performer['total_points'])} story points delivered\n"
        response += f"   - {int(performer['items_count'])} work items completed\n"
        response += f"   - {cycle_time_text}\n\n"
    
    # Additional insights
    total_team_points = assignee_stats['total_points'].sum()
    top_performer_points = top_performers.iloc[0]['total_points']
    top_performer_percentage = (top_performer_points / total_team_points * 100) if total_team_points > 0 else 0
    
    response += f"💡 **Insights:**\n"
    response += f"- Top performer delivered {top_performer_percentage:.1f}% of total team story points\n"
    response += f"- Team has {len(assignee_stats)} active contributors\n"
    response += f"- Average team member delivered {assignee_stats['total_points'].mean():.1f} story points"
    
    return response

def process_ai_question(question, df, completed_df):
    """Process user question and generate AI response based on data analysis"""
    question_lower = question.lower()
    
    # Calculate common metrics
    completion_rate = (len(completed_df) / len(df)) * 100 if len(df) > 0 else 0
    total_points = completed_df['story_points'].sum()
    total_targeted_points = df['story_points'].sum()
    
    # Get current context
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    current_sprint = st.session_state.get('selected_sprint', '2025_S15_Jul16-Jul29')
    
    # Sprint date mapping
    sprint_date_mapping = {
        "2025_S14_Jul02-Jul15": "July 2-15, 2025",
        "2025_S15_Jul16-Jul29": "July 16-29, 2025",
        "2025_S16_Jul30-Aug12": "July 30 - August 12, 2025",
        "2025_S17_Aug13-Aug26": "August 13-26, 2025"
    }
    sprint_period = sprint_date_mapping.get(current_sprint, "Unknown Sprint Period")
    
    # Question routing based on keywords
    if any(word in question_lower for word in ['summary', 'overview', 'status', 'how are we doing']):
        return generate_sprint_summary_response(df, completed_df, current_team, sprint_period, completion_rate, total_points, total_targeted_points)
    
    elif any(word in question_lower for word in ['top performer', 'best', 'hero', 'most productive', 'leader']):
        return generate_top_performers_response(completed_df)
    
    elif any(word in question_lower for word in ['blocker', 'issue', 'problem', 'concern', 'risk', 'delay']):
        return generate_issues_response(df, completed_df)
    
    elif any(word in question_lower for word in ['cycle time', 'how long', 'duration', 'time to complete']):
        return generate_cycle_time_response(completed_df)
    
    elif any(word in question_lower for word in ['category', 'type', 'breakdown', 'distribution']):
        return generate_category_breakdown_response(completed_df)
    
    elif any(word in question_lower for word in ['goal', 'target', 'objective', 'tracking']):
        return generate_goals_tracking_response(df, completed_df, completion_rate, total_points, total_targeted_points)
    
    elif any(word in question_lower for word in ['velocity', 'pace', 'speed', 'rate']):
        return generate_velocity_response(completed_df, current_sprint)
    
    elif any(word in question_lower for word in ['assignee', 'who', 'team member', 'developer']):
        return generate_assignee_analysis_response(completed_df)
    
    elif any(word in question_lower for word in ['backend', 'frontend', 'ux', 'bug', 'testing']):
        return generate_category_specific_response(question_lower, df, completed_df)
    
    elif any(word in question_lower for word in ['story points', 'points', 'effort', 'complexity']):
        return generate_story_points_response(df, completed_df, total_points, total_targeted_points)
    
    elif any(word in question_lower for word in ['remaining', 'left', 'incomplete', 'pending']):
        return generate_remaining_work_response(df, completed_df)
    
    else:
        # Generic response with data insights
        return generate_generic_response(question, df, completed_df, current_team, sprint_period)

def generate_sprint_summary_response(df, completed_df, current_team, sprint_period, completion_rate, total_points, total_targeted_points):
    """Generate comprehensive sprint summary response"""
    
    # Category breakdown
    category_summary = completed_df.groupby('category').agg({
        'id': 'count',
        'story_points': 'sum'
    }).reset_index()
    
    top_category = category_summary.loc[category_summary['story_points'].idxmax()] if not category_summary.empty else None
    
    # Cycle time analysis
    cycle_time_items = completed_df[completed_df['cycle_time_days'].notna()]
    avg_cycle_time = cycle_time_items['cycle_time_days'].mean() if len(cycle_time_items) > 0 else 0
    
    response = f"""
📊 **Sprint Summary for {current_team}**

**Sprint Period**: {sprint_period}

**🎯 Key Achievements:**
- ✅ **{completion_rate:.1f}% completion rate** ({len(completed_df)} of {len(df)} items completed)
- 🚀 **{int(total_points)} story points delivered** out of {int(total_targeted_points)} targeted
- ⚡ **{avg_cycle_time:.1f} days average cycle time** for completed items

**📋 Work Distribution:**
"""
    
    if not category_summary.empty:
        for _, row in category_summary.head(3).iterrows():
            percentage = (row['story_points'] / total_points * 100) if total_points > 0 else 0
            response += f"- **{row['Category']}**: {row['id']} items, {int(row['story_points'])} points ({percentage:.1f}%)\n"
    
    # Performance assessment
    if completion_rate >= 85:
        response += "\n🏆 **Performance**: Excellent sprint execution with strong delivery rate!"
    elif completion_rate >= 70:
        response += "\n✅ **Performance**: Good sprint progress with solid completion rate."
    else:
        response += "\n⚠️ **Performance**: Below target completion rate - review sprint planning and capacity."
    
    if top_category is not None:
        response += f"\n🎨 **Focus Area**: This was a {top_category['Category'].lower()}-heavy sprint with significant progress in that area."
    
    return response

def generate_issues_response(df, completed_df):
    """Generate response about potential issues and blockers"""
    
    issues = []
    
    # Check completion rate
    completion_rate = (len(completed_df) / len(df)) * 100 if len(df) > 0 else 0
    if completion_rate < 70:
        issues.append(f"⚠️ **Low completion rate** ({completion_rate:.1f}%) - Sprint may be over-committed")
    
    # Check for items with long cycle times
    cycle_time_items = completed_df[completed_df['cycle_time_days'].notna()]
    if len(cycle_time_items) > 0:
        avg_cycle_time = cycle_time_items['cycle_time_days'].mean()
        long_items = cycle_time_items[cycle_time_items['cycle_time_days'] > avg_cycle_time * 1.5]
        if len(long_items) > 0:
            issues.append(f"🐌 **{len(long_items)} items took longer than expected** (>{avg_cycle_time * 1.5:.1f} days)")
    
    # Check for unassigned items
    unassigned_items = df[df['assignee'] == 'Unassigned']
    if len(unassigned_items) > 0:
        issues.append(f"👤 **{len(unassigned_items)} unassigned items** - May cause delays")
    
    # Check for items without story points
    no_points_items = df[df['story_points'] == 0]
    if len(no_points_items) > 0:
        issues.append(f"📊 **{len(no_points_items)} items without story points** - Estimation needed")
    
    # Check remaining work distribution
    remaining_items = df[~df['is_completed']]
    if len(remaining_items) > 0:
        remaining_by_assignee = remaining_items.groupby('assignee')['story_points'].sum().sort_values(ascending=False)
        if len(remaining_by_assignee) > 0 and remaining_by_assignee.iloc[0] > remaining_by_assignee.mean() * 2:
            overloaded_person = remaining_by_assignee.index[0]
            overloaded_points = remaining_by_assignee.iloc[0]
            issues.append(f"⚖️ **Workload imbalance** - {overloaded_person} has {int(overloaded_points)} remaining points")
    
    if not issues:
        return "✅ **No major issues detected!** The sprint appears to be progressing well with no significant blockers identified."
    
    response = "⚠️ **Potential Issues & Blockers Identified:**\n\n"
    for issue in issues:
        response += f"{issue}\n"
    
    response += "\n💡 **Recommendations:**\n"
    response += "- Review sprint capacity and scope\n"
    response += "- Address unassigned items promptly\n"
    response += "- Consider pair programming for complex items\n"
    response += "- Balance workload across team members"
    
    return response

def generate_cycle_time_response(completed_df):
    """Generate cycle time analysis response"""
    
    cycle_time_items = completed_df[completed_df['cycle_time_days'].notna()]
    
    if cycle_time_items.empty:
        return "❌ **No cycle time data available** - Items may be missing activation or completion dates."
    
    avg_cycle_time = cycle_time_items['cycle_time_days'].mean()
    median_cycle_time = cycle_time_items['cycle_time_days'].median()
    max_cycle_time = cycle_time_items['cycle_time_days'].max()
    min_cycle_time = cycle_time_items['cycle_time_days'].min()
    
    # Performance categories
    fast_items = len(cycle_time_items[cycle_time_items['cycle_time_days'] <= 7])
    normal_items = len(cycle_time_items[(cycle_time_items['cycle_time_days'] > 7) & (cycle_time_items['cycle_time_days'] <= 14)])
    slow_items = len(cycle_time_items[cycle_time_items['cycle_time_days'] > 14])
    
    response = f"⏱️ **Cycle Time Analysis:**\n\n"
    response += f"📊 **Overall Metrics:**\n"
    response += f"- **Average**: {avg_cycle_time:.1f} days\n"
    response += f"- **Median**: {median_cycle_time:.1f} days\n"
    response += f"- **Range**: {min_cycle_time} - {max_cycle_time} days\n\n"
    
    response += f"🎯 **Performance Distribution:**\n"
    response += f"- 🟢 **Fast (≤7 days)**: {fast_items} items ({fast_items/len(cycle_time_items)*100:.1f}%)\n"
    response += f"- 🟡 **Normal (8-14 days)**: {normal_items} items ({normal_items/len(cycle_time_items)*100:.1f}%)\n"
    response += f"- 🔴 **Slow (>14 days)**: {slow_items} items ({slow_items/len(cycle_time_items)*100:.1f}%)\n\n"
    
    # Category analysis
    cycle_by_category = cycle_time_items.groupby('category')['cycle_time_days'].mean().sort_values(ascending=False)
    if not cycle_by_category.empty:
        response += f"📋 **By Category:**\n"
        for category, avg_time in cycle_by_category.head(3).items():
            response += f"- **{category}**: {avg_time:.1f} days average\n"
    
    # Recommendations
    if avg_cycle_time > 10:
        response += f"\n💡 **Recommendations**: Consider breaking down larger items and addressing blockers to improve cycle time."
    else:
        response += f"\n✅ **Good Performance**: Team is maintaining efficient cycle times!"
    
    return response

def generate_category_breakdown_response(completed_df):
    """Generate work category breakdown response"""
    
    if completed_df.empty:
        return "❌ No completed work items available for category analysis."
    
    category_summary = completed_df.groupby('category').agg({
        'id': 'count',
        'story_points': 'sum'
    }).reset_index()
    category_summary.columns = ['Category', 'Items', 'Story Points']
    
    total_items = category_summary['Items'].sum()
    total_points = category_summary['Story Points'].sum()
    
    response = f"📋 **Work Category Breakdown:**\n\n"
    
    for _, row in category_summary.sort_values('Story Points', ascending=False).iterrows():
        item_pct = (row['Items'] / total_items * 100) if total_items > 0 else 0
        points_pct = (row['Story Points'] / total_points * 100) if total_points > 0 else 0
        
        response += f"**{row['Category']}:**\n"
        response += f"- {row['Items']} items ({item_pct:.1f}%)\n"
        response += f"- {int(row['Story Points'])} story points ({points_pct:.1f}%)\n\n"
    
    # Insights
    top_category = category_summary.loc[category_summary['Story Points'].idxmax()]
    response += f"🎯 **Key Insight**: This sprint was {top_category['Category'].lower()}-focused, "
    response += f"representing {(top_category['Story Points']/total_points*100):.1f}% of delivered story points."
    
    return response

def generate_goals_tracking_response(df, completed_df, completion_rate, total_points, total_targeted_points):
    """Generate sprint goals tracking response"""
    
    response = f"🎯 **Sprint Goals Tracking:**\n\n"
    
    # Completion tracking
    if completion_rate >= 90:
        response += f"✅ **Completion Goal**: EXCEEDED - {completion_rate:.1f}% completion rate\n"
    elif completion_rate >= 80:
        response += f"✅ **Completion Goal**: MET - {completion_rate:.1f}% completion rate\n"
    elif completion_rate >= 70:
        response += f"⚠️ **Completion Goal**: APPROACHING - {completion_rate:.1f}% completion rate\n"
    else:
        response += f"❌ **Completion Goal**: BEHIND - {completion_rate:.1f}% completion rate\n"
    
    # Story points tracking
    points_completion = (total_points / total_targeted_points * 100) if total_targeted_points > 0 else 0
    if points_completion >= 90:
        response += f"✅ **Story Points Goal**: EXCEEDED - {int(total_points)}/{int(total_targeted_points)} points ({points_completion:.1f}%)\n"
    elif points_completion >= 80:
        response += f"✅ **Story Points Goal**: MET - {int(total_points)}/{int(total_targeted_points)} points ({points_completion:.1f}%)\n"
    else:
        response += f"⚠️ **Story Points Goal**: BEHIND - {int(total_points)}/{int(total_targeted_points)} points ({points_completion:.1f}%)\n"
    
    # Quality goals
    bug_items = completed_df[completed_df['category'].str.contains('Bug', case=False, na=False)]
    if len(bug_items) <= 2:
        response += f"✅ **Quality Goal**: EXCELLENT - Only {len(bug_items)} bugs resolved\n"
    else:
        response += f"⚠️ **Quality Goal**: REVIEW NEEDED - {len(bug_items)} bugs resolved\n"
    
    # Team collaboration
    assignees_count = len(df['assignee'].unique()) - (1 if 'Unassigned' in df['assignee'].unique() else 0)
    response += f"👥 **Team Engagement**: {assignees_count} team members actively contributing\n"
    
    # Recommendations
    remaining_items = len(df) - len(completed_df)
    if remaining_items > 0:
        response += f"\n📋 **Remaining Work**: {remaining_items} items still in progress\n"
        response += f"💡 **Focus Areas**: Prioritize high-value items and address any blockers"
    else:
        response += f"\n🎉 **Sprint Complete**: All planned work has been delivered!"
    
    return response

def generate_velocity_response(completed_df, current_sprint):
    """Generate velocity analysis response"""
    
    if completed_df.empty:
        return "❌ No completed work items available for velocity analysis."
    
    # Sprint duration (assuming 2-week sprints)
    sprint_duration = 14  # days
    
    # Calculate velocity metrics
    total_items = len(completed_df)
    total_points = completed_df['story_points'].sum()
    
    items_per_day = total_items / sprint_duration
    points_per_day = total_points / sprint_duration
    
    response = f"🚀 **Team Velocity Analysis:**\n\n"
    response += f"📊 **Current Sprint ({current_sprint}):**\n"
    response += f"- **Items Velocity**: {items_per_day:.1f} items/day\n"
    response += f"- **Points Velocity**: {points_per_day:.1f} story points/day\n"
    response += f"- **Total Delivered**: {total_items} items, {int(total_points)} points\n\n"
    
    # Velocity by category
    category_velocity = completed_df.groupby('category').agg({
        'id': 'count',
        'story_points': 'sum'
    }).reset_index()
    category_velocity.columns = ['category', 'items_count', 'story_points']
    
    response += f"📋 **Velocity by Category:**\n"
    for _, row in category_velocity.sort_values('story_points', ascending=False).iterrows():
        cat_points_per_day = row['story_points'] / sprint_duration
        response += f"- **{row['category']}**: {cat_points_per_day:.1f} points/day\n"
    
    # Performance assessment
    if points_per_day >= 3:
        response += f"\n🏆 **High Velocity**: Team is delivering at an excellent pace!"
    elif points_per_day >= 2:
        response += f"\n✅ **Good Velocity**: Team is maintaining a solid delivery pace."
    else:
        response += f"\n⚠️ **Low Velocity**: Consider reviewing sprint planning and capacity."
    
    return response

def generate_assignee_analysis_response(completed_df):
    """Generate assignee/team member analysis response"""
    
    if completed_df.empty:
        return "❌ No completed work items available for team analysis."
    
    # Assignee statistics
    assignee_stats = completed_df.groupby('assignee').agg({
        'id': 'count',
        'story_points': 'sum',
        'cycle_time_days': 'mean'
    }).reset_index()
    assignee_stats.columns = ['Assignee', 'Items', 'Story Points', 'Avg Cycle Time']
    assignee_stats = assignee_stats[assignee_stats['Assignee'] != 'Unassigned']
    
    if assignee_stats.empty:
        return "❌ No assigned work items available for team analysis."
    
    assignee_stats = assignee_stats.sort_values('Story Points', ascending=False)
    
    response = f"👥 **Team Member Analysis:**\n\n"
    
    for _, member in assignee_stats.iterrows():
        cycle_time_text = f"{member['Avg Cycle Time']:.1f} days" if pd.notna(member['Avg Cycle Time']) else "N/A"
        response += f"**{member['Assignee']}:**\n"
        response += f"- {int(member['Items'])} items completed\n"
        response += f"- {int(member['Story Points'])} story points delivered\n"
        response += f"- {cycle_time_text} average cycle time\n\n"
    
    # Team insights
    total_points = assignee_stats['Story Points'].sum()
    avg_points_per_person = assignee_stats['Story Points'].mean()
    
    response += f"📊 **Team Insights:**\n"
    response += f"- **Active Contributors**: {len(assignee_stats)} team members\n"
    response += f"- **Average per Person**: {avg_points_per_person:.1f} story points\n"
    response += f"- **Total Team Output**: {int(total_points)} story points\n"
    
    # Workload distribution
    max_points = assignee_stats['Story Points'].max()
    min_points = assignee_stats['Story Points'].min()
    if max_points > min_points * 2:
        response += f"⚖️ **Workload Distribution**: Uneven - consider balancing in future sprints"
    else:
        response += f"✅ **Workload Distribution**: Well balanced across team members"
    
    return response

def generate_category_specific_response(question_lower, df, completed_df):
    """Generate response for category-specific questions"""
    
    # Determine which category is being asked about
    if 'backend' in question_lower:
        category = 'Backend'
    elif 'frontend' in question_lower:
        category = 'Frontend'
    elif 'ux' in question_lower:
        category = 'UX'
    elif 'bug' in question_lower:
        category = 'Bug'
    elif 'testing' in question_lower or 'qa' in question_lower:
        category = 'Testing/QA'
    else:
        category = None
    
    if not category:
        return "❌ Could not identify specific category from your question. Try asking about 'backend', 'frontend', 'UX', 'bugs', or 'testing' work items."
    
    # Filter items by category
    category_items = df[df['category'].str.contains(category, case=False, na=False)]
    completed_category_items = completed_df[completed_df['category'].str.contains(category, case=False, na=False)]
    
    if category_items.empty:
        return f"❌ No {category.lower()} work items found in the current sprint data."
    
    response = f"📋 **{category} Work Items Analysis:**\n\n"
    
    # Basic stats
    total_items = len(category_items)
    completed_items = len(completed_category_items)
    completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    
    response += f"📊 **Overview:**\n"
    response += f"- **Total {category} Items**: {total_items}\n"
    response += f"- **Completed**: {completed_items} ({completion_rate:.1f}%)\n"
    response += f"- **Remaining**: {total_items - completed_items}\n\n"
    
    # Story points analysis
    if not completed_category_items.empty:
        total_points = completed_category_items['story_points'].sum()
        avg_points = completed_category_items['story_points'].mean()
        response += f"📈 **Story Points:**\n"
        response += f"- **Total Delivered**: {int(total_points)} points\n"
        response += f"- **Average per Item**: {avg_points:.1f} points\n\n"
    
    # Cycle time analysis
    cycle_time_items = completed_category_items[completed_category_items['cycle_time_days'].notna()]
    if not cycle_time_items.empty:
        avg_cycle_time = cycle_time_items['cycle_time_days'].mean()
        response += f"⏱️ **Cycle Time:**\n"
        response += f"- **Average**: {avg_cycle_time:.1f} days\n"
        response += f"- **Items with Data**: {len(cycle_time_items)}\n\n"
    
    # Top items
    if not completed_category_items.empty:
        response += f"🎯 **Completed {category} Items:**\n"
        for _, item in completed_category_items.head(5).iterrows():
            response += f"- **#{item['id']}**: {item['title'][:60]}{'...' if len(item['title']) > 60 else ''}\n"
    
    return response

def generate_story_points_response(df, completed_df, total_points, total_targeted_points):
    """Generate story points analysis response"""
    
    response = f"📊 **Story Points Analysis:**\n\n"
    
    # Overall metrics
    points_completion = (total_points / total_targeted_points * 100) if total_targeted_points > 0 else 0
    response += f"🎯 **Overall Progress:**\n"
    response += f"- **Delivered**: {int(total_points)} story points\n"
    response += f"- **Targeted**: {int(total_targeted_points)} story points\n"
    response += f"- **Completion**: {points_completion:.1f}%\n\n"
    
    # Distribution analysis
    if not completed_df.empty:
        points_dist = completed_df['story_points'].value_counts().sort_index()
        response += f"📈 **Points Distribution (Completed Items):**\n"
        for points, count in points_dist.items():
            if points > 0:  # Skip 0-point items
                response += f"- **{points} points**: {count} items\n"
        
        # Average complexity
        avg_points = completed_df[completed_df['story_points'] > 0]['story_points'].mean()
        response += f"\n📋 **Average Complexity**: {avg_points:.1f} story points per item\n"
    
    # Category breakdown
    if not completed_df.empty:
        category_points = completed_df.groupby('category')['story_points'].sum().sort_values(ascending=False)
        response += f"\n🏷️ **Points by Category:**\n"
        for category, points in category_points.head(5).items():
            percentage = (points / total_points * 100) if total_points > 0 else 0
            response += f"- **{category}**: {int(points)} points ({percentage:.1f}%)\n"
    
    # Performance assessment
    if points_completion >= 90:
        response += f"\n🏆 **Excellent Progress**: Team exceeded story point targets!"
    elif points_completion >= 80:
        response += f"\n✅ **Good Progress**: Team met most story point targets."
    else:
        response += f"\n⚠️ **Behind Target**: Consider reviewing sprint scope and capacity."
    
    return response

def generate_remaining_work_response(df, completed_df):
    """Generate remaining work analysis response"""
    
    remaining_df = df[~df['is_completed']]
    
    if remaining_df.empty:
        return "🎉 **All Work Complete!** No remaining work items in the current sprint."
    
    response = f"📋 **Remaining Work Analysis:**\n\n"
    
    # Basic metrics
    total_remaining = len(remaining_df)
    remaining_points = remaining_df['story_points'].sum()
    
    response += f"📊 **Overview:**\n"
    response += f"- **Remaining Items**: {total_remaining}\n"
    response += f"- **Remaining Story Points**: {int(remaining_points)}\n"
    response += f"- **Completion Progress**: {len(completed_df)}/{len(df)} items ({(len(completed_df)/len(df)*100):.1f}%)\n\n"
    
    # Breakdown by status
    status_breakdown = remaining_df['state'].value_counts()
    response += f"🔄 **By Status:**\n"
    for status, count in status_breakdown.items():
        response += f"- **{status}**: {count} items\n"
    
    # Breakdown by assignee
    assignee_breakdown = remaining_df.groupby('assignee').agg({
        'id': 'count',
        'story_points': 'sum'
    }).sort_values('story_points', ascending=False)
    
    response += f"\n👥 **By Assignee:**\n"
    for assignee, data in assignee_breakdown.head(5).iterrows():
        response += f"- **{assignee}**: {data['id']} items, {int(data['story_points'])} points\n"
    
    # Category breakdown
    category_breakdown = remaining_df.groupby('category').agg({
        'id': 'count',
        'story_points': 'sum'
    }).sort_values('story_points', ascending=False)
    
    response += f"\n🏷️ **By Category:**\n"
    for category, data in category_breakdown.head(5).iterrows():
        response += f"- **{category}**: {data['id']} items, {int(data['story_points'])} points\n"
    
    # Recommendations
    response += f"\n💡 **Recommendations:**\n"
    if total_remaining > len(completed_df):
        response += "- Sprint appears over-committed - consider scope reduction\n"
    response += "- Focus on high-priority items first\n"
    response += "- Address any blockers preventing progress\n"
    response += "- Consider pair programming for complex items"
    
    return response

def generate_generic_response(question, df, completed_df, current_team, sprint_period):
    """Generate generic response with data insights"""
    
    completion_rate = (len(completed_df) / len(df)) * 100 if len(df) > 0 else 0
    total_points = completed_df['story_points'].sum()
    
    response = f"🤖 **AI Assistant Response:**\n\n"
    response += f"I understand you're asking about: *\"{question}\"*\n\n"
    response += f"Here's what I can tell you about your current sprint:\n\n"
    
    response += f"📊 **Quick Stats for {current_team}:**\n"
    response += f"- **Sprint**: {sprint_period}\n"
    response += f"- **Completion Rate**: {completion_rate:.1f}%\n"
    response += f"- **Story Points Delivered**: {int(total_points)}\n"
    response += f"- **Total Work Items**: {len(df)}\n\n"
    
    response += f"💡 **Try asking more specific questions like:**\n"
    response += f"- \"What's our sprint completion rate?\"\n"
    response += f"- \"Who are the top performers?\"\n"
    response += f"- \"Show me cycle time analysis\"\n"
    response += f"- \"What are the potential blockers?\"\n"
    response += f"- \"Break down work by categories\"\n\n"
    
    response += f"I'm here to help you analyze your team's performance and sprint progress! 🚀"
    
    return response

if __name__ == "__main__":
    main()
