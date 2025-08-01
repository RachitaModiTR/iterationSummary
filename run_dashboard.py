#!/usr/bin/env python3
"""
Azure DevOps Sprint Dashboard Runner
Run this script to start the interactive Streamlit dashboard
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Azure DevOps Sprint Dashboard...")
    print("=" * 50)
    print("Dashboard Features:")
    print("• Interactive sprint overview with key metrics")
    print("• Cycle time analysis with drill-down capabilities")
    print("• Work categorization (Frontend, Backend, Testing, etc.)")
    print("• Visual charts and analytics")
    print("• Detailed work item filtering and search")
    print("• CSV export functionality")
    print("=" * 50)

    # Check if streamlit is installed
    try:
        import streamlit
        print("✓ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
    
    # Run the dashboard
    try:
        print("\n🌐 Starting dashboard server...")
        print("📱 The dashboard will open in your default web browser")
        print("🔗 URL: http://localhost:8501")
        print("\n💡 To stop the server, press Ctrl+C in this terminal")
        print("=" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "azure_devops_dashboard.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error running dashboard: {e}")
        print("Please ensure azure_devops_dashboard.py exists in the current directory")

if __name__ == "__main__":
    main()
