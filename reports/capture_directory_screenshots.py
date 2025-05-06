#!/usr/bin/env python3
"""
Directory Screenshot Tool for TOSCA

This script opens file explorer windows to show patient directories and captures screenshots.
"""

import os
import subprocess
import time
from pathlib import Path
import pyautogui

def create_screenshot_dir():
    """Create directory for screenshots."""
    screenshots_dir = Path("./docs/screenshots")
    screenshots_dir.mkdir(exist_ok=True, parents=True)
    return screenshots_dir

def open_patient_directory():
    """
    Open the patients directory in file explorer.
    
    Returns:
        bool: True if directory exists and was opened
    """
    patient_dir = Path("./data/patients")
    
    if not patient_dir.exists():
        print(f"Patient directory not found: {patient_dir}")
        return False
    
    # Get absolute path
    abs_path = patient_dir.absolute()
    
    # Open directory in file explorer
    if os.name == 'nt':  # Windows
        subprocess.Popen(f'explorer "{abs_path}"')
    elif os.name == 'posix':  # Linux/Mac
        if os.system('which xdg-open') == 0:
            subprocess.Popen(['xdg-open', abs_path])
        elif os.system('which open') == 0:
            subprocess.Popen(['open', abs_path])
        else:
            print("Could not find a way to open the file explorer")
            return False
    
    print(f"Opened directory: {abs_path}")
    return True

def capture_directory_screenshot():
    """Open patient directory and capture screenshot."""
    screenshots_dir = create_screenshot_dir()
    
    if open_patient_directory():
        # Wait for file explorer to open
        time.sleep(2)
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Save as patient directory screenshot
        filename = f"patient_directory_{int(time.time())}.png"
        filepath = screenshots_dir / filename
        screenshot.save(filepath)
        
        print(f"Saved directory screenshot to: {filepath}")

def open_specific_patient_dir():
    """Prompt for a patient ID and open their directory."""
    patient_id = input("Enter patient ID to open (or press Enter to list all): ")
    
    if patient_id:
        patient_specific_dir = Path("./data/patients") / patient_id
        if not patient_specific_dir.exists():
            print(f"Patient directory not found: {patient_specific_dir}")
            return False
            
        # Get absolute path
        abs_path = patient_specific_dir.absolute()
    else:
        abs_path = Path("./data/patients").absolute()
    
    # Open directory in file explorer
    if os.name == 'nt':  # Windows
        subprocess.Popen(f'explorer "{abs_path}"')
    elif os.name == 'posix':  # Linux/Mac
        if os.system('which xdg-open') == 0:
            subprocess.Popen(['xdg-open', abs_path])
        elif os.system('which open') == 0:
            subprocess.Popen(['open', abs_path])
        else:
            print("Could not find a way to open the file explorer")
            return False
    
    # Wait for file explorer to open
    time.sleep(2)
    
    # Take screenshot
    screenshots_dir = create_screenshot_dir()
    screenshot = pyautogui.screenshot()
    
    # Save screenshot
    if patient_id:
        filename = f"patient_{patient_id}_directory_{int(time.time())}.png"
    else:
        filename = f"patients_directory_{int(time.time())}.png"
        
    filepath = screenshots_dir / filename
    screenshot.save(filepath)
    
    print(f"Saved directory screenshot to: {filepath}")
    return True

if __name__ == "__main__":
    print("TOSCA Directory Screenshot Tool")
    print("------------------------------")
    print("1. Capture all patients directory")
    print("2. Capture specific patient directory")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        capture_directory_screenshot()
    elif choice == "2":
        open_specific_patient_dir()
    else:
        print("Invalid choice.") 