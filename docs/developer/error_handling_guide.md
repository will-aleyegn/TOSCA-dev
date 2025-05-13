# TOSCA Error Handling Guide

This guide provides detailed information on how to use the standardized error handling system in the TOSCA application.

## Overview

The TOSCA application uses a standardized error handling approach defined in `src/utils/error_handling.py`. This approach ensures consistent error reporting, logging, and handling across all components of the application, particularly for hardware-related operations.

## Key Components

### 1. Error Types and Severity Levels

#### Hardware Error Types

```python
class HardwareErrorType(Enum):
    CONNECTION     # Connection errors (failed to connect, disconnected)
    COMMUNICATION  # Communication errors (failed to send/receive)
    TIMEOUT        # Timeout errors (operation took too long)
    PARAMETER      # Parameter errors (invalid parameters)
    STATE          # State errors (invalid state for operation)
    HARDWARE       # Hardware-specific errors (device malfunction)
    UNKNOWN        # Unknown errors
```

#### Error Severity Levels

```python
class ErrorSeverity(Enum):
    INFO       # Informational, non-critical errors
    WARNING    # Warning, operation can continue but with caution
    ERROR      # Error, operation failed but system can continue
    CRITICAL   # Critical error, system stability may be compromised
    FATAL      # Fatal error, system cannot continue
```

### 2. Custom Exception Classes

#### Base Hardware Error

```python
class HardwareError(Exception):
    def __init__(
        self, 
        device_type: str,
        error_type: HardwareErrorType,
        severity: ErrorSeverity,
        message: str,
        original_exception: Optional[Exception] = None
    )
```

#### Device-Specific Errors

- `CameraError`: For camera-related errors
- `ActuatorError`: For actuator-related errors
- `LaserError`: For laser-related errors

### 3. Helper Functions and Decorators

#### Error Handling Decorator

```python
@handle_hardware_errors(
    device_type: str,
    default_return: Any = None,
    rethrow: bool = False,
    error_map: Optional[Dict[Type[Exception], Tuple[HardwareErrorType, ErrorSeverity]]] = None
)
```

#### Try Operation Helper

```python
try_operation(
    operation: Callable,
    device_type: str,
    error_message: str,
    error_type: HardwareErrorType = HardwareErrorType.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    default_return: Any = None,
    rethrow: bool = False,
    *args, **kwargs
) -> Any
```

#### Exception Logging Helper

```python
log_exception(
    logger: logging.Logger,
    message: str,
    exception: Exception,
    level: int = logging.ERROR
) -> None
```

## Best Practices

### 1. Raising Custom Exceptions

When an error occurs in hardware-related code, raise a custom exception with appropriate error type and severity:

```python
# Camera controller example
def connect(self):
    try:
        # Connection code...
    except ConnectionError as e:
        raise CameraError(
            HardwareErrorType.CONNECTION,
            ErrorSeverity.ERROR,
            "Failed to connect to camera",
            e
        )
    except TimeoutError as e:
        raise CameraError(
            HardwareErrorType.TIMEOUT,
            ErrorSeverity.WARNING,
            "Connection timed out",
            e
        )
```

### 2. Using the Error Handling Decorator

Apply the decorator to methods that interact with hardware to automatically handle and log exceptions:

```python
from src.utils.error_handling import handle_hardware_errors, HardwareErrorType, ErrorSeverity

class CameraController:
    @handle_hardware_errors(
        "camera", 
        default_return=False,
        error_map={
            ConnectionError: (HardwareErrorType.CONNECTION, ErrorSeverity.ERROR),
            TimeoutError: (HardwareErrorType.TIMEOUT, ErrorSeverity.WARNING)
        }
    )
    def start_stream(self):
        # Implementation
        return True
```

### 3. Using the Try Operation Helper

For one-off operations or when you need more control over the error handling:

```python
from src.utils.error_handling import try_operation, HardwareErrorType, ErrorSeverity

def capture_image(self):
    # Use try_operation for the camera capture
    frame = try_operation(
        self.camera.capture_frame,
        "camera",
        "Failed to capture image",
        HardwareErrorType.COMMUNICATION,
        ErrorSeverity.ERROR,
        default_return=None
    )
    
    if frame is not None:
        # Process the frame
        return True
    return False
```

### 4. Logging Exceptions

Use the standardized logging helper for consistent log messages:

```python
from src.utils.error_handling import log_exception
import logging

logger = logging.getLogger(__name__)

def process_data(self, data):
    try:
        # Processing code...
    except ValueError as e:
        log_exception(logger, "Invalid data format", e, logging.WARNING)
        return None
```

## Error Handling in GUI Components

GUI components should handle hardware errors gracefully and display appropriate messages to the user:

```python
def on_connect_camera(self):
    try:
        success = self.camera_controller.connect()
        if success:
            self.status_label.setText("Camera connected")
        else:
            self.status_label.setText("Failed to connect camera")
    except CameraError as e:
        QMessageBox.warning(
            self,
            "Camera Connection Error",
            f"Error connecting to camera: {e.message}"
        )
```

## Error Handling in Background Threads

When working with background threads, ensure errors are properly propagated to the main thread:

```python
def _frame_handler(self, cam, stream, frame):
    try:
        # Process frame...
    except Exception as e:
        # Log the error
        log_exception(logger, "Error processing frame", e)
        
        # Signal the error to the main thread
        self.error_signal.emit(str(e))
```

## Common Error Scenarios and Handling

### 1. Connection Errors

```python
try:
    self.connection = serial.Serial(port=self.port, baudrate=self.baudrate)
except serial.SerialException as e:
    raise ActuatorError(
        HardwareErrorType.CONNECTION,
        ErrorSeverity.ERROR,
        f"Failed to connect to port {self.port}",
        e
    )
```

### 2. Timeout Errors

```python
try:
    response = self._send_command("STATUS", timeout=2.0)
    if not response:
        raise LaserError(
            HardwareErrorType.TIMEOUT,
            ErrorSeverity.WARNING,
            "Command timed out, device may be busy"
        )
except Exception as e:
    # Handle other exceptions
```

### 3. State Errors

```python
if not self.is_connected():
    raise ActuatorError(
        HardwareErrorType.STATE,
        ErrorSeverity.ERROR,
        "Cannot move: Not connected to actuator"
    )
```

### 4. Parameter Errors

```python
if position < self.MIN_POSITION or position > self.MAX_POSITION:
    raise ActuatorError(
        HardwareErrorType.PARAMETER,
        ErrorSeverity.ERROR,
        f"Position {position} out of valid range ({self.MIN_POSITION} to {self.MAX_POSITION})"
    )
```

## Error Recovery Strategies

### 1. Automatic Reconnection

```python
def ensure_connected(self):
    if not self.is_connected():
        try:
            logger.info("Attempting to reconnect...")
            return self.connect()
        except HardwareError as e:
            logger.error(f"Reconnection failed: {e}")
            return False
    return True
```

### 2. Graceful Degradation

```python
def capture_image(self):
    try:
        # Try high-resolution capture
        return self.capture_high_res()
    except CameraError as e:
        if e.error_type == HardwareErrorType.HARDWARE:
            logger.warning("Falling back to low-resolution capture")
            try:
                return self.capture_low_res()
            except CameraError:
                return None
        raise
```

### 3. User Notification and Intervention

```python
def handle_critical_error(self, error):
    QMessageBox.critical(
        self,
        "Critical Hardware Error",
        f"A critical error occurred: {error}\n\nThe application may be unstable. Please save your work and restart."
    )
    # Log the error
    logger.critical(f"Critical error: {error}")
    # Disable critical functionality
    self._disable_critical_features()
```

## Conclusion

Following these error handling best practices ensures:

1. **Consistency**: All errors are handled in a standardized way
2. **Traceability**: Errors are properly logged with context
3. **Robustness**: The application can recover from many error conditions
4. **User Experience**: Users receive appropriate feedback when errors occur

By using the provided error handling utilities, you can make the TOSCA application more reliable and maintainable.
