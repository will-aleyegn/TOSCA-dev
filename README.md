# TOSCA Laser Device Control Application

## Overview
This application provides a GUI for controlling a laser device and acquiring images from Allied Vision cameras using the Vimba X SDK and VmbPy. Only Allied Vision (Vimba X/VmbPy) cameras are supported.

## Quick Start
1. Install Python 3.7+ (64-bit recommended).
2. Install the Vimba X SDK and VmbPy (see docs/vmbpy_summary.md for details).
3. Copy the required .cti files to `docs/cti` and ensure the environment variable is set (handled in app.py).
4. Run the application:
   ```bash
   python app.py
   ```
5. Use the GUI to connect, stream, and capture images from your Allied Vision camera.

## Documentation
- See `docs/vmbpy_summary.md` for VmbPy usage, best practices, and troubleshooting.
- Example scripts for camera usage are in `docs/vmpy/examples/`.

## Supported Features
- Camera connection, streaming, and image capture (VmbPy only)
- GUI controls for camera operations

## Not Supported
- OpenCV/USB cameras
- Legacy camera controllers

---
For more details, see the summary and example scripts in the documentation folder.

## Features

- Hardware interface for laser device control
- Image acquisition and processing
- Data input/output management
- Interactive graphical user interface
- Real-time monitoring and analysis

## Setup and Installation

1. Clone this repository:
```
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment (recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```
pip install -r requirements.txt
pip install docs/vmpy/vmbpy-1.1.0-py3-none-win_amd64.whl
```

## Project Structure

- `src/hardware/` - Hardware control modules
- `src/image_processing/` - Image acquisition and processing
- `src/data_io/` - Data input/output management
- `src/gui/` - Graphical user interface components
- `docs/` - Documentation
- `tests/` - Test files

## Usage

*Coming soon...*

## License

*Specify your license here* 