# app.py
import streamlit as st
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def main():
    """Main entry point for the application"""
    import pages.Home as Home
    Home.run()

if __name__ == "__main__":
    main()
