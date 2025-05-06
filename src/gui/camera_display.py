#!/usr/bin/env python3
"""
Camera Display Widget Module

This module provides a PyQt6 widget for displaying camera frames and controls.
"""

import sys
import logging
import time
from pathlib import Path
import cv2
import numpy as np
from threading import Lock
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QCheckBox, QSlider, QGroupBox, QFileDialog, 
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QImage, QPixmap

# Import our camera controllers
from src.hardware.vmpy_camera import VMPyCameraController

logger = logging.getLogger(__name__)

class CameraDisplayWidget(QWidget):
    """
    Widget for displaying camera frames and controlling camera functions.
    This widget only supports the VMPy interface for Allied Vision cameras.
    """
    
    # Signal emitted when a new frame is available
    frame_available = pyqtSignal(np.ndarray)
    
    def __init__(self, parent=None, vmb=None):
        """
        Initialize the camera display widget.
        
        Args:
            parent (QWidget): Parent widget
            vmb (VmbSystem): An active VmbSystem instance (from a context manager)
        """
        super().__init__(parent)
        
        self.vmb = vmb
        self.camera_controller = None
        self.current_frame = None
        self.frame_lock = Lock()
        
        # Frame update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_frame)
        
        # Initialize UI
        self._init_ui()
        
        # Try to initialize camera on startup if auto-connect is checked
        if self.auto_connect_checkbox.isChecked():
            QTimer.singleShot(500, self.on_connect_camera)
    
    def _init_ui(self):
        """Initialize the widget's UI elements."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Camera selection and control panel
        control_panel = QGroupBox("Camera Controls")
        control_layout = QVBoxLayout(control_panel)
        
        # Camera selection row
        camera_row = QHBoxLayout()
        self.camera_id_combo = QComboBox()
        self.camera_id_combo.addItem("Default/Auto-detect", None)
        self.camera_id_combo.addItem("Camera 0", 0)
        self.camera_id_combo.addItem("Camera 1", 1)
        
        self.auto_connect_checkbox = QCheckBox("Auto-connect")
        self.auto_connect_checkbox.setChecked(True)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect_camera)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.on_disconnect_camera)
        self.disconnect_btn.setEnabled(False)
        
        camera_row.addWidget(QLabel("Camera ID:"))
        camera_row.addWidget(self.camera_id_combo)
        camera_row.addWidget(self.auto_connect_checkbox)
        camera_row.addWidget(self.connect_btn)
        camera_row.addWidget(self.disconnect_btn)
        
        control_layout.addLayout(camera_row)
        
        # Capture and display controls
        capture_row = QHBoxLayout()
        
        self.capture_btn = QPushButton("Capture Image")
        self.capture_btn.clicked.connect(self.on_capture_image)
        self.capture_btn.setEnabled(False)
        
        self.start_stream_btn = QPushButton("Start Stream")
        self.start_stream_btn.clicked.connect(self.on_start_stream)
        self.start_stream_btn.setEnabled(False)
        
        self.stop_stream_btn = QPushButton("Stop Stream")
        self.stop_stream_btn.clicked.connect(self.on_stop_stream)
        self.stop_stream_btn.setEnabled(False)
        
        capture_row.addWidget(self.capture_btn)
        capture_row.addWidget(self.start_stream_btn)
        capture_row.addWidget(self.stop_stream_btn)
        
        control_layout.addLayout(capture_row)
        
        # Add control panel to main layout
        layout.addWidget(control_panel)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        self.image_label.setStyleSheet("background-color: black;")
        
        # Add a "No Camera" text to the display
        self.image_label.setText("No Camera Connected")
        self.image_label.setStyleSheet("color: white; background-color: black;")
        
        layout.addWidget(self.image_label)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)
    
    def on_connect_camera(self):
        """Connect to the camera."""
        try:
            # Disconnect existing camera if any
            if self.camera_controller is not None:
                self.on_disconnect_camera()
            
            camera_id = self.camera_id_combo.currentData()
            
            # Create the appropriate camera controller
            self.camera_controller = VMPyCameraController(vmb=self.vmb, camera_id=camera_id)
            self.status_label.setText("Connecting to VMPy camera...")
            
            # Initialize the camera
            success = self.camera_controller.initialize()
            if not success:
                QMessageBox.critical(
                    self, "Camera Error", 
                    "Failed to initialize VMPy camera. Check connections and try again."
                )
                self.camera_controller = None
                self.status_label.setText("Camera initialization failed")
                return
            
            # Update UI elements
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_stream_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            
            self.status_label.setText("VMPy camera connected successfully")
            
            # Optionally start streaming immediately
            self.on_start_stream()
            
        except Exception as e:
            logger.error(f"Error connecting to camera: {str(e)}")
            QMessageBox.critical(
                self, "Camera Error", 
                f"An error occurred while connecting to the camera: {str(e)}"
            )
            self.status_label.setText(f"Error: {str(e)}")
    
    def on_disconnect_camera(self):
        """Disconnect from the camera."""
        if self.camera_controller is not None:
            # Stop streaming if active
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.on_stop_stream()
            
            # Release camera resources
            self.camera_controller.release()
            self.camera_controller = None
            
            # Update UI
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.start_stream_btn.setEnabled(False)
            self.stop_stream_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            
            # Clear display
            self.image_label.setText("No Camera Connected")
            self.image_label.setPixmap(QPixmap())
            
            self.status_label.setText("Camera disconnected")
    
    def on_start_stream(self):
        """Start the camera stream."""
        if self.camera_controller is None:
            return
        
        try:
            # Start camera streaming
            success = self.camera_controller.start_stream()
            if not success:
                logger.error("Failed to start camera stream")
                self.status_label.setText("Failed to start camera stream")
                return
            
            # Start the frame update timer
            self.update_timer.start(33)  # ~30 FPS
            
            # Update UI
            self.start_stream_btn.setEnabled(False)
            self.stop_stream_btn.setEnabled(True)
            
            self.status_label.setText("Camera streaming started")
            
        except Exception as e:
            logger.error(f"Error starting camera stream: {str(e)}")
            self.status_label.setText(f"Streaming error: {str(e)}")
    
    def on_stop_stream(self):
        """Stop the camera stream."""
        if self.camera_controller is None:
            return
        
        try:
            # Stop the update timer
            if self.update_timer.isActive():
                self.update_timer.stop()
            
            # Stop camera streaming
            self.camera_controller.stop_stream()
            
            # Update UI
            self.start_stream_btn.setEnabled(True)
            self.stop_stream_btn.setEnabled(False)
            
            self.status_label.setText("Camera streaming stopped")
            
        except Exception as e:
            logger.error(f"Error stopping camera stream: {str(e)}")
            self.status_label.setText(f"Error stopping stream: {str(e)}")
    
    def on_capture_image(self):
        """Capture a single image and save it to file."""
        if self.camera_controller is None:
            return
        
        try:
            # Capture frame
            frame = None
            
            # If streaming, use the current frame
            if hasattr(self, 'current_frame') and self.current_frame is not None:
                with self.frame_lock:
                    if self.current_frame is not None:
                        frame = self.current_frame.copy()
            
            # If no current frame, capture a new one
            if frame is None:
                frame = self.camera_controller.capture_frame()
            
            if frame is None:
                logger.error("Failed to capture image")
                self.status_label.setText("Failed to capture image")
                return
            
            # Get save location from user
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"capture_{timestamp}.png"
            
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Save Image", suggested_name, "Images (*.png *.jpg)"
            )
            
            if not filepath:
                return  # User cancelled
            
            # Save the image
            success = self.camera_controller.save_image(filepath, frame)
            
            if success:
                self.status_label.setText(f"Image saved to {filepath}")
            else:
                self.status_label.setText("Failed to save image")
            
        except Exception as e:
            logger.error(f"Error capturing image: {str(e)}")
            self.status_label.setText(f"Capture error: {str(e)}")
    
    def _update_frame(self):
        """Update the displayed frame from the camera stream."""
        if self.camera_controller is None:
            return
        
        try:
            # Get current frame from the camera
            frame = self.camera_controller.get_current_frame()
            if frame is None:
                return
            
            # Store the current frame
            with self.frame_lock:
                self.current_frame = frame.copy()
            
            # Convert the frame to QImage
            height, width, channels = frame.shape
            bytes_per_line = channels * width
            
            # Convert BGR to RGB
            if channels >= 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            qt_image = QImage(
                frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
            )
            
            # Resize to fit the label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(qt_image)
            
            # Get the size of the label
            label_size = self.image_label.size()
            
            # Create a scaled pixmap that fits the label size but maintains aspect ratio
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Update the image in the label
            self.image_label.setPixmap(scaled_pixmap)
            
            # Emit the frame available signal with the raw frame
            self.frame_available.emit(self.current_frame)
            
        except Exception as e:
            logger.error(f"Error updating frame: {str(e)}")
            self.status_label.setText(f"Frame update error: {str(e)}")
            self.update_timer.stop()
    
    def closeEvent(self, event):
        """Handle widget close event."""
        # Stop streaming and release camera
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        
        if self.camera_controller is not None:
            self.camera_controller.release()
            self.camera_controller = None
        
        super().closeEvent(event) 