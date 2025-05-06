"""
Main Window Module

This module defines the main application window for the TOSCA laser control application.
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QStatusBar, QMessageBox, QFileDialog, 
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon, QAction, QPixmap

# Import the camera display widget
from .camera_display import CameraDisplayWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    Main application window for the TOSCA laser device control application.
    """
    
    def __init__(self, vmb=None):
        """Initialize the main window."""
        super().__init__()
        self.vmb = vmb
        
        self.setWindowTitle("TOSCA Laser Control System")
        self.setMinimumSize(1200, 800)
        
        # Set up the UI
        self._create_actions()
        self._create_menus()
        self._create_status_bar()
        self._create_central_widget()
        self._create_connections()
        
        # Initialize hardware controllers
        self._initialize_hardware()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        logger.info("Main window initialized")
    
    def closeEvent(self, event):
        """Handle the window close event."""
        # Ask for confirmation
        reply = QMessageBox.question(
            self, "Confirm Exit",
            "Are you sure you want to exit the application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Disconnect from hardware
            self._shutdown_hardware()
            event.accept()
        else:
            event.ignore()
    
    def _create_actions(self):
        """Create the application actions."""
        # File actions
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Exit the application")
        
        self.new_patient_action = QAction("&New Patient", self)
        self.new_patient_action.setShortcut("Ctrl+N")
        self.new_patient_action.setStatusTip("Create a new patient record")
        
        self.open_patient_action = QAction("&Open Patient", self)
        self.open_patient_action.setShortcut("Ctrl+O")
        self.open_patient_action.setStatusTip("Open an existing patient record")
        
        self.export_data_action = QAction("&Export Data", self)
        self.export_data_action.setStatusTip("Export patient data")
        
        self.import_data_action = QAction("&Import Data", self)
        self.import_data_action.setStatusTip("Import patient data")
        
        # Hardware actions
        self.connect_hardware_action = QAction("&Connect Hardware", self)
        self.connect_hardware_action.setStatusTip("Connect to the TOSCA hardware")
        
        self.disconnect_hardware_action = QAction("&Disconnect Hardware", self)
        self.disconnect_hardware_action.setStatusTip("Disconnect from the TOSCA hardware")
        
        # Camera actions
        self.start_camera_action = QAction("Start &Camera", self)
        self.start_camera_action.setStatusTip("Start the camera feed")
        
        self.stop_camera_action = QAction("Stop C&amera", self)
        self.stop_camera_action.setStatusTip("Stop the camera feed")
        
        self.capture_image_action = QAction("&Capture Image", self)
        self.capture_image_action.setShortcut("Ctrl+I")
        self.capture_image_action.setStatusTip("Capture an image from the camera")
        
        # Help actions
        self.about_action = QAction("&About", self)
        self.about_action.setStatusTip("Show information about the application")
        
        self.help_action = QAction("&Help", self)
        self.help_action.setShortcut("F1")
        self.help_action.setStatusTip("Show the application help")
    
    def _create_menus(self):
        """Create the application menus."""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_patient_action)
        self.file_menu.addAction(self.open_patient_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.export_data_action)
        self.file_menu.addAction(self.import_data_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        
        # Hardware menu
        self.hardware_menu = self.menuBar().addMenu("&Hardware")
        self.hardware_menu.addAction(self.connect_hardware_action)
        self.hardware_menu.addAction(self.disconnect_hardware_action)
        
        # Camera menu
        self.camera_menu = self.menuBar().addMenu("&Camera")
        self.camera_menu.addAction(self.start_camera_action)
        self.camera_menu.addAction(self.stop_camera_action)
        self.camera_menu.addAction(self.capture_image_action)
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.help_action)
        self.help_menu.addAction(self.about_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create status indicators
        self.laser_status = QLabel("Laser: Disconnected")
        self.laser_status.setStyleSheet("color: red;")
        self.laser_status.setMinimumWidth(150)
        
        self.actuator_status = QLabel("Actuator: Disconnected")
        self.actuator_status.setStyleSheet("color: red;")
        self.actuator_status.setMinimumWidth(180)
        
        self.camera_status = QLabel("Camera: Disconnected")
        self.camera_status.setStyleSheet("color: red;")
        self.camera_status.setMinimumWidth(180)
        
        self.patient_status = QLabel("Patient: None")
        self.patient_status.setMinimumWidth(200)
        
        # Add indicators to the status bar
        self.status_bar.addPermanentWidget(self.laser_status)
        self.status_bar.addPermanentWidget(self.actuator_status)
        self.status_bar.addPermanentWidget(self.camera_status)
        self.status_bar.addPermanentWidget(self.patient_status)
        
        # Initial status message
        self.status_bar.showMessage("Application ready")
    
    def _create_central_widget(self):
        """Create the central widget with tabs."""
        # Create the central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create placeholder tabs (will be replaced with actual implementations)
        # These will eventually be replaced with the custom panel widgets
        
        # Patient information tab
        self.patient_tab = QWidget()
        self.tab_widget.addTab(self.patient_tab, "Patient Information")
        
        # Laser control tab
        self.laser_tab = QWidget()
        self.tab_widget.addTab(self.laser_tab, "Laser Control")
        
        # Camera and imaging tab - using our CameraDisplayWidget
        self.camera_tab = QWidget()
        self.camera_tab_layout = QVBoxLayout(self.camera_tab)
        self.camera_display = CameraDisplayWidget(parent=self.camera_tab, vmb=self.vmb)
        self.camera_tab_layout.addWidget(self.camera_display)
        self.tab_widget.addTab(self.camera_tab, "Camera & Imaging")
        
        # Treatment tab
        self.treatment_tab = QWidget()
        self.tab_widget.addTab(self.treatment_tab, "Treatment")
        
        # Quick access buttons at the bottom
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        
        self.connect_btn = QPushButton("Connect Hardware")
        self.start_camera_btn = QPushButton("Start Camera")
        self.capture_btn = QPushButton("Capture Image")
        self.emergency_stop_btn = QPushButton("EMERGENCY STOP")
        self.emergency_stop_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        
        self.button_layout.addWidget(self.connect_btn)
        self.button_layout.addWidget(self.start_camera_btn)
        self.button_layout.addWidget(self.capture_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.emergency_stop_btn)
    
    def _create_connections(self):
        """Connect signals and slots."""
        # File menu actions
        self.exit_action.triggered.connect(self.close)
        self.new_patient_action.triggered.connect(self._on_new_patient)
        self.open_patient_action.triggered.connect(self._on_open_patient)
        self.export_data_action.triggered.connect(self._on_export_data)
        self.import_data_action.triggered.connect(self._on_import_data)
        
        # Hardware menu actions
        self.connect_hardware_action.triggered.connect(self._on_connect_hardware)
        self.disconnect_hardware_action.triggered.connect(self._on_disconnect_hardware)
        
        # Camera menu actions
        self.start_camera_action.triggered.connect(self._on_start_camera)
        self.stop_camera_action.triggered.connect(self._on_stop_camera)
        self.capture_image_action.triggered.connect(self._on_capture_image)
        
        # Help menu actions
        self.about_action.triggered.connect(self._on_about)
        self.help_action.triggered.connect(self._on_help)
        
        # Quick access buttons
        self.connect_btn.clicked.connect(self._on_connect_hardware)
        self.start_camera_btn.clicked.connect(self._on_start_camera)
        self.capture_btn.clicked.connect(self._on_capture_image)
        self.emergency_stop_btn.clicked.connect(self._on_emergency_stop)
    
    def _initialize_hardware(self):
        """Initialize hardware controllers."""
        # This method will be implemented to create instances of
        # the laser controller, actuator controller, and camera controller
        
        # For now, we'll just set some placeholders
        self.laser_controller = None
        self.actuator_controller = None
        
        # Camera controller is now handled by the CameraDisplayWidget
        self.camera_controller = self.camera_display
        
        logger.info("Hardware controllers initialized")
    
    def _shutdown_hardware(self):
        """Shutdown hardware controllers."""
        # Disconnect from all hardware devices
        
        # Disconnect laser
        if hasattr(self, 'laser_controller') and self.laser_controller:
            try:
                self.laser_controller.disconnect()
                logger.info("Laser disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting laser: {str(e)}")
        
        # Disconnect actuator
        if hasattr(self, 'actuator_controller') and self.actuator_controller:
            try:
                self.actuator_controller.disconnect()
                logger.info("Actuator disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting actuator: {str(e)}")
        
        # Camera is handled by the CameraDisplayWidget which has its own cleanup
        
        logger.info("Hardware shutdown complete")
    
    def _update_status(self):
        """Update the status indicators."""
        # Update camera status based on our CameraDisplayWidget
        if hasattr(self, 'camera_display'):
            if self.camera_display.camera_controller is not None:
                self.camera_status.setText("Camera: Connected")
                self.camera_status.setStyleSheet("color: green;")
            else:
                self.camera_status.setText("Camera: Disconnected")
                self.camera_status.setStyleSheet("color: red;")
    
    # Action handlers
    
    def _on_new_patient(self):
        """Handle new patient action."""
        logger.info("New patient action triggered")
        # Will open a dialog to create a new patient
        QMessageBox.information(self, "New Patient", "New patient dialog will be implemented.")
    
    def _on_open_patient(self):
        """Handle open patient action."""
        logger.info("Open patient action triggered")
        # Will open a dialog to select an existing patient
        QMessageBox.information(self, "Open Patient", "Open patient dialog will be implemented.")
    
    def _on_export_data(self):
        """Handle export data action."""
        logger.info("Export data action triggered")
        # Will open a dialog to export patient data
        export_dir = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if export_dir:
            # Will implement data export
            QMessageBox.information(self, "Export Data", f"Data will be exported to {export_dir}")
    
    def _on_import_data(self):
        """Handle import data action."""
        logger.info("Import data action triggered")
        # Will open a dialog to import patient data
        import_dir = QFileDialog.getExistingDirectory(
            self, "Select Import Directory", str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if import_dir:
            # Will implement data import
            QMessageBox.information(self, "Import Data", f"Data will be imported from {import_dir}")
    
    def _on_connect_hardware(self):
        """Handle connect hardware action."""
        logger.info("Connect hardware action triggered")
        # Will connect to all hardware devices
        QMessageBox.information(self, "Connect Hardware", "Hardware connection will be implemented.")
        
        # Update the status indicators when implemented
        # For now just change the text for demonstration
        self.laser_status.setText("Laser: Connected")
        self.laser_status.setStyleSheet("color: green;")
        
        self.actuator_status.setText("Actuator: Connected")
        self.actuator_status.setStyleSheet("color: green;")
        
        # Camera is handled via the CameraDisplayWidget
        
        # Update the button text
        self.connect_btn.setText("Disconnect Hardware")
        # Change the button action
        self.connect_btn.clicked.disconnect()
        self.connect_btn.clicked.connect(self._on_disconnect_hardware)
    
    def _on_disconnect_hardware(self):
        """Handle disconnect hardware action."""
        logger.info("Disconnect hardware action triggered")
        # Will disconnect from all hardware devices
        QMessageBox.information(self, "Disconnect Hardware", "Hardware disconnection will be implemented.")
        
        # Update the status indicators when implemented
        # For now just change the text for demonstration
        self.laser_status.setText("Laser: Disconnected")
        self.laser_status.setStyleSheet("color: red;")
        
        self.actuator_status.setText("Actuator: Disconnected")
        self.actuator_status.setStyleSheet("color: red;")
        
        # Camera is handled via the CameraDisplayWidget
        
        # Update the button text
        self.connect_btn.setText("Connect Hardware")
        # Change the button action
        self.connect_btn.clicked.disconnect()
        self.connect_btn.clicked.connect(self._on_connect_hardware)
    
    def _on_start_camera(self):
        """Handle start camera action."""
        logger.info("Start camera action triggered")
        # Switch to camera tab
        self.tab_widget.setCurrentWidget(self.camera_tab)
        
        # Connect to camera if not already connected
        if self.camera_display.camera_controller is None:
            self.camera_display.on_connect_camera()
        else:
            # Start streaming if not already streaming
            self.camera_display.on_start_stream()
        
        # Update button text
        self.start_camera_btn.setText("Stop Camera")
        # Change button action
        self.start_camera_btn.clicked.disconnect()
        self.start_camera_btn.clicked.connect(self._on_stop_camera)
    
    def _on_stop_camera(self):
        """Handle stop camera action."""
        logger.info("Stop camera action triggered")
        
        # Stop the camera streaming
        if self.camera_display.camera_controller is not None:
            self.camera_display.on_stop_stream()
        
        # Update button text
        self.start_camera_btn.setText("Start Camera")
        # Change button action
        self.start_camera_btn.clicked.disconnect()
        self.start_camera_btn.clicked.connect(self._on_start_camera)
    
    def _on_capture_image(self):
        """Handle capture image action."""
        logger.info("Capture image action triggered")
        
        # Forward to the camera display widget
        if self.camera_display.camera_controller is not None:
            self.camera_display.on_capture_image()
        else:
            QMessageBox.warning(self, "Camera Not Connected", 
                               "Cannot capture image: Camera is not connected.")
    
    def _on_emergency_stop(self):
        """Handle emergency stop action."""
        logger.info("EMERGENCY STOP triggered")
        # Will implement emergency stop functionality
        QMessageBox.critical(self, "EMERGENCY STOP", "Emergency stop functionality will be implemented.")
        
        # Disconnect from all hardware as a safety measure
        self._on_disconnect_hardware()
    
    def _on_about(self):
        """Handle about action."""
        logger.info("About action triggered")
        QMessageBox.about(
            self, "About TOSCA Laser Control System",
            "TOSCA Laser Control System\nVersion 0.1\n\n"
            "A control system for laser-based treatments."
        )
    
    def _on_help(self):
        """Handle help action."""
        logger.info("Help action triggered")
        QMessageBox.information(
            self, "Help", 
            "Help documentation will be implemented."
        ) 