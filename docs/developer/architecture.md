# TOSCA System Architecture

## Overview

The TOSCA (Tissue Optical Scanning and Control Application) is a PyQt6-based application designed for controlling laser devices with integrated camera and actuator functionality. It provides a comprehensive interface for patient management, treatment planning, and hardware control.

## System Components

The application is organized into several key components:

### 1. Core Application

- **Entry Point**: `app.py` - Initializes the application and sets up the environment
- **Main Module**: `src/main.py` - Contains the main application logic and initialization

### 2. User Interface (GUI)

- **Main Window**: `src/gui/main_window.py` - The primary window containing tabs for different functionalities
- **Camera Display**: `src/gui/camera_display.py` - UI for camera control and image capture
- **Actuator Control**: `src/gui/actuator_control.py` - UI for controlling the actuator hardware
- **Patient Forms**: `src/gui/patient_form.py` and `src/gui/session_form.py` - UI for patient data management

### 3. Hardware Interfaces

- **Camera Controller**: `src/hardware/vmpy_camera.py` - Interface to the camera hardware using VmbPy SDK
- **Actuator Controller**: `src/hardware/actuator_controller.py` - Interface to the actuator hardware
- **Laser Controller**: `src/hardware/laser_controller.py` - Interface to the laser hardware
- **Xeryon Integration**: `src/hardware/actuator-control/Xeryon.py` - External library for actuator control

### 4. Data Management

- **Patient Data**: `src/data_io/patient_data.py` - Database management for patient records

### 5. Utilities

- **Error Handling**: `src/utils/error_handling.py` - Standardized error handling mechanisms

## Data Flow

1. **User Interaction**: The user interacts with the GUI components in the main window
2. **Hardware Control**: GUI components communicate with hardware controllers
3. **Data Storage**: Patient and session data is stored in the SQLite database
4. **Image Capture**: Camera images are captured and stored in the patient's directory

## Directory Structure

```
TOSCA-dev/
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py             # Main application logic
│   ├── data_io/            # Data input/output modules
│   │   ├── __init__.py
│   │   └── patient_data.py # Patient database management
│   ├── gui/                # GUI components
│   │   ├── __init__.py
│   │   ├── actuator_control.py
│   │   ├── camera_display.py
│   │   ├── main_window.py
│   │   ├── patient_dialogs.py
│   │   ├── patient_form.py
│   │   └── session_form.py
│   ├── hardware/           # Hardware interface modules
│   │   ├── __init__.py
│   │   ├── actuator_controller.py
│   │   ├── laser_controller.py
│   │   ├── vmpy_camera.py
│   │   └── actuator-control/
│   │       ├── Xeryon.py
│   │       └── xeryon_sequence_builder.py
│   └── utils/              # Utility modules
│       ├── __init__.py
│       └── error_handling.py
├── lib/                    # External libraries
│   └── vmpy/               # VmbPy SDK
├── docs/                   # Documentation
│   ├── developer/          # Developer documentation
│   │   └── architecture.md # This file
│   ├── cti/                # Camera Transport Interface files
│   └── VmbPy_Function_Reference/ # VmbPy documentation
├── data/                   # Application data
│   ├── tosca.db            # SQLite database
│   └── patients/           # Patient data directories
├── logs/                   # Log files
└── reports/                # Reports and screenshots
```

## Error Handling

The application uses a standardized error handling approach defined in `src/utils/error_handling.py`. This module provides:

1. **Custom Exception Classes**:
   - `HardwareError`: Base class for all hardware-related errors
   - `CameraError`: Camera-specific errors
   - `ActuatorError`: Actuator-specific errors
   - `LaserError`: Laser-specific errors

2. **Error Types and Severity Levels**:
   - `HardwareErrorType`: Categorizes errors (CONNECTION, COMMUNICATION, TIMEOUT, etc.)
   - `ErrorSeverity`: Defines severity levels (INFO, WARNING, ERROR, CRITICAL, FATAL)

3. **Helper Functions and Decorators**:
   - `handle_hardware_errors`: Decorator for standardized error handling
   - `try_operation`: Helper function for executing operations with error handling
   - `log_exception`: Standardized exception logging

### Error Handling Best Practices

1. **Use Custom Exception Classes**:
   ```python
   from src.utils.error_handling import CameraError, HardwareErrorType, ErrorSeverity

   # Instead of:
   raise Exception("Failed to connect to camera")

   # Use:
   raise CameraError(
       HardwareErrorType.CONNECTION,
       ErrorSeverity.ERROR,
       "Failed to connect to camera"
   )
   ```

2. **Use the Error Handling Decorator**:
   ```python
   from src.utils.error_handling import handle_hardware_errors

   @handle_hardware_errors("camera", default_return=False)
   def connect_to_camera(self):
       # Implementation
       return True
   ```

3. **Use the Try Operation Helper**:
   ```python
   from src.utils.error_handling import try_operation, HardwareErrorType, ErrorSeverity

   result = try_operation(
       self.camera.start_stream,
       "camera",
       "Failed to start camera stream",
       HardwareErrorType.COMMUNICATION,
       ErrorSeverity.ERROR,
       default_return=False
   )
   ```

## Threading Model

The application uses a combination of the main GUI thread and background threads:

1. **Main Thread**: Handles the GUI and user interactions
2. **Camera Thread**: Handles asynchronous camera streaming
3. **Actuator Thread**: Handles actuator movement sequences

Thread safety is maintained through:
- Locks for shared resources
- Signal/slot connections for thread-safe GUI updates
- QTimer for periodic updates

## Configuration

The application uses several configuration mechanisms:

1. **Environment Variables**: For controlling debug levels and paths
2. **Settings Files**: For hardware-specific settings
3. **Database**: For persistent application data

## Logging

The application uses Python's built-in logging module with:

1. **File Handler**: Logs to `laser_control.log`
2. **Stream Handler**: Logs to the console
3. **Custom Formatting**: Includes timestamp, module name, and log level

## Testing

The application can be tested using:

1. **Unit Tests**: For individual components
2. **Integration Tests**: For hardware interfaces
3. **Manual Testing**: For GUI functionality

## Extending the Application

### Adding a New Hardware Controller

1. Create a new controller class in `src/hardware/`
2. Implement the standard interface methods (connect, disconnect, etc.)
3. Use the standardized error handling approach
4. Create a corresponding UI component in `src/gui/`

### Adding a New GUI Component

1. Create a new widget class in `src/gui/`
2. Add the widget to the main window or appropriate parent widget
3. Connect signals and slots for user interactions
4. Update the main window to include the new component

### Adding a New Database Table

1. Update the `_init_database` method in `src/data_io/patient_data.py`
2. Add corresponding methods for CRUD operations
3. Update the UI to interact with the new data

## Performance Considerations

1. **Image Processing**: Minimize processing in the camera callback to avoid frame drops
2. **Database Operations**: Use transactions for multiple operations
3. **GUI Updates**: Use signals/slots for thread-safe updates
