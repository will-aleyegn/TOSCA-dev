#!/usr/bin/env python3
"""
VMPY Camera Controller Module

This module provides functionality to interface with AVT cameras using VmbPy SDK.
"""

import cv2
import numpy as np
import logging
import time
from threading import Thread, Lock
try:
    import vmbpy
    from vmbpy import VmbSystem, VmbCameraError, Camera, Frame, FrameStatus, PixelFormat, AccessMode
except ImportError:
    logging.error("VmbPy module not found. Please install the VmbPy package.")
    # Define dummy classes if VmbPy is not available to avoid runtime errors on import
    class VmbSystem:
        @staticmethod
        def get_instance(): raise ImportError("VmbPy not found")
    class VmbCameraError(Exception): pass
    class Camera: pass
    class Frame: pass
    class FrameStatus: Complete = None
    class PixelFormat: Mono8=None; Bgr8=None # Add others if needed
    class AccessMode:
        None_ = 0
        Full = 1
        Read = 2
        Unknown = 4
        Exclusive = 8

logger = logging.getLogger(__name__)

# Define a default buffer count for streaming
DEFAULT_BUFFER_COUNT = 10

class VMPyCameraController:
    """
    Controller class for interfacing with AVT cameras using VmbPy SDK.

    Uses VmbPy's asynchronous streaming API with a callback.
    """

    # Signal to be potentially connected by the GUI widget to receive frames
    # Note: This requires making this class a QObject if used directly with Qt signals.
    # For simplicity, we'll stick to the get_current_frame() pull method for now.
    # frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, vmb, camera_id=None, resolution=None, pixel_format=PixelFormat.Mono8, access_mode=AccessMode.Full):
        """
        Initialize the camera controller.

        Args:
            vmb (VmbSystem): An active VmbSystem instance (from a context manager)
            camera_id (str): Camera ID or index. If None, first available camera will be used.
            resolution (tuple): Desired resolution (width, height). Applied if possible.
            pixel_format (vmbpy.PixelFormat): Desired pixel format. Defaults to Mono8.
            access_mode (vmbpy.AccessMode): Desired access mode. Defaults to Full.
        """
        if PixelFormat.Mono8 is None and vmb is not None: # Check if VmbPy loaded correctly
            raise ImportError("VmbPy types (PixelFormat) not available.")

        self.vmb = vmb
        self.camera_id = camera_id
        self.resolution = resolution
        self.pixel_format = pixel_format
        self.access_mode = access_mode
        self.camera: Camera | None = None
        self.is_running: bool = False
        self.current_frame: np.ndarray | None = None
        self.frame_lock: Lock = Lock()
        self._shutdown_requested: bool = False # Flag for cleanup

    def initialize(self) -> bool:
        """
        Initialize VmbSystem, find and open the camera, and configure it.

        Returns:
            bool: True if camera was successfully initialized, False otherwise
        """
        if self.vmb is None:
            logger.error("VmbSystem instance not available. Cannot initialize.")
            return False
        if self.camera is not None:
            logger.warning("Camera already initialized.")
            return True

        try:
            available_cameras = self.vmb.get_all_cameras()
            if not available_cameras:
                logger.error("No cameras detected by Vimba SDK.")
                return False

            # Select camera
            found_cam = None
            if self.camera_id is not None:
                for cam in available_cameras:
                    # Check by ID, Serial Number, or Model Name potentially
                    if self.camera_id == cam.get_id() or \
                        self.camera_id == cam.get_serial() or \
                        self.camera_id == cam.get_model():
                        found_cam = cam
                        break
                if not found_cam:
                    logger.error(f"Camera matching ID '{self.camera_id}' not found.")
                    # Attempt to use the first camera as a fallback
                    found_cam = available_cameras[0]
                    logger.warning(f"Falling back to first available camera: {found_cam.get_id()}")
                    # return False # Optional: strict check for ID
                else:
                    logger.info(f"Found specified camera: {found_cam.get_id()}")

            else:
                found_cam = available_cameras[0]
                logger.info(f"Using first available camera: {found_cam.get_id()}")

            self.camera = found_cam

            # Set access mode before opening camera context
            try:
                self.camera.set_access_mode(self.access_mode)
                logger.info(f"Set camera access mode to: {self.access_mode}")
            except Exception as e:
                logger.warning(f"Could not set access mode {self.access_mode}: {e}. Using camera default.")

            with self.camera as cam:
                logger.info(f"Opened camera: {cam.get_id()}")

                # --- Configuration ---
                # Set Pixel Format (important for consistency)
                try:
                    logger.info(f"Setting pixel format to: {self.pixel_format}")
                    cam.set_pixel_format(self.pixel_format)
                except (VmbCameraError, AttributeError, ValueError) as e:
                    logger.warning(f"Could not set pixel format {self.pixel_format}: {e}. Using camera default.")
                    # Store the actual format being used
                    try:
                        self.pixel_format = cam.get_pixel_format()
                        logger.info(f"Camera is using pixel format: {self.pixel_format}")
                    except VmbCameraError:
                        logger.error("Failed to get current pixel format.")


                # Set Resolution (Width/Height) if specified
                if self.resolution is not None:
                    try:
                        cam.Width.set(self.resolution[0])
                        cam.Height.set(self.resolution[1])
                        logger.info(f"Set resolution to {self.resolution[0]}x{self.resolution[1]}")
                    except (VmbCameraError, AttributeError) as e:
                        logger.warning(f"Could not set resolution: {e}. Using camera default.")

                # --- Log Camera Info ---
                try:
                    width = cam.Width.get()
                    height = cam.Height.get()
                    payload = cam.PayloadSize.get()
                    logger.info(f"Camera Info: ID={cam.get_id()}, Model={cam.get_model()}, Serial={cam.get_serial()}")
                    logger.info(f"Resolution: {width}x{height}, PayloadSize: {payload} bytes")
                except (VmbCameraError, AttributeError) as e:
                    logger.warning(f"Could not retrieve full camera info: {e}")

            # If we reach here, initialization was successful.
            # The camera object self.camera remains valid outside the 'with cam:' block
            # until the outer 'with self.vmb:' block exits or release() is called.
            # However, accessing features requires re-entering the camera context.
            return True

        except VmbCameraError as e:
            logger.error(f"Vimba specific error during initialization: {e}")
            self._cleanup() # Clean up partial state
            return False
        except Exception as e:
            logger.error(f"Unexpected error during camera initialization: {e}", exc_info=True)
            self._cleanup() # Clean up partial state
            return False

    def _frame_handler(self, cam: Camera, stream, frame: Frame):
        """Callback function executed for each incoming frame during async streaming. (VmbPy 1.1.0+ requires cam, stream, frame)"""
        try:
            if frame.get_status() == FrameStatus.Complete:
                # Process the completed frame
                opencv_frame = frame.as_opencv_image() # Converts to BGR8 by default if possible

                # Store the frame
                with self.frame_lock:
                    self.current_frame = opencv_frame # Store the converted frame

                # Emit signal if using Qt signals (requires QObject inheritance)
                # self.frame_ready.emit(opencv_frame)

            elif frame.get_status() == FrameStatus.Incomplete:
                logger.warning(f"Received incomplete frame: {frame.get_status()}")
            else:
                logger.error(f"Received frame with error status: {frame.get_status()}")

        except Exception as e:
            logger.error(f"Error processing frame in callback: {e}", exc_info=True)
        finally:
            # CRITICAL: Re-queue the frame for continuous acquisition
            try:
                cam.queue_frame(frame)
            except VmbCameraError as e:
                logger.error(f"Error requeuing frame: {e}. Stopping stream.")
                # Need a way to signal the main thread/widget to stop
                self.stop_stream() # Attempt to stop from callback context (may have issues)
            except Exception as e:
                logger.error(f"Unexpected error requeuing frame: {e}", exc_info=True)


    def start_stream(self) -> bool:
        """Start asynchronous frame acquisition using VmbPy's streaming API."""
        if self.is_running:
            logger.warning("Streaming is already running.")
            return True
        if not self.camera:
            logger.error("Camera not initialized. Cannot start stream.")
            return False

        try:
            # Re-enter camera context to access streaming methods
            with self.camera as cam:
                logger.info("Starting asynchronous stream...")
                cam.start_streaming(handler=self._frame_handler, buffer_count=DEFAULT_BUFFER_COUNT)
                self.is_running = True
                logger.info("Asynchronous stream started.")
                return True
        except VmbCameraError as e:
            logger.error(f"Vimba specific error starting stream: {e}")
            self.is_running = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting stream: {e}", exc_info=True)
            self.is_running = False
            return False

    def stop_stream(self) -> bool:
        """Stop the asynchronous frame acquisition."""
        if not self.is_running:
            # logger.warning("Streaming is not running.") # Can be noisy
            return True
        if not self.camera:
            logger.error("Camera not initialized or already released.")
            return False # Or True depending on desired idempotency

        logger.info("Stopping asynchronous stream...")
        self.is_running = False # Set flag early
        try:
            # Re-enter camera context to access streaming methods
            with self.camera as cam:
                # cam.stop_streaming() should be called automatically when exiting
                # the 'with cam:' block where start_streaming was called,
                # but explicit call is safer for clarity and immediate effect.
                # However, VmbPy examples suggest it's handled by context exit.
                # Let's try relying on the context manager first.
                # If issues arise, uncomment the line below.
                cam.stop_streaming() # Explicit stop
                logger.info("Asynchronous stream stopped.")

        except VmbCameraError as e:
            logger.error(f"Vimba specific error stopping stream: {e}")
            return False
        except Exception as e:
            # Catch potential errors if context is invalid, etc.
            logger.error(f"Unexpected error stopping stream: {e}", exc_info=True)
            return False
        finally:
            # Clear the last frame when stopping
            with self.frame_lock:
                self.current_frame = None

        return True


    def capture_frame(self) -> np.ndarray | None:
        """Capture a single frame synchronously."""
        if self.is_running:
            logger.warning("Capturing single frame while streaming is active. Consider stopping stream first.")
            # Return the latest streamed frame instead?
            # return self.get_current_frame()
        if not self.camera:
            logger.error("Camera not initialized. Cannot capture frame.")
            return None

        logger.info("Capturing single frame...")
        try:
            with self.camera as cam:
                frame = cam.get_frame(timeout_ms=2000) # 2-second timeout
                logger.info(f"Single frame received with status: {frame.get_status()}")
                if frame.get_status() == FrameStatus.Complete:
                    return frame.as_opencv_image()
                else:
                    logger.error(f"Failed to capture complete frame: {frame.get_status()}")
                    return None
        except VmbCameraError as e:
            logger.error(f"Vimba specific error capturing frame: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error capturing frame: {e}", exc_info=True)
            return None

    def get_current_frame(self) -> np.ndarray | None:
        """Get the most recent frame captured during asynchronous streaming."""
        with self.frame_lock:
            if self.current_frame is None:
                return None
            # Return a copy to prevent external modification of the internal buffer
            return self.current_frame.copy()

    def save_image(self, filepath: str, frame: np.ndarray | None = None) -> bool:
        """Save the current or a provided frame to a file."""
        img_to_save = frame if frame is not None else self.get_current_frame()

        if img_to_save is None:
            # Try capturing a single frame if not streaming and no frame provided
            if not self.is_running and frame is None:
                logger.info("No current frame, attempting single capture for save...")
                img_to_save = self.capture_frame()

        if img_to_save is None:
            logger.error("Cannot save image: No frame available.")
            return False

        try:
            success = cv2.imwrite(filepath, img_to_save)
            if success:
                logger.info(f"Image saved successfully to {filepath}")
                return True
            else:
                logger.error(f"Failed to save image to {filepath} using OpenCV.")
                return False
        except Exception as e:
            logger.error(f"Error saving image: {e}", exc_info=True)
            return False

    def release(self):
        """Stop streaming and release camera resources."""
        logger.info("Releasing VMPyCameraController resources...")
        self._shutdown_requested = True # Signal intent to shutdown
        if self.is_running:
            self.stop_stream()

        # The VmbSystem context manager handles VmbApiShutdown when its 'with' block exits.
        # We don't manage VmbSystem context here directly after initialization.
        # We primarily need to ensure the camera object is no longer used.
        self.camera = None # Allow garbage collection
        self.vmb = None    # Release reference to VmbSystem
        logger.info("Camera resources released.")

    def _cleanup(self):
        """Internal cleanup helper."""
        self.camera = None
        self.vmb = None # Release VmbSystem reference

    # Ensure cleanup on deletion
    # def __del__(self):
    #     if not self._shutdown_requested:
    #          logger.warning("VMPyCameraController deleted without explicit release(). Attempting cleanup.")
    #          self.release()

    def _convert_frame_to_opencv(self, frame: Frame) -> np.ndarray | None:
        """Convert VmbPy Frame to OpenCV compatible format (BGR8)."""
        if not frame:
            return None
        try:
            # as_opencv_image tries to convert to BGR8 by default
            return frame.as_opencv_image()
        except VmbCameraError as e:
            logger.error(f"Error converting frame to OpenCV format: {e}")
            # Fallback: try converting to numpy array first
            try:
                img_np = frame.as_numpy_ndarray()
                # Manual conversion might be needed depending on source format
                # Example: If Mono8
                if frame.get_pixel_format() == PixelFormat.Mono8:
                    return cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
                # Add other conversions if necessary (e.g., RGB to BGR)
                else:
                    logger.warning(f"NumPy conversion succeeded, but format {frame.get_pixel_format()} requires manual OpenCV conversion.")
                    return None # Or attempt conversion if format is known
            except Exception as e_np:
                logger.error(f"Fallback NumPy conversion also failed: {e_np}")
                return None
        except Exception as e_generic:
            logger.error(f"Unexpected error during frame conversion: {e_generic}", exc_info=True)
            return None

    def get_available_pixel_formats(self):
        """Get a list of pixel formats supported by the camera."""
        if not self.camera:
            logger.error("Camera not initialized. Cannot get pixel formats.")
            return []
        try:
            # Camera features must be accessed within the camera's context
            with self.camera as cam:
                formats = cam.get_pixel_formats()
                # Convert to string representations if they are VmbPy enum objects for easier use in GUI
                return [str(f) for f in formats] # Example, adjust based on actual VmbPy return type
        except VmbCameraError as e:
            logger.error(f"Vimba specific error getting pixel formats: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting available pixel formats: {e}", exc_info=True)
            return []

    def save_settings(self, file_path: str) -> bool:
        """Save current camera settings to an XML file."""
        if not self.camera:
            logger.error("Camera not initialized. Cannot save settings.")
            return False
        try:
            with self.camera as cam:
                cam.save_settings_to_xml(file_path)
                logger.info(f"Camera settings saved to {file_path}")
                return True
        except VmbCameraError as e:
            logger.error(f"Vimba specific error saving settings: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving settings to {file_path}: {e}", exc_info=True)
            return False

    def load_settings(self, file_path: str) -> bool:
        """Load camera settings from an XML file."""
        if not self.camera:
            logger.error("Camera not initialized. Cannot load settings.")
            return False
        try:
            with self.camera as cam:
                cam.load_settings_from_xml(file_path)
                logger.info(f"Camera settings loaded from {file_path}")
                # After loading settings, internal state like self.pixel_format might need update
                # Also, GUI controls should be refreshed.
                try:
                    self.pixel_format = cam.get_pixel_format()
                    logger.info(f"Pixel format after loading settings: {self.pixel_format}")
                except Exception as e_pf:
                    logger.warning(f"Could not read pixel format after loading settings: {e_pf}")
                return True
        except VmbCameraError as e:
            logger.error(f"Vimba specific error loading settings: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading settings from {file_path}: {e}", exc_info=True)
            return False

    def get_feature_value(self, feature_name: str):
        """Get the value of a camera feature by its name."""
        if not self.camera:
            logger.error(f"Camera not initialized. Cannot get feature {feature_name}.")
            return None
        try:
            with self.camera as cam:
                feature = cam.get_feature_by_name(feature_name)
                return feature.get()
        except VmbCameraError as e:
            logger.error(f"Vimba error getting feature {feature_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting feature {feature_name}: {e}", exc_info=True)
            return None

    def set_feature_value(self, feature_name: str, value) -> bool:
        """Set the value of a camera feature by its name."""
        if not self.camera:
            logger.error(f"Camera not initialized. Cannot set feature {feature_name}.")
            return False
        try:
            with self.camera as cam:
                feature = cam.get_feature_by_name(feature_name)
                feature.set(value)
                logger.info(f"Set feature {feature_name} to {value}")
                return True
        except VmbCameraError as e:
            logger.error(f"Vimba error setting feature {feature_name} to {value}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting feature {feature_name} to {value}: {e}", exc_info=True)
            return False

# Example Usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Test Initialization
    # controller = VMPyCameraController(pixel_format=PixelFormat.Bgr8) # Test BGR
    controller = VMPyCameraController()
    if not controller.initialize():
        print("Failed to initialize camera.")
        exit()

    # # Test Single Frame Capture
    # print("Capturing single frame...")
    # single_frame = controller.capture_frame()
    # if single_frame is not None:
    #     print(f"Captured frame shape: {single_frame.shape}")
    #     cv2.imshow("Single Frame", single_frame)
    #     cv2.waitKey(1000)
    #     cv2.destroyWindow("Single Frame")
    #     controller.save_image("single_capture_test.png", single_frame)
    # else:
    #     print("Failed to capture single frame.")

    # Test Streaming
    print("Starting stream...")
    if controller.start_stream():
        print("Stream started. Press Ctrl+C to stop.")
        try:
            start_time = time.time()
            frame_count = 0
            while True:
                frame = controller.get_current_frame()
                if frame is not None:
                    cv2.imshow("Streaming Frame", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    if key == ord('s'): # Save frame on 's' key
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        filename = f"stream_capture_{timestamp}.png"
                        controller.save_image(filename, frame)

                    frame_count += 1
                else:
                    time.sleep(0.01) # Avoid busy-waiting if no frame yet

                # Stop after 20 seconds for testing
                if time.time() - start_time > 20:
                    print("Stopping test stream after 20s.")
                    break

        except KeyboardInterrupt:
            print("Ctrl+C detected.")
        finally:
            print("Stopping stream...")
            controller.stop_stream()
            cv2.destroyAllWindows()
            print(f"Frames processed during stream: {frame_count}")

    else:
        print("Failed to start stream.")

    # Release resources
    print("Releasing camera...")
    controller.release()
    print("Done.") 