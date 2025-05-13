#!/usr/bin/env python3
"""
Setup script for TOSCA reporting tools

This script installs all necessary dependencies for the TOSCA reporting tools
and sets up the required directories.
"""

import subprocess
import sys
import os
from pathlib import Path

def ensure_dependencies():
    """Ensure all required packages are installed."""
    required_packages = [
        "pyautogui",
        "markdown",
        "pillow",
    ]
    
    print("Checking and installing required packages...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"✓ {package} installed successfully")

def setup_directories():
    """Set up the necessary directories for reports."""
    # Create reports directory
    reports_dir = Path("./reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create screenshots directory
    screenshots_dir = reports_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    
    print(f"✓ Created reports directory: {reports_dir}")
    print(f"✓ Created screenshots directory: {screenshots_dir}")

def copy_reporting_scripts():
    """Copy reporting scripts to the reports directory if they exist elsewhere."""
    source_files = [
        "../screenshot_tool.py",
        "../capture_directory_screenshots.py",
    ]
    
    for src_file in source_files:
        src_path = Path(src_file)
        if src_path.exists():
            dest_path = Path("./") / src_path.name
            with open(src_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())
            print(f"✓ Copied {src_path} to {dest_path}")

def main():
    """Main function to set up the reporting environment."""
    print("TOSCA Reporting Setup")
    print("====================")
    
    # Ensure we're in the reports directory
    if Path.cwd().name != "reports":
        if (Path.cwd() / "reports").exists():
            os.chdir("reports")
            print("Changed directory to reports/")
    
    # Install dependencies
    ensure_dependencies()
    
    # Set up directories
    setup_directories()
    
    # Copy scripts if needed
    copy_reporting_scripts()
    
    print("\nSetup complete! You can now run the reporting tools:")
    print("1. Run 'python feature_reporter.py' to generate a comprehensive feature report")
    print("2. View 'new_features_summary.md' for a concise overview of new features")

if __name__ == "__main__":
    main() 