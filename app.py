#!/usr/bin/env python3
"""
TOSCA Laser Device Control Application - Launcher

This script serves as the entry point for the TOSCA laser device control application.
It initializes and launches the application.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure the src directory is in the Python path
sys.path.append(str(Path(__file__).parent))

# Import and run the main entry point
from src.main import main

if __name__ == "__main__":
    # Configure basic logging to console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Run the application
    sys.exit(main()) 