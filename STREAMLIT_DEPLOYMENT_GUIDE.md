# 🚀 Streamlit Cloud Deployment Guide - Azure DevOps Dashboard

## 📁 Required Files for Deployment

### **Essential Files (Must Have):**

1. **`streamlit_app.py`** - Main entry point
2. **`azure_devops_dashboard.py`** - Core application
3. **`config.py`** - Configuration settings
4. **`requirements.txt`** - Dependencies
5. **`.streamlit/config.toml`** - Streamlit configuration

### **Supporting Files (Recommended):**

6. **`email_notifier.py`** - Email notifications
7. **`azure_data_monitor.py`** - File monitoring
8. **`.gitignore`** - Version control exclusions

## 📋 Step-by-Step Deployment Instructions

### **Step 1: Prepare Your Repository**

1. **Create a new GitHub repository** or use existing one
2. **Upload these files** to your repository:

```
your-repo/
├── streamlit_app.py
├── azure_devops_dashboard.py
├── config.py
├── email_notifier.py
├── azure_data_monitor.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── .gitignore
```

3. **Commit and push** all files:
```bash
git add .
git commit -m "Add Azure DevOps Dashboard for Streamlit deployment"
git push origin main
```

### **Step 2: Deploy on Streamlit Cloud**

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App**
   - Click **"New app"** button
   - Select **"From existing repo"**

3. **Configure App Settings**
   - **Repository**: Select your GitHub repository
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose a custom URL (optional)

4. **Deploy**
   - Click **"Deploy!"**
   - Wait for deployment (usually 2-5 minutes)

### **Step 3: First Time Setup**

Once deployed, users need to:

1. **Enter PAT Token**
   - Go to the deployed app URL
   - In the sidebar, enter Azure DevOps Personal Access Token

2. **Select Configuration**
   - Choose Team (ADGE-Prep, ADGE-Deliver, etc.)
   - Select Sprint (2025_S14, 2025_S15, etc.)
   - Select Pod (if using reviewready-agentic-ai-workflow team)

3. **Fetch Data**
   - Click "🔄 Fetch Data" button
   - Wait for data to load from Azure DevOps

4. **Explore Dashboard**
   - Navigate through all 8 tabs
   - Use AI Assistant for insights

## 🔧 File Contents

### **1. streamlit_app.py** (Entry Point)
```python
"""
Azure DevOps Sprint Dashboard - Streamlit Cloud Entry Point
Main application file for Streamlit Cloud deployment
"""

# Import the main dashboard application
from azure_devops_dashboard import main

if __name__ == "__main__":
    main()
```

### **2. requirements.txt** (Dependencies)
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

### **3. .streamlit/config.toml** (Configuration)
```toml
[global]
developmentMode = false

[server]
runOnSave = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#2d3436"
font = "sans serif"

[client]
caching = true
displayEnabled = true
showErrorDetails = true
```

### **4. .gitignore** (Version Control)
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
Thumbs.db

# Streamlit
.streamlit/secrets.toml

# Data files (optional)
data/
*.json
*.csv
*.xlsx

# Temporary files
temp/
tmp/
*.tmp
*.bak
*.backup

# Azure DevOps specific
*.pat
*.token

# PowerPoint presentations
*.pptx
```

## 🔐 Security Configuration

### **Personal Access Token Setup**

Users need to create Azure DevOps PAT tokens:

1. **Go to Azure DevOps**
   - Visit: https://dev.azure.com/tr-tax/_usersSettings/tokens

2. **Create New Token**
   - Click "New Token"
   - Name: "Streamlit Dashboard Access"
   - Expiration: 90 days (or as needed)
   - Scopes: Select "Work Items (Read)"

3. **Copy Token**
   - Copy the generated token
   - Enter it in the Streamlit app sidebar

### **No Secrets Configuration Needed**
- All authentication is user-managed
- No server-side secrets required
- Tokens are stored in session state only

## 🚨 Troubleshooting

### **Common Deployment Issues**

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'azure_devops_dashboard'
   ```
   **Solution**: Ensure `streamlit_app.py` and `azure_devops_dashboard.py` are in the same directory

2. **Requirements Issues**
   ```
   ERROR: Could not find a version that satisfies the requirement
   ```
   **Solution**: Check `requirements.txt` format and versions

3. **Configuration Errors**
   ```
   Config file not found
   ```
   **Solution**: Ensure `.streamlit/config.toml` exists with proper structure

### **Runtime Issues**

1. **Authentication Errors**
   ```
   401 Unauthorized
   ```
   **Solution**: 
   - Verify PAT token is correct
   - Check token permissions include "Work Items (Read)"
   - Ensure token hasn't expired

2. **Data Loading Issues**
   ```
   No work items found
   ```
   **Solution**:
   - Verify team name is correct
   - Check sprint selection
   - Ensure work items exist in selected iteration

3. **Performance Issues**
   **Solution**:
   - Use specific team filters
   - Limit date ranges
   - Clear browser cache
   - Restart Streamlit app

## 📊 Testing Your Deployment

### **Basic Functionality Test**
1. ✅ App loads without errors
2. ✅ Sidebar shows configuration options
3. ✅ PAT token input works
4. ✅ Team/sprint dropdowns populate
5. ✅ "Fetch Data" button responds

### **Data Loading Test**
1. ✅ Work items load successfully
2. ✅ All 8 tabs are accessible
3. ✅ Charts render properly
4. ✅ Data displays correctly

### **AI Assistant Test**
1. ✅ Chat interface displays
2. ✅ Quick action buttons work
3. ✅ Text input accepts messages
4. ✅ AI responses generate
5. ✅ Chat history persists

### **Advanced Features Test**
1. ✅ Email notifications (optional)
2. ✅ Export functionality
3. ✅ Recent changes analysis
4. ✅ Cycle time calculations

## 🎯 Post-Deployment

### **Share Your App**
- Your app will be available at: `https://your-app-name.streamlit.app`
- Share this URL with your team
- Users can bookmark for easy access

### **Monitor Usage**
- Check Streamlit Cloud dashboard for:
  - App performance metrics
  - Error logs
  - Resource usage
  - User activity

### **Updates**
- Push changes to GitHub repository
- Streamlit Cloud auto-deploys updates
- Changes are live within minutes

## 📞 Support

### **Streamlit Cloud Support**
- Documentation: https://docs.streamlit.io
- Community: https://discuss.streamlit.io
- GitHub: https://github.com/streamlit/streamlit

### **Azure DevOps API**
- Documentation: https://docs.microsoft.com/en-us/rest/api/azure/devops/
- PAT Token Guide: https://docs.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate

---

**Prepared by**: Rachita Modi, Technology Manager (Tax Evolution)  
**Last Updated**: August 2025  
**Version**: 1.0
