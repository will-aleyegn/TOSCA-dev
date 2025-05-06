#!/usr/bin/env python3
"""
TOSCA Screenshot Tool

This script captures screenshots of the TOSCA application for documentation purposes.
Run this script while the TOSCA application is open.
"""

import os
import time
import datetime
from pathlib import Path
import pyautogui
import sys
import argparse

def create_screenshot_dir():
    """Create a directory for screenshots if it doesn't exist."""
    screenshots_dir = Path("./docs/screenshots")
    screenshots_dir.mkdir(exist_ok=True, parents=True)
    return screenshots_dir

def take_screenshot(name, delay=1, region=None):
    """
    Take a screenshot and save it to the screenshots directory.
    
    Args:
        name (str): Name of the screenshot (without extension)
        delay (int): Delay in seconds before taking the screenshot
        region (tuple): Region to capture (left, top, width, height) or None for full screen
    
    Returns:
        Path: Path to the saved screenshot
    """
    # Create the screenshots directory
    screenshots_dir = create_screenshot_dir()
    
    # Wait for the specified delay
    time.sleep(delay)
    
    # Generate a filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = screenshots_dir / filename
    
    # Take the screenshot
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()
    
    # Save the screenshot
    screenshot.save(filepath)
    print(f"Screenshot saved to: {filepath}")
    
    return filepath

def capture_all_screens(delay_between=2):
    """
    Capture screenshots of all main screens in the TOSCA application.
    User will need to navigate to each screen manually.
    
    Args:
        delay_between (int): Delay in seconds between prompts
    """
    screens = [
        "main_window",
        "patient_form",
        "patient_selection",
        "treatment_session",
        "camera_display",
        "laser_control",
    ]
    
    for screen in screens:
        input(f"Navigate to the {screen.replace('_', ' ')} screen, then press Enter to capture...")
        take_screenshot(screen)
        time.sleep(delay_between)

def main():
    """Main function to parse arguments and execute screenshot capture."""
    parser = argparse.ArgumentParser(description="Capture screenshots of the TOSCA application")
    parser.add_argument("--all", action="store_true", help="Capture all main screens (interactive)")
    parser.add_argument("--name", type=str, help="Name for the screenshot")
    parser.add_argument("--delay", type=int, default=1, help="Delay in seconds before capture")
    
    args = parser.parse_args()
    
    if args.all:
        capture_all_screens()
    elif args.name:
        take_screenshot(args.name, args.delay)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScreenshot capture interrupted by user.")
        sys.exit(0) 