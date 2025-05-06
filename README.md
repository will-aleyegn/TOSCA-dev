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
- `code_structure_report.md`: Brief overview of the source code structure.
- `functional_report.md`: Detailed description of module and function purposes.
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
- `data/`: Data storage directory (Created automatically)
  - `patients/`: Patient-specific data and session images
  - `tosca.db`: SQLite database
- `docs/`: Documentation files
  - `cti/`: GenICam Transport Layer files (Needed for Vimba X)
- `reports/`: Directory for generated reports (Note: Ignored by Git).


### Adding New Features

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
