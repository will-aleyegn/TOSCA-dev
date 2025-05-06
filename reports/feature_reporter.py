#!/usr/bin/env python3
"""
TOSCA Feature Reporter

This script generates a comprehensive feature report with screenshots for the TOSCA application.
It captures screenshots of key features and creates a detailed markdown report highlighting
recent improvements to camera integration, patient data management, and UI.
"""

import os
import time
import datetime
import subprocess
import shutil
from pathlib import Path
import argparse
import sys

try:
    import pyautogui
    import markdown
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Required packages not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyautogui", "markdown", "pillow"])
    import pyautogui
    import markdown
    from PIL import Image, ImageDraw, ImageFont

# Configuration
REPORT_TITLE = "TOSCA Laser Control System - Technical Documentation"
HIGHLIGHT_COLOR = "#e6f2ff"  # Light blue for highlighting new features

def create_report_dir():
    """Create directories for reports and screenshots."""
    report_dir = Path("./reports")
    screenshots_dir = report_dir / "screenshots"
    report_dir.mkdir(exist_ok=True)
    screenshots_dir.mkdir(exist_ok=True)
    return report_dir, screenshots_dir

def take_screenshot(name, screenshots_dir, delay=5, region=None, highlight_area=None):
    """
    Take a screenshot and save it to the screenshots directory.
    
    Args:
        name (str): Name of the screenshot (without extension)
        screenshots_dir (Path): Directory to save screenshots
        delay (int): Delay in seconds before taking the screenshot
        region (tuple): Region to capture (left, top, width, height) or None for full screen
        highlight_area (tuple): Area to highlight (left, top, width, height) or None
    
    Returns:
        Path: Path to the saved screenshot
    """
    # Print a countdown to give user time to move the terminal
    print(f"\n⚠️ PREPARING TO CAPTURE {name.upper()} ⚠️")
    print("Please arrange the application window and move this terminal out of the way.")
    for i in range(delay, 0, -1):
        print(f"Taking screenshot in {i} seconds...", end="\r")
        time.sleep(1)
    print("📸 CAPTURING NOW! 📸                    ")
    
    # Generate a filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = screenshots_dir / filename
    
    # Take the screenshot
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()
    
    # Add highlight if specified
    if highlight_area:
        img = screenshot
        draw = ImageDraw.Draw(img)
        left, top, width, height = highlight_area
        draw.rectangle((left, top, left+width, top+height), outline="red", width=3)
        
    # Save the screenshot
    screenshot.save(filepath)
    print(f"✅ Screenshot saved to: {filepath}")
    
    return filepath

def capture_feature_screens(interactive=True):
    """
    Capture screenshots of all main features in the TOSCA application.
    
    Args:
        interactive (bool): If True, prompts user to navigate to each screen
                           If False, assumes screens are already set up
    
    Returns:
        dict: Mapping of feature names to screenshot file paths
    """
    _, screenshots_dir = create_report_dir()
    
    features = {
        "main_window": "Main application window with tabs and emergency stop button",
        "patient_form": "Patient information form with personal/medical data fields",
        "patient_selection": "Patient selection dialog with search functionality",
        "treatment_session": "Treatment session management with image integration",
        "camera_display": "Camera control with patient-linked image capture",
        "patient_directory": "Patient-specific directory structure"
    }
    
    screenshots = {}
    
    for feature_name, description in features.items():
        if interactive:
            input(f"\n📋 Navigate to the {feature_name.replace('_', ' ')} screen, then press Enter when ready...\n")
        
        # Special case for patient directory
        if feature_name == "patient_directory":
            if os.name == 'nt':  # Windows
                patient_dir = Path("./data/patients").absolute()
                subprocess.Popen(f'explorer "{patient_dir}"')
                print(f"Opening file explorer to: {patient_dir}")
                time.sleep(2)  # Wait for explorer to open
        
        screenshot_path = take_screenshot(feature_name, screenshots_dir)
        screenshots[feature_name] = screenshot_path
        print(f"Captured {feature_name}: {description}")
        # Give user time to prepare for next screenshot
        if interactive and feature_name != list(features.keys())[-1]:  # Not the last item
            print("\nPreparing for next screenshot...")
            time.sleep(2)
        
    return screenshots

def generate_feature_descriptions():
    """
    Generate detailed descriptions of key features with technical details.
    
    Returns:
        dict: Mapping of feature names to description dictionaries
    """
    return {
        "main_window": {
            "title": "Main Application Interface",
            "description": "Centralized control interface with organized access to all TOSCA subsystems.",
            "highlights": [
                "Tabbed interface architecture for logical system organization",
                "Status bar with real-time patient and system information",
                "Emergency controls with hardware safety interlocks"
            ]
        },
        "patient_form": {
            "title": "Patient Data Management",
            "description": "Comprehensive patient information system with structured data entry and retrieval.",
            "highlights": [
                "Standardized fields for clinical documentation",
                "Automatic data validation and error prevention",
                "Integrated session and image metadata linking"
            ]
        },
        "patient_selection": {
            "title": "Patient Record Access",
            "description": "Efficient patient lookup system with search and filtering capabilities.",
            "highlights": [
                "Multi-parameter search functionality (ID, name, date)",
                "Direct navigation to patient history and treatments",
                "Integration with the imaging subsystem"
            ]
        },
        "treatment_session": {
            "title": "Treatment Session Documentation",
            "description": "Comprehensive treatment documentation with standardized parameters and imaging integration.",
            "highlights": [
                "Structured parameter recording for treatment reproducibility",
                "Chronological treatment history with comparative analysis",
                "Multi-modal imaging attachment capability"
            ]
        },
        "camera_display": {
            "title": "Imaging Subsystem",
            "description": "High-resolution imaging system with real-time capture and processing capabilities.",
            "highlights": [
                "Automated image storage with patient record association",
                "Consistent naming conventions for chronological tracking",
                "Configurable camera parameters with preset capabilities",
                "Direct session integration with metadata preservation"
            ]
        },
        "patient_directory": {
            "title": "Data Organization Structure",
            "description": "Hierarchical data management system ensuring consistent information organization and retrieval.",
            "highlights": [
                "Patient-centric directory structure",
                "Session-based image organization",
                "Standardized file naming with embedded metadata",
                "Consistent access patterns for programmatic data retrieval"
            ]
        }
    }

def generate_markdown_report(feature_screenshots, feature_descriptions):
    """
    Generate a markdown report with feature descriptions and screenshots.
    
    Args:
        feature_screenshots (dict): Mapping of feature names to screenshot file paths
        feature_descriptions (dict): Mapping of feature names to description dictionaries
    
    Returns:
        str: Path to the generated markdown report
    """
    report_dir, _ = create_report_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"TOSCA_Technical_Report_{timestamp}.md"
    
    # Create images directory for the report
    report_images_dir = report_dir / "images"
    report_images_dir.mkdir(exist_ok=True)
    
    # Copy all screenshots to the report images directory
    report_screenshot_paths = {}
    for feature_name, screenshot_path in feature_screenshots.items():
        src_path = Path(screenshot_path)
        if src_path.exists():
            dest_filename = f"{feature_name}_{src_path.name}"
            dest_path = report_images_dir / dest_filename
            
            # Copy the image
            try:
                shutil.copy2(src_path, dest_path)
                print(f"Copied screenshot from {src_path} to {dest_path}")
                # Store the relative path for use in markdown
                report_screenshot_paths[feature_name] = f"images/{dest_filename}"
            except Exception as e:
                print(f"Failed to copy screenshot {src_path}: {str(e)}")
                report_screenshot_paths[feature_name] = str(screenshot_path)
        else:
            print(f"Screenshot not found: {src_path}")
            report_screenshot_paths[feature_name] = str(screenshot_path)
    
    with open(report_path, 'w') as f:
        # Write header
        f.write(f"# TOSCA Laser Control System - Technical Documentation\n\n")
        f.write(f"*Documentation generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # Write executive summary
        f.write("## System Overview\n\n")
        f.write("The TOSCA Laser Control System is an integrated platform designed for medical laser treatments with the following subsystems:\n\n")
        f.write("1. **Centralized Control Interface** - Unified access to all system components\n")
        f.write("2. **Patient Information Management** - Structured clinical data organization\n")
        f.write("3. **Treatment Documentation** - Standardized parameter recording and session tracking\n")
        f.write("4. **Imaging Capabilities** - High-resolution image capture with metadata integration\n\n")
        
        # System Architecture section
        f.write("## System Architecture\n\n")
        f.write("TOSCA employs a modular architecture with distinct functional components that interact through standardized data pathways. The system organizes data in a patient-centric hierarchy, ensuring consistent data access patterns across all modules.\n\n")
        
        # Write detailed technical descriptions with screenshots
        f.write("## System Components\n\n")
        for feature_name, details in feature_descriptions.items():
            f.write(f"### {details['title']}\n\n")
            f.write(f"{details['description']}\n\n")
            
            # Add technical specifications
            if details.get("highlights"):
                f.write("**Technical specifications:**\n\n")
                for highlight in details['highlights']:
                    f.write(f"- {highlight}\n")
                f.write("\n")
            
            # Add screenshot if available
            if feature_name in report_screenshot_paths:
                screenshot_path = report_screenshot_paths[feature_name]
                f.write(f"![{details['title']}]({screenshot_path})\n\n")
    
    print(f"Generated technical report: {report_path}")
    return report_path

def generate_html_report(markdown_path):
    """
    Convert markdown report to HTML.
    
    Args:
        markdown_path (str): Path to markdown file
        
    Returns:
        str: Path to HTML report
    """
    html_path = markdown_path.with_suffix('.html')
    
    with open(markdown_path, 'r') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content)
    
    # Add CSS for styling
    css = """
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            line-height: 1.6; 
            max-width: 1100px; 
            margin: 0 auto; 
            padding: 20px;
            color: #333;
        }
        h1 { 
            color: #2c3e50; 
            border-bottom: 2px solid #2c3e50; 
            padding-bottom: 10px; 
            font-weight: 600;
        }
        h2 { 
            color: #2c3e50; 
            border-bottom: 1px solid #cccccc; 
            padding-bottom: 5px; 
            margin-top: 30px;
            font-weight: 500;
        }
        h3 { 
            color: #34495e; 
            margin-top: 25px;
            font-weight: 500;
        }
        img { 
            max-width: 100%; 
            border: 1px solid #ddd; 
            box-shadow: 0 0 10px rgba(0,0,0,0.1); 
            margin: 20px 0;
            display: block;
        }
        .image-gallery { display: flex; flex-wrap: wrap; justify-content: space-around; }
        .image-container { margin: 15px; text-align: center; max-width: 300px; }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: 600;
        }
        code {
            background-color: #f9f9f9;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', monospace;
        }
        ul {
            padding-left: 25px;
        }
        li {
            margin-bottom: 8px;
        }
        strong {
            color: #2c3e50;
        }
    </style>
    """
    
    # Add HTML head and CSS
    html_document = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TOSCA Laser Control System - Technical Documentation</title>
        {css}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    with open(html_path, 'w') as f:
        f.write(html_document)
    
    print(f"Generated HTML technical documentation: {html_path}")
    return html_path

def copy_files_to_reports():
    """Copy screenshot scripts to reports folder for reference and create necessary directories."""
    source_files = [
        "screenshot_tool.py",
        "capture_directory_screenshots.py",
        "docs/features_screenshots.md"
    ]
    
    report_dir, screenshots_dir = create_report_dir()
    
    # Create images directory for reports
    images_dir = report_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    for src_file in source_files:
        src_path = Path(src_file)
        if src_path.exists():
            dest_path = report_dir / src_path.name
            shutil.copy2(src_path, dest_path)
            print(f"Copied {src_path} to {dest_path}")
    
    print(f"Created directory structure for reports: {report_dir}")
    print(f"Images will be saved to: {images_dir}")
    print(f"Screenshots will be saved to: {screenshots_dir}")

def main():
    """Main function to generate the feature report."""
    parser = argparse.ArgumentParser(description="Generate feature report for TOSCA application")
    parser.add_argument("--non-interactive", action="store_true", help="Run without interactive prompts")
    
    args = parser.parse_args()
    
    try:
        print("TOSCA Feature Reporter")
        print("=====================")
        
        # Create report directories
        report_dir, screenshots_dir = create_report_dir()
        
        # Copy reference files to reports folder
        copy_files_to_reports()
        
        # Capture screenshots
        print("\nCapturing feature screenshots...")
        feature_screenshots = capture_feature_screens(interactive=not args.non_interactive)
        
        # Generate feature descriptions
        feature_descriptions = generate_feature_descriptions()
        
        # Generate markdown report
        print("\nGenerating markdown report...")
        markdown_path = generate_markdown_report(feature_screenshots, feature_descriptions)
        
        # Generate HTML report
        print("\nGenerating HTML report...")
        html_path = generate_html_report(markdown_path)
        
        print("\nReport generation complete!")
        print(f"Markdown report: {markdown_path}")
        print(f"HTML report: {html_path}")
        print(f"Screenshots: {screenshots_dir}")
        
        # Open the report
        if not args.non_interactive:
            open_report = input("\nOpen the HTML report now? (y/n): ")
            if open_report.lower() == 'y':
                if os.name == 'nt':  # Windows
                    os.startfile(html_path)
                elif os.name == 'posix':  # macOS or Linux
                    subprocess.run(['xdg-open', html_path], check=False)
        
    except KeyboardInterrupt:
        print("\nReport generation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError generating report: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 