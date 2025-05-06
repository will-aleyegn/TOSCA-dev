"""
Camera Interface Module

This module provides functionality to interface with the camera on the TOSCA laser device
for image acquisition and basic processing.
"""

import cv2
import numpy as np
import logging
import time
from threading import Thread, Lock

logger = logging.getLogger(__name__)

class CameraController:
    """
    Controller class for interfacing with the TOSCA device camera.
    
    This class provides methods to initialize, capture images from, and manage
    the camera connected to the TOSCA laser device.
    """
    
    def __init__(self, camera_id=0, resolution=(1280, 720), fps=30):
        """
        Initialize the camera controller.
        
        Args:
            camera_id (int or str): Camera identifier (device index or path)
            resolution (tuple): Desired resolution as (width, height)
            fps (int): Desired frames per second
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps
        self.camera = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = Lock()
        self.stream_thread = None
        
    def initialize(self):
        """
        Initialize and configure the camera.
        
        Returns:
            bool: True if camera was successfully initialized, False otherwise
        """
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Check if camera is opened
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera (ID: {self.camera_id})")
                return False
                
            # Read a test frame to verify
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Camera opened but failed to capture test frame")
                self.camera.release()
                self.camera = None
                return False
                
            logger.info(f"Camera initialized successfully (ID: {self.camera_id})")
            actual_resolution = (
                int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            logger.info(f"Camera resolution: {actual_resolution}, FPS: {actual_fps}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {str(e)}")
            if self.camera is not None:
                self.camera.release()
                self.camera = None
            return False
    
    def capture_frame(self):
        """
        Capture a single frame from the camera.
        
        Returns:
            numpy.ndarray or None: The captured frame as an image array, or None if failed
        """
        if self.camera is None or not self.camera.isOpened():
            logger.error("Cannot capture frame: Camera not initialized")
            return None
            
        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.error("Failed to capture frame")
                return None
                
            return frame
            
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
            
        if self.camera is None or not self.camera.isOpened():
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
            bool: True if resources were released successfully, False otherwise
        """
        try:
            # Stop streaming if active
            if self.is_running:
                self.stop_stream()
                
            # Release the camera
            if self.camera is not None:
                self.camera.release()
                self.camera = None
                logger.info("Camera resources released")
                
            return True
            
        except Exception as e:
            logger.error(f"Error releasing camera resources: {str(e)}")
            return False
    
    def _stream_function(self):
        """
        Internal function for continuous frame acquisition in a separate thread.
        """
        while self.is_running:
            try:
                # Capture frame
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    logger.error("Error in stream: Failed to capture frame")
                    time.sleep(0.1)  # Short sleep to prevent CPU hogging
                    continue
                    
                # Update the current frame
                with self.frame_lock:
                    self.current_frame = frame
                    
                # Sleep to maintain frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                logger.error(f"Error in camera stream thread: {str(e)}")
                time.sleep(0.5)  # Longer sleep on error
                
        logger.debug("Camera stream thread terminated")


class ImageProcessor:
    """
    Image processing utilities for TOSCA laser device.
    
    This class provides methods to process images captured from the TOSCA device camera.
    """
    
    @staticmethod
    def detect_treatment_area(image):
        """
        Detect the treatment area in the image.
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            tuple or None: (x, y, width, height) of the detected treatment area, or None if not detected
        """
        # This is a placeholder implementation
        # Replace with actual treatment area detection algorithm for TOSCA device
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold to create binary image
            _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the largest contour (assuming it's the treatment area)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                return (x, y, w, h)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error detecting treatment area: {str(e)}")
            return None
    
    @staticmethod
    def enhance_image(image):
        """
        Enhance the image for better visualization.
        
        Args:
            image (numpy.ndarray): Input image
            
        Returns:
            numpy.ndarray: Enhanced image
        """
        try:
            # Convert to Lab color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Split the Lab image into L, a, and b channels
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l)
            
            # Merge the enhanced L channel with the original a and b channels
            enhanced_lab = cv2.merge([enhanced_l, a, b])
            
            # Convert back to BGR color space
            enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            
            return enhanced_image
            
        except Exception as e:
            logger.error(f"Error enhancing image: {str(e)}")
            return image  # Return original image on error
    
    @staticmethod
    def measure_distance(image, point1, point2):
        """
        Measure the distance between two points in the image (in pixels).
        
        Args:
            image (numpy.ndarray): Input image
            point1 (tuple): First point coordinates (x, y)
            point2 (tuple): Second point coordinates (x, y)
            
        Returns:
            float: Distance in pixels
        """
        try:
            # Calculate Euclidean distance
            distance = np.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)
            return distance
            
        except Exception as e:
            logger.error(f"Error measuring distance: {str(e)}")
            return -1.0
    
    @staticmethod
    def overlay_targeting_grid(image, center=None, grid_size=50, color=(0, 255, 0), thickness=1):
        """
        Overlay a targeting grid on the image.
        
        Args:
            image (numpy.ndarray): Input image
            center (tuple, optional): Grid center (x, y). If None, uses image center.
            grid_size (int): Distance between grid lines in pixels
            color (tuple): Grid color in BGR format
            thickness (int): Line thickness
            
        Returns:
            numpy.ndarray: Image with targeting grid
        """
        try:
            # Create a copy of the input image
            result = image.copy()
            
            # Get image dimensions
            height, width = image.shape[:2]
            
            # If center is not provided, use the image center
            if center is None:
                center = (width // 2, height // 2)
                
            # Draw the center crosshair
            cv2.line(result, (center[0] - 20, center[1]), (center[0] + 20, center[1]), color, thickness)
            cv2.line(result, (center[0], center[1] - 20), (center[0], center[1] + 20), color, thickness)
            
            # Draw concentric circles
            for radius in range(grid_size, max(width, height) // 2, grid_size):
                cv2.circle(result, center, radius, color, thickness)
                
            # Draw radial lines
            for angle in range(0, 360, 30):
                radians = np.deg2rad(angle)
                max_length = max(width, height)
                end_x = int(center[0] + max_length * np.cos(radians))
                end_y = int(center[1] + max_length * np.sin(radians))
                cv2.line(result, center, (end_x, end_y), color, thickness)
                
            return result
            
        except Exception as e:
            logger.error(f"Error overlaying targeting grid: {str(e)}")
            return image  # Return original image on error 