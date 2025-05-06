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
import os

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
if os.environ.get("TOSCA_DEBUG") == "1":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

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
        
        # --- Camera Feature Controls ---
        feature_row = QHBoxLayout()
        # Exposure
        self.exposure_auto_checkbox = QCheckBox("Auto Exposure")
        self.exposure_auto_checkbox.stateChanged.connect(self.on_exposure_auto_changed)
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setMinimum(100)  # in microseconds
        self.exposure_slider.setMaximum(1000000)
        self.exposure_slider.setValue(20000)
        self.exposure_slider.setSingleStep(1000)
        self.exposure_slider.setTickInterval(10000)
        self.exposure_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.exposure_slider.valueChanged.connect(self.on_exposure_slider_changed)
        self.exposure_value_label = QLabel("20,000 us")
        feature_row.addWidget(self.exposure_auto_checkbox)
        feature_row.addWidget(QLabel("Exposure:"))
        feature_row.addWidget(self.exposure_slider)
        feature_row.addWidget(self.exposure_value_label)
        # Gain
        self.gain_auto_checkbox = QCheckBox("Auto Gain")
        self.gain_auto_checkbox.stateChanged.connect(self.on_gain_auto_changed)
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setMinimum(0)
        self.gain_slider.setMaximum(240)
        self.gain_slider.setValue(10)
        self.gain_slider.setSingleStep(1)
        self.gain_slider.setTickInterval(10)
        self.gain_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gain_slider.valueChanged.connect(self.on_gain_slider_changed)
        self.gain_value_label = QLabel("1.0 dB")
        feature_row.addWidget(self.gain_auto_checkbox)
        feature_row.addWidget(QLabel("Gain:"))
        feature_row.addWidget(self.gain_slider)
        feature_row.addWidget(self.gain_value_label)
        control_layout.addLayout(feature_row)
        # --- End Camera Feature Controls ---
        
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
            # Set auto exposure and auto gain ON by default
            try:
                cam = self.camera_controller.camera
                with cam:
                    cam.get_feature_by_name("ExposureAuto").set_value("On")
                    cam.get_feature_by_name("GainAuto").set_value("On")
            except Exception as e:
                logger.warning(f"Could not set auto exposure/gain on connect: {e}")
            # Update UI elements
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_stream_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            self.status_label.setText("VMPy camera connected successfully")
            # Read and set camera feature UI
            self._update_feature_controls_from_camera()
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
            # Get camera settings for filename
            exposure = gain = None
            auto_exp = auto_gain = None
            try:
                cam = self.camera_controller.camera
                with cam:
                    try:
                        exposure = cam.get_feature_by_name("ExposureTime").get()
                    except Exception:
                        exposure = None
                    try:
                        gain = cam.get_feature_by_name("Gain").get()
                    except Exception:
                        gain = None
                    try:
                        auto_exp = cam.get_feature_by_name("ExposureAuto").get()
                    except Exception:
                        auto_exp = None
                    try:
                        auto_gain = cam.get_feature_by_name("GainAuto").get()
                    except Exception:
                        auto_gain = None
            except Exception:
                pass
            # Build output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            exp_str = f"exp{int(exposure)}us" if exposure is not None else "expNA"
            gain_str = f"gain{gain:.1f}dB" if gain is not None else "gainNA"
            autoexp_str = f"autoExp{auto_exp}" if auto_exp is not None else "autoExpNA"
            autogain_str = f"autoGain{auto_gain}" if auto_gain is not None else "autoGainNA"
            filename = f"capture_{timestamp}_{exp_str}_{gain_str}_{autoexp_str}_{autogain_str}.png"
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
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
            if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
                return
            # Store the current frame
            with self.frame_lock:
                self.current_frame = frame.copy()
            # Convert the frame to QImage
            height, width = frame.shape[:2]
            if frame.ndim == 2:
                # Grayscale
                qt_image = QImage(
                    frame.data, width, height, width, QImage.Format.Format_Grayscale8
                )
            elif frame.ndim == 3 and frame.shape[2] == 1:
                # Grayscale with singleton channel
                frame2d = np.squeeze(frame, axis=2)
                qt_image = QImage(
                    frame2d.data, width, height, width, QImage.Format.Format_Grayscale8
                )
            elif frame.ndim == 3 and frame.shape[2] == 3:
                # BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = 3 * width
                qt_image = QImage(
                    rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
                )
            else:
                logger.warning("Unsupported frame format for display.")
                return
            # Resize to fit the label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(qt_image)
            if pixmap.isNull():
                logger.warning("QPixmap is null, not displaying.")
                return
            label_size = self.image_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size, 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.frame_available.emit(self.current_frame)
        except Exception as e:
            logger.error(f"Error updating frame: {str(e)}")
            self.status_label.setText(f"Frame update error: {str(e)}")
            self.update_timer.stop()
    
    def _update_feature_controls_from_camera(self):
        """Read camera feature values and update UI controls."""
        try:
            cam = self.camera_controller.camera
            with cam:
                # Exposure
                try:
                    exposure_auto = cam.get_feature_by_name("ExposureAuto").get_value()
                    self.exposure_auto_checkbox.setChecked(exposure_auto == "On")
                except Exception:
                    self.exposure_auto_checkbox.setChecked(False)
                try:
                    exposure_time = cam.get_feature_by_name("ExposureTime").get()
                    self.exposure_slider.setValue(int(exposure_time))
                    self.exposure_value_label.setText(f"{int(exposure_time):,} us")
                except Exception:
                    pass
                # Gain
                try:
                    gain_auto = cam.get_feature_by_name("GainAuto").get_value()
                    self.gain_auto_checkbox.setChecked(gain_auto == "On")
                except Exception:
                    self.gain_auto_checkbox.setChecked(False)
                try:
                    gain = cam.get_feature_by_name("Gain").get()
                    self.gain_slider.setValue(int(gain * 10))
                    self.gain_value_label.setText(f"{gain:.1f} dB")
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error updating feature controls from camera: {e}")
    
    def on_exposure_auto_changed(self, state):
        if self.camera_controller and self.camera_controller.camera:
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("ExposureAuto").set_value("On" if state else "Off")
                    # Read back and update UI
                    actual = cam.get_feature_by_name("ExposureAuto").get_value()
                    self.exposure_auto_checkbox.setChecked(actual == "On")
                    if (actual == "On") != bool(state):
                        self.status_label.setText("Warning: ExposureAuto setting not applied!")
                        logger.warning("ExposureAuto set to %s but read back as %s", "On" if state else "Off", actual)
                except Exception as e:
                    logger.error(f"Failed to set ExposureAuto: {e}")
                    self.status_label.setText("Failed to set Auto Exposure")
    
    def on_exposure_slider_changed(self, value):
        self.exposure_value_label.setText(f"{value:,} us")
        if self.camera_controller and self.camera_controller.camera:
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("ExposureTime").set(value)
                    # Read back and update UI
                    actual = cam.get_feature_by_name("ExposureTime").get()
                    self.exposure_slider.setValue(int(actual))
                    self.exposure_value_label.setText(f"{int(actual):,} us")
                    if int(actual) != value:
                        self.status_label.setText("Warning: Exposure setting not applied!")
                        logger.warning("ExposureTime set to %d but read back as %d", value, int(actual))
                except Exception as e:
                    logger.error(f"Failed to set ExposureTime: {e}")
                    self.status_label.setText("Failed to set Exposure")
    
    def on_gain_auto_changed(self, state):
        if self.camera_controller and self.camera_controller.camera:
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("GainAuto").set_value("On" if state else "Off")
                    # Read back and update UI
                    actual = cam.get_feature_by_name("GainAuto").get_value()
                    self.gain_auto_checkbox.setChecked(actual == "On")
                    if (actual == "On") != bool(state):
                        self.status_label.setText("Warning: GainAuto setting not applied!")
                        logger.warning("GainAuto set to %s but read back as %s", "On" if state else "Off", actual)
                except Exception as e:
                    logger.error(f"Failed to set GainAuto: {e}")
                    self.status_label.setText("Failed to set Auto Gain")
    
    def on_gain_slider_changed(self, value):
        gain_db = value / 10.0
        self.gain_value_label.setText(f"{gain_db:.1f} dB")
        if self.camera_controller and self.camera_controller.camera:
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("Gain").set(gain_db)
                    # Read back and update UI
                    actual = cam.get_feature_by_name("Gain").get()
                    self.gain_slider.setValue(int(actual * 10))
                    self.gain_value_label.setText(f"{actual:.1f} dB")
                    if abs(actual - gain_db) > 0.05:
                        self.status_label.setText("Warning: Gain setting not applied!")
                        logger.warning("Gain set to %.1f but read back as %.1f", gain_db, actual)
                except Exception as e:
                    logger.error(f"Failed to set Gain: {e}")
                    self.status_label.setText("Failed to set Gain")
    
    def closeEvent(self, event):
        """Handle widget close event."""
        # Stop streaming and release camera
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        
        if self.camera_controller is not None:
            self.camera_controller.release()
            self.camera_controller = None
        
        super().closeEvent(event) 