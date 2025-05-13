#!/usr/bin/env python3
"""
TOSCA Feature Report Launcher

This script launches the feature reporting tool from the root directory.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the feature reporter tool."""
    print("TOSCA Feature Report Launcher")
    print("=============================")
    
    # Check if reports directory exists
    reports_dir = Path("./reports")
    if not reports_dir.exists():
        print("Creating reports directory...")
        reports_dir.mkdir(exist_ok=True)
    
    # Check if feature_reporter.py exists in reports directory
    reporter_path = reports_dir / "feature_reporter.py"
    if not reporter_path.exists():
        print("Error: feature_reporter.py not found in reports directory.")
        print("Please ensure you have set up the reporting tools correctly.")
        return 1
    
    print("Launching feature reporter...")
    # Change to reports directory and run the feature reporter
    os.chdir(reports_dir)
    result = subprocess.run([sys.executable, "feature_reporter.py"])
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 