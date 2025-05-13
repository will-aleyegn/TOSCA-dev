#!/usr/bin/env python3
"""
Test Feature Report Generator

Generates a feature report using existing screenshots without capturing new ones.
"""

import os
import sys
from pathlib import Path
from reports.feature_reporter import (
    generate_feature_descriptions,
    generate_markdown_report,
    generate_html_report
)

def main():
    """Generate feature report using existing screenshots."""
    print("TOSCA Feature Report Generator (Using Existing Screenshots)")
    print("=========================================================")
    
    # Check if screenshots directory exists
    screenshots_dir = Path("./reports/reports/screenshots")
    if not screenshots_dir.exists() or not screenshots_dir.is_dir():
        print(f"Error: Screenshots directory not found: {screenshots_dir}")
        return 1
    
    # Get existing screenshots
    feature_screenshots = {}
    
    # Map of features to look for in filenames
    features = [
        "main_window",
        "patient_form",
        "patient_selection",
        "treatment_session",
        "camera_display",
        "patient_directory"
    ]
    
    # Find the latest screenshot for each feature
    for feature in features:
        matching_files = list(screenshots_dir.glob(f"{feature}_*.png"))
        if matching_files:
            # Sort by modification time to get the latest
            latest_file = sorted(matching_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
            feature_screenshots[feature] = latest_file
            print(f"Found screenshot for {feature}: {latest_file.name}")
        else:
            print(f"Warning: No screenshot found for {feature}")
    
    if not feature_screenshots:
        print("Error: No screenshots found. Cannot generate report.")
        return 1
    
    # Generate feature descriptions
    feature_descriptions = generate_feature_descriptions()
    
    # Generate markdown report
    print("\nGenerating markdown report...")
    markdown_path = generate_markdown_report(feature_screenshots, feature_descriptions)
    
    # Generate HTML report
    print("Generating HTML report...")
    html_path = generate_html_report(markdown_path)
    
    print("\nReport generation complete!")
    print(f"HTML report: {html_path}")
    
    # Open the report
    open_report = input("\nOpen the HTML report now? (y/n): ")
    if open_report.lower() == 'y':
        if os.name == 'nt':  # Windows
            os.startfile(html_path)
        elif os.name == 'posix':  # macOS or Linux
            import subprocess
            subprocess.run(['xdg-open', html_path], check=False)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 