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
except ImportError:
    logging.error("VmbPy module not found. Please install the VmbPy package.")

logger = logging.getLogger(__name__)

class VMPyCameraController:
    """
    Controller class for interfacing with AVT cameras using VmbPy SDK.
    
    This class provides methods to initialize, capture images from, and manage
    cameras connected via the Vimba SDK.
    """
    
    def __init__(self, camera_id=None, resolution=None, fps=30):
        """
        Initialize the camera controller.
        
        Args:
            camera_id (str): Camera ID or index. If None, first available camera will be used.
            resolution (tuple): Desired resolution as (width, height). If None, use camera default.
            fps (int): Desired frames per second
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps
        self.camera = None
        self.vmb = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = Lock()
        self.stream_thread = None
        
    def initialize(self):
        """
        Initialize and configure the camera using Vimba SDK.
        
        Returns:
            bool: True if camera was successfully initialized, False otherwise
        """
        try:
            # Get Vimba instance
            self.vmb = vmbpy.VmbSystem.get_instance()
            with self.vmb:
                # List available cameras
                available_cameras = self.vmb.get_all_cameras()
                
                if not available_cameras:
                    logger.error("No cameras detected by Vimba SDK")
                    return False
                
                # Select camera either by ID or first available
                if self.camera_id is not None:
                    # Find camera by ID
                    self.camera = next((cam for cam in available_cameras 
                                      if self.camera_id in cam.get_id()), None)
                    if not self.camera:
                        logger.error(f"Camera with ID '{self.camera_id}' not found")
                        return False
                else:
                    # Use first available camera
                    self.camera = available_cameras[0]
                    logger.info(f"Using first available camera: {self.camera.get_id()}")
                
                # Open the camera
                with self.camera:
                    # Set camera features if resolution is specified
                    if self.resolution is not None:
                        try:
                            self.camera.get_feature_by_name("Width").set_value(self.resolution[0])
                            self.camera.get_feature_by_name("Height").set_value(self.resolution[1])
                        except Exception as e:
                            logger.warning(f"Could not set resolution: {str(e)}")
                    
                    # Print camera info
                    logger.info(f"Camera initialized: {self.camera.get_id()}")
                    
                    # Try to get camera info
                    try:
                        width = self.camera.get_feature_by_name("Width").get_value()
                        height = self.camera.get_feature_by_name("Height").get_value()
                        logger.info(f"Camera resolution: {width}x{height}")
                    except Exception as e:
                        logger.warning(f"Could not get camera resolution: {str(e)}")
                        
                return True
                
        except Exception as e:
            logger.error(f"Error initializing Vimba camera: {str(e)}")
            self.camera = None
            self.vmb = None
            return False
    
    def capture_frame(self):
        """
        Capture a single frame from the camera.
        
        Returns:
            numpy.ndarray or None: The captured frame as an image array, or None if failed
        """
        if self.camera is None or self.vmb is None:
            logger.error("Cannot capture frame: Camera not initialized")
            return None
            
        try:
            with self.vmb:
                with self.camera:
                    # Get a frame
                    frame = self.camera.get_frame()
                    # Convert to OpenCV format
                    opencv_image = self._convert_frame_to_opencv(frame)
                    return opencv_image
                    
        except Exception as e:
            logger.error(f"Error capturing frame: {str(e)}")
            return None
    
    def start_stream(self):
        """
        Start continuous frame acquisition in a separate thread.
        
        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Camera streaming is already running")
            return True
            
        if self.camera is None or self.vmb is None:
            logger.error("Cannot start streaming: Camera not initialized")
            return False
            
        # Start the streaming thread
        self.is_running = True
        self.stream_thread = Thread(target=self._stream_function)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        logger.info("Camera streaming started")
        return True
    
    def stop_stream(self):
        """
        Stop the continuous frame acquisition.
        
        Returns:
            bool: True if streaming was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Camera streaming is not running")
            return True
            
        self.is_running = False
        if self.stream_thread is not None:
            self.stream_thread.join(timeout=1.0)
            self.stream_thread = None
            
        logger.info("Camera streaming stopped")
        return True
    
    def get_current_frame(self):
        """
        Get the most recent frame captured during streaming.
        
        Returns:
            numpy.ndarray or None: The most recent frame, or None if no frame is available
        """
        with self.frame_lock:
            if self.current_frame is None:
                return None
            return self.current_frame.copy()
    
    def save_image(self, filepath, frame=None):
        """
        Save the current frame or a provided frame to a file.
        
        Args:
            filepath (str): Path where to save the image
            frame (numpy.ndarray, optional): Frame to save. If None, captures a new frame.
            
        Returns:
            bool: True if image was saved successfully, False otherwise
        """
        try:
            # If no frame provided, capture one
            if frame is None:
                frame = self.capture_frame()
                
            if frame is None:
                logger.error("Cannot save image: No frame available")
                return False
                
            # Save the image
            result = cv2.imwrite(filepath, frame)
            if result:
                logger.info(f"Image saved successfully to {filepath}")
                return True
            else:
                logger.error(f"Failed to save image to {filepath}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return False
    
    def release(self):
        """
        Release the camera resources.
        
        Returns:
            bool: True if the resources were released successfully, False otherwise
        """
        if self.is_running:
            self.stop_stream()
            
        self.camera = None
        self.vmb = None
        logger.info("Camera resources released")
        return True
    
    def _stream_function(self):
        """Background thread function for continuous frame capture."""
        try:
            with self.vmb:
                with self.camera:
                    # Create frame handler and start acquisition
                    handler = self._create_frame_handler()
                    
                    try:
                        # Start streaming
                        self.camera.start_streaming(handler=handler)
                        logger.info(f"Camera streaming started on {self.camera.get_id()}")
                        
                        while self.is_running:
                            # Sleep to avoid busy waiting
                            time.sleep(0.01)
                            
                        # Stop streaming
                        self.camera.stop_streaming()
                        logger.info(f"Camera streaming stopped on {self.camera.get_id()}")
                        
                    except Exception as e:
                        logger.error(f"Error during streaming: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error in camera streaming thread: {str(e)}")
            self.is_running = False
    
    def _create_frame_handler(self):
        """Create a frame handler for the continuous acquisition."""
        def frame_callback(camera, frame):
            try:
                # Process the frame
                opencv_frame = self._convert_frame_to_opencv(frame)
                if opencv_frame is not None:
                    # Update the current frame
                    with self.frame_lock:
                        self.current_frame = opencv_frame
                
                # Queue the frame
                try:
                    camera.queue_frame(frame)
                except Exception as e:
                    logger.error(f"Error queuing frame: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Error in frame callback: {str(e)}")
                # Try to queue the frame anyway to avoid losing frames
                try:
                    camera.queue_frame(frame)
                except:
                    pass
        
        return frame_callback
    
    def _convert_frame_to_opencv(self, frame):
        """
        Convert a VmbPy frame to an OpenCV image.
        
        Args:
            frame (vmbpy.Frame): The frame to convert
            
        Returns:
            numpy.ndarray: The converted frame as an OpenCV image
        """
        try:
            # Try to convert using as_opencv_image if available
            if hasattr(frame, 'as_opencv_image'):
                image = frame.as_opencv_image()
                return image
            # Fall back to numpy array conversion
            elif hasattr(frame, 'as_numpy_array'):
                image = frame.as_numpy_array()
                return image
            else:
                logger.error("Frame object doesn't support conversion to OpenCV image or numpy array")
                return None
        except Exception as e:
            logger.error(f"Error converting frame to OpenCV format: {str(e)}")
            return None 