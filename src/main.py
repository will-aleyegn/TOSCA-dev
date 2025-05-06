#!/usr/bin/env python3
"""
Laser Device Control Application - Main Entry Point

This script serves as the main entry point for the laser device control application.
It initializes all necessary components and starts the GUI.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

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
    app.setApplicationName("Laser Device Control")
    
    try:
        # Initialize the main window
        main_window = MainWindow()
        main_window.show()
        
        # Start the application event loop
        logger.info("Application initialized successfully")
        return app.exec()
    
    except Exception as e:
        logger.error(f"Error during application startup: {e}", exc_info=True)
        return 1
    
if __name__ == "__main__":
    sys.exit(main()) 