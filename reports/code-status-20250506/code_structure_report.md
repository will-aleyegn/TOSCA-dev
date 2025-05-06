Project: TOSCA Laser Control System

Core Application Logic (src/):
  - main.py:
    - Main application entry point.
    - Initializes logging, Qt application, and VmbSystem.
    - Creates and shows the MainWindow.

  - gui/ (Graphical User Interface - PyQt6):
    - main_window.py (MainWindow):
      - Central application window, manages overall layout, menus, status bar.
      - Hosts tabbed interface for different functionalities.
      - Delegates hardware interactions and data management.
    - camera_display.py (CameraDisplayWidget):
      - UI for camera selection, controls (exposure, gain), and live feed display.
      - Interacts with VMPyCameraController for camera operations.
    - patient_form.py (PatientFormWidget):
      - UI for creating, viewing, and editing patient demographic and medical information.
      - Interacts with PatientDataManager.
    - session_form.py (SessionFormWidget):
      - UI for managing treatment sessions associated with a patient.
      - Lists sessions and provides a form for session details (operator, settings, notes, images).
      - Interacts with PatientDataManager.
    - patient_dialogs.py (PatientSelectDialog, QuickPatientDialog):
      - Helper dialogs for selecting existing patients and quickly creating new ones.

  - data_io/ (Data Input/Output and Persistence):
    - patient_data.py (PatientDataManager):
      - Manages all data persistence using an SQLite database (tosca.db).
      - Handles CRUD operations for patients, treatment sessions, and image metadata.
      - Manages file system directories for patient-specific data/images.
      - Provides import/export functionality.

  - hardware/ (Hardware Interface and Control):
    - vmpy_camera.py (VMPyCameraController):
      - Interface for Allied Vision cameras using the VmbPy SDK.
      - Handles camera initialization, configuration (pixel format, resolution),
        asynchronous streaming, frame capture, and settings management.
    - laser_controller.py (LaserController):
      - Interface for the laser device via serial communication.
      - Manages connection, command sending (power, enable), and status retrieval.
      - Includes auto-detection for serial port.
    - actuator_controller.py (ActuatorController):
      - Interface for a motion actuator via serial communication.
      - Manages connection, movement commands (home, move to absolute/relative),
        and status/position querying.
      - Includes auto-detection and uses a motion lock. 