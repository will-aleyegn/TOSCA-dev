"""
Patient Information Form Module

This module provides a form for entering and managing patient information.
"""

import os
import uuid
import logging
import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QDateEdit, QComboBox, QTextEdit, QPushButton, QGroupBox, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from src.data_io.patient_data import PatientDataManager
from src.gui.patient_dialogs import PatientSelectDialog, QuickPatientDialog

logger = logging.getLogger(__name__)

class PatientFormWidget(QWidget):
    """
    Widget for patient information entry and management.
    """
    
    # Signal emitted when a patient is loaded/saved
    patient_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, data_dir="./data"):
        """Initialize the patient form widget."""
        super().__init__(parent)
        
        # Initialize data manager
        self.data_manager = PatientDataManager(data_dir)
        
        # Current patient data
        self.current_patient = None
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Patient ID and control buttons
        id_controls_layout = QHBoxLayout()
        
        # Patient ID (readonly)
        id_layout = QFormLayout()
        self.patient_id_edit = QLineEdit()
        self.patient_id_edit.setReadOnly(True)
        self.patient_id_edit.setPlaceholderText("Auto-generated when saved")
        id_layout.addRow("Patient ID:", self.patient_id_edit)
        id_controls_layout.addLayout(id_layout, 3)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("New Patient")
        self.load_btn = QPushButton("Load Patient")
        self.save_btn = QPushButton("Save Patient")
        
        self.new_btn.clicked.connect(self.on_new_patient)
        self.load_btn.clicked.connect(self.on_load_patient)
        self.save_btn.clicked.connect(self.on_save_patient)
        
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        id_controls_layout.addLayout(btn_layout, 2)
        
        main_layout.addLayout(id_controls_layout)
        
        # Personal Information Group
        personal_group = QGroupBox("Personal Information")
        personal_layout = QFormLayout()
        
        self.first_name_edit = QLineEdit()
        personal_layout.addRow("First Name:", self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        personal_layout.addRow("Last Name:", self.last_name_edit)
        
        self.dob_edit = QDateEdit()
        self.dob_edit.setDisplayFormat("yyyy-MM-dd")
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        personal_layout.addRow("Date of Birth:", self.dob_edit)
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "Male", "Female", "Other", "Prefer not to say"])
        personal_layout.addRow("Gender:", self.gender_combo)
        
        personal_group.setLayout(personal_layout)
        main_layout.addWidget(personal_group)
        
        # Contact Information Group
        contact_group = QGroupBox("Contact Information")
        contact_layout = QFormLayout()
        
        self.contact_edit = QTextEdit()
        self.contact_edit.setPlaceholderText("Address, phone, email, etc.")
        self.contact_edit.setMaximumHeight(80)
        contact_layout.addRow("Contact Details:", self.contact_edit)
        
        contact_group.setLayout(contact_layout)
        main_layout.addWidget(contact_group)
        
        # Medical Information Group
        medical_group = QGroupBox("Medical Information")
        medical_layout = QFormLayout()
        
        self.medical_history_edit = QTextEdit()
        self.medical_history_edit.setPlaceholderText("Relevant medical history")
        medical_layout.addRow("Medical History:", self.medical_history_edit)
        
        medical_group.setLayout(medical_layout)
        main_layout.addWidget(medical_group)
        
        # Notes Group
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)
        
        # Data Export/Import
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Patient Data")
        self.import_btn = QPushButton("Import Patient Data")
        
        self.export_btn.clicked.connect(self.on_export_data)
        self.import_btn.clicked.connect(self.on_import_data)
        
        export_layout.addWidget(self.export_btn)
        export_layout.addWidget(self.import_btn)
        main_layout.addLayout(export_layout)
        
        # Set initial state
        self.clear_form()
        
    def clear_form(self):
        """Clear all form fields."""
        self.patient_id_edit.clear()
        self.first_name_edit.clear()
        self.last_name_edit.clear()
        self.dob_edit.setDate(QDate.currentDate())
        self.gender_combo.setCurrentIndex(0)
        self.contact_edit.clear()
        self.medical_history_edit.clear()
        self.notes_edit.clear()
        
        self.current_patient = None
        
    def populate_form(self, patient_data):
        """
        Populate form with patient data.
        
        Args:
            patient_data (dict): Patient data to populate the form with
        """
        self.clear_form()
        
        if not patient_data:
            return
        
        self.current_patient = patient_data
        
        # Set form fields
        self.patient_id_edit.setText(patient_data.get('patient_id', ''))
        self.first_name_edit.setText(patient_data.get('first_name', ''))
        self.last_name_edit.setText(patient_data.get('last_name', ''))
        
        # Set date if available
        dob_str = patient_data.get('date_of_birth', '')
        if dob_str:
            try:
                dob = QDate.fromString(dob_str, "yyyy-MM-dd")
                self.dob_edit.setDate(dob)
            except Exception as e:
                logger.warning(f"Invalid date format: {dob_str}")
        
        # Set gender
        gender = patient_data.get('gender', '')
        gender_index = self.gender_combo.findText(gender)
        if gender_index >= 0:
            self.gender_combo.setCurrentIndex(gender_index)
        
        # Set other fields
        self.contact_edit.setText(patient_data.get('contact_info', ''))
        self.medical_history_edit.setText(patient_data.get('medical_history', ''))
        self.notes_edit.setText(patient_data.get('notes', ''))
        
    def get_form_data(self):
        """
        Get patient data from form fields.
        
        Returns:
            dict: Patient data from form fields
        """
        # Get patient ID (or generate a new one if none exists)
        patient_id = self.patient_id_edit.text()
        if not patient_id:
            patient_id = str(uuid.uuid4())
        
        # Get other form data
        patient_data = {
            'patient_id': patient_id,
            'first_name': self.first_name_edit.text(),
            'last_name': self.last_name_edit.text(),
            'date_of_birth': self.dob_edit.date().toString("yyyy-MM-dd"),
            'gender': self.gender_combo.currentText(),
            'contact_info': self.contact_edit.toPlainText(),
            'medical_history': self.medical_history_edit.toPlainText(),
            'notes': self.notes_edit.toPlainText()
        }
        
        return patient_data
    
    # Event handlers
    
    def on_new_patient(self):
        """Handle new patient button click."""
        # Check if current form has unsaved changes
        if self.current_patient:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to create a new patient anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Open the quick patient dialog
        dialog = QuickPatientDialog(self, self.data_manager)
        patient_data = dialog.exec()
        
        if patient_data:
            # If a patient was created, populate the form with the data
            self.populate_form(patient_data)
            self.patient_updated.emit(patient_data)
            logger.info(f"New patient {patient_data.get('patient_id')} created via dialog and loaded.")
        else:
            # If no patient was created (dialog cancelled), just clear the form
            self.clear_form()
            logger.info("New patient creation cancelled")
    
    def on_load_patient(self):
        """Handle load patient button click."""
        # Check if current form has unsaved changes
        if self.current_patient and self._is_form_dirty():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to load a different patient anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        dialog = PatientSelectDialog(self, self.data_manager)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # A patient was selected from the list
            patient_id = dialog.selected_patient_id
            
            if patient_id:
                patient_data = self.data_manager.get_patient(patient_id)
                
                if patient_data:
                    # Populate the form with the selected patient data
                    self.populate_form(patient_data)
                    
                    # Emit signal that a patient was loaded
                    self.patient_updated.emit(patient_data)
                    
                    logger.info(f"Loaded patient: {patient_data.get('patient_id')}")
                else:
                    QMessageBox.warning(self, "Error", "Could not load patient data.")
        elif result == QDialog.DialogCode.Accepted + 1:
            # The "New Patient" button was clicked in the dialog
            self.on_new_patient()
        else:
            # Dialog cancelled
            logger.info("Patient loading cancelled")
        
        # Set initial state
        self.clear_form()
    
    def on_save_patient(self):
        """Handle save patient button click."""
        # Get form data
        patient_data = self.get_form_data()
        
        # Validate required fields
        if not patient_data['first_name'] or not patient_data['last_name']:
            QMessageBox.warning(self, "Missing Information", "First name and last name are required.")
            return
        
        try:
            # Determine if this is a new patient or an update
            if self.current_patient and self.current_patient.get('patient_id') == patient_data['patient_id']:
                # Update existing patient
                success = self.data_manager.update_patient(
                    patient_data['patient_id'],
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    date_of_birth=patient_data['date_of_birth'],
                    gender=patient_data['gender'],
                    contact_info=patient_data['contact_info'],
                    notes=patient_data['notes']
                )
                
                message = "Patient information updated successfully."
            else:
                # Add new patient
                success = self.data_manager.add_patient(
                    patient_data['patient_id'],
                    patient_data['first_name'],
                    patient_data['last_name'],
                    patient_data['date_of_birth'],
                    patient_data['gender'],
                    patient_data['contact_info'],
                    patient_data['notes']
                )
                
                message = "New patient added successfully."
            
            if success:
                # Update the form with the saved patient data
                self.patient_id_edit.setText(patient_data['patient_id'])
                self.current_patient = patient_data
                
                # Emit signal that patient was saved
                self.patient_updated.emit(patient_data)
                
                # Show success message
                QMessageBox.information(self, "Success", message)
                logger.info(f"Saved patient: {patient_data['patient_id']}")
            else:
                QMessageBox.warning(self, "Error", "Could not save patient information.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            logger.error(f"Error saving patient: {str(e)}")
    
    def on_export_data(self):
        """Handle export data button click."""
        if not self.current_patient:
            QMessageBox.warning(self, "No Patient Selected", "Please load a patient record first.")
            return
        
        # Get export directory
        export_dir = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if export_dir:
            try:
                # Export patient data
                self.data_manager.export_patient_data(
                    self.current_patient['patient_id'],
                    export_dir,
                    include_images=True  # Include images in export
                )
                
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Patient data exported to {export_dir}"
                )
                logger.info(f"Exported patient data: {self.current_patient['patient_id']} to {export_dir}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"An error occurred: {str(e)}")
                logger.error(f"Error exporting patient data: {str(e)}")
    
    def on_import_data(self):
        """Handle import data button click."""
        # Get import directory
        import_dir = QFileDialog.getExistingDirectory(
            self, "Select Import Directory", str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if import_dir:
            try:
                # Import patient data
                imported_patients = self.data_manager.import_patient_data(import_dir)
                
                if imported_patients:
                    # Load the first imported patient
                    patient_data = self.data_manager.get_patient(imported_patients[0])
                    
                    if patient_data:
                        self.populate_form(patient_data)
                        self.patient_updated.emit(patient_data)
                    
                    QMessageBox.information(
                        self, "Import Successful", 
                        f"Imported {len(imported_patients)} patient records."
                    )
                    logger.info(f"Imported {len(imported_patients)} patient records from {import_dir}")
                else:
                    QMessageBox.warning(self, "Import Warning", "No patient records found.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"An error occurred: {str(e)}")
                logger.error(f"Error importing patient data: {str(e)}")

    def _is_form_dirty(self):
        """Check if the form has unsaved changes compared to current_patient."""
        if not self.current_patient:
            # If no patient is loaded, any data in form means it's dirty (for a new record)
            # However, this check is typically for loaded patients. For a new unsaved patient, 
            # self.current_patient would be None, but fields might be filled.
            # A more robust check might see if any field has content if no current_patient.
            # For now, consider dirty if no current_patient but fields are not default.
            if self.first_name_edit.text() or self.last_name_edit.text() or self.notes_edit.toPlainText(): # Example check
                return True
            return False

        current_form_data = self.get_form_data()       
        
        # Compare relevant fields, ignoring fields that might change due to re-serialization (like timestamps if any)
        # For simplicity, comparing all fields retrieved by get_form_data which doesn't include created_at/updated_at
        # Note: get_form_data() generates a new patient_id if self.patient_id_edit is empty,
        # so we must compare with self.current_patient['patient_id'] carefully.

        if self.current_patient.get('patient_id') != current_form_data.get('patient_id') and self.patient_id_edit.text(): # if ID exists and changed
             return True # this case should ideally not happen as ID is usually read-only after load

        fields_to_compare = ['first_name', 'last_name', 'date_of_birth', 'gender', 'contact_info', 'medical_history', 'notes']
        for field in fields_to_compare:
            if self.current_patient.get(field) != current_form_data.get(field):
                # Special handling for QTextEdit default empty string vs None if field was missing
                if self.current_patient.get(field) is None and current_form_data.get(field) == '':
                    continue
                if current_form_data.get(field) is None and self.current_patient.get(field) == '':
                    continue
                logger.debug(f"Form dirty. Field: {field}, Current: '{self.current_patient.get(field)}', Form: '{current_form_data.get(field)}'")
                return True
        return False 