import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import base64
from datetime import datetime, timedelta
import os
from config import AZURE_DEVOPS_CONFIG, COMPLETED_STATES, WORK_ITEM_TYPES, SPRINT_CONFIG
from azure_data_monitor import AzureDataMonitor, start_monitoring, stop_monitoring
import threading

# Page configuration
st.set_page_config(
    page_title="Azure DevOps Sprint Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for beautiful, professional dashboard styling
st.markdown("""
<style>
    /* Global Styles */
    .main > div {
        padding-top: 1rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
                   [System.CreatedDate], [Microsoft.VSTS.Common.StateChangeDate],
                   [System.IterationPath], [System.AreaPath], [Microsoft.VSTS.Common.ActivatedDate],
                   [Microsoft.VSTS.Common.ResolvedDate], [Microsoft.VSTS.Common.ClosedDate],
                   [System.Tags]
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
            
            # Calculate cycle time
            cycle_time_days = None
            activated_date = fields.get('Microsoft.VSTS.Common.ActivatedDate', '')
            resolved_date = fields.get('Microsoft.VSTS.Common.ResolvedDate', '')
            closed_date = fields.get('Microsoft.VSTS.Common.ClosedDate', '')
            
            if activated_date and (resolved_date or closed_date):
                try:
                    activated_dt = datetime.fromisoformat(activated_date.replace('Z', '+00:00'))
                    completion_dt = None
                    if resolved_date:
                        completion_dt = datetime.fromisoformat(resolved_date.replace('Z', '+00:00'))
                    elif closed_date:
                        completion_dt = datetime.fromisoformat(closed_date.replace('Z', '+00:00'))
                    
                    if completion_dt:
                        cycle_time_days = (completion_dt - activated_dt).days
                except:
                    cycle_time_days = None
            
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
                'created_date': fields.get('System.CreatedDate', ''),
                'activated_date': activated_date,
                'resolved_date': resolved_date,
                'closed_date': closed_date,
                'cycle_time_days': cycle_time_days,
                'category': category,
                'tags': tags,
                'is_completed': fields.get('System.State', '') in COMPLETED_STATES
            })
        
        return pd.DataFrame(processed_items)
    
    def categorize_work_item(self, title, work_type, tags=""):
        """Categorize work item based on title, type, and tags"""
        title_lower = title.lower()
        tags_lower = tags.lower() if tags else ""
        
        if work_type == 'Bug':
            return 'Bug'
        elif work_type == 'Investigate':
            return 'Investigate'
        
        # Check tags first for UXE priority - if UXE tag exists, categorize as UX
        if 'uxe' in tags_lower:
            return 'UX'
        
        # UX keywords - check in title (highest priority after tags)
        ux_keywords = ['ux ', 'user experience', 'usability', 'user interface design', 
                       'interaction design', 'user research', 'wireframe', 'mockup', 'prototype']
        
        # Frontend keywords
        frontend_keywords = ['frontend', 'fe ', 'ui', 'button', 'screen', 'window', 'tab', 'grid', 
                           'upload', 'branding', 'text', 'alert', 'breadcrumb', 'scroll', 'menu', 
                           'welcome', 'settings', 'angular', 'saffron', 'component']
        
        # Backend keywords
        backend_keywords = ['backend', 'api', 'service', 'endpoint', 'lambda', 'aws', 'database', 
                          'postgres', 'server', 'deprecate', 'ultratax', 'taxassistant', 'workflow', 
                          'metric', 'email']
        
        # SQA keywords
        sqa_keywords = ['sqa', 'software quality', 'quality assurance', 'qa engineer', 'qa lead']
        
        # Check UX keywords in title (after tag check)
        for keyword in ux_keywords:
            if keyword in title_lower:
                return 'UX'
        
        # Check SQA keywords second
        for keyword in sqa_keywords:
            if keyword in title_lower:
                return 'SQA'
        
        # Then check other categories
        for keyword in frontend_keywords:
            if keyword in title_lower:
                return 'Frontend'
        
        for keyword in backend_keywords:
            if keyword in title_lower:
                return 'Backend'
        
        return 'Other'

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
    
    # Fetch data button - moved below both fields
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
                    st.success(f"Successfully fetched {len(dashboard.work_items)} work items for {selected_team}!")
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
        "👁️ Data Monitor",
        "🔄 Recent Changes"
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
        render_data_monitor_tab()
    
    with tab8:
        render_recent_changes_tab(df, pat_token)

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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Work Items",
            len(df),
            delta=f"{len(completed_df)} completed"
        )
    
    with col2:
        st.metric(
            "Completion Rate",
            f"{completion_rate:.1f}%",
            delta=f"{len(df) - len(completed_df)} remaining"
        )
    
    with col3:
        st.metric(
            "Story Points Delivered",
            int(total_points),
            delta=f"Avg: {total_points/len(completed_df):.1f}" if len(completed_df) > 0 else "0"
        )
    
    with col4:
        st.metric(
            "Avg Cycle Time",
            f"{avg_cycle_time:.1f} days",
            delta=f"{len(cycle_time_items)} items tracked"
        )
    
    # 3. Sprint Configuration - third
    st.subheader("⚙️ Sprint Configuration")
    col1, col2 = st.columns(2)
    
    # Get the current team and calculate area path dynamically
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    
    # Calculate area path based on selected team (same logic as in data fetching)
    if current_team.startswith("ADGE-"):
        team_suffix = current_team.split('-')[1]  # Get "Prep", "Deliver", "Gather"
        calculated_area_path = SPRINT_CONFIG["area_path"].replace("ADGE\\Prep", f"ADGE\\{team_suffix}")
    elif current_team == "reviewready-agentic-ai-workflow":
        calculated_area_path = "TaxProf\\us\\taxAuto\\agenticaiworkflow"
    else:
        calculated_area_path = current_team
    
    with col1:
        st.info(f"""
        **Organization:** {AZURE_DEVOPS_CONFIG['organization']}  
        **Project:** {AZURE_DEVOPS_CONFIG['project']}  
        **Team:** {current_team}
        """)
    
    with col2:
        st.info(f"""
        **Iteration:** {SPRINT_CONFIG['iteration_path']}  
        **Area Path:** {calculated_area_path}  
        **Work Item Types:** {', '.join(WORK_ITEM_TYPES)}
        """)
    
    # 4. Sprint Summary - fourth (matching Sprint_Summary_Markdown.md format exactly)
    
    # Get current team for dynamic summary
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    
    # Sprint Overview Section (exact format from markdown)
    st.markdown("## 📊 Sprint Overview")
    st.markdown(f"""
- **Sprint Period**: July 16-29, 2025
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
    
    cycle_time_df = completed_df[completed_df['cycle_time_days'].notna()].copy()
    
    if cycle_time_df.empty:
        st.warning("No cycle time data available for completed work items.")
        return
    
    # Cycle time statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Items with Data", len(cycle_time_df))
    
    with col2:
        avg_time = cycle_time_df['cycle_time_days'].mean()
        st.metric("Average", f"{avg_time:.1f} days")
    
    with col3:
        median_time = cycle_time_df['cycle_time_days'].median()
        st.metric("Median", f"{median_time:.1f} days")
    
    with col4:
        max_time = cycle_time_df['cycle_time_days'].max()
        st.metric("Maximum", f"{max_time} days")
    
    # Simplified Cycle Time Analysis
    st.subheader("📊 Cycle Time Performance")
    
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
        # Simple bar chart showing performance categories with pastel colors
        fig_performance = px.bar(
            x=performance_summary.index,
            y=performance_summary.values,
            title="Work Items by Cycle Time Performance",
            labels={'x': 'Performance Category', 'y': 'Number of Items'},
            color=performance_summary.index,
            color_discrete_map={
                'Fast (≤7 days)': PASTEL_COLORS['performance'][0],
                'Normal (8-14 days)': PASTEL_COLORS['performance'][1],
                'Slow (>14 days)': PASTEL_COLORS['performance'][2]
            }
        )
        fig_performance.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16
        )
        st.plotly_chart(fig_performance, use_container_width=True)
    
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
    
    # Long cycle items
    if len(cycle_time_df) > 1:
        std_dev = cycle_time_df['cycle_time_days'].std()
        threshold = avg_time + std_dev
        long_cycle_items = cycle_time_df[cycle_time_df['cycle_time_days'] > threshold]
        
        if not long_cycle_items.empty:
            st.subheader(f"Items Taking Longer Than Expected ({len(long_cycle_items)} items)")
            st.caption(f"Threshold: {threshold:.1f} days (Average + 1 Standard Deviation)")
            
            for _, item in long_cycle_items.iterrows():
                with st.expander(f"#{item['id']}: {item['title'][:60]}... ({item['cycle_time_days']} days)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {item['type']}")
                        st.write(f"**Assignee:** {item['assignee']}")
                        st.write(f"**Story Points:** {item['story_points']}")
                    with col2:
                        if item['activated_date']:
                            activated = item['activated_date'][:10]
                            completed = (item['resolved_date'] or item['closed_date'])[:10]
                            st.write(f"**Activated:** {activated}")
                            st.write(f"**Completed:** {completed}")
                            st.write(f"**Cycle Time:** {item['cycle_time_days']} days")

def render_categories_tab(completed_df):
    """Render the work categories tab"""
    st.header("Work Categories Analysis")
    
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
    
    # Display summary table
    st.subheader("Category Summary")
    st.dataframe(category_summary, use_container_width=True)
    
    # Category breakdown charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_items = px.pie(
            category_summary, 
            values='Items', 
            names='Category',
            title="Work Items by Category",
            color_discrete_sequence=PASTEL_COLORS['categories']
        )
        fig_items.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16
        )
        st.plotly_chart(fig_items, use_container_width=True)
    
    with col2:
        fig_points = px.pie(
            category_summary, 
            values='Story Points', 
            names='Category',
            title="Story Points by Category",
            color_discrete_sequence=PASTEL_COLORS['categories']
        )
        fig_points.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16
        )
        st.plotly_chart(fig_points, use_container_width=True)
    
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
    fig_points_dist = px.bar(
        x=story_points_dist.index,
        y=story_points_dist.values,
        title="Distribution of Story Points",
        labels={'x': 'Story Points', 'y': 'Number of Items'},
        color=story_points_dist.values,
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
    
    # Define sprint dates based on configuration
    # Sprint: 2025_S15_Jul16-Jul29 (July 16-29, 2025)
    sprint_start_date = datetime(2025, 7, 16).date()
    sprint_end_date = datetime(2025, 7, 29).date()
    
    # Get selected team from session state or default
    current_team = st.session_state.get('selected_team', 'ADGE-Prep')
    
    # Display sprint information
    st.info(f"""
    **Sprint Period**: July 16-29, 2025 (2025_S15_Jul16-Jul29)  
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
    
    # DEBUG: Show detailed data analysis
    st.subheader("🔍 Debug Information - Burndown Data Analysis")
    
    with st.expander("📊 Click to view detailed burndown data analysis"):
        st.markdown("### All Work Item States in Data:")
        all_states = df['state'].value_counts()
        st.write(all_states.to_dict())
        
        st.markdown("### Work Items with Completion Dates:")
        items_with_resolved = df[df['resolved_date'].notna()]
        items_with_closed = df[df['closed_date'].notna()]
        st.write(f"Items with resolved_date: {len(items_with_resolved)}")
        st.write(f"Items with closed_date: {len(items_with_closed)}")
        
        if len(items_with_resolved) > 0:
            st.markdown("**Sample resolved dates:**")
            st.write(items_with_resolved[['id', 'title', 'state', 'resolved_date']].head().to_dict('records'))
        
        if len(items_with_closed) > 0:
            st.markdown("**Sample closed dates:**")
            st.write(items_with_closed[['id', 'title', 'state', 'closed_date']].head().to_dict('records'))
        
        st.markdown("### Scope Calculation:")
        scope_items = df[df['state'].isin(REMAINING_STATES + COMPLETED_STATES)]
        st.write(f"Total items in scope (Remaining + Completed states): {len(scope_items)}")
        st.write(f"Total story points in scope: {scope_items['story_points'].sum()}")
        
        st.markdown("### Items by State (In Scope Only):")
        scope_states = scope_items['state'].value_counts()
        st.write(scope_states.to_dict())
        
        st.markdown("### Date Range Analysis:")
        st.write(f"Sprint start: {sprint_start_date}")
        st.write(f"Sprint end: {sprint_end_date}")
        
        # Show completion dates within sprint range
        completed_items = df[df['state'].isin(COMPLETED_STATES)]
        dates_in_range = []
        dates_outside_range = []
        
        for _, item in completed_items.iterrows():
            completion_date = None
            if item['resolved_date']:
                try:
                    completion_date = datetime.fromisoformat(item['resolved_date'].replace('Z', '+00:00')).date()
                except:
                    pass
            elif item['closed_date']:
                try:
                    completion_date = datetime.fromisoformat(item['closed_date'].replace('Z', '+00:00')).date()
                except:
                    pass
            
            if completion_date:
                if sprint_start_date <= completion_date <= sprint_end_date:
                    dates_in_range.append({
                        'id': item['id'],
                        'title': item['title'][:50],
                        'completion_date': completion_date,
                        'story_points': item['story_points']
                    })
                else:
                    dates_outside_range.append({
                        'id': item['id'],
                        'title': item['title'][:50],
                        'completion_date': completion_date,
                        'story_points': item['story_points']
                    })
        
        st.markdown(f"**Completed items within sprint range ({sprint_start_date} to {sprint_end_date}):**")
        st.write(f"Count: {len(dates_in_range)}")
        if dates_in_range:
            st.write(dates_in_range[:10])  # Show first 10
        
        st.markdown("**Completed items outside sprint range:**")
        st.write(f"Count: {len(dates_outside_range)}")
        if dates_outside_range:
            st.write(dates_outside_range[:5])  # Show first 5
    
    # Create sprint timeline based on sprint dates
    st.subheader("📉 Sprint Burndown Analysis")
    
    # Use sprint dates for analysis
    start_date = sprint_start_date
    end_date = sprint_end_date
    
    # Generate daily data points
    current_date = start_date
    burndown_data = []
    
    # Define remaining work states (Active, Ready, New)
    REMAINING_STATES = ['Active', 'Ready', 'New']
    
    # Calculate total scope based on remaining + completed states only
    scope_items = df[df['state'].isin(REMAINING_STATES + COMPLETED_STATES)]
    total_items = len(scope_items)
    total_story_points = scope_items['story_points'].sum()
    
    while current_date <= end_date:
        # Count completed items by this date (considering both Closed and Resolved states)
        completed_by_date_items = 0
        completed_by_date_points = 0
        
        for _, item in df.iterrows():
            # Only consider items that are in scope (remaining + completed states)
            if item['state'] not in (REMAINING_STATES + COMPLETED_STATES):
                continue
                
            # Check if item is completed
            if item['state'] in COMPLETED_STATES:
                completion_date = None
                # Priority: resolved_date first, then closed_date
                if item['resolved_date']:
                    try:
                        completion_date = datetime.fromisoformat(item['resolved_date'].replace('Z', '+00:00')).date()
                    except:
                        pass
                elif item['closed_date']:
                    try:
                        completion_date = datetime.fromisoformat(item['closed_date'].replace('Z', '+00:00')).date()
                    except:
                        pass
                
                # For sprint burndown, count all completed items as completed on the last day
                # This represents the current state of sprint work
                if completion_date and completion_date <= current_date:
                    completed_by_date_items += 1
                    completed_by_date_points += item['story_points']
                elif not completion_date and current_date == end_date:
                    # If no completion date but item is in completed state, count it on the last day
                    completed_by_date_items += 1
                    completed_by_date_points += item['story_points']
        
        # Calculate remaining items = total scope - completed by this date
        remaining_items = total_items - completed_by_date_items
        remaining_points = total_story_points - completed_by_date_points
        
        # Ensure remaining counts don't go negative
        remaining_items = max(0, remaining_items)
        remaining_points = max(0, remaining_points)
        
        burndown_data.append({
            'date': current_date,
            'remaining_items': remaining_items,
            'remaining_points': remaining_points,
            'completed_items': completed_by_date_items,
            'completed_points': completed_by_date_points
        })
        
        current_date += timedelta(days=1)
    
    burndown_df = pd.DataFrame(burndown_data)
    
    # Create burndown and burnup charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Burndown Chart - Story Count
        fig_burndown_items = go.Figure()
        
        # Actual burndown
        fig_burndown_items.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=burndown_df['remaining_items'],
            mode='lines+markers',
            name='Remaining Items',
            line=dict(color=PASTEL_COLORS['warning'][1], width=3),
            marker=dict(size=6)
        ))
        
        # Ideal burndown line
        sprint_days = len(burndown_df)
        ideal_burndown = [total_items - (total_items * i / (sprint_days - 1)) for i in range(sprint_days)]
        fig_burndown_items.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=ideal_burndown,
            mode='lines',
            name='Ideal Burndown',
            line=dict(color=PASTEL_COLORS['success'][0], width=2, dash='dash')
        ))
        
        fig_burndown_items.update_layout(
            title="Burndown Chart - Story Count",
            xaxis_title="Date",
            yaxis_title="Remaining Items",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_burndown_items, use_container_width=True)
    
    with col2:
        # Burndown Chart - Story Points
        fig_burndown_points = go.Figure()
        
        # Actual burndown
        fig_burndown_points.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=burndown_df['remaining_points'],
            mode='lines+markers',
            name='Remaining Points',
            line=dict(color=PASTEL_COLORS['warning'][2], width=3),
            marker=dict(size=6)
        ))
        
        # Ideal burndown line
        ideal_burndown_points = [total_story_points - (total_story_points * i / (sprint_days - 1)) for i in range(sprint_days)]
        fig_burndown_points.add_trace(go.Scatter(
            x=burndown_df['date'],
            y=ideal_burndown_points,
            mode='lines',
            name='Ideal Burndown',
            line=dict(color=PASTEL_COLORS['success'][1], width=2, dash='dash')
        ))
        
        fig_burndown_points.update_layout(
            title="Burndown Chart - Story Points",
            xaxis_title="Date",
            yaxis_title="Remaining Story Points",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            title_font_size=16,
            hovermode='x unified'
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
            # Format the dataframe for display
            display_df = filtered_df[display_columns].copy()
            
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
            
            st.dataframe(display_df, use_container_width=True)
            
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
                'ID': item['id'],
                'Title': item['title'][:50] + "..." if len(item['title']) > 50 else item['title'],
                'Type': item['type'],
                'State': item['state'],
                'Assignee': item['assignee'],
                'Last Changed': item['state_change_datetime'].strftime('%Y-%m-%d %H:%M') if pd.notna(item['state_change_datetime']) else 'N/A',
                'History': change_summary
            })
    
    summary_df = pd.DataFrame(summary_data)
    st.table(summary_df)
    
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
                - **Created**: {item['created_date'][:10] if item['created_date'] else 'N/A'}
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

def render_data_monitor_tab():
    """Render the data monitoring tab"""
    st.header("👁️ Data Monitor")
    st.markdown("Real-time monitoring of Azure DevOps data files and changes")
    
    # Initialize session state for monitoring
    if 'monitor_active' not in st.session_state:
        st.session_state.monitor_active = False
    if 'monitor_observer' not in st.session_state:
        st.session_state.monitor_observer = None
    if 'monitor_handler' not in st.session_state:
        st.session_state.monitor_handler = None
    
    # Monitor controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        data_directory = st.text_input(
            "Data Directory to Monitor:",
            value="./data",
            help="Directory path to monitor for Azure DevOps data files"
        )
    
    with col2:
        if st.button("🚀 Start Monitor", disabled=st.session_state.monitor_active):
            try:
                def data_change_callback(file_info):
                    """Callback for data changes"""
                    # Store the change in session state for display
                    if 'recent_changes' not in st.session_state:
                        st.session_state.recent_changes = []
                    
                    st.session_state.recent_changes.append(file_info)
                    # Keep only last 50 changes
                    if len(st.session_state.recent_changes) > 50:
                        st.session_state.recent_changes = st.session_state.recent_changes[-50:]
                
                observer, handler = start_monitoring(data_directory, data_change_callback)
                st.session_state.monitor_observer = observer
                st.session_state.monitor_handler = handler
                st.session_state.monitor_active = True
                st.success(f"✅ Monitor started for directory: {data_directory}")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to start monitor: {str(e)}")
    
    with col3:
        if st.button("🛑 Stop Monitor", disabled=not st.session_state.monitor_active):
            try:
                if st.session_state.monitor_observer:
                    stop_monitoring(st.session_state.monitor_observer)
                    st.session_state.monitor_observer = None
                    st.session_state.monitor_handler = None
                    st.session_state.monitor_active = False
                    st.success("✅ Monitor stopped")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to stop monitor: {str(e)}")
    
    # Monitor status
    if st.session_state.monitor_active:
        st.success(f"🟢 **Monitor Active** - Watching: {data_directory}")
    else:
        st.info("🔴 **Monitor Inactive** - Click 'Start Monitor' to begin watching for file changes")
    
    # Monitoring statistics
    st.subheader("📊 Monitoring Statistics")
    
    if st.session_state.monitor_handler:
        try:
            stats = st.session_state.monitor_handler.get_monitoring_stats()
            
            if 'error' not in stats:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Events", stats['total_events'])
                
                with col2:
                    st.metric("File Types", len(stats['file_types']))
                
                with col3:
                    st.metric("Data Sources", len(stats['data_sources']))
                
                with col4:
                    recent_count = len(stats['recent_events'])
                    st.metric("Recent Events", recent_count)
                
                # File types breakdown
                if stats['file_types']:
                    st.subheader("📁 File Types Monitored")
                    file_types_df = pd.DataFrame(list(stats['file_types'].items()), columns=['File Type', 'Count'])
                    
                    fig_file_types = px.pie(
                        file_types_df,
                        values='Count',
                        names='File Type',
                        title="File Types Distribution",
                        color_discrete_sequence=PASTEL_COLORS['categories']
                    )
                    fig_file_types.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        title_font_size=16
                    )
                    st.plotly_chart(fig_file_types, use_container_width=True)
                
                # Data sources breakdown
                if stats['data_sources'] and len([k for k in stats['data_sources'].keys() if k != 'unknown']) > 0:
                    st.subheader("🎯 Data Sources")
                    data_sources_df = pd.DataFrame(list(stats['data_sources'].items()), columns=['Data Source', 'Count'])
                    data_sources_df = data_sources_df[data_sources_df['Data Source'] != 'unknown']
                    
                    if not data_sources_df.empty:
                        fig_data_sources = px.bar(
                            data_sources_df,
                            x='Data Source',
                            y='Count',
                            title="Data Sources Detected",
                            color='Count',
                            color_continuous_scale=PASTEL_COLORS['primary']
                        )
                        fig_data_sources.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(size=12),
                            title_font_size=16,
                            showlegend=False
                        )
                        st.plotly_chart(fig_data_sources, use_container_width=True)
            else:
                st.error(f"Error getting monitoring stats: {stats['error']}")
                
        except Exception as e:
            st.error(f"Error displaying monitoring statistics: {str(e)}")
    else:
        st.info("Start the monitor to see statistics")
    
    # Recent changes
    st.subheader("🔄 Recent File Changes")
    
    if 'recent_changes' in st.session_state and st.session_state.recent_changes:
        # Display recent changes
        for i, change in enumerate(reversed(st.session_state.recent_changes[-10:])):  # Show last 10
            with st.expander(f"{change['event_type'].upper()}: {change['file_name']} - {change['timestamp'][:19]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**File:** {change['file_name']}")
                    st.write(f"**Type:** {change['file_extension']}")
                    st.write(f"**Size:** {change['file_size']} bytes")
                    st.write(f"**Event:** {change['event_type']}")
                
                with col2:
                    if 'content_type' in change:
                        st.write(f"**Content Type:** {change['content_type']}")
                    if 'record_count' in change:
                        st.write(f"**Records:** {change['record_count']}")
                    if 'data_source' in change:
                        st.write(f"**Data Source:** {change['data_source']}")
                    if 'work_items' in change:
                        st.write(f"**Work Items:** {change['work_items']}")
        
        # Clear changes button
        if st.button("🗑️ Clear Change History"):
            st.session_state.recent_changes = []
            st.rerun()
    else:
        st.info("No recent file changes detected. Start the monitor and add/modify files in the monitored directory to see changes here.")
    
    # Instructions
    st.subheader("📋 How to Use Data Monitor")
    st.markdown("""
    **Getting Started:**
    1. **Set Directory**: Specify the directory path to monitor (default: `./data`)
    2. **Start Monitor**: Click 'Start Monitor' to begin watching for file changes
    3. **Monitor Activity**: View real-time statistics and recent file changes
    4. **Stop Monitor**: Click 'Stop Monitor' when done
    
    **Monitored File Types:**
    - 📄 **JSON files** (.json) - Azure DevOps API responses
    - 📊 **CSV files** (.csv) - Exported work item data
    - 📈 **Excel files** (.xlsx, .xls) - Spreadsheet data
    - 📝 **Text files** (.txt) - Log files and reports
    
    **Features:**
    - 🔍 **Smart Detection**: Automatically identifies Azure DevOps data files
    - 📊 **Content Analysis**: Extracts metadata like record counts and data types
    - 🕒 **Real-time Updates**: Shows file changes as they happen
    - 📈 **Statistics**: Track file types, data sources, and activity patterns
    - 🔄 **Change History**: View recent file modifications with details
    
    **Use Cases:**
    - Monitor Azure DevOps data exports and imports
    - Track changes to work item data files
    - Detect when new sprint data becomes available
    - Monitor automated data processing workflows
    """)

if __name__ == "__main__":
    main()
