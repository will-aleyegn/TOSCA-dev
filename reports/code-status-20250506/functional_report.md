# TOSCA Laser Control System - Detailed Functional Report

## 1. `src/main.py`

### Function: `main()`
- **Purpose**: Main entry point of the TOSCA application.
- **Actions**:
    - Logs the start of the application.
    - Creates a `QApplication` instance.
    - Sets the application name.
    - Initializes the `VmbSystem` (from `vmbpy`) using a context manager to ensure proper setup and teardown of the camera SDK.
    - Instantiates `MainWindow`, passing the active `VmbSystem` instance to it.
    - Shows the `MainWindow`.
    - Logs successful application initialization.
    - Starts the Qt application event loop (`app.exec()`).
    - Catches any exceptions during startup, logs them with a traceback, and returns an error code (1).
- **Returns**: Application exit code (0 on normal exit, 1 on error during startup).

## 2. `src/gui/main_window.py` - Class `MainWindow(QMainWindow)`

### `__init__(self, vmb=None)`
- **Purpose**: Initializes the main application window.
- **Parameters**:
    - `vmb`: An active `VmbSystem` instance from `vmbpy`, used for camera operations.
- **Actions**:
    - Sets window title and minimum size.
    - Calls internal helper methods:
        - `_create_actions()`: Defines `QAction` objects for all menu items (File, Hardware, Camera, Help).
        - `_create_menus()`: Populates the menu bar with the defined actions.
        - `_create_status_bar()`: Sets up the status bar with labels for Laser, Actuator, Camera, and Patient status.
        - `_create_central_widget()`: Creates the main layout, a `QTabWidget`, and populates it with tabs:
            - "Patient Information": Uses `PatientFormWidget`. Connects `patient_updated` signal.
            - "Laser Control": Placeholder tab (marked with TODO).
            - "Camera & Imaging": Uses `CameraDisplayWidget`, passing the `vmb` instance.
            - "Treatment": Uses `SessionFormWidget`. Connects `session_updated` signal.
            - Adds an "EMERGENCY STOP" button.
        - `_create_connections()`: Connects signals from actions and widgets to their respective handler methods (slots).
    - Calls `_initialize_hardware()` (currently a placeholder).
    - Starts a `QTimer` (`status_timer`) to call `_update_status()` periodically (every 5 seconds).
    - Switches to the "Camera & Imaging" tab and uses `QTimer.singleShot()` to trigger `self.camera_display.on_connect_camera()` shortly after startup, attempting to auto-connect the camera.
- **Key Members Initialized**: `self.vmb`, UI elements (menus, tabs, widgets), `self.status_timer`.

### `closeEvent(self, event)`
- **Purpose**: Handles the window close event (e.g., user clicks 'X' button).
- **Parameters**:
    - `event`: The `QCloseEvent` object.
- **Actions**:
    - Displays a `QMessageBox.question` to confirm if the user really wants to exit.
    - If "Yes":
        - Calls `_shutdown_hardware()` (placeholder).
        - Accepts the close event (`event.accept()`), allowing the window to close.
    - If "No":
        - Ignores the close event (`event.ignore()`), keeping the window open.

### UI Creation Methods (`_create_actions`, `_create_menus`, `_create_status_bar`, `_create_central_widget`)
- **Purpose**: Standard Qt methods for building the UI elements.
- **Details**:
    - `_create_actions`: Defines actions like `exit_action`, `new_patient_action`, `connect_hardware_action`, `start_camera_action`, etc., with shortcuts and status tips.
    - `_create_menus`: Organizes these actions into "File", "Hardware", "Camera", and "Help" menus in the menu bar.
    - `_create_status_bar`: Initializes `QStatusBar` and adds `QLabel` widgets for `laser_status`, `actuator_status`, `camera_status`, and `patient_status`. These are styled with red color initially.
    - `_create_central_widget`:
        - Sets up the main `QTabWidget`.
        - Instantiates `PatientFormWidget`, `CameraDisplayWidget`, and `SessionFormWidget`.
        - The `data_dir` for forms is now robustly set to `PROJECT_DATA_DIR` (resolved to `TOSCA-dev/data`).
        - Connects `patient_updated` from `PatientFormWidget` to `_on_patient_updated`.
        - Connects `session_updated` from `SessionFormWidget` to `_on_session_updated`.

### `_create_connections(self)`
- **Purpose**: Connects signals from UI elements (actions, buttons) to their corresponding handler methods (slots).
- **Examples of Connections**:
    - `self.exit_action.triggered.connect(self.close)`
    - `self.new_patient_action.triggered.connect(self._on_new_patient)`
    - `self.connect_hardware_action.triggered.connect(self._on_connect_hardware)`
    - `self.start_camera_action.triggered.connect(self._on_start_camera)` (delegates to `self.camera_display`)
    - `self.emergency_stop_btn.clicked.connect(self._on_emergency_stop)`

### Handler Methods (Slots - e.g., `_on_new_patient`, `_on_connect_hardware`, etc.)
- **Purpose**: These methods are executed when their connected signals are emitted (e.g., a menu item is clicked).
- **General Pattern**:
    - `_on_new_patient()`: Calls `self.patient_form.on_new_patient()`. Switches to the patient tab.
    - `_on_open_patient()`: Calls `self.patient_form.on_load_patient()`. Switches to the patient tab.
    - `_on_export_data()` / `_on_import_data()`: Delegate to `self.patient_form`.
    - `_on_connect_hardware()` / `_on_disconnect_hardware()`: Placeholder logic, logs action. Intended to interact with `LaserController` and `ActuatorController`.
    - `_on_start_camera()` / `_on_stop_camera()` / `_on_capture_image()`: Delegate to the corresponding methods in `self.camera_display`.
    - `_on_emergency_stop()`: Placeholder for emergency stop logic (critical).
    - `_on_about()` / `_on_help()`: Display `QMessageBox` for "About" and placeholder for "Help".
- **Key Callbacks for Data Updates**:
    - `_on_patient_updated(self, patient_data)`:
        - Receives `patient_data` dictionary when a patient is loaded/saved in `PatientFormWidget`.
        - Updates `self.patient_status` label in the status bar.
        - Informs `self.session_form` about the current patient using `self.session_form.set_patient(patient_data)`.
        - Informs `self.camera_display` about the current patient using `self.camera_display.set_current_patient(patient_data)`.
    - `_on_session_updated(self, session_data)`:
        - Receives `session_data` when a session is updated.
        - Logs the update. (Could potentially update status bar if relevant session info is displayed there).

### Hardware and Status Methods
- **`_initialize_hardware(self)`**:
    - Placeholder for initializing `LaserController` and `ActuatorController`.
    - TODO: Instantiate controllers, attempt connection, update status bar.
- **`_shutdown_hardware(self)`**:
    - Placeholder for disconnecting from hardware.
    - TODO: Call `disconnect()` on controllers.
- **`_update_status(self)`**:
    - Called periodically by `self.status_timer`.
    - Placeholder for querying actual status from `LaserController`, `ActuatorController`, and `CameraDisplayWidget.camera_controller`.
    - TODO: Update `self.laser_status`, `self.actuator_status`, `self.camera_status` labels based on real hardware states.

### `on_add_image_to_session(self, image_path)`
- **Purpose**: Slot likely intended to be connected if `CameraDisplayWidget` emits a signal when an image is captured and needs to be associated with the current session.
- **Action**: Calls `self.session_form.add_image_to_current_session(image_path)` (assuming `SessionFormWidget` has such a method).

## 3. `src/gui/camera_display.py` - Class `CameraDisplayWidget(QWidget)`

### `__init__(self, parent=None, vmb=None)`
- **Purpose**: Initializes the widget for camera display and control.
- **Parameters**:
    - `parent`: Parent QWidget.
    - `vmb`: Active `VmbSystem` instance.
- **Actions**:
    - Stores `vmb`. Initializes `camera_controller = None`, `current_frame = None`, and `frame_lock = Lock()`.
    - Creates `update_timer` (QTimer) connected to `_update_frame()` for displaying streamed frames.
    - Calls `_init_ui()` to build the interface.
    - If `self.vmb` is valid, calls `_populate_camera_list()` to fill the camera selection dropdown.
    - If "Auto-connect" is checked, schedules `self.on_connect_camera()` using `QTimer.singleShot()`.
- **Key Members**: `self.vmb`, `self.camera_controller` (instance of `VMPyCameraController`), `self.current_frame`, `self.update_timer`, various UI elements.

### `_init_ui(self)`
- **Purpose**: Creates and arranges all UI elements for camera control and display.
- **Elements Created**:
    - **Camera Selection & Control Panel (QGroupBox)**:
        - `camera_id_combo` (QComboBox): For selecting camera ID. Populated by `_populate_camera_list()`.
        - `pixel_format_combo` (QComboBox): For selecting pixel format. Populated after camera connection.
        - `access_mode_combo` (QComboBox): For selecting VmbPy camera access mode.
        - `auto_connect_checkbox` (QCheckBox).
        - `connect_btn`, `disconnect_btn` (QPushButtons).
    - **Camera Feature Controls**:
        - Exposure: `exposure_auto_checkbox`, `exposure_slider`, `exposure_value_label`.
        - Gain: `gain_auto_checkbox`, `gain_slider`, `gain_value_label`.
        - Settings: `save_settings_btn`, `load_settings_btn`, `show_features_btn`.
    - **Capture and Display Controls**:
        - `capture_btn`, `start_stream_btn`, `stop_stream_btn`.
    - **Image Display**:
        - `image_label` (QLabel): Displays the camera feed.
    - **Status Bar**:
        - `status_label` (QLabel): Displays operational status messages.
- **Connections**: Connects button clicks and value changes to handler methods (e.g., `connect_btn.clicked.connect(self.on_connect_camera)`).

### `_populate_camera_list(self)`
- **Purpose**: Dynamically populates the `camera_id_combo` with cameras detected by the `VmbSystem`.
- **Actions**:
    - Clears existing items. Adds a "Default/Auto-detect" option.
    - If `self.vmb` is available, calls `self.vmb.get_all_cameras()`.
    - For each detected camera, adds its name and ID to the combo box. Stores the camera ID using `item.setData()`.
    - Handles cases where no cameras are found or errors occur during listing.

### `on_connect_camera(self)`
- **Purpose**: Handles the "Connect" button click. Initializes and connects to the selected camera.
- **Actions**:
    - If already connected, calls `on_disconnect_camera()` first.
    - Retrieves selected `camera_id`, `pixel_format`, and `access_mode` from combo boxes.
    - Instantiates `VMPyCameraController` with these parameters and `self.vmb`.
    - Calls `self.camera_controller.initialize()`.
    - If successful:
        - Updates status label and button states (enable/disable).
        - Calls `_populate_pixel_formats()` to fill the pixel format combo box from the connected camera.
        - Calls `_update_feature_controls_from_camera()` to set UI controls (sliders) based on camera's current feature values and ranges.
    - Handles exceptions and shows error messages using `QMessageBox`.

### `on_disconnect_camera(self)`
- **Purpose**: Handles the "Disconnect" button click. Releases the camera.
- **Actions**:
    - If `self.camera_controller` exists:
        - Calls `self.camera_controller.release_camera()`.
        - Stops `self.update_timer`.
        - Resets UI elements (image label, button states, status label).
        - Sets `self.camera_controller = None`.

### `on_start_stream(self)` & `on_stop_stream(self)`
- **Purpose**: Start/stop asynchronous video streaming.
- **Actions**:
    - `on_start_stream()`:
        - Calls `self.camera_controller.start_stream()`.
        - If successful, starts `self.update_timer` (if not already running for a different purpose) to call `_update_frame()` periodically. Updates button states.
    - `on_stop_stream()`:
        - Calls `self.camera_controller.stop_stream()`.
        - Stops `self.update_timer`. Updates button states.

### `on_capture_image(self)`
- **Purpose**: Captures a single still image from the camera.
- **Actions**:
    - If `self.camera_controller` is active:
        - Calls `frame = self.camera_controller.capture_frame()`. (Note: `capture_frame` was in outline; if using streaming, might get from `get_current_frame`).
        - If frame is obtained:
            - Displays the frame using `_update_image_display()`.
            - If `self.current_patient` is set, constructs a save path within the patient's data directory (e.g., `data/<patient_id>/sessions/<session_id_if_applicable>/images/`). Creates directories if needed.
            - Prompts user with `QFileDialog.getSaveFileName` for the image filename.
            - If a filename is provided, calls `self.camera_controller.save_image(filepath, frame)`.
            - Emits `image_captured_signal(filepath)` (signal not explicitly defined in snippet, but typical).

### `_update_frame(self)`
- **Purpose**: Called by `self.update_timer` to get and display the latest frame during streaming.
- **Actions**:
    - If `self.camera_controller` and streaming:
        - Calls `frame_data = self.camera_controller.get_current_frame()`.
        - If `frame_data` is not `None`, calls `_update_image_display(frame_data)`.

### `_update_image_display(self, frame_data: np.ndarray)`
- **Purpose**: Converts a NumPy frame to QPixmap and displays it on `image_label`.
- **Actions**:
    - Converts `frame_data` (NumPy array, likely BGR) to `QImage`. Handles different formats (e.g., Grayscale, RGB).
    - Converts `QImage` to `QPixmap`.
    - Scales pixmap to fit `image_label` while maintaining aspect ratio.
    - Sets the pixmap on `self.image_label`.

### Feature Control Slots (e.g., `on_exposure_auto_changed`, `on_exposure_slider_changed`, etc.)
- **Purpose**: Handle UI interactions for camera features like exposure and gain.
- **Actions**:
    - Read state from checkbox/slider.
    - Call corresponding `set_feature_value` method on `self.camera_controller` (e.g., `self.camera_controller.set_feature_value("ExposureAuto", state)`).
    - Update UI (e.g., enable/disable slider if "Auto" is checked, update value label).
    - `_update_feature_controls_from_camera()`: Reads current values and ranges for features (e.g., ExposureTime, Gain) from the camera via `camera_controller.get_feature_value` and `camera_controller.get_feature_range` (if available) and updates the corresponding UI sliders (min, max, value) and labels.

### Settings Management (`on_save_settings`, `on_load_settings`)
- **Purpose**: Save/load camera feature settings to/from an XML file.
- **Actions**:
    - Use `QFileDialog` to get file path.
    - Call `self.camera_controller.save_settings(filepath)` or `self.camera_controller.load_settings(filepath)`.
    - After loading, call `_update_feature_controls_from_camera()` to refresh the UI.

### `set_current_patient(self, patient_data)`
- **Purpose**: Receives current patient context from `MainWindow`.
- **Action**: Stores `patient_data` in `self.current_patient` for use in image save paths.

## 4. `src/gui/patient_form.py` - Class `PatientFormWidget(QWidget)`

### `__init__(self, parent=None, data_dir="./data")`
- **Purpose**: Initializes the patient information form.
- **Parameters**:
    - `parent`: Parent QWidget.
    - `data_dir`: Directory for storing patient data (passed to `PatientDataManager`).
- **Actions**:
    - Instantiates `PatientDataManager(data_dir)`.
    - `current_patient = None`.
    - Calls `_init_ui()`.
- **Signal**: `patient_updated = pyqtSignal(dict)` (emitted on save/load).

### `_init_ui(self)`
- **Purpose**: Creates and arranges UI elements for patient data entry.
- **Elements Created**:
    - Patient ID (ReadOnly `QLineEdit`), "New", "Load", "Save" buttons.
    - **QGroupBoxes** for "Personal Information" (First/Last Name, DOB, Gender), "Contact Information", "Medical Information", "Notes". Uses `QLineEdit`, `QDateEdit`, `QComboBox`, `QTextEdit`.
    - "Export Patient Data", "Import Patient Data" buttons.
- **Connections**: Connects button clicks to handler methods.

### Form Management (`clear_form`, `populate_form`, `get_form_data`)
- **`clear_form()`**: Resets all input fields to default/empty states and `self.current_patient = None`.
- **`populate_form(patient_data)`**: Fills form fields from a `patient_data` dictionary. Handles QDate conversion.
- **`get_form_data()`**: Collects data from form fields into a dictionary. Generates a new UUID for `patient_id` if it's empty.

### Event Handlers (`on_new_patient`, `on_load_patient`, `on_save_patient`, `on_export_data`, `on_import_data`)
- **`on_new_patient()`**:
    - Checks for unsaved changes using `_is_form_dirty()`.
    - Opens `QuickPatientDialog`. If successful, populates form with new patient data and emits `patient_updated`.
- **`on_load_patient()`**:
    - Checks for unsaved changes using `_is_form_dirty()`.
    - Opens `PatientSelectDialog`.
    - If a patient is selected (dialog accepted): calls `self.data_manager.load_patient()` and then `populate_form()`. Emits `patient_updated`.
    - If "New Patient" was chosen in `PatientSelectDialog` (custom dialog code): calls `self.on_new_patient()`.
- **`on_save_patient()`**:
    - Calls `get_form_data()`. Validates required fields (First/Last Name).
    - Calls `self.data_manager.save_patient()`.
    - Updates `self.current_patient` with saved data (which includes `created_at`, `updated_at` from data manager).
    - Emits `patient_updated`. Shows success/error `QMessageBox`.
- **`on_export_data()` / `on_import_data()`**:
    - Use `QFileDialog` for path selection.
    - Call `self.data_manager.export_patient_data()` or `self.data_manager.import_patient_data()`.
    - `on_import_data` populates form if successful.

### `_is_form_dirty(self)`
- **Purpose**: Checks if the current form data differs from `self.current_patient` (if loaded).
- **Logic**: Compares values of relevant fields between `self.get_form_data()` and `self.current_patient`.

## 5. `src/gui/session_form.py` - Class `SessionFormWidget(QWidget)`

### `__init__(self, parent=None, data_dir="./data")`
- **Purpose**: Initializes the treatment session management form.
- **Actions**: Similar to `PatientFormWidget`, instantiates `PatientDataManager`. `current_patient = None`, `current_session = None`. Calls `_init_ui()`.
- **Signal**: `session_updated = pyqtSignal(dict)`.

### `_init_ui(self)`
- **Purpose**: Creates a two-panel UI using `QSplitter`.
- **Left Panel**:
    - `sessions_table` (QTableWidget): Lists sessions for the current patient (Date, ID, Notes).
    - "New Session", "View Session" buttons.
- **Right Panel (QScrollArea with session details form)**:
    - QGroupBoxes for "Session Information" (ID, Date, Operator, Treatment Area), "Device Settings" (QTextEdit), "Session Notes" (QTextEdit), "Session Images" (`images_table` (QTableWidget), "Add Image", "View Image" buttons).
    - "Save Session" button.
- **Connections**: Session table clicks, button clicks to handlers.

### Patient and Session Management
- **`set_patient(self, patient_data)`**:
    - Called by `MainWindow` to set the current patient context.
    - Stores `patient_data` in `self.current_patient`.
    - Calls `_load_patient_sessions()` to update the `sessions_table`.
    - Clears the session detail form.
- **`_load_patient_sessions(self)`**:
    - If `current_patient`, calls `self.data_manager.get_patient_sessions()`.
    - Populates `sessions_table`. Stores session ID with each item.
- **`clear_form(self)`**: Clears session detail fields and `images_table`. `current_session = None`.
- **`populate_form(self, session_data)`**: Fills session detail form from `session_data`. Calls `_load_session_images()`.
- **`_load_session_images(self, session_id)`**:
    - If `session_id`, calls `self.data_manager.get_session_images(session_id)`.
    - Populates `images_table` with image filename, type, timestamp.

### Event Handlers
- **`_on_session_selected(self)`**: When a session is clicked in `sessions_table`.
    - Retrieves session ID. Calls `self.data_manager.load_session_data()`. Populates form with details.
- **`_on_new_session(self)`**: Clears form, generates a new temporary session ID (for display before save), sets default date.
- **`_on_save_session(self)`**:
    - Collects data from form. Generates new UUID for session ID if `self.current_session` is `None` or ID is missing.
    - Validates required fields (e.g., operator).
    - Calls `self.data_manager.save_session_data()`.
    - Reloads patient sessions list, emits `session_updated`.
- **`_on_add_image(self)`**:
    - If `current_session`, opens `QFileDialog.getOpenFileNames()`.
    - For each selected image:
        - Creates target path: `self.data_manager.patients_dir / self.current_patient['patient_id'] / "sessions" / self.current_session['session_id'] / "images" / image_filename`.
        - Copies the image file to the target path.
        - Calls `self.data_manager.add_image_record()` to save image metadata to DB.
        - Reloads images for the current session using `_load_session_images()`.
- **`_update_ui_state(self)`**: Enables/disables buttons and fields based on whether a patient is loaded and a session is active.

## 6. `src/gui/patient_dialogs.py`

### Class `PatientSelectDialog(QDialog)`
- **Purpose**: Dialog to select an existing patient from a searchable list.
- **`__init__(self, parent=None, data_manager=None)`**: Stores `data_manager`. Initializes UI and loads patients.
- **`_init_ui(self)`**: Creates search `QLineEdit`, `QListWidget` for patients, "New Patient" button, OK/Cancel `QDialogButtonBox`.
- **`_load_patients(self)`**: Populates `QListWidget` from `data_manager.get_all_patients()`.
- **`_filter_patients(self)`**: Filters list based on search text.
- **`_on_new_patient(self)`**: Calls `self.done(QDialog.DialogCode.Accepted + 1)` to signal "New Patient" was clicked.
- **`get_selected_patient_id(self)`**: Returns ID of the selected patient.
- **`exec(self)`**: Stores selected ID if dialog is accepted. Returns dialog result.

### Class `QuickPatientDialog(QDialog)`
- **Purpose**: Dialog for quickly creating a new patient with minimal essential information.
- **`__init__(self, parent=None, data_manager=None)`**: Stores `data_manager`. Initializes UI.
- **`_init_ui(self)`**: Creates `QFormLayout` for First Name, Last Name, DOB, Gender. OK/Cancel buttons.
- **`_on_accept(self)`**:
    - Validates First/Last Name.
    - Generates UUID for patient ID.
    - Calls `self.data_manager.add_patient()`.
    - If successful, retrieves full patient data via `self.data_manager.get_patient()` and stores in `self.patient_data`, then accepts dialog.
- **`exec(self)`**: Returns `self.patient_data` if accepted, else `None`.

## 7. `src/data_io/patient_data.py` - Class `PatientDataManager`

### `__init__(self, data_dir="./data")`
- **Purpose**: Initializes the data manager responsible for all patient/session data persistence.
- **Parameters**:
    - `data_dir`: Path to the root directory for storing data (defaults to `./data`).
- **Actions**:
    - Resolves `data_dir` to a `Path` object.
    - Defines paths for `patients_dir` (subdirectory for patient-specific files) and `db_path` (the SQLite database file).
    - Creates `data_dir` and `patients_dir` if they don't exist.
    - Calls `_init_database()` to ensure the SQLite database and tables are set up.
- **Key Members**: `self.data_dir`, `self.patients_dir`, `self.db_path`.

### `_init_database(self)`
- **Purpose**: Creates the SQLite database file and necessary tables if they don't already exist.
- **Actions**:
    - Connects to the SQLite database at `self.db_path`.
    - Creates three tables using `CREATE TABLE IF NOT EXISTS`:
        - `patients`: Stores patient demographics (patient_id PRIMARY KEY, first_name, last_name, dob, gender, contact_info, notes, created_at, updated_at).
        - `treatment_sessions`: Stores session info (session_id PRIMARY KEY, patient_id FOREIGN KEY, date, operator, device_settings, treatment_area, notes, created_at).
        - `image_records`: Stores image metadata (image_id PRIMARY KEY, session_id FOREIGN KEY, patient_id FOREIGN KEY, image_path, image_type, timestamp, notes).
    - Commits changes and closes the connection. Handles `sqlite3.Error`.

### Patient CRUD Methods
- **`add_patient(self, patient_id, first_name, last_name, date_of_birth, gender=None, contact_info=None, notes=None)`**:
    - **Purpose**: Adds a new patient record to the database.
    - **Actions**: Checks if patient ID already exists. Inserts a row into the `patients` table with provided details and current timestamps for `created_at`, `updated_at`. Creates a directory `self.patients_dir / patient_id`.
    - **Returns**: `True` on success, `False` otherwise.
- **`update_patient(self, patient_id, **kwargs)`**:
    - **Purpose**: Updates specified fields of an existing patient record.
    - **Actions**: Checks if patient exists. Builds an SQL `UPDATE` query dynamically based on allowed fields in `kwargs`. Updates the `updated_at` timestamp. Executes the update.
    - **Returns**: `True` on success, `False` otherwise.
- **`get_patient(self, patient_id)`**:
    - **Purpose**: Retrieves a single patient record by ID.
    - **Actions**: Queries the `patients` table for the given `patient_id`. Uses `sqlite3.Row` factory to return results as dict-like objects.
    - **Returns**: A dictionary containing patient data, or `None` if not found or on error.
- **`delete_patient(self, patient_id)`**:
    - **Purpose**: Deletes a patient record and associated data (sessions, images). (Implementation details based on outline).
    - **Actions**: Would delete records from `patients`, `treatment_sessions`, and `image_records` tables where `patient_id` matches. Would also delete the corresponding patient directory `self.patients_dir / patient_id` and its contents. Needs careful cascading or multi-step deletion.
    - **Returns**: Likely `True` on success, `False` otherwise.
- **`get_all_patients(self)`**:
    - **Purpose**: Retrieves all patient records. (Implementation based on outline).
    - **Actions**: Queries the `patients` table (`SELECT * FROM patients`). Orders results (e.g., by last name, first name).
    - **Returns**: A list of dictionaries, where each dictionary represents a patient.
- **`search_patients(self, criteria)`**:
    - **Purpose**: Searches for patients based on given criteria (e.g., name, ID). (Implementation based on outline).
    - **Actions**: Builds a `SELECT` query with `WHERE` clauses based on `criteria` dictionary (e.g., using `LIKE` for name searches). Parameterizes query values.
    - **Returns**: A list of matching patient dictionaries.

### Session CRUD Methods
- **`add_treatment_session(self, session_id, patient_id, date, operator, device_settings=None, treatment_area=None, notes=None)`**:
    - **Purpose**: Adds a new treatment session record for a patient. (Implementation based on outline, parameters might differ slightly from `SessionFormWidget` usage).
    - **Actions**: Checks if patient exists. Inserts a row into `treatment_sessions` table with provided details and current `created_at` timestamp. Creates session-specific directories if needed (e.g., `patients/<pid>/sessions/<sid>/images`).
    - **Returns**: Likely `True` on success, `False` otherwise.
- **`get_treatment_sessions(self, patient_id)`**:
    - **Purpose**: Retrieves all treatment sessions for a specific patient. (Implementation based on outline).
    - **Actions**: Queries `treatment_sessions` table `WHERE patient_id = ?`. Orders results (e.g., by date).
    - **Returns**: A list of session dictionaries for the given patient.
- **`update_treatment_session(self, session_id, **kwargs)`**: (Method likely exists or needed)
    - **Purpose**: Updates an existing treatment session.
    - **Actions**: Builds dynamic `UPDATE` query for `treatment_sessions` table.
    - **Returns**: `True` on success, `False` otherwise.
- **`delete_treatment_session(self, session_id)`**: (Method likely exists or needed)
    - **Purpose**: Deletes a session and its associated images/records.
    - **Actions**: Deletes from `treatment_sessions` and `image_records` tables. Deletes the session's directory (`patients/<pid>/sessions/<sid>`).
    - **Returns**: `True` on success, `False` otherwise.

### Image Record Methods
- **`add_image_record(self, image_id, session_id, patient_id, image_path, image_type, timestamp=None, notes=None)`**:
    - **Purpose**: Adds a record for an image associated with a session. (Implementation based on outline).
    - **Actions**: Inserts a row into `image_records` table. `image_path` likely stored relative to `data_dir` or `patients_dir` for portability. `timestamp` defaults to now if not provided.
    - **Returns**: `True` on success, `False` otherwise.
- **`get_session_images(self, session_id)`**:
    - **Purpose**: Retrieves all image records for a specific session. (Implementation based on outline).
    - **Actions**: Queries `image_records` table `WHERE session_id = ?`.
    - **Returns**: A list of image record dictionaries.
- **`delete_image_record(self, image_id)`**: (Method likely exists or needed)
    - **Purpose**: Deletes an image record from the DB and the corresponding image file from the filesystem.
    - **Actions**: Deletes row from `image_records`. Constructs the full image file path based on `image_path` field and deletes the file.
    - **Returns**: `True` on success, `False` otherwise.

### Data Import/Export Methods
- **`export_patient_data(self, patient_id, export_dir, include_images=False)`**:
    - **Purpose**: Exports a patient's data (DB records and optionally images) to a specified directory. (Implementation based on outline).
    - **Actions**:
        - Queries DB for patient, all their sessions, and all their image records.
        - Saves DB data to a structured format (e.g., JSON files `patient.json`, `sessions.json`, `images.json`) within `export_dir`.
        - If `include_images` is `True`, copies all associated image files (finding them using `image_path` from DB) into an `images` subdirectory within `export_dir`.
    - **Returns**: `True` on success, `False` otherwise.
- **`import_patient_data(self, import_dir)`**:
    - **Purpose**: Imports patient data from a previously exported directory structure. (Implementation based on outline).
    - **Actions**:
        - Reads structured data files (e.g., `patient.json`, `sessions.json`, `images.json`) from `import_dir`.
        - Checks for conflicts (e.g., existing patient ID). Might need an overwrite/merge strategy or generate new IDs.
        - Inserts data into the corresponding DB tables (`patients`, `treatment_sessions`, `image_records`).
        - Copies image files from the import directory's `images` subdirectory to the appropriate location within the application's `data_dir` structure. Updates `image_path` in DB accordingly if paths change.
    - **Returns**: List of imported patient IDs or indicator of success/failure.

### Reporting Methods
- **`generate_session_report(self, session_id, output_path=None)`**:
    - **Purpose**: Generates a report (e.g., PDF, HTML) summarizing a treatment session. (Implementation based on outline).
    - **Actions**:
        - Queries DB for session details, associated patient info, and image records for the given `session_id`.
        - Formats the data into a report template. Might use libraries like `reportlab` (for PDF) or template engines (`jinja2` for HTML).
        - Includes thumbnails or references to images.
        - Saves the report to `output_path` or returns it.

## 8. `src/hardware/vmpy_camera.py` - Class `VMPyCameraController`

### `__init__(self, vmb, camera_id=None, resolution=None, pixel_format=PixelFormat.Mono8, access_mode=AccessMode.Full)`
- **Purpose**: Initializes controller for an Allied Vision camera using VmbPy.
- **Parameters**: Takes active `VmbSystem`, optional camera ID, resolution, pixel format, and access mode.
- **Actions**: Stores parameters, initializes state variables (`camera=None`, `is_running=False`, `current_frame=None`), creates `frame_lock`. Includes ImportError handling for `vmbpy`.

### `initialize(self) -> bool`
- **Purpose**: Finds, opens, and configures the specified or default camera.
- **Actions**: Gets available cameras via `vmb.get_all_cameras()`. Selects camera based on `camera_id` (matching ID, serial, or model) or defaults to first found. Sets camera access mode. Enters camera context (`with self.camera as cam:`), sets pixel format and resolution (with fallbacks), logs camera info. Handles `VmbCameraError` and other exceptions.
- **Returns**: `True` if successful, `False` otherwise.

### `_frame_handler(self, cam: Camera, stream, frame: Frame)`
- **Purpose**: Internal callback for VmbPy's asynchronous streaming.
- **Actions**: Called by VmbPy for each frame. Checks frame status. If `Complete`: converts frame using `frame.as_opencv_image()`, acquires `frame_lock`, updates `self.current_frame`. Critically, re-queues the frame (`cam.queue_frame(frame)`) in a `finally` block for continuous acquisition. Handles errors during processing or re-queuing.

### `start_stream(self) -> bool`
- **Purpose**: Starts asynchronous frame acquisition.
- **Actions**: Checks if already running or not initialized. Enters camera context. Calls `cam.start_streaming(handler=self._frame_handler, buffer_count=DEFAULT_BUFFER_COUNT)`. Sets `is_running = True`.
- **Returns**: `True` if stream started successfully, `False` otherwise.

### `stop_stream(self) -> bool`
- **Purpose**: Stops asynchronous frame acquisition.
- **Actions**: Checks if running. Sets `is_running = False`. Enters camera context. Calls `cam.stop_streaming()` (explicitly, though context exit might also handle it). Clears `self.current_frame`.
- **Returns**: `True` if successful, `False` otherwise.

### `capture_frame(self) -> np.ndarray | None`
- **Purpose**: Captures a single frame synchronously.
- **Actions**: Checks if initialized. Enters camera context. Calls `cam.get_frame(timeout_ms=2000)`. If frame is `Complete`, converts using `frame.as_opencv_image()`.
- **Returns**: NumPy array of the frame, or `None` on failure/timeout.

### `get_current_frame(self) -> np.ndarray | None`
- **Purpose**: Provides thread-safe access to the latest frame received during streaming.
- **Actions**: Acquires `frame_lock`. Returns a copy of `self.current_frame`.
- **Returns**: Copy of the latest NumPy frame array, or `None`.

### `save_image(self, filepath: str, frame: np.ndarray | None = None) -> bool`
- **Purpose**: Saves a given NumPy frame (or the latest `current_frame`) to a file.
- **Actions**: Uses `cv2.imwrite(filepath, img_to_save)`. Attempts single capture if no frame is available/provided and not streaming.
- **Returns**: `True` on success, `False` otherwise.

### `release(self)`
- **Purpose**: Stops streaming and releases camera resources cleanly.
- **Actions**: Sets internal shutdown flag. Calls `stop_stream()`. Sets `self.camera = None` and `self.vmb = None`.

### `get_available_pixel_formats(self)`
- **Purpose**: Retrieves list of pixel formats supported by the connected camera.
- **Actions**: Checks initialization. Enters camera context. Calls `cam.get_pixel_formats()`. Returns list of format names (as strings). Handles errors.
- **Returns**: List of string representations of supported `PixelFormat`s.

### `save_settings(self, file_path: str) -> bool`
- **Purpose**: Saves the camera's current configuration to an XML file.
- **Actions**: Checks initialization. Enters camera context. Calls `cam.save_settings_to_xml(file_path)`.
- **Returns**: `True` on success, `False` otherwise.

### `load_settings(self, file_path: str) -> bool`
- **Purpose**: Loads camera configuration from an XML file.
- **Actions**: Checks initialization. Enters camera context. Calls `cam.load_settings_from_xml(file_path)`. Attempts to re-read `pixel_format` after loading.
- **Returns**: `True` on success, `False` otherwise.

### `get_feature_value(self, feature_name: str)`
- **Purpose**: Generic method to get the value of any camera feature by name.
- **Actions**: Checks initialization. Enters camera context. Uses `cam.get_feature_by_name(feature_name).get()`.
- **Returns**: Feature value, or `None` on error.

### `set_feature_value(self, feature_name: str, value) -> bool`
- **Purpose**: Generic method to set the value of any camera feature by name.
- **Actions**: Checks initialization. Enters camera context. Uses `cam.get_feature_by_name(feature_name).set(value)`.
- **Returns**: `True` on success, `False` otherwise.


## 9. `src/hardware/laser_controller.py` - Class `LaserController`

### `__init__(self, port=None, baudrate=9600, timeout=1)`
- **Purpose**: Initializes controller for a laser device via serial port.
- **Parameters**: Optional serial port, baudrate, read timeout.
- **Actions**: Stores parameters. Initializes `connection = None`, `connected = False`.

### `list_available_ports(self)`
- **Purpose**: Utility to list available system serial ports.
- **Actions**: Uses `serial.tools.list_ports.comports()`.
- **Returns**: List of port device names (e.g., `['COM1', 'COM3']`).

### `connect(self, port=None)`
- **Purpose**: Establishes and verifies connection to the laser device.
- **Actions**: If `port` is None, iterates through `list_available_ports()`, attempts to open each, calls `_verify_connection()` on it. If verification succeeds, connection is established. If `port` is specified, attempts connection directly and verifies. Calls `_get_device_info()` on success. Handles `serial.SerialException`.
- **Returns**: `True` on successful verified connection, `False` otherwise.

### `disconnect(self)`
- **Purpose**: Closes the serial connection.
- **Actions**: Calls `self.connection.close()`. Resets state variables.
- **Returns**: `True` if disconnected successfully or already disconnected, `False` on error.

### `is_connected(self)`
- **Purpose**: Checks current connection status.
- **Returns**: `True` if `self.connected` is True and `self.connection` is open.

### `send_command(self, command, wait_for_response=True, timeout=1.0)`
- **Purpose**: Sends a formatted command string over the serial connection.
- **Actions**: Checks connection. Appends `\r\n` if needed. Encodes to UTF-8. Writes to serial port. Optionally calls `_read_response()` to get reply. Handles `serial.SerialException`.
- **Returns**: Response string if `wait_for_response` is True and successful, else `None`.

### `_read_response(self, timeout=1.0)`
- **Purpose**: Reads lines from the serial port until a newline or timeout.
- **Actions**: Reads data using `self.connection.readline()` within a timeout loop. Decodes using UTF-8.
- **Returns**: The received response string (stripped), or `None` on timeout/error.

### `_verify_connection(self)`
- **Purpose**: Sends an identification command (`*IDN?`) to confirm communication with the correct device.
- **Actions**: Calls `send_command("*IDN?")`. Checks if response is not None and contains expected identifier (e.g., "TOSCA" - placeholder, actual response needed).
- **Returns**: `True` if verified, `False` otherwise.

### `_get_device_info(self)`
- **Purpose**: Retrieves identification info (manufacturer, model, serial) from the device.
- **Actions**: Sends `*IDN?` command. Parses the response (assuming comma-separated format, needs adjustment for actual device). Stores info in `self.device_info`.
- **Returns**: The `self.device_info` dictionary.

### Device Control Methods (`set_power`, `enable_laser`, `get_status`)
- **Purpose**: Implement high-level laser control actions.
- **Actions**: Format device-specific commands (e.g., `POWER {level:.1f}`, `ENABLE`/`DISABLE`, `STATUS`). Call `send_command()`. Check/parse response to confirm success or extract status information. Log actions. **Note**: Command formats and response parsing are placeholders requiring specific device protocol details.

## 10. `src/hardware/actuator_controller.py` - Class `ActuatorController`

### `__init__(self, port=None, baudrate=115200, timeout=1.0)`
- **Purpose**: Initializes controller for a motion actuator via serial port.
- **Parameters**: Optional serial port, baudrate, read timeout.
- **Actions**: Stores parameters. Initializes `connection = None`, `connected = False`, `current_position = None`, `is_moving = False`. Creates `motion_lock` (threading.Lock).

### `connect(self, port=None)`
- **Purpose**: Establishes and verifies connection to the actuator device.
- **Actions**: If `port` is None, uses `list_ports` to find ports containing "TOSCA_ACTUATOR" or "ACTUATOR" in description. Attempts connection and calls `_verify_connection()`. On success, calls `get_position()` to initialize `current_position`. Handles `serial.SerialException`.
- **Returns**: `True` on successful verified connection, `False` otherwise.

### `disconnect(self)`
- **Purpose**: Closes the serial connection, stopping motion first.
- **Actions**: If `is_moving`, calls `stop()`. Calls `self.connection.close()`. Resets state.
- **Returns**: `True` on success, `False` on error.

### `is_connected(self)`
- **Purpose**: Checks current connection status.
- **Returns**: `True` if connected and connection is open.

### Motion Commands (`home`, `move_to`, `move_relative`, `stop`)
- **Purpose**: Control actuator movement.
- **Actions**:
    - Acquire `self.motion_lock`. Set `self.is_moving = True`.
    - Format and send device-specific commands (e.g., `HOME`, `MOVE X{x} Y{y} Z{z} S{speed}`, `STOP`).
    - **Blocking Wait**: For `home` and `move_to`, after sending command and getting "OK" response, enter a `while self._is_actuator_busy(): time.sleep(0.1)` loop to wait for completion. Includes a timeout check to prevent indefinite blocking.
    - `stop()`: Sends stop command, sets `is_moving = False`, updates position.
    - Update `self.current_position` after move/home/stop.
    - Release `self.motion_lock`. Log actions. Handle errors.
- **Returns**: `True` on success, `False` on failure/timeout.

### Status/Position Methods (`get_position`, `get_status`, `_is_actuator_busy`)
- **Purpose**: Query information from the actuator.
- **Actions**: Send device-specific query commands (e.g., `GET_POS`, `STATUS`, `IS_BUSY?`). Parse response strings (parsing logic is placeholder, needs device details). Update `self.current_position` or `self.is_moving` based on response.
- **Returns**: Position tuple `(x, y, z)`, status dictionary, or busy status (`True`/`False`). Returns `None` on communication failure.

### Internal Methods (`_send_command`, `_verify_connection`)
- **`_send_command`**: Handles sending command (with `\r\n`), reading response line-by-line with timeout. Similar to `LaserController`.
- **`_verify_connection`**: Sends `*IDN?`, checks for "TOSCA" in response (placeholder check).

</rewritten_file>