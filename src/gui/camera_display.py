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
import threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QCheckBox, QSlider, QGroupBox, QFileDialog, 
    QSizePolicy, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QImage, QPixmap

# Import our camera controllers
from src.hardware.vmpy_camera import VMPyCameraController

# Only import directly used symbols to avoid initializing VmbSystem at import time
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
        self._frame_update_lock = threading.Lock()
        
        # Current patient data
        self.current_patient = None
        
        # Initialize UI
        self._init_ui()
        
        # Set auto-connect checkbox to false by default now
        self.auto_connect_checkbox.setChecked(False)
        
        # Connect the frame_available signal to the image update slot
        self.frame_available.connect(self._on_frame_available)
    
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
        # self.camera_id_combo.addItem("Default/Auto-detect", None) # Will be populated by _populate_camera_list
        # self.camera_id_combo.addItem("Camera 0", 0) # Remove hardcoded items
        # self.camera_id_combo.addItem("Camera 1", 1) # Remove hardcoded items
        
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
        self.auto_connect_checkbox.setChecked(False)  # Default to false
        
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
        # Exposure controls
        exposure_group = QGroupBox("Exposure")
        exposure_layout = QVBoxLayout(exposure_group)
        
        # Auto exposure checkbox
        self.exposure_auto_checkbox = QCheckBox("Auto Exposure")
        self.exposure_auto_checkbox.stateChanged.connect(self.on_exposure_auto_changed)
        self.exposure_auto_checkbox.setChecked(False)  # Default to manual exposure
        exposure_layout.addWidget(self.exposure_auto_checkbox)
        
        # Exposure slider and input field
        exposure_slider_layout = QHBoxLayout()
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setMinimum(100)  # in microseconds
        self.exposure_slider.setMaximum(1000000)
        self.exposure_slider.setValue(20000)
        self.exposure_slider.setSingleStep(1000)
        self.exposure_slider.setTickInterval(10000)
        self.exposure_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.exposure_slider.valueChanged.connect(self.on_exposure_slider_changed)
        
        self.exposure_input = QLineEdit()
        self.exposure_input.setText("20000")
        self.exposure_input.setFixedWidth(80)
        self.exposure_input.returnPressed.connect(self.on_exposure_input_changed)
        
        exposure_slider_layout.addWidget(QLabel("Exposure:"))
        exposure_slider_layout.addWidget(self.exposure_slider)
        exposure_slider_layout.addWidget(self.exposure_input)
        exposure_slider_layout.addWidget(QLabel("μs"))
        
        exposure_layout.addLayout(exposure_slider_layout)
        feature_row.addWidget(exposure_group)
        
        # Gain controls
        gain_group = QGroupBox("Gain")
        gain_layout = QVBoxLayout(gain_group)
        
        # Auto gain checkbox
        self.gain_auto_checkbox = QCheckBox("Auto Gain")
        self.gain_auto_checkbox.stateChanged.connect(self.on_gain_auto_changed)
        self.gain_auto_checkbox.setChecked(False)  # Default to manual gain
        gain_layout.addWidget(self.gain_auto_checkbox)
        
        # Gain slider and input field
        gain_slider_layout = QHBoxLayout()
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setMinimum(0)
        self.gain_slider.setMaximum(240)
        self.gain_slider.setValue(0)  # Start with gain zero
        self.gain_slider.setSingleStep(1)
        self.gain_slider.setTickInterval(10)
        self.gain_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gain_slider.valueChanged.connect(self.on_gain_slider_changed)
        
        self.gain_input = QLineEdit()
        self.gain_input.setText("0.0")
        self.gain_input.setFixedWidth(80)
        self.gain_input.returnPressed.connect(self.on_gain_input_changed)
        
        gain_slider_layout.addWidget(QLabel("Gain:"))
        gain_slider_layout.addWidget(self.gain_slider)
        gain_slider_layout.addWidget(self.gain_input)
        gain_slider_layout.addWidget(QLabel("dB"))
        
        gain_layout.addLayout(gain_slider_layout)
        feature_row.addWidget(gain_group)
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
        
        # Display area
        display_box = QGroupBox("Camera Preview")
        display_layout = QVBoxLayout(display_box)
        
        self.image_label = QLabel("No camera connected")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setMinimumSize(QSize(640, 480))
        self.image_label.setStyleSheet("background-color: #333333; color: #FFFFFF;")
        
        display_layout.addWidget(self.image_label)
        
        layout.addWidget(display_box)
        
        # Add status label - always create this to ensure the attribute exists
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def _populate_camera_list(self):
        """Populate the camera ID combo box with available cameras."""
        if not self.vmb:
            try:
                from vmbpy import VmbSystem
                self.vmb = VmbSystem.get_instance()
            except ImportError:
                logger.error("VmbPy not installed - camera functionality disabled")
                QMessageBox.critical(self, "Camera Error", 
                                    "VmbPy not installed or not found. Camera functionality disabled.")
                return
            except Exception as e:
                logger.error(f"Error initializing VmbSystem: {str(e)}")
                QMessageBox.critical(self, "Camera Error", 
                                   f"Error initializing camera system: {str(e)}")
                return
        try:
            current_camera_id = self.camera_id_combo.currentData()
            self.camera_id_combo.clear()
            self.camera_id_combo.addItem("Default/Auto-detect", None)
            cameras = self.vmb.get_all_cameras()
            for i, cam in enumerate(cameras):
                self.camera_id_combo.addItem(f"{cam.get_id()} ({cam.get_name()})", cam.get_id())
            if current_camera_id:
                index = self.camera_id_combo.findData(current_camera_id)
                if index >= 0:
                    self.camera_id_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Error populating camera list: {str(e)}")
            QMessageBox.warning(self, "Camera List Error", 
                              f"Error listing available cameras: {str(e)}")
    
    def on_connect_camera(self):
        """Connect to the selected camera."""
        if self.camera_controller is not None:
            logger.warning("Already connected to camera")
            return
        if not self.vmb:
            try:
                from vmbpy import VmbSystem
                self.vmb = VmbSystem.get_instance()
                logger.info("VmbSystem initialized")
            except ImportError:
                logger.error("VmbPy not installed - camera functionality disabled")
                QMessageBox.critical(self, "Camera Error", 
                                    "VmbPy not installed or not found. Camera functionality disabled.")
                return
            except Exception as e:
                logger.error(f"Error initializing VmbSystem: {str(e)}")
                QMessageBox.critical(self, "Camera Error", 
                                   f"Error initializing camera system: {str(e)}")
                return
        try:
            self._populate_camera_list()
            camera_id = self.camera_id_combo.currentData()
            pixel_format = self.pixel_format_combo.currentData()
            access_mode = self.access_mode_combo.currentData()
            self.camera_controller = VMPyCameraController(
                self.vmb, camera_id=camera_id, 
                pixel_format=pixel_format, 
                access_mode=access_mode
            )
            # Set the parent_widget attribute so the controller can notify us
            self.camera_controller.parent_widget = self
            success = self.camera_controller.initialize()
            if not success:
                raise Exception("Failed to initialize camera")
            self.pixel_format_combo.clear()
            available_formats = self.camera_controller.get_available_pixel_formats()
            for fmt in available_formats:
                self.pixel_format_combo.addItem(fmt.name, fmt)
            # Always set to Bgr8 or Mono8 if available
            opencv_compatible = [fmt for fmt in available_formats if fmt.name in ('Bgr8', 'Mono8')]
            if opencv_compatible:
                preferred = opencv_compatible[0]
                if self.camera_controller.pixel_format != preferred:
                    self.camera_controller.pixel_format = preferred
                    self.camera_controller.initialize()
                    idx = self.pixel_format_combo.findText(preferred.name)
                    if idx >= 0:
                        self.pixel_format_combo.setCurrentIndex(idx)
            else:
                logger.error("No OpenCV-compatible pixel format available (Bgr8 or Mono8).")
                QMessageBox.critical(self, "Camera Error", "No OpenCV-compatible pixel format (Bgr8 or Mono8) available.")
                self.on_disconnect_camera()
                return
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.start_stream_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            self.save_settings_btn.setEnabled(True)
            self.load_settings_btn.setEnabled(True)
            self.show_features_btn.setEnabled(True)
            self._update_feature_controls_from_camera()
            if self.auto_connect_checkbox.isChecked():
                self.on_start_stream()
            self.pixel_format_combo.currentIndexChanged.connect(self.on_pixel_format_changed)
            # Log the actual connected camera ID
            if self.camera_controller and self.camera_controller.camera:
                logger.info(f"Connected to camera: {self.camera_controller.camera.get_id()}")
            else:
                logger.info("Connected to camera: None")
        except Exception as e:
            logger.error(f"Error connecting to camera: {str(e)}")
            QMessageBox.warning(self, "Camera Connection Error", 
                              f"Error connecting to camera: {str(e)}")
            if self.camera_controller:
                try:
                    self.camera_controller.release()
                except:
                    pass
                self.camera_controller = None
    
    def on_disconnect_camera(self):
        """Disconnect from the camera."""
        if self.camera_controller is None:
            return
        try:
            # Stop streaming if active
            self.camera_controller.stop_stream()
            self.camera_controller.release()
            self.camera_controller = None
            # Update UI
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.start_stream_btn.setEnabled(False)
            self.stop_stream_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            self.save_settings_btn.setEnabled(False)
            self.load_settings_btn.setEnabled(False)
            self.show_features_btn.setEnabled(False)
            # Reset image label
            self.image_label.setText("No camera connected")
            self.image_label.setPixmap(QPixmap())
            # Disconnect pixel format combo handler to avoid issues
            try:
                self.pixel_format_combo.currentIndexChanged.disconnect(self.on_pixel_format_changed)
            except:
                pass
            logger.info("Disconnected from camera")
        except Exception as e:
            logger.error(f"Error disconnecting from camera: {str(e)}")
            QMessageBox.warning(self, "Camera Disconnection Error", 
                              f"Error disconnecting from camera: {str(e)}")
            # Force cleanup
            self.camera_controller = None
    
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
            self.camera_controller.stop_stream()
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
                # Use a directory within the working directory
                output_dir = os.path.join(os.getcwd(), "data", "captures")
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
        # This method is now obsolete and not used. All updates are signal-based.
        pass
    
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
                    self.exposure_input.setText(str(int(exposure_time)))
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
                    self.gain_input.setText(f"{gain:.1f}")
                except Exception as e:
                    logger.error(f"Error reading Gain: {e}")
                    pass
        except Exception as e:
            logger.error(f"Error updating feature controls from camera: {e}")
    
    def _apply_camera_setting_with_restart(self, setting_func, *args, **kwargs):
        """
        Helper to stop stream, apply a camera setting, and restart if needed.
        setting_func: function to call to apply the setting
        *args, **kwargs: arguments to pass to setting_func
        """
        if self.camera_controller is None:
            return
        was_running = self.camera_controller.is_running
        if was_running:
            self.camera_controller.stop_stream()
        setting_func(*args, **kwargs)
        if was_running:
            self.camera_controller.start_stream()

    def on_pixel_format_changed(self, index):
        if self.camera_controller is None:
            return
        new_format = self.pixel_format_combo.itemData(index)
        if new_format is None:
            return
        def set_pixel_format():
            self.camera_controller.pixel_format = new_format
            self.camera_controller.initialize()
        self._apply_camera_setting_with_restart(set_pixel_format)
        self.status_label.setText("Pixel format changed.")

    # Add similar wrappers for exposure, gain, auto exposure, auto gain
    def on_exposure_auto_changed(self, state):
        def set_exposure_auto():
            cam = self.camera_controller.camera
            target_state_str = "Continuous" if state else "Off"
            with cam:
                try:
                    cam.get_feature_by_name("ExposureAuto").set(target_state_str)
                    actual = cam.get_feature_by_name("ExposureAuto").get()
                    self.exposure_auto_checkbox.setChecked(actual != "Off")
                    if actual != target_state_str:
                        self.status_label.setText(f"Warning: ExposureAuto set to {target_state_str} but read {actual}!")
                        logger.warning(f"ExposureAuto set to {target_state_str} but read back as {actual}")
                except Exception as e:
                    logger.error(f"Failed to set ExposureAuto to {target_state_str}: {e}")
                    self.status_label.setText("Failed to set Auto Exposure")
        self._apply_camera_setting_with_restart(set_exposure_auto)

    def on_exposure_slider_changed(self, value):
        # Update the input field when slider changes
        self.exposure_input.setText(str(value))
        def set_exposure():
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("ExposureTime").set(value)
                    actual = cam.get_feature_by_name("ExposureTime").get()
                    self.exposure_slider.setValue(int(actual))
                    self.exposure_input.setText(str(int(actual)))
                    if int(actual) != value:
                        self.status_label.setText("Warning: Exposure setting not applied!")
                        logger.warning("ExposureTime set to %d but read back as %d", value, int(actual))
                except Exception as e:
                    logger.error(f"Failed to set ExposureTime: {e}")
                    self.status_label.setText("Failed to set Exposure")
        self._apply_camera_setting_with_restart(set_exposure)

    def on_gain_auto_changed(self, state):
        def set_gain_auto():
            cam = self.camera_controller.camera
            target_state_str = "Continuous" if state else "Off"
            with cam:
                try:
                    cam.get_feature_by_name("GainAuto").set(target_state_str)
                    actual = cam.get_feature_by_name("GainAuto").get()
                    self.gain_auto_checkbox.setChecked(actual != "Off")
                    if actual != target_state_str:
                        self.status_label.setText(f"Warning: GainAuto set to {target_state_str} but read {actual}!")
                        logger.warning(f"GainAuto set to {target_state_str} but read back as {actual}")
                except Exception as e:
                    logger.error(f"Failed to set GainAuto to {target_state_str}: {e}")
                    self.status_label.setText("Failed to set Auto Gain")
        self._apply_camera_setting_with_restart(set_gain_auto)

    def on_gain_slider_changed(self, value):
        gain_db = value / 10.0
        # Update the input field when slider changes
        self.gain_input.setText(f"{gain_db:.1f}")
        
        def set_gain():
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("Gain").set(gain_db)
                    actual = cam.get_feature_by_name("Gain").get()
                    self.gain_slider.setValue(int(actual * 10))
                    if abs(actual - gain_db) > 0.05:
                        self.status_label.setText("Warning: Gain setting not applied!")
                        logger.warning("Gain set to %.1f but read back as %.1f", gain_db, actual)
                except Exception as e:
                    logger.error(f"Failed to set Gain: {e}")
                    self.status_label.setText("Failed to set Gain")
        self._apply_camera_setting_with_restart(set_gain)
        
    def on_exposure_input_changed(self):
        """Handle manual input of exposure value"""
        try:
            value = int(self.exposure_input.text())
            if value < self.exposure_slider.minimum():
                value = self.exposure_slider.minimum()
                self.exposure_input.setText(str(value))
            elif value > self.exposure_slider.maximum():
                value = self.exposure_slider.maximum()
                self.exposure_input.setText(str(value))
            
            # Update slider (which will trigger the camera update)
            self.exposure_slider.setValue(value)
        except ValueError:
            # Restore the previous value if input is invalid
            self.exposure_input.setText(str(self.exposure_slider.value()))
            
    def on_gain_input_changed(self):
        """Handle manual input of gain value"""
        try:
            gain_db = float(self.gain_input.text())
            value = int(gain_db * 10)
            
            if value < self.gain_slider.minimum():
                value = self.gain_slider.minimum()
                self.gain_input.setText(f"{value/10.0:.1f}")
            elif value > self.gain_slider.maximum():
                value = self.gain_slider.maximum()
                self.gain_input.setText(f"{value/10.0:.1f}")
            
            # Update slider (which will trigger the camera update)
            self.gain_slider.setValue(value)
        except ValueError:
            # Restore the previous value if input is invalid
            gain_db = self.gain_slider.value() / 10.0
            self.gain_input.setText(f"{gain_db:.1f}")
        def set_gain():
            cam = self.camera_controller.camera
            with cam:
                try:
                    cam.get_feature_by_name("Gain").set(gain_db)
                    actual = cam.get_feature_by_name("Gain").get()
                    self.gain_slider.setValue(int(actual * 10))
                    self.gain_input.setText(f"{actual:.1f}")
                    if abs(actual - gain_db) > 0.05:
                        self.status_label.setText("Warning: Gain setting not applied!")
                        logger.warning("Gain set to %.1f but read back as %.1f", gain_db, actual)
                except Exception as e:
                    logger.error(f"Failed to set Gain: {e}")
                    self.status_label.setText("Failed to set Gain")
        self._apply_camera_setting_with_restart(set_gain)
    
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
        if self.camera_controller is not None:
            self.camera_controller.release()
            self.camera_controller = None
        super().closeEvent(event)

    def _on_frame_available(self, frame):
        """Slot to update the displayed image when a new frame is available."""
        logger.debug(f"_on_frame_available called. Frame shape: {getattr(frame, 'shape', None)}")
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return
        height, width = frame.shape[:2]
        if frame.ndim == 2:
            qt_image = QImage(
                frame.data, width, height, width, QImage.Format.Format_Grayscale8
            )
        elif frame.ndim == 3 and frame.shape[2] == 1:
            frame2d = np.squeeze(frame, axis=2)
            qt_image = QImage(
                frame2d.data, width, height, width, QImage.Format.Format_Grayscale8
            )
        elif frame.ndim == 3 and frame.shape[2] == 3:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bytes_per_line = 3 * width
            qt_image = QImage(
                rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
            )
        else:
            logger.warning("Unsupported frame format for display.")
            return
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

    def notify_new_frame(self, frame):
        """Called by the camera controller when a new frame is available."""
        # This method is thread-safe and emits the signal to the GUI thread
        self.frame_available.emit(frame)
