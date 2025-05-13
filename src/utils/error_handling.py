"""
Standardized Error Handling Module

This module provides standardized error handling mechanisms for the TOSCA application,
including custom exceptions, error logging, and helper functions for consistent
error handling across all hardware controllers.
"""

import logging
import traceback
import functools
from enum import Enum, auto
from typing import Optional, Callable, Any, Dict, Type, Union

# Configure logger
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Enumeration for error severity levels."""
    INFO = auto()       # Informational, non-critical errors
    WARNING = auto()    # Warning, operation can continue but with caution
    ERROR = auto()      # Error, operation failed but system can continue
    CRITICAL = auto()   # Critical error, system stability may be compromised
    FATAL = auto()      # Fatal error, system cannot continue

class HardwareErrorType(Enum):
    """Enumeration for hardware error types."""
    CONNECTION = auto()     # Connection errors (failed to connect, disconnected)
    COMMUNICATION = auto()  # Communication errors (failed to send/receive)
    TIMEOUT = auto()        # Timeout errors (operation took too long)
    PARAMETER = auto()      # Parameter errors (invalid parameters)
    STATE = auto()          # State errors (invalid state for operation)
    HARDWARE = auto()       # Hardware-specific errors (device malfunction)
    UNKNOWN = auto()        # Unknown errors

class HardwareError(Exception):
    """
    Base exception class for all hardware-related errors.
    
    Attributes:
        device_type (str): Type of device that caused the error (e.g., "camera", "actuator")
        error_type (HardwareErrorType): Type of error that occurred
        severity (ErrorSeverity): Severity level of the error
        message (str): Error message
        original_exception (Exception, optional): Original exception that caused this error
    """
    
    def __init__(
        self, 
        device_type: str,
        error_type: HardwareErrorType,
        severity: ErrorSeverity,
        message: str,
        original_exception: Optional[Exception] = None
    ):
        self.device_type = device_type
        self.error_type = error_type
        self.severity = severity
        self.message = message
        self.original_exception = original_exception
        
        # Construct the full error message
        full_message = f"[{device_type.upper()}] {error_type.name} error: {message}"
        if original_exception:
            full_message += f" (Caused by: {type(original_exception).__name__}: {str(original_exception)})"
            
        super().__init__(full_message)
        
        # Log the error based on severity
        self._log_error()
        
    def _log_error(self):
        """Log the error with the appropriate severity level."""
        log_message = f"{self.device_type.upper()} {self.error_type.name} error: {self.message}"
        
        if self.severity == ErrorSeverity.INFO:
            logger.info(log_message)
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        elif self.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif self.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif self.severity == ErrorSeverity.FATAL:
            logger.critical(f"FATAL: {log_message}")
        
        # Log stack trace for ERROR and above
        if self.severity.value >= ErrorSeverity.ERROR.value and self.original_exception:
            logger.error(f"Original exception: {traceback.format_exc()}")

# Specific hardware error classes
class CameraError(HardwareError):
    """Exception class for camera-related errors."""
    
    def __init__(
        self,
        error_type: HardwareErrorType,
        severity: ErrorSeverity,
        message: str,
        original_exception: Optional[Exception] = None
    ):
        super().__init__("camera", error_type, severity, message, original_exception)

class ActuatorError(HardwareError):
    """Exception class for actuator-related errors."""
    
    def __init__(
        self,
        error_type: HardwareErrorType,
        severity: ErrorSeverity,
        message: str,
        original_exception: Optional[Exception] = None
    ):
        super().__init__("actuator", error_type, severity, message, original_exception)

class LaserError(HardwareError):
    """Exception class for laser-related errors."""
    
    def __init__(
        self,
        error_type: HardwareErrorType,
        severity: ErrorSeverity,
        message: str,
        original_exception: Optional[Exception] = None
    ):
        super().__init__("laser", error_type, severity, message, original_exception)

# Error handling decorators
def handle_hardware_errors(
    device_type: str,
    default_return: Any = None,
    rethrow: bool = False,
    error_map: Optional[Dict[Type[Exception], Tuple[HardwareErrorType, ErrorSeverity]]] = None
):
    """
    Decorator for handling hardware-related errors in a standardized way.
    
    Args:
        device_type (str): Type of device (e.g., "camera", "actuator")
        default_return (Any, optional): Default return value if an error occurs
        rethrow (bool, optional): Whether to rethrow the error after handling
        error_map (Dict, optional): Mapping from exception types to (error_type, severity) tuples
        
    Returns:
        Callable: Decorated function
    """
    if error_map is None:
        error_map = {}
        
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HardwareError as e:
                # Already a HardwareError, just re-raise if needed
                if rethrow:
                    raise
                return default_return
            except Exception as e:
                # Map the exception to a HardwareError
                error_type, severity = error_map.get(
                    type(e), 
                    (HardwareErrorType.UNKNOWN, ErrorSeverity.ERROR)
                )
                
                # Create the appropriate hardware error
                if device_type == "camera":
                    hardware_error = CameraError(error_type, severity, str(e), e)
                elif device_type == "actuator":
                    hardware_error = ActuatorError(error_type, severity, str(e), e)
                elif device_type == "laser":
                    hardware_error = LaserError(error_type, severity, str(e), e)
                else:
                    hardware_error = HardwareError(device_type, error_type, severity, str(e), e)
                
                if rethrow:
                    raise hardware_error
                    
                return default_return
                
        return wrapper
    return decorator

# Helper functions for common error handling patterns
def try_operation(
    operation: Callable,
    device_type: str,
    error_message: str,
    error_type: HardwareErrorType = HardwareErrorType.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    default_return: Any = None,
    rethrow: bool = False,
    *args, **kwargs
) -> Any:
    """
    Try to execute an operation with standardized error handling.
    
    Args:
        operation (Callable): Function to execute
        device_type (str): Type of device (e.g., "camera", "actuator")
        error_message (str): Error message if the operation fails
        error_type (HardwareErrorType, optional): Type of error
        severity (ErrorSeverity, optional): Severity level of the error
        default_return (Any, optional): Default return value if an error occurs
        rethrow (bool, optional): Whether to rethrow the error after handling
        *args, **kwargs: Arguments to pass to the operation
        
    Returns:
        Any: Result of the operation or default_return if an error occurs
    """
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        # Create the appropriate hardware error
        if device_type == "camera":
            hardware_error = CameraError(error_type, severity, f"{error_message}: {str(e)}", e)
        elif device_type == "actuator":
            hardware_error = ActuatorError(error_type, severity, f"{error_message}: {str(e)}", e)
        elif device_type == "laser":
            hardware_error = LaserError(error_type, severity, f"{error_message}: {str(e)}", e)
        else:
            hardware_error = HardwareError(device_type, error_type, severity, f"{error_message}: {str(e)}", e)
        
        if rethrow:
            raise hardware_error
            
        return default_return

def log_exception(
    logger: logging.Logger,
    message: str,
    exception: Exception,
    level: int = logging.ERROR
) -> None:
    """
    Log an exception with a custom message at the specified level.
    
    Args:
        logger (logging.Logger): Logger to use
        message (str): Message to log
        exception (Exception): Exception to log
        level (int, optional): Logging level
    """
    logger.log(level, f"{message}: {str(exception)}")
    if level >= logging.ERROR:
        logger.log(level, f"Exception details: {traceback.format_exc()}")
