 # TOSCA Laser Control System

A comprehensive control system for laser-based treatments with integrated patient management, camera control, and treatment session tracking.

## Features

- **Patient Management**
  - Create, edit, and store patient records
  - Search and filter patient database
  - Import/export patient data
  - User-friendly patient selection dialog
  - Patient data automatically linked to treatment sessions and images

- **Camera Control**
  - Support for Allied Vision cameras via VmbPy
  - Live video streaming
  - Image capture and storage
  - Advanced camera settings (pixel format, exposure, gain, etc.)
  - Automatic image saving to patient-specific folders
  - Integration with treatment sessions

- **Treatment Session Management**
  - Create treatment sessions linked to patients
  - Record treatment parameters and results
  - Add and view session images
  - Track treatment history
  - Direct integration with camera capture system

- **Hardware Integration**
  - Camera control via VmbPy
  - Laser device control (placeholder for implementation)
  - Actuator control (placeholder for implementation)
  - Status indicators in application status bar

- **User Interface**
  - Clean, intuitive tabbed interface
  - Streamlined controls with redundant buttons removed
  - Patient information displayed in status bar
  - Emergency stop button for safety

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd TOSCA-dev
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Install Allied Vision Vimba X SDK:
   - Download from the [Allied Vision website](https://www.alliedvision.com/en/products/software.html)
   - Install according to your operating system

## Usage

### Starting the Application

Run the main application:
```
python app.py
```

### Patient Management

#### Creating a New Patient
1. Click **File > New Patient** or use the **New Patient** button in the Patient Information tab
2. Enter patient details (first name, last name, date of birth, etc.)
3. Click **Save**

#### Opening an Existing Patient
1. Click **File > Open Patient** or use the **Load Patient** button in the Patient Information tab
2. Select a patient from the list
3. Filter patients using the search box if needed

#### Editing Patient Information
1. Load the patient record
2. Modify the information in the form
3. Click **Save Patient**

#### Exporting/Importing Patient Data
1. Load the patient record
2. Click **Export Patient Data** to save patient data to an external location
3. Use **Import Patient Data** to load patient data from an external location

### Treatment Sessions

#### Creating a New Treatment Session
1. Load a patient record
2. Go to the **Treatment** tab
3. Click **New Session**
4. Enter session details (operator, treatment area, device settings, notes)
5. Click **Save Session**

#### Recording Treatment Images
1. Open an existing session or create a new one
2. Option 1: Click **Add Image** in the session form and select an image file
3. Option 2: Capture an image from the camera tab - you'll be prompted to add it to the current session
4. Choose the image type (e.g., "Before Treatment", "After Treatment")

#### Viewing Treatment History
1. Load a patient record
2. Go to the **Treatment** tab
3. Browse the list of sessions on the left panel
4. Click on a session to view its details and associated images

### Camera Control

#### Connecting to a Camera
1. Go to the **Camera & Imaging** tab
2. Select a camera from the dropdown list
3. Choose pixel format and access mode
4. Click **Connect**

#### Capturing Images
1. Start the camera stream
2. Click **Capture** to take a photo
3. If a patient is selected, the image will be saved to that patient's folder
4. You'll be prompted to add the image to the current treatment session

## Data Organization

- Patient data is stored in SQLite database (`data/tosca.db`)
- Patient-specific files are organized in folders:
  - `data/patients/{patient_id}/` - Base patient directory
  - `data/patients/{patient_id}/sessions/{session_id}/images/` - Images associated with a specific treatment session

- Image files include patient information in filenames
- Treatment sessions are linked to patients and their images

## Directory Structure

- `app.py`: Main application entry point
- `src/`: Source code directory
  - `data_io/`: Data input/output modules
    - `patient_data.py`: Patient data management (SQLite backend)
  - `gui/`: GUI modules (PyQt6)
    - `main_window.py`: Main application window
    - `patient_form.py`: Patient information form
    - `patient_dialogs.py`: Patient selection/creation dialogs
    - `session_form.py`: Treatment session form
    - `camera_display.py`: Camera display and control widget
  - `hardware/`: Hardware control modules
    - `vmpy_camera.py`: Allied Vision camera controller (VmbPy)
    - `laser_controller.py`: Laser device controller (Serial)
    - `actuator_controller.py`: Motion actuator controller (Serial)
    - `actuator-control/`: Xeryon actuator control libraries
  - `utils/`: Utility modules
    - `error_handling.py`: Standardized error handling system
- `lib/`: External libraries
  - `vmpy/`: VmbPy SDK for camera control
    - `cti/`: GenICam Transport Layer files
- `data/`: Data storage directory (Created automatically)
  - `patients/`: Patient-specific data and session images
  - `tosca.db`: SQLite database
- `docs/`: Documentation files
  - `developer/`: Developer documentation
    - `architecture.md`: System architecture overview
    - `error_handling_guide.md`: Error handling best practices
  - `cti/`: GenICam Transport Layer files (Needed for Vimba X)
- `reports/`: Directory for reports and screenshots
  - `images/`: Image files for reports
  - `screenshots/`: Application screenshots
  - `generated/`: Generated report files
  - `api_summaries/`: API documentation summaries
- `tools/`: Utility scripts for development and reporting
- `logs/`: Application log files


## Developer Documentation

The project includes comprehensive developer documentation:

### System Architecture

The `docs/developer/architecture.md` file provides a detailed overview of the system architecture, including:
- Component descriptions
- Data flow
- Directory structure
- Threading model
- Configuration
- Logging
- Testing
- Extension guidelines

### Error Handling

The project uses a standardized error handling approach defined in `src/utils/error_handling.py`. This approach ensures consistent error reporting, logging, and handling across all components of the application.

The `docs/developer/error_handling_guide.md` file provides detailed information on:
- Custom exception classes
- Error types and severity levels
- Helper functions and decorators
- Best practices for error handling
- Error handling in GUI components and background threads
- Common error scenarios and recovery strategies

## Recent Updates (May 13, 2025)

The following improvements and fixes have been implemented:

1. **User Interface Enhancements**
   - Added direct numeric input fields for camera exposure and gain values
   - Changed default startup tab to Patient Information for better workflow
   - Updated default COM port to COM4 for actuator control

2. **File Organization**
   - Standardized file locations for all data storage
   - Implemented consistent directory structure:
     - Patient data: `data/patients/[patient_id]/`
     - Captured images (no patient): `data/captures/`
     - Patient images: `data/patients/[patient_id]/images/`

3. **Bug Fixes**
   - Fixed UI element references in camera display module
   - Resolved missing import issues
   - Improved error handling for camera settings

For a detailed list of changes, see [docs/developer/changes_summary.md](docs/developer/changes_summary.md).

## Adding New Features

1. Camera features
   - Add support for additional camera parameters
   - Implement camera calibration
   - Add advanced image processing

2. Patient Management
   - Extend patient data fields
   - Add reporting capabilities
   - Implement data visualization

3. Treatment
   - Add specialized treatment protocols
   - Implement treatment planning tools
   - Add outcome tracking

4. Error Handling
   - Implement standardized error handling in all modules
   - Add error recovery strategies
   - Improve user feedback for error conditions
