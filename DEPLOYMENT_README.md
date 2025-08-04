# 🚀 Azure DevOps Sprint Dashboard - Streamlit Cloud Deployment Guide

A comprehensive, interactive dashboard for analyzing Azure DevOps sprint data with AI-powered insights and real-time monitoring capabilities.

## 🌟 Features

### 📊 **Sprint Analytics**
- **Overview Tab**: Sprint summary, key metrics, and sprint hero analysis
- **Burndown/Burnup Charts**: Visual sprint progress tracking
- **Cycle Time Analysis**: Performance categorization and improvement insights
- **Work Categories**: Distribution analysis across Frontend/Backend/UX/Testing
- **Visual Charts**: Interactive charts and graphs for data visualization
- **Detailed View**: Comprehensive work item analysis with filtering

### 🤖 **AI Assistant**
- **Modern Chat Interface**: Professional chat UI matching modern design standards
- **Smart Question Processing**: Intelligent analysis of sprint data
- **Quick Action Buttons**: One-click access to common insights
- **Context-Aware Responses**: Uses current team and sprint data
- **Performance Analysis**: Top performers, blockers, and recommendations

### 🔄 **Real-Time Monitoring**
- **Data Change Detection**: Monitor Azure DevOps data files
- **Email Notifications**: Automated alerts for sprint changes
- **Recent Changes Analysis**: Track work item modifications
- **File System Monitoring**: Watch for data updates

## 🚀 **Deployment on Streamlit Cloud**

### **Prerequisites**
1. GitHub repository with the application code
2. Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
3. Azure DevOps Personal Access Token (PAT)

### **Step-by-Step Deployment**

#### 1. **Prepare Your Repository**
```bash
# Clone or create your repository
git clone <your-repo-url>
cd azure-devops-dashboard

# Ensure all required files are present:
# - streamlit_app.py (main entry point)
# - azure_devops_dashboard.py (main application)
# - config.py (configuration)
# - requirements.txt (dependencies)
# - .streamlit/config.toml (Streamlit configuration)

# Commit all files
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### 2. **Deploy on Streamlit Cloud**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository
5. Set **Main file path**: `streamlit_app.py`
6. Click **"Deploy!"**

#### 3. **Configure Application Settings**
In your Streamlit Cloud app dashboard:

1. **App Settings** → **Secrets**
2. Add the following secrets (optional, for enhanced security):
```toml
# Azure DevOps Configuration (Optional - can be entered in UI)
AZURE_DEVOPS_ORG = "your-organization"
AZURE_DEVOPS_PROJECT = "your-project"

# Email Configuration (Optional - for notifications)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
```

#### 4. **First Time Setup**
Once deployed, users will need to:
1. Enter their Azure DevOps Personal Access Token
2. Select their team and sprint
3. Click "Fetch Data" to load work items

## 🔧 **Configuration Files**

### **streamlit_app.py** (Entry Point)
```python
from azure_devops_dashboard import main

if __name__ == "__main__":
    main()
```

### **requirements.txt** (Dependencies)
```
streamlit==1.28.1
pandas==2.0.3
plotly==5.17.0
requests==2.31.0
python-pptx==0.6.21
matplotlib==3.7.2
urllib3==1.26.18
watchdog==3.0.0
```

### **.streamlit/config.toml** (Streamlit Configuration)
```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#2d3436"
font = "sans serif"
```

## 🔐 **Security Considerations**

### **Personal Access Token (PAT)**
- Users enter their own PAT tokens in the sidebar
- Tokens are stored in Streamlit session state (not persistent)
- Tokens are not logged or stored permanently
- Each user manages their own authentication

### **Data Privacy**
- No work item data is stored permanently
- All data processing happens in memory
- Session data is cleared when the browser session ends
- No external data sharing or storage

## 🛠 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```
ModuleNotFoundError: No module named 'azure_devops_dashboard'
```
**Solution**: Ensure `streamlit_app.py` is in the same directory as `azure_devops_dashboard.py`

#### **2. Authentication Errors**
```
Error fetching data: 401 Unauthorized
```
**Solution**: 
- Verify PAT token has correct permissions
- Check organization and project names
- Ensure PAT token hasn't expired

#### **3. Data Loading Issues**
```
No work items found
```
**Solution**:
- Verify team name and sprint selection
- Check iteration path configuration
- Ensure work items exist in the selected sprint

#### **4. Performance Issues**
**Solution**:
- Use smaller date ranges
- Filter by specific teams
- Clear browser cache
- Restart the Streamlit app

### **Debug Mode**
To enable debug information:
1. Check the "Debug Information" expander in the Burndown tab
2. Review console logs in browser developer tools
3. Check Streamlit Cloud logs in the app dashboard

## 📊 **Usage Guide**

### **Getting Started**
1. **Enter PAT Token**: In the sidebar, enter your Azure DevOps Personal Access Token
2. **Select Sprint**: Choose the sprint you want to analyze
3. **Select Team**: Pick your team from the dropdown
4. **Fetch Data**: Click "Fetch Data" to load work items
5. **Explore Tabs**: Navigate through different analysis tabs

### **Key Features**

#### **Overview Tab**
- Sprint success metrics
- Key performance indicators
- Sprint hero analysis
- Work breakdown by category

#### **AI Assistant Tab**
- Ask questions about your sprint
- Get intelligent insights
- Use quick action buttons
- Chat with the AI about team performance

#### **Burndown/Burnup Tab**
- Visual sprint progress
- Ideal vs actual burndown
- Completion rate tracking
- Velocity analysis

#### **Cycle Time Tab**
- Performance categorization
- Improvement recommendations
- Items taking longer than expected
- Category-wise cycle time analysis

## 🔄 **Updates and Maintenance**

### **Updating the Application**
1. Make changes to your code
2. Commit and push to GitHub
3. Streamlit Cloud will automatically redeploy
4. Changes will be live within minutes

### **Monitoring**
- Check Streamlit Cloud dashboard for app health
- Monitor resource usage and performance
- Review error logs if issues occur

## 📞 **Support**

### **Getting Help**
- Check the troubleshooting section above
- Review Streamlit Cloud documentation
- Check Azure DevOps API documentation
- Contact your system administrator for PAT token issues

### **Feature Requests**
- Submit issues on the GitHub repository
- Provide detailed descriptions of requested features
- Include sample data or use cases when possible

## 🎯 **Best Practices**

### **For Users**
- Keep PAT tokens secure and don't share them
- Regularly refresh data for up-to-date insights
- Use specific team and sprint filters for better performance
- Explore all tabs to get comprehensive insights

### **For Administrators**
- Monitor app usage and performance
- Keep dependencies updated
- Review security settings regularly
- Provide user training on dashboard features

---

**Prepared by:** Rachita Modi, Technology Manager (Tax Evolution)  
**Last Updated:** August 2025  
**Version:** 2.0
