"""
Treatment Session Form Module

This module provides a form for managing patient treatment sessions.
"""

import os
import uuid
import logging
import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QDateEdit, QComboBox, QTextEdit, QPushButton, QGroupBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QScrollArea,
    QSplitter, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.data_io.patient_data import PatientDataManager

logger = logging.getLogger(__name__)

class SessionFormWidget(QWidget):
    """
    Widget for managing patient treatment sessions.
    """
    
    # Signal emitted when a session is created/updated
    session_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, data_dir="./data"):
        """Initialize the session form widget."""
        super().__init__(parent)
        
        # Initialize data manager
        self.data_manager = PatientDataManager(data_dir)
        
        # Current patient and session data
        self.current_patient = None
        self.current_session = None
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create a splitter for sessions list and session details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Session list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Title for sessions
        title_label = QLabel("Treatment Sessions")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(title_label)
        
        # Sessions table
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(3)
        self.sessions_table.setHorizontalHeaderLabels(["Date", "ID", "Notes"])
        self.sessions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.sessions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.sessions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.clicked.connect(self._on_session_selected)
        
        left_layout.addWidget(self.sessions_table)
        
        # Buttons for sessions list
        btn_layout = QHBoxLayout()
        self.new_session_btn = QPushButton("New Session")
        self.new_session_btn.clicked.connect(self._on_new_session)
        
        self.view_session_btn = QPushButton("View Session")
        self.view_session_btn.clicked.connect(self._on_view_session)
        
        btn_layout.addWidget(self.new_session_btn)
        btn_layout.addWidget(self.view_session_btn)
        
        left_layout.addLayout(btn_layout)
        
        # Right panel: Session details
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setFrameShape(QFrame.Shape.NoFrame)
        
        session_widget = QWidget()
        session_layout = QVBoxLayout(session_widget)
        
        # Session info group
        info_group = QGroupBox("Session Information")
        info_layout = QFormLayout()
        
        self.session_id_label = QLabel("")
        info_layout.addRow("Session ID:", self.session_id_label)
        
        self.session_date_edit = QDateEdit()
        self.session_date_edit.setCalendarPopup(True)
        self.session_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("Session Date:", self.session_date_edit)
        
        self.operator_edit = QLineEdit()
        info_layout.addRow("Operator:", self.operator_edit)
        
        self.treatment_area_edit = QLineEdit()
        info_layout.addRow("Treatment Area:", self.treatment_area_edit)
        
        info_group.setLayout(info_layout)
        session_layout.addWidget(info_group)
        
        # Device settings group
        settings_group = QGroupBox("Device Settings")
        settings_layout = QVBoxLayout()
        
        self.settings_edit = QTextEdit()
        self.settings_edit.setPlaceholderText("Enter device settings...")
        settings_layout.addWidget(self.settings_edit)
        
        settings_group.setLayout(settings_layout)
        session_layout.addWidget(settings_group)
        
        # Notes group
        notes_group = QGroupBox("Session Notes")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter session notes...")
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        session_layout.addWidget(notes_group)
        
        # Images group
        images_group = QGroupBox("Session Images")
        images_layout = QVBoxLayout()
        
        self.images_table = QTableWidget()
        self.images_table.setColumnCount(3)
        self.images_table.setHorizontalHeaderLabels(["Filename", "Type", "Timestamp"])
        self.images_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        images_layout.addWidget(self.images_table)
        
        # Image buttons
        img_btn_layout = QHBoxLayout()
        self.add_image_btn = QPushButton("Add Image")
        self.add_image_btn.clicked.connect(self._on_add_image)
        self.view_image_btn = QPushButton("View Image")
        self.view_image_btn.clicked.connect(self._on_view_image)
        
        img_btn_layout.addWidget(self.add_image_btn)
        img_btn_layout.addWidget(self.view_image_btn)
        
        images_layout.addLayout(img_btn_layout)
        
        images_group.setLayout(images_layout)
        session_layout.addWidget(images_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_session_btn = QPushButton("Save Session")
        self.save_session_btn.clicked.connect(self._on_save_session)
        save_layout.addWidget(self.save_session_btn)
        
        session_layout.addLayout(save_layout)
        
        right_panel.setWidget(session_widget)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial sizes (40% left, 60% right)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # Set initial state
        self.clear_form()
        self._update_ui_state()
        
    def clear_form(self):
        """Clear all form fields."""
        self.session_id_label.setText("")
        self.session_date_edit.setDate(QDate.currentDate())
        self.operator_edit.clear()
        self.treatment_area_edit.clear()
        self.settings_edit.clear()
        self.notes_edit.clear()
        
        # Clear images table
        self.images_table.setRowCount(0)
        
        self.current_session = None
        
    def populate_form(self, session_data):
        """
        Populate form with session data.
        
        Args:
            session_data (dict): Session data to populate the form with
        """
        self.clear_form()
        
        if not session_data:
            return
        
        self.current_session = session_data
        
        # Set form fields
        self.session_id_label.setText(session_data.get('session_id', ''))
        
        # Set date if available
        date_str = session_data.get('date', '')
        if date_str:
            try:
                date = QDate.fromString(date_str, "yyyy-MM-dd")
                self.session_date_edit.setDate(date)
            except Exception as e:
                logger.warning(f"Invalid date format: {date_str}")
        
        self.operator_edit.setText(session_data.get('operator', ''))
        self.treatment_area_edit.setText(session_data.get('treatment_area', ''))
        self.settings_edit.setText(session_data.get('device_settings', ''))
        self.notes_edit.setText(session_data.get('notes', ''))
        
        # Load images if available
        self._load_session_images(session_data.get('session_id', ''))
        
    def _load_session_images(self, session_id):
        """
        Load images for a session.
        
        Args:
            session_id (str): Session ID to load images for
        """
        self.images_table.setRowCount(0)
        
        if not session_id:
            return
        
        try:
            images = self.data_manager.get_session_images(session_id)
            
            if not images:
                return
            
            self.images_table.setRowCount(len(images))
            
            for i, image in enumerate(images):
                # Extract filename from path
                path = Path(image.get('image_path', ''))
                filename = path.name
                
                # Create table items
                file_item = QTableWidgetItem(filename)
                file_item.setData(Qt.ItemDataRole.UserRole, image.get('image_path', ''))
                
                type_item = QTableWidgetItem(image.get('image_type', ''))
                time_item = QTableWidgetItem(image.get('timestamp', ''))
                
                self.images_table.setItem(i, 0, file_item)
                self.images_table.setItem(i, 1, type_item)
                self.images_table.setItem(i, 2, time_item)
            
        except Exception as e:
            logger.error(f"Error loading session images: {str(e)}")
            
    def set_patient(self, patient_data):
        """
        Set the current patient and load their sessions.
        
        Args:
            patient_data (dict): Patient data
        """
        self.current_patient = patient_data
        self.clear_form()
        self._load_patient_sessions()
        self._update_ui_state()
        
    def _load_patient_sessions(self):
        """Load sessions for the current patient."""
        self.sessions_table.setRowCount(0)
        
        if not self.current_patient:
            return
        
        try:
            sessions = self.data_manager.get_treatment_sessions(self.current_patient.get('patient_id', ''))
            
            if not sessions:
                return
            
            self.sessions_table.setRowCount(len(sessions))
            
            for i, session in enumerate(sessions):
                date_item = QTableWidgetItem(session.get('date', ''))
                id_item = QTableWidgetItem(session.get('session_id', ''))
                notes_item = QTableWidgetItem(session.get('notes', '')[:50] + '...' if len(session.get('notes', '')) > 50 else session.get('notes', ''))
                
                self.sessions_table.setItem(i, 0, date_item)
                self.sessions_table.setItem(i, 1, id_item)
                self.sessions_table.setItem(i, 2, notes_item)
            
            # Auto-select the first session
            if self.sessions_table.rowCount() > 0:
                self.sessions_table.selectRow(0)
                self._on_session_selected()
            
        except Exception as e:
            logger.error(f"Error loading patient sessions: {str(e)}")
    
    def _update_ui_state(self):
        """Update UI state based on current patient and session."""
        has_patient = self.current_patient is not None
        has_session = self.current_session is not None
        
        # Enable/disable buttons based on state
        self.new_session_btn.setEnabled(has_patient)
        self.view_session_btn.setEnabled(has_patient and has_session)
        self.save_session_btn.setEnabled(has_patient)
        self.add_image_btn.setEnabled(has_patient and has_session)
        self.view_image_btn.setEnabled(has_patient and has_session)
        
        # Enable/disable form fields
        enabled = has_patient
        self.session_date_edit.setEnabled(enabled)
        self.operator_edit.setEnabled(enabled)
        self.treatment_area_edit.setEnabled(enabled)
        self.settings_edit.setEnabled(enabled)
        self.notes_edit.setEnabled(enabled)
    
    def _on_session_selected(self):
        """Handle session selection in the table."""
        selected_rows = self.sessions_table.selectedItems()
        
        if not selected_rows:
            return
        
        # Get session ID from the selected row
        current_row = self.sessions_table.currentRow()
        session_id = self.sessions_table.item(current_row, 1).text()
        
        if not session_id:
            return
        
        try:
            # Get session data
            session_data = None
            sessions = self.data_manager.get_treatment_sessions(self.current_patient.get('patient_id', ''))
            
            for session in sessions:
                if session.get('session_id', '') == session_id:
                    session_data = session
                    break
            
            if session_data:
                # Populate form with session data
                self.populate_form(session_data)
                self._update_ui_state()
            
        except Exception as e:
            logger.error(f"Error loading session data: {str(e)}")
    
    def _on_new_session(self):
        """Handle new session button click."""
        if not self.current_patient:
            QMessageBox.warning(self, "No Patient Selected", "Please select a patient first.")
            return
        
        # Clear the form
        self.clear_form()
        
        # Generate a new session ID
        self.session_id_label.setText(str(uuid.uuid4()))
        
        # Set current date
        self.session_date_edit.setDate(QDate.currentDate())
        
        # Focus on the operator field
        self.operator_edit.setFocus()
        
        self._update_ui_state()
    
    def _on_view_session(self):
        """Handle view session button click."""
        # Just make sure something is selected
        self._on_session_selected()
    
    def _on_save_session(self):
        """Handle save session button click."""
        if not self.current_patient:
            QMessageBox.warning(self, "No Patient Selected", "Please select a patient first.")
            return
        
        # Get session ID (or use the current one)
        session_id = self.session_id_label.text()
        if not session_id:
            session_id = str(uuid.uuid4())
            self.session_id_label.setText(session_id)
        
        # Get form data
        patient_id = self.current_patient.get('patient_id', '')
        session_date = self.session_date_edit.date().toString("yyyy-MM-dd")
        operator = self.operator_edit.text()
        treatment_area = self.treatment_area_edit.text()
        device_settings = self.settings_edit.toPlainText()
        notes = self.notes_edit.toPlainText()
        
        # Validate required fields
        if not operator:
            QMessageBox.warning(self, "Missing Information", "Operator name is required.")
            self.operator_edit.setFocus()
            return
        
        try:
            # Add or update session
            success = self.data_manager.add_treatment_session(
                session_id, patient_id, operator,
                device_settings=device_settings,
                treatment_area=treatment_area,
                notes=notes
            )
            
            if success:
                # Get the session data
                sessions = self.data_manager.get_treatment_sessions(patient_id)
                session_data = None
                
                for session in sessions:
                    if session.get('session_id', '') == session_id:
                        session_data = session
                        break
                
                if session_data:
                    # Update current session
                    self.current_session = session_data
                    
                    # Reload sessions
                    self._load_patient_sessions()
                    
                    # Select the saved session
                    for i in range(self.sessions_table.rowCount()):
                        if self.sessions_table.item(i, 1).text() == session_id:
                            self.sessions_table.selectRow(i)
                            break
                    
                    # Emit signal
                    self.session_updated.emit(session_data)
                    
                    # Show success message
                    QMessageBox.information(self, "Success", "Session saved successfully.")
                    logger.info(f"Saved session: {session_id} for patient: {patient_id}")
            else:
                QMessageBox.warning(self, "Error", "Could not save session data.")
                
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _on_add_image(self):
        """Handle add image button click."""
        if not self.current_patient or not self.current_session:
            QMessageBox.warning(self, "No Session Active", "Please create or select a session first.")
            return
        
        # Select an image file
        image_file, _ = QFileDialog.getOpenFileName(
            self, "Select Image File", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)"
        )
        
        if not image_file:
            return
        
        # Get image details
        image_id = str(uuid.uuid4())
        session_id = self.current_session.get('session_id', '')
        patient_id = self.current_patient.get('patient_id', '')
        timestamp = datetime.datetime.now().isoformat()
        
        # Ask for image type
        from PyQt6.QtWidgets import QInputDialog
        image_type, ok = QInputDialog.getItem(
            self, "Image Type", "Select image type:",
            ["Treatment Area", "Before Treatment", "After Treatment", "Progress", "Other"],
            0, False
        )
        
        if not ok:
            return
        
        # Copy the image to the patient directory
        try:
            # Create patient images directory if it doesn't exist
            patient_dir = Path("./data/patients") / patient_id
            images_dir = patient_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Get the original file extension
            ext = Path(image_file).suffix
            
            # Create the destination filename
            dest_filename = f"{session_id}_{image_id}{ext}"
            dest_path = images_dir / dest_filename
            
            # Copy the file
            import shutil
            shutil.copy2(image_file, dest_path)
            
            # Add the image to the database
            success = self.data_manager.add_image_record(
                image_id, session_id, patient_id, str(dest_path),
                image_type, notes=""
            )
            
            if success:
                # Reload images
                self._load_session_images(session_id)
                
                QMessageBox.information(self, "Success", "Image added successfully.")
                logger.info(f"Added image {image_id} to session {session_id}")
            else:
                QMessageBox.warning(self, "Error", "Could not add image to database.")
                
        except Exception as e:
            logger.error(f"Error adding image: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _on_view_image(self):
        """Handle view image button click."""
        selected_items = self.images_table.selectedItems()
        
        if not selected_items:
            QMessageBox.information(self, "No Image Selected", "Please select an image to view.")
            return
        
        # Get the image path
        current_row = self.images_table.currentRow()
        image_path_item = self.images_table.item(current_row, 0)
        
        if not image_path_item:
            return
        
        image_path = image_path_item.data(Qt.ItemDataRole.UserRole)
        
        if not image_path:
            return
        
        try:
            # Open the image with the default system viewer
            import subprocess
            import os
            
            if os.name == 'nt':  # Windows
                os.startfile(image_path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.call(('xdg-open', image_path))
            
        except Exception as e:
            logger.error(f"Error opening image: {str(e)}")
            QMessageBox.critical(self, "Error", f"Could not open image: {str(e)}") 