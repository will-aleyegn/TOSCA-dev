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

try:
    from vmbpy import PixelFormat, AccessMode
except ImportError:
    class PixelFormat:
        Mono8 = None
    class AccessMode:
        None_ = 0
        Full = 1
        Read = 2
        Unknown = 4
        Exclusive = 8

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
        
        # Current patient data
        self.current_patient = None
        
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
        
        # Pixel Format selection
        self.pixel_format_combo = QComboBox()
        self.pixel_format_combo.addItem("Auto", None)  # Will populate after camera connect
        camera_row.addWidget(QLabel("Pixel Format:"))
        camera_row.addWidget(self.pixel_format_combo)
        
        # Access Mode selection
        self.access_mode_combo = QComboBox()
        self.access_mode_combo.addItem("Full", AccessMode.Full)
        self.access_mode_combo.addItem("Read", AccessMode.Read)
        self.access_mode_combo.addItem("Exclusive", AccessMode.Exclusive)
        self.access_mode_combo.addItem("None", AccessMode.None_)
        camera_row.addWidget(QLabel("Access Mode:"))
        camera_row.addWidget(self.access_mode_combo)
        
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
        # Save/Load Settings buttons
        settings_row = QHBoxLayout()
        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.clicked.connect(self.on_save_settings)
        self.save_settings_btn.setEnabled(False)
        self.load_settings_btn = QPushButton("Load Settings")
        self.load_settings_btn.clicked.connect(self.on_load_settings)
        self.load_settings_btn.setEnabled(False)
        # Advanced: Show Features button
        self.show_features_btn = QPushButton("Show All Features")
        self.show_features_btn.clicked.connect(self.on_show_features)
        self.show_features_btn.setEnabled(False)
        settings_row.addWidget(self.save_settings_btn)
        settings_row.addWidget(self.load_settings_btn)
        settings_row.addWidget(self.show_features_btn)
        control_layout.addLayout(settings_row)
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
            if self.camera_controller is not None:
                self.on_disconnect_camera()
            camera_id = self.camera_id_combo.currentData()
            # Get selected pixel format and access mode
            pixel_format = self.pixel_format_combo.currentData()
            if pixel_format is None:
                pixel_format = PixelFormat.Mono8  # Default fallback
            access_mode = self.access_mode_combo.currentData()
            if access_mode is None:
                access_mode = AccessMode.Full
            self.camera_controller = VMPyCameraController(
                vmb=self.vmb, camera_id=camera_id,
                pixel_format=pixel_format, access_mode=access_mode
            )
            self.status_label.setText("Connecting to VMPy camera...")
            success = self.camera_controller.initialize()
            if not success:
                QMessageBox.critical(
                    self, "Camera Error", 
                    "Failed to initialize VMPy camera. Check connections and try again."
                )
                self.camera_controller = None
                self.status_label.setText("Camera initialization failed")
                return
            # Populate pixel format combo with available formats
            self.pixel_format_combo.clear()
            formats = self.camera_controller.get_available_pixel_formats()
            for fmt in formats:
                self.pixel_format_combo.addItem(str(fmt), fmt)
            # Set the current pixel format in the combo
            idx = self.pixel_format_combo.findData(self.camera_controller.pixel_format)
            if idx >= 0:
                self.pixel_format_combo.setCurrentIndex(idx)
            # Enable Save/Load Settings buttons
            self.save_settings_btn.setEnabled(True)
            self.load_settings_btn.setEnabled(True)
            self.show_features_btn.setEnabled(True)
            # Set auto exposure and auto gain ON by default (Try 'Continuous')
            auto_on_value = "Continuous" # Common alternative to 'On'
            auto_off_value = "Off"
            try:
                cam = self.camera_controller.camera
                with cam:
                    # Try setting to Continuous first
                    cam.get_feature_by_name("ExposureAuto").set(auto_on_value)
                    cam.get_feature_by_name("GainAuto").set(auto_on_value)
            except Exception as e:
                logger.warning(f"Could not set auto exposure/gain to '{auto_on_value}' on connect: {e}")
                # If 'Continuous' fails, maybe 'On' works on some models? Try that? (Less likely given previous error)
                # Or just default to Off?
                try:
                    with cam:
                         cam.get_feature_by_name("ExposureAuto").set(auto_off_value)
                         cam.get_feature_by_name("GainAuto").set(auto_off_value)
                    logger.info("Defaulting auto exposure/gain to Off after failing to set 'Continuous'")
                except Exception as e2:
                     logger.error(f"Also failed to set auto exposure/gain to Off: {e2}")

            # Update UI elements (reading back values)
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
    
    def set_current_patient(self, patient_data):
        """
        Set the current patient data.
        
        Args:
            patient_data (dict): Patient data dict or None to clear
        """
        self.current_patient = patient_data
        
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
            
            # Determine the output directory and filename
            if self.current_patient:
                # Use patient directory if a patient is loaded
                patient_id = self.current_patient.get('patient_id', 'unknown')
                patient_dir = Path("./data/patients") / patient_id / "images"
                patient_dir.mkdir(exist_ok=True, parents=True)
                
                # Include patient ID in filename
                patient_name = f"{self.current_patient.get('first_name', '')}-{self.current_patient.get('last_name', '')}"
                filename = f"patient_{patient_id}_{patient_name}_{timestamp}_{exp_str}_{gain_str}.png"
                filepath = str(patient_dir / filename)
                
                # Also save the image as the latest for this patient
                latest_filepath = str(patient_dir / f"patient_{patient_id}_latest.png")
            else:
                # Use standard output directory if no patient
                autoexp_str = f"autoExp{auto_exp}" if auto_exp is not None else "autoExpNA"
                autogain_str = f"autoGain{auto_gain}" if auto_gain is not None else "autoGainNA"
                filename = f"capture_{timestamp}_{exp_str}_{gain_str}_{autoexp_str}_{autogain_str}.png"
                output_dir = os.path.join(os.getcwd(), "output")
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, filename)
                latest_filepath = None
                
            # Save the image
            success = self.camera_controller.save_image(filepath, frame)
            
            # Save latest image for patient if applicable
            if success and latest_filepath:
                self.camera_controller.save_image(latest_filepath, frame)
                
            if success:
                self.status_label.setText(f"Image saved to {filepath}")
                
                # Ask if user wants to save this image to the current treatment session
                if self.current_patient:
                    reply = QMessageBox.question(
                        self, "Add to Session",
                        "Do you want to add this image to the current treatment session?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.parent().parent().parent().on_add_image_to_session(filepath)
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
                    exposure_auto = cam.get_feature_by_name("ExposureAuto").get()
                    # Check if the current value indicates 'on' (e.g., not 'Off')
                    is_on = (exposure_auto != "Off") 
                    self.exposure_auto_checkbox.setChecked(is_on)
                except Exception as e:
                    logger.error(f"Error reading ExposureAuto: {e}")
                    self.exposure_auto_checkbox.setChecked(False)
                try:
                    exposure_time = cam.get_feature_by_name("ExposureTime").get()
                    self.exposure_slider.setValue(int(exposure_time))
                    self.exposure_value_label.setText(f"{int(exposure_time):,} us")
                except Exception as e:
                    logger.error(f"Error reading ExposureTime: {e}")
                    pass
                # Gain
                try:
                    gain_auto = cam.get_feature_by_name("GainAuto").get()
                    # Check if the current value indicates 'on' (e.g., not 'Off')
                    is_on = (gain_auto != "Off")
                    self.gain_auto_checkbox.setChecked(is_on)
                except Exception as e:
                    logger.error(f"Error reading GainAuto: {e}")
                    self.gain_auto_checkbox.setChecked(False)
                try:
                    gain = cam.get_feature_by_name("Gain").get()
                    self.gain_slider.setValue(int(gain * 10))
                    self.gain_value_label.setText(f"{gain:.1f} dB")
                except Exception as e:
                    logger.error(f"Error reading Gain: {e}")
                    pass
        except Exception as e:
            logger.error(f"Error updating feature controls from camera: {e}")
    
    def on_exposure_auto_changed(self, state):
        if self.camera_controller and self.camera_controller.camera:
            cam = self.camera_controller.camera
            # Determine target state string (Assume 'Continuous' for On, 'Off' for Off)
            target_state_str = "Continuous" if state else "Off"
            with cam:
                try:
                    cam.get_feature_by_name("ExposureAuto").set(target_state_str)
                    # Read back and update UI
                    actual = cam.get_feature_by_name("ExposureAuto").get()
                    self.exposure_auto_checkbox.setChecked(actual != "Off")
                    if actual != target_state_str:
                        self.status_label.setText(f"Warning: ExposureAuto set to {target_state_str} but read {actual}!")
                        logger.warning(f"ExposureAuto set to {target_state_str} but read back as {actual}")
                except Exception as e:
                    logger.error(f"Failed to set ExposureAuto to {target_state_str}: {e}")
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
             # Determine target state string (Assume 'Continuous' for On, 'Off' for Off)
            target_state_str = "Continuous" if state else "Off"
            with cam:
                try:
                    cam.get_feature_by_name("GainAuto").set(target_state_str)
                    # Read back and update UI
                    actual = cam.get_feature_by_name("GainAuto").get()
                    self.gain_auto_checkbox.setChecked(actual != "Off")
                    if actual != target_state_str:
                        self.status_label.setText(f"Warning: GainAuto set to {target_state_str} but read {actual}!")
                        logger.warning(f"GainAuto set to {target_state_str} but read back as {actual}")
                except Exception as e:
                    logger.error(f"Failed to set GainAuto to {target_state_str}: {e}")
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
    
    def on_save_settings(self):
        if self.camera_controller is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Camera Settings", "settings.xml", "XML Files (*.xml)")
        if file_path:
            success = self.camera_controller.save_settings(file_path)
            if success:
                QMessageBox.information(self, "Success", f"Settings saved to {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save camera settings.")
    
    def on_load_settings(self):
        if self.camera_controller is None:
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Camera Settings", "settings.xml", "XML Files (*.xml)")
        if file_path:
            success = self.camera_controller.load_settings(file_path)
            if success:
                QMessageBox.information(self, "Success", f"Settings loaded from {file_path}")
                self._update_feature_controls_from_camera()
            else:
                QMessageBox.critical(self, "Error", "Failed to load camera settings.")
    
    def on_show_features(self):
        if self.camera_controller is None:
            return
        cam = self.camera_controller.camera
        if cam is None:
            return
        try:
            with cam:
                features = cam.get_all_features()
                feature_texts = []
                for feat in features:
                    try:
                        name = getattr(feat, 'get_name', lambda: str(feat))()
                        value = getattr(feat, 'get', lambda: 'N/A')()
                        feature_texts.append(f"{name}: {value}")
                    except Exception as e:
                        feature_texts.append(f"{str(feat)}: [Error: {e}]")
                text = '\n'.join(feature_texts)
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Camera Features")
                dlg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                dlg.setIcon(QMessageBox.Icon.Information)
                dlg.setText(f"<pre>{text}</pre>")
                dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
                dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve features: {e}")
    
    def closeEvent(self, event):
        """Handle widget close event."""
        # Stop streaming and release camera
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        
        if self.camera_controller is not None:
            self.camera_controller.release()
            self.camera_controller = None
        
        super().closeEvent(event) 