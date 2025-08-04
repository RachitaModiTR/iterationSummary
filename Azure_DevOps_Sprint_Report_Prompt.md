# Azure DevOps Sprint Report Generation - Complete Prompt

## Objective
Create a comprehensive Azure DevOps sprint report system that fetches work items, analyzes performance, and generates detailed reports with cycle time analysis and work categorization.

## Requirements

### 1. Data Fetching
- Connect to Azure DevOps using Personal Access Token
- Fetch work items from specific iteration path: `https://dev.azure.com/tr-tax/TaxProf/_boards/board/t/ADGE-Prep/Stories`
- Filter for work items with states: 'Done', 'Completed', 'Closed', 'Resolved'
- Include work item types: Bug, User Story, Investigate
- Extract fields: ID, Title, Type, Assignee, Story Points, State, Created Date, Activated Date, Resolved Date, Closed Date

### 2. Analysis Requirements
- **Total Metrics**: Count completed work items and sum story points
- **Cycle Time Analysis**: Calculate time from activation to completion
  - Identify work items that took longer than average + 1 standard deviation
  - Provide average, median, and maximum cycle times
  - Show activation and completion dates for long-cycle items
- **Work Categorization**: Classify work items by:
  - **Frontend**: UI, buttons, screens, windows, tabs, grids, upload, branding, text, alerts, breadcrumbs, scroll, menus, welcome, settings, Angular, Saffron, components
  - **Backend**: APIs, services, endpoints, Lambda, AWS, database, PostgreSQL, server, deprecate, UltraTax, TaxAssistant, workflow, metrics, email
  - **Bug**: Work items with type 'Bug'
  - **Investigate**: Work items with type 'Investigate'
  - **Testing/QA**: SQA, test, testing, QA, automate, validation, regression, deployment, health check, scripts
  - **Other**: Items not matching above categories
- **Important Items**: Identify items for review meetings based on:
  - High story points (≥5)
  - Critical work item types (User Story, Bug, Investigate)
  - Keywords: critical, important, major, feature, integration, security, performance

### 3. Report Generation
Generate the following outputs:

#### A. PowerPoint Presentation (.pptx)
- **Slide 1**: Sprint Summary (dates, team, total work items, total story points)
- **Slide 2**: Completed Work Items (table format with ID, Title, Type, Assignee, Points)
- **Slide 3**: Burndown Chart (visual representation of remaining work over time)
- **Slide 4**: Important Work Items for Review (key items with reasons for importance)
- **Slide 5**: Key Highlights & Blockers (summary by category, space for manual input)

#### B. Burndown Chart (.png)
- Visual chart showing actual vs. ideal burndown
- X-axis: Sprint dates, Y-axis: Remaining story points
- Professional styling with grid and legends

#### C. Console Output
Provide detailed analysis including:
- Sprint summary with totals
- Individual work item details with cycle times
- Cycle time statistics and long-cycle item identification
- Work breakdown by category with percentages
- Category summary table
- Important items list with reasoning

#### D. Markdown Summary (Single PowerPoint Slide Format)
Create a markdown file with:
- Sprint overview with key metrics
- Cycle time analysis summary
- Work breakdown table (Category | Items | Percentage | Story Points | Points %)
- Key highlights and problem areas
- Success metrics with visual indicators

### 4. Technical Implementation
- Use Python with libraries: requests, pandas, matplotlib, python-pptx
- Handle authentication via Personal Access Token
- Implement error handling for API calls
- Create safe filenames by replacing problematic characters
- Generate professional charts and presentations
- Support both environment variable and prompt-based token input

### 5. Configuration
- Organization: tr-tax
- Project: TaxProf
- Team: ADGE-Prep
- Iteration Path: TaxProf\2025\Q3\2025_S15_Jul16-Jul29
- Area Path: TaxProf\us\taxAuto\ADGE\Prep
- Sprint Dates: July 16-29, 2025

### 6. Output Structure
The system should generate:
1. **Sprint_Report_[IterationName].pptx** - Complete PowerPoint presentation
2. **burndown_chart_[IterationName].png** - Burndown visualization
3. **Sprint_Summary_Markdown.md** - Markdown summary for single slide
4. Console output with comprehensive analysis

### 7. Key Features
- **Dependency Management**: Handle numpy/pandas compatibility issues
- **Cycle Time Focus**: Identify bottlenecks and delays in work completion
- **Work Categorization**: Provide insights into team focus areas (Frontend vs Backend vs QA)
- **Professional Output**: Generate presentation-ready materials
- **Comprehensive Analysis**: Include both quantitative metrics and qualitative insights

### 8. Sprint Hero Analysis
- **Performance Scoring**: Calculate Sprint Hero based on multiple factors:
  - **Story Points Delivered** (40% weight): Total story points completed
  - **Efficiency** (30% weight): Story points per day (points/cycle time)
  - **Complexity Score** (20% weight): Combination of total points and average complexity
  - **Volume** (10% weight): Number of work items completed
- **Hero Metrics**: Display hero's contribution percentage, cycle time, and category focus
- **Recognition**: Highlight top performer with detailed performance breakdown

### 9. Simplified Cycle Time Visualization
- **Performance Categories**: 
  - Fast (≤7 days) - Green indicator
  - Normal (8-14 days) - Yellow indicator  
  - Slow (>14 days) - Red indicator
- **Performance Score**: Calculate team performance score (1-3 scale)
- **Visual Simplification**: Replace complex histograms with clear bar charts
- **Actionable Insights**: Focus on performance improvement recommendations

### 10. Enhanced Dashboard Layout
- **Overview Tab Structure** (in order):
  1. Sprint Success Metrics (color-coded performance indicators) - **MOVED TO TOP**
  2. Key Metrics (completion rate, story points, cycle time)
  3. Sprint Configuration (organization, project, team details)
  4. Sprint Overview (period, team, completion summary)
  5. Key Highlights (performance insights and recommendations)
  6. Sprint Hero (top performer recognition and analysis)

- **New Burndown/Burnup Tab**:
  - **Sprint Date Integration**: Uses actual sprint dates (July 16-29, 2025) for accurate timeline
  - **Day-wise Data Visualization**: Shows daily progress throughout the sprint period
  - **Smart State Recognition**: Only considers "Active", "Ready", and "New" states as remaining work
  - **Completed States Recognition**: Properly considers both "Closed" and "Resolved" states as completed
  - **Accurate Scope Tracking**: Burndown scope limited to Active/Ready/New → Closed/Resolved transitions
  - **Burndown Charts**: Both story count and story points with ideal vs actual lines
  - **Burnup Charts**: Progress visualization with scope lines and cumulative tracking
  - **Sprint Information Display**: Clear sprint period, duration, and team information
  - **Sprint Progress Summary**: Completion rates, duration, and velocity metrics
  - **Trend Analysis**: Velocity trends, acceleration detection, and completion projections
  - **Pastel Color Scheme**: Professional visualization with clean backgrounds
  - **Daily Timeline**: Complete day-by-day breakdown from sprint start to end
  - **State-Based Completion Logic**: Uses COMPLETED_STATES configuration for accurate tracking
  - **Scope Information Display**: Shows breakdown of remaining vs completed states for transparency

### 11. Enhanced Visual Design & Formatting
- **Custom CSS Styling**: Professional gradient backgrounds and card layouts
- **Pastel Color Palettes**: Carefully selected color schemes for all charts:
  - **Primary Colors**: Soft pastels for general charts (#FFB3BA, #BAFFC9, #BAE1FF, etc.)
  - **Performance Colors**: Traffic light pastels (Light green, khaki, light pink)
  - **Category Colors**: Subtle pastels for work categorization
  - **Success/Warning Colors**: Appropriate color coding for status indicators
- **Improved Readability**: Enhanced spacing, typography, and visual hierarchy
- **Card-Based Layout**: Gradient cards for metrics, hero recognition, and key sections
- **Transparent Backgrounds**: Clean chart backgrounds for professional appearance
- **Consistent Styling**: Unified design language across all dashboard components

### 12. Dashboard Branding & Attribution
- **Sidebar Attribution**: Display "Prepared by" information at the bottom of the left sidebar:
  - **Prepared by:** Rachita Modi
  - **Title:** Technology Manager (Tax Evolution)
- **Bottom Corner Placement**: Attribution positioned at the bottom corner of the sidebar for professional appearance
- **Professional Presentation**: Ensure attribution is clearly visible but not intrusive
- **Consistent Branding**: Maintain professional appearance throughout the dashboard
- **Always Visible**: Attribution appears both when data is loaded and when waiting for data input

### 13. Dynamic Team Selection
- **Team Dropdown**: Sidebar dropdown for selecting different ADGE teams:
  - **Available Teams**: ADGE-Prep (default), ADGE-Deliver, ADGE-Gather
  - **Dynamic Path Construction**: Automatically updates iteration and area paths based on selected team
  - **URL Path Mapping**: Changes from `ADGE-Prep` to selected team value in Azure DevOps queries
- **Team-Specific Data Fetching**: 
  - **Area Path Updates**: Dynamically constructs area path as `TaxProf\us\taxAuto\ADGE\{selected_team_suffix}`
  - **Session State Management**: Stores selected team for consistent display across tabs
  - **Team Display**: Shows current team in sprint information and burndown charts
- **Multi-Team Support**: Enables dashboard to work with different ADGE teams without code changes
- **Default Behavior**: ADGE-Prep selected by default for backward compatibility

### 13. Success Criteria
- Successfully connect to Azure DevOps and fetch real data
- Generate accurate cycle time calculations with simplified visualization
- Properly categorize work items by type
- Identify and celebrate Sprint Hero based on comprehensive performance analysis
- Create professional PowerPoint presentation
- Provide actionable insights for sprint retrospectives
- Output markdown format suitable for single PowerPoint slide
- Handle all edge cases (missing data, authentication issues, file naming)
- Deliver intuitive, easy-to-understand performance metrics
- Present data with professional visual design using pastel colors and clean formatting
- Ensure excellent readability and user experience across all dashboard components
- Display proper attribution and branding information

This prompt encompasses the complete requirements for generating a comprehensive Azure DevOps sprint report with cycle time analysis, work categorization, Sprint Hero recognition, enhanced visual design with pastel colors, professional branding, and multiple output formats including beautifully formatted interactive dashboards, PowerPoint presentations, and markdown summaries.
