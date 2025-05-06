#!/usr/bin/env python3
"""
TOSCA Laser Device Control Application - Launcher

This script serves as the entry point for the TOSCA laser device control application.
It initializes and launches the application.
"""

import sys
import os
import logging
import platform
from pathlib import Path

# --- Start: Set GenICam TL Path ---
# Point GenICam to the Transport Layer (TL) files copied into the project directory.
# This ensures the application uses the bundled TL instead of a system-wide installation.
try:
    project_root = Path(__file__).parent
    cti_path = (project_root / 'docs' / 'cti').resolve() # Calculate absolute path

    if cti_path.is_dir():
        # Choose the correct env var based on 32/64 bit Python
        # Note: Vimba X typically installs 64-bit TLs. Adjust if using 32-bit.
        is_64bits = sys.maxsize > 2**32
        env_var = 'GENICAM_GENTL64_PATH' if is_64bits else 'GENICAM_GENTL32_PATH'

        current_gentl_path = os.environ.get(env_var, '')
        paths = current_gentl_path.split(os.pathsep) if current_gentl_path else []

        # Add the path if it's not already present
        if str(cti_path) not in paths:
            paths.insert(0, str(cti_path)) # Prepend to prioritize project TL
            os.environ[env_var] = os.pathsep.join(paths)
            print(f"Set {env_var} to: {os.environ[env_var]}") # Optional: print for verification
        else:
            print(f"Project TL path '{cti_path}' already in {env_var}.") # Optional
    else:
        print(f"Warning: Project TL directory not found at '{cti_path}'. Using system default.", file=sys.stderr)

except Exception as e:
    print(f"Error setting GenICam TL path: {e}", file=sys.stderr)
# --- End: Set GenICam TL Path ---

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