#!/bin/bash

echo "Azure DevOps Sprint Report Generator - Setup Script"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip first."
    exit 1
fi

echo "pip3 found: $(pip3 --version)"

# Install required packages
echo ""
echo "Installing required Python packages..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "To run the script:"
    echo "  python3 azure_devops_sprint_report.py"
    echo ""
    echo "Make sure you have your Azure DevOps Personal Access Token ready."
else
    echo ""
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
