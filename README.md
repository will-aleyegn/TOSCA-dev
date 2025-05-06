# TOSCA Laser Device Control Application

## Overview
This application provides a GUI for controlling a laser device and acquiring images from Allied Vision cameras using the Vimba X SDK and VmbPy. Only Allied Vision (Vimba X/VmbPy) cameras are supported.

## Quick Start
1. Install Python 3.7+ (64-bit recommended).
2. Install the Vimba X SDK and VmbPy (see `docs/vmbpy_summary.md` for details).
3. Copy the required .cti files to `docs/cti` (handled in `app.py`).
4. Run the application:
   ```bash
   python app.py
   ```
5. Use the GUI to connect, stream, capture images, and control settings (Exposure, Gain) from your Allied Vision camera. The app starts in auto-exposure/gain mode.

## Documentation
- See `docs/vmbpy_summary.md` for VmbPy usage, best practices, and troubleshooting.
- Example scripts for camera usage are in `docs/vmpy/examples/`.

## Core Features
- VMPy Camera Control:
    - Auto-detection and connection.
    - Live streaming and display.
    - Image capture with settings in filename (saved to `output/` folder).
    - Real-time control of Exposure and Gain (manual/auto).
- Basic GUI Structure:
    - Camera control tab (functional).
    - Placeholder tabs for Patient Info, Laser Control, Treatment (TODO).
- Hardware modules for Laser and Actuator control (placeholders/not implemented).

## Not Supported / Archived
- OpenCV/USB camera support (legacy code moved to `trash/`).
- Advanced image processing (legacy code moved to `trash/`).
- Extensive Vimba X SDK documentation (moved to `trash/` to reduce repo size; refer to original SDK installation if needed).

---

## Setup and Installation

1. Clone this repository.
2. Create and activate a Python virtual environment.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: VmbPy is typically installed via a .whl file provided with the Vimba X SDK, see `docs/vmbpy_summary.md` for details. The `requirements.txt` may need updating based on your exact VmbPy installation method.)*

## Project Structure

- `src/`:
    - `hardware/`: VMPy camera controller, placeholder laser/actuator controllers.
    - `data_io/`: Placeholder for data management.
    - `gui/`: PyQt GUI components (main window, camera display).
    - `main.py`: Application entry point.
- `docs/`:
    - `vmbpy_summary.md`: Key VmbPy documentation.
    - `vmpy/examples/`: Useful VmbPy example scripts.
    - `cti/`: Transport Layer files (ensure these are present).
- `output/`: Default directory for saved images.
- `trash/`: Archived legacy code and documentation.
- `app.py`: Main application launcher.
- `requirements.txt`: Python dependencies.

## Usage
Run `python app.py`. The application will open, connect to the first available Allied Vision camera, and start streaming on the "Camera & Imaging" tab.

## License
*Specify your license here* 