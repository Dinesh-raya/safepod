"""Wrapper script to run the Streamlit app with custom uuid module"""
import sys
import os

# Add our custom uuid module to the path before system packages
sys.path.insert(0, '/workspace')

# Now import and run the app
from app.main import main

if __name__ == "__main__":
    main()