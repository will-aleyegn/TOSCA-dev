"""
Patient Dialog Module

This module provides dialogs for patient selection and management.
"""

import logging
import uuid
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QDialogButtonBox,
    QLabel, QPushButton, QLineEdit, QFormLayout, QMessageBox, QComboBox,
    QDateEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QDate

from src.data_io.patient_data import PatientDataManager

logger = logging.getLogger(__name__)

class PatientSelectDialog(QDialog):
    """Dialog for selecting an existing patient."""
    
    def __init__(self, parent=None, data_manager=None):
        """Initialize the patient selection dialog."""
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.selected_patient_id = None
        
        self.setWindowTitle("Select Patient")
        self.setMinimumSize(500, 400)
        
        self._init_ui()
        self._load_patients()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Search field
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter patient name or ID")
        self.search_edit.textChanged.connect(self._filter_patients)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Patient list
        self.patient_list = QListWidget()
        self.patient_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.patient_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Add "New Patient" button
        self.new_patient_btn = QPushButton("New Patient")
        self.new_patient_btn.clicked.connect(self._on_new_patient)
        button_layout.addWidget(self.new_patient_btn)
        
        # Add spacer
        button_layout.addStretch()
        
        # Standard dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(self.button_box)
        
        layout.addLayout(button_layout)
        
    def _load_patients(self):
        """Load patients into the list widget."""
        self.patient_list.clear()
        
        try:
            patients = self.data_manager.get_all_patients()
            
            for patient in patients:
                name = f"{patient['first_name']} {patient['last_name']}"
                item_text = f"{name} (ID: {patient['patient_id']})"
                
                self.patient_list.addItem(item_text)
                # Store patient_id in the item's data
                self.patient_list.item(self.patient_list.count() - 1).setData(Qt.ItemDataRole.UserRole, patient['patient_id'])
            
            if self.patient_list.count() > 0:
                self.patient_list.setCurrentRow(0)
            
        except Exception as e:
            logger.error(f"Error loading patients: {str(e)}")
            QMessageBox.critical(self, "Error", f"Could not load patient list: {str(e)}")
    
    def _filter_patients(self):
        """Filter patients based on search text."""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.patient_list.count()):
            item = self.patient_list.item(i)
            if search_text in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _on_new_patient(self):
        """Handle new patient button click."""
        # Close this dialog with a special return code
        self.done(QDialog.DialogCode.Accepted + 1)  # Use a custom return code
    
    def get_selected_patient_id(self):
        """Get the ID of the selected patient."""
        if self.patient_list.currentItem():
            return self.patient_list.currentItem().data(Qt.ItemDataRole.UserRole)
        return None
    
    def exec(self):
        """Execute the dialog."""
        result = super().exec()
        
        if result == QDialog.DialogCode.Accepted:
            self.selected_patient_id = self.get_selected_patient_id()
            
        return result

class QuickPatientDialog(QDialog):
    """Dialog for quick patient creation."""
    
    def __init__(self, parent=None, data_manager=None):
        """Initialize the quick patient creation dialog."""
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.patient_data = None
        
        self.setWindowTitle("Create New Patient")
        self.setMinimumWidth(400)
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Form layout for patient information
        form_layout = QFormLayout()
        
        self.first_name_edit = QLineEdit()
        form_layout.addRow("First Name:", self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        form_layout.addRow("Last Name:", self.last_name_edit)
        
        from PyQt6.QtCore import QDate
        from PyQt6.QtWidgets import QDateEdit
        
        self.dob_edit = QDateEdit()
        self.dob_edit.setDisplayFormat("yyyy-MM-dd")
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        form_layout.addRow("Date of Birth:", self.dob_edit)
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["", "Male", "Female", "Other", "Prefer not to say"])
        form_layout.addRow("Gender:", self.gender_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
    def _on_accept(self):
        """Handle OK button click."""
        # Validate required fields
        if not self.first_name_edit.text() or not self.last_name_edit.text():
            QMessageBox.warning(self, "Missing Information", "First name and last name are required.")
            return
        
        # Create patient object
        import uuid
        
        patient_id = str(uuid.uuid4())
        first_name = self.first_name_edit.text()
        last_name = self.last_name_edit.text()
        dob = self.dob_edit.date().toString("yyyy-MM-dd")
        gender = self.gender_combo.currentText()
        
        try:
            # Add patient to database
            success = self.data_manager.add_patient(
                patient_id, first_name, last_name, dob, gender
            )
            
            if success:
                # Get complete patient data
                self.patient_data = self.data_manager.get_patient(patient_id)
                
                if self.patient_data:
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Patient created but could not retrieve data.")
            else:
                QMessageBox.warning(self, "Error", "Could not create new patient.")
                
        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def exec(self):
        """Execute the dialog."""
        result = super().exec()
        
        if result == QDialog.DialogCode.Accepted:
            return self.patient_data
        
        return None 