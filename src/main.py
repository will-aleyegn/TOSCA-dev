#!/usr/bin/env python3
"""
Laser Device Control Application - Main Entry Point

This script serves as the main entry point for the laser device control application.
It initializes all necessary components and starts the GUI.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

# Import VmbSystem for persistent context
from vmbpy import VmbSystem

# Import project modules
from src.gui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("laser_control.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to initialize and run the application."""
    logger.info("Starting Laser Device Control Application")
    
    # Create the Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("TOSCA Control System")
    
    # Enter VmbSystem context for the whole app lifetime
    vmb = VmbSystem.get_instance()
    vmb.__enter__()
    try:
        # Initialize the main window with persistent vmb
        main_window = MainWindow(vmb=vmb)
        main_window.show()
        
        # Start the application event loop
        logger.info("Application initialized successfully")
        result = app.exec()
    except Exception as e:
        logger.error(f"Error during application startup: {e}", exc_info=True)
        result = 1
    finally:
        # Exit VmbSystem context on app exit
        vmb.__exit__(None, None, None)
    return result

if __name__ == "__main__":
    sys.exit(main()) 