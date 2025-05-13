"""
Actuator Control Widget Module

This module provides a GUI widget for controlling actuators and creating movement sequences.
It integrates with the Xeryon actuator control library.
"""

import os
import sys
import time
import json
import logging
from enum import Enum
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QGroupBox, QMessageBox, QListWidget,
    QScrollArea, QFrame, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QSplitter, QTabWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, pyqtSlot, QTimer

# Import the Xeryon library and sequence builder
sys.path.append(str(Path(__file__).resolve().parent.parent / "hardware" / "actuator-control"))
from Xeryon import Xeryon, Stage, Units, Communication
from xeryon_sequence_builder import ActionType, StepAction

logger = logging.getLogger(__name__)

class ActuatorControlWidget(QWidget):
    """
    Widget for controlling actuators and creating movement sequences.
    """
    
    # Signal when actuator status changes
    actuator_status_changed = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        """Initialize the actuator control widget."""
        super().__init__(parent)
        
        # Controller and axis variables
        self.controller = None
        self.axis = None
        self.is_connected = False
        self.current_sequence = []
        self.current_file = None
        self.loop_enabled = False
        self.loop_count = 1
        self.running = False
        
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget for different control modes
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create the manual control tab
        self.manual_tab = QWidget()
        self.tab_widget.addTab(self.manual_tab, "Manual Control")
        self._create_manual_control_ui()
        
        # Create the sequence builder tab
        self.sequence_tab = QWidget()
        self.tab_widget.addTab(self.sequence_tab, "Sequence Builder")
        self._create_sequence_builder_ui()
        
        # Status bar at the bottom
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setStyleSheet("color: red;")
        self.position_label = QLabel("Position: N/A")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.position_label)
        main_layout.addLayout(status_layout)
        
        # Connection status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(500)  # Update every 500ms
        
        # Now that all UI elements are initialized, update the UI state
        self._update_ui_state()
        
    def _create_manual_control_ui(self):
        """Create the manual control UI."""
        layout = QVBoxLayout(self.manual_tab)
        
        # Connection frame
        conn_frame = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_frame)
        
        self.port_label = QLabel("COM Port:")
        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton("Refresh Ports")
        self.connect_btn = QPushButton("Connect")
        
        self.port_combo.setEditable(True)
        self.port_combo.addItem("COM4")  # Default port
        
        conn_layout.addWidget(self.port_label)
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.refresh_ports_btn)
        conn_layout.addWidget(self.connect_btn)
        
        layout.addWidget(conn_frame)
        
        # Movement control
        movement_frame = QGroupBox("Movement Control")
        movement_layout = QVBoxLayout(movement_frame)
        
        # Position control
        pos_layout = QHBoxLayout()
        self.position_label_static = QLabel("Position:")
        self.position_input = QDoubleSpinBox()
        self.position_input.setRange(-1000, 1000)
        self.position_input.setSingleStep(0.1)
        self.position_input.setDecimals(3)
        self.position_input.setSuffix(" mm")
        self.move_to_btn = QPushButton("Move To")
        
        pos_layout.addWidget(self.position_label_static)
        pos_layout.addWidget(self.position_input)
        pos_layout.addWidget(self.move_to_btn)
        
        # Relative movement
        rel_layout = QHBoxLayout()
        self.step_label = QLabel("Step:")
        self.step_input = QDoubleSpinBox()
        self.step_input.setRange(-100, 100)
        self.step_input.setSingleStep(0.1)
        self.step_input.setDecimals(3)
        self.step_input.setSuffix(" mm")
        self.step_input.setValue(1.0)
        
        self.move_left_btn = QPushButton("← Move Left")
        self.move_right_btn = QPushButton("Move Right →")
        self.home_btn = QPushButton("Home")
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setStyleSheet("background-color: red; color: white;")
        
        rel_layout.addWidget(self.step_label)
        rel_layout.addWidget(self.step_input)
        rel_layout.addWidget(self.move_left_btn)
        rel_layout.addWidget(self.move_right_btn)
        
        # Speed control
        speed_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed:")
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.1, 100)
        self.speed_input.setSingleStep(0.1)
        self.speed_input.setDecimals(1)
        self.speed_input.setSuffix(" mm/s")
        self.speed_input.setValue(1.0)
        self.set_speed_btn = QPushButton("Set Speed")
        
        speed_layout.addWidget(self.speed_label)
        speed_layout.addWidget(self.speed_input)
        speed_layout.addWidget(self.set_speed_btn)
        speed_layout.addWidget(self.home_btn)
        speed_layout.addWidget(self.stop_btn)
        
        # Add layouts to the movement frame
        movement_layout.addLayout(pos_layout)
        movement_layout.addLayout(rel_layout)
        movement_layout.addLayout(speed_layout)
        
        layout.addWidget(movement_frame)
        layout.addStretch()
        
        # Connect signals
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.connect_disconnect)
        self.move_to_btn.clicked.connect(self.move_to_position)
        self.move_left_btn.clicked.connect(self.move_left)
        self.move_right_btn.clicked.connect(self.move_right)
        self.set_speed_btn.clicked.connect(self.set_speed)
        self.home_btn.clicked.connect(self.home)
        self.stop_btn.clicked.connect(self.stop)
        
    def _create_sequence_builder_ui(self):
        """Create the sequence builder UI."""
        layout = QVBoxLayout(self.sequence_tab)
        
        # Action parameters frame
        param_frame = QGroupBox("Action Parameters")
        param_layout = QFormLayout(param_frame)
        
        # Action type selection
        self.action_combo = QComboBox()
        self.action_combo.addItems([a.value for a in ActionType])
        param_layout.addRow("Action Type:", self.action_combo)
        
        # Position/Distance
        self.pos_input = QDoubleSpinBox()
        self.pos_input.setRange(-1000, 1000)
        self.pos_input.setSingleStep(0.1)
        self.pos_input.setDecimals(3)
        param_layout.addRow("Position (mm):", self.pos_input)
        
        # Speed
        self.seq_speed_input = QDoubleSpinBox()
        self.seq_speed_input.setRange(0.1, 100)
        self.seq_speed_input.setSingleStep(0.1)
        self.seq_speed_input.setDecimals(1)
        self.seq_speed_input.setValue(1.0)
        param_layout.addRow("Speed (mm/s):", self.seq_speed_input)
        
        # Direction
        self.dir_combo = QComboBox()
        self.dir_combo.addItems(["positive", "negative"])
        param_layout.addRow("Direction:", self.dir_combo)
        
        # Duration
        self.dur_input = QDoubleSpinBox()
        self.dur_input.setRange(0.1, 60)
        self.dur_input.setSingleStep(0.1)
        self.dur_input.setDecimals(1)
        self.dur_input.setValue(1.0)
        param_layout.addRow("Duration (s):", self.dur_input)
        
        # Units
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["mm", "mu", "nm"])
        param_layout.addRow("Units:", self.unit_combo)
        
        # Add step button
        self.add_step_btn = QPushButton("Add Step")
        param_layout.addRow("", self.add_step_btn)
        
        layout.addWidget(param_frame)
        
        # Sequence frame
        seq_frame = QGroupBox("Sequence")
        seq_layout = QVBoxLayout(seq_frame)
        
        # Sequence list
        self.sequence_list = QListWidget()
        seq_layout.addWidget(self.sequence_list)
        
        # Sequence buttons
        btn_layout = QHBoxLayout()
        self.delete_step_btn = QPushButton("Delete Step")
        self.clear_seq_btn = QPushButton("Clear All")
        self.move_up_btn = QPushButton("Move Up")
        self.move_down_btn = QPushButton("Move Down")
        
        btn_layout.addWidget(self.delete_step_btn)
        btn_layout.addWidget(self.clear_seq_btn)
        btn_layout.addWidget(self.move_up_btn)
        btn_layout.addWidget(self.move_down_btn)
        
        seq_layout.addLayout(btn_layout)
        
        # Loop control
        loop_layout = QHBoxLayout()
        self.loop_check = QCheckBox("Loop Sequence")
        self.loop_count_spin = QSpinBox()
        self.loop_count_spin.setRange(1, 100)
        self.loop_count_spin.setValue(1)
        
        loop_layout.addWidget(self.loop_check)
        loop_layout.addWidget(QLabel("Loop Count:"))
        loop_layout.addWidget(self.loop_count_spin)
        loop_layout.addStretch()
        
        seq_layout.addLayout(loop_layout)
        
        layout.addWidget(seq_frame)
        
        # Run and file buttons
        run_layout = QHBoxLayout()
        self.run_seq_btn = QPushButton("Run Sequence")
        self.run_seq_btn.setStyleSheet("background-color: green; color: white;")
        self.stop_seq_btn = QPushButton("Stop")
        self.stop_seq_btn.setStyleSheet("background-color: red; color: white;")
        self.save_seq_btn = QPushButton("Save Sequence")
        self.load_seq_btn = QPushButton("Load Sequence")
        
        run_layout.addWidget(self.run_seq_btn)
        run_layout.addWidget(self.stop_seq_btn)
        run_layout.addWidget(self.save_seq_btn)
        run_layout.addWidget(self.load_seq_btn)
        
        layout.addLayout(run_layout)
        
        # Connect signals
        self.action_combo.currentIndexChanged.connect(self._update_param_visibility)
        self.add_step_btn.clicked.connect(self.add_step)
        self.delete_step_btn.clicked.connect(self.delete_step)
        self.clear_seq_btn.clicked.connect(self.clear_sequence)
        self.move_up_btn.clicked.connect(self.move_step_up)
        self.move_down_btn.clicked.connect(self.move_step_down)
        self.run_seq_btn.clicked.connect(self.run_sequence)
        self.stop_seq_btn.clicked.connect(self.stop_sequence)
        self.save_seq_btn.clicked.connect(self.save_sequence)
        self.load_seq_btn.clicked.connect(self.load_sequence)
        
        # Initial update
        self._update_param_visibility()
        
    def _update_param_visibility(self):
        """Update parameter field visibility based on selected action type."""
        action_text = self.action_combo.currentText()
        action_type = None
        
        for action in ActionType:
            if action.value == action_text:
                action_type = action
                break
        
        # Hide all fields first
        for row in range(1, 6):  # Position, Speed, Direction, Duration, Units
            self.sequence_tab.layout().itemAt(0).widget().layout().itemAt(row, QFormLayout.ItemRole.FieldRole).widget().hide()
            
        # Show fields based on action type
        if action_type == ActionType.MOVE_ABSOLUTE:
            self.pos_input.show()
            self.seq_speed_input.show()
            self.unit_combo.show()
            
        elif action_type == ActionType.MOVE_RELATIVE:
            self.pos_input.show()
            self.seq_speed_input.show()
            self.unit_combo.show()
            
        elif action_type == ActionType.HOME:
            self.seq_speed_input.show()
            
        elif action_type == ActionType.PAUSE:
            self.dur_input.show()
            
        elif action_type == ActionType.SET_SPEED:
            self.seq_speed_input.show()
            self.unit_combo.show()
            
        elif action_type == ActionType.SCAN:
            self.seq_speed_input.show()
            self.dir_combo.show()
            self.dur_input.show()
            self.unit_combo.show()
            
    def _update_status(self):
        """Update status information periodically."""
        if self.is_connected and self.axis:
            try:
                # Get current position
                epos = self.axis.getEPOS()
                self.position_label.setText(f"Position: {epos:.3f} mm")
            except Exception as e:
                logger.error(f"Error updating status: {str(e)}")
                
    # Connection methods
    def refresh_ports(self):
        """Refresh available COM ports."""
        try:
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            
            # Save current selection
            current_text = self.port_combo.currentText()
            
            # Update combo box
            self.port_combo.clear()
            self.port_combo.addItems(ports)
            
            # Restore selection if it still exists
            index = self.port_combo.findText(current_text)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
                
        except Exception as e:
            logger.error(f"Error refreshing COM ports: {str(e)}")
            QMessageBox.warning(self, "Port Refresh Error", f"Error refreshing COM ports: {str(e)}")
            
    def connect_disconnect(self):
        """Connect or disconnect from the actuator controller."""
        if self.is_connected:
            # Disconnect
            try:
                if self.controller:
                    self.controller.stop()
                self.controller = None
                self.axis = None
                self.is_connected = False
                logger.info("Disconnected from actuator controller")
                self._update_ui_state()
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")
                QMessageBox.warning(self, "Disconnect Error", f"Error disconnecting: {str(e)}")
        else:
            # Connect
            try:
                port = self.port_combo.currentText()
                if not port:
                    QMessageBox.warning(self, "Connection Error", "No COM port specified")
                    return
                    
                # Create controller
                self.controller = Xeryon(port)
                
                # Add an axis - using generic XLS stage for now
                self.axis = self.controller.addAxis(Stage.XLS_1250, 'X')
                
                # Start controller
                self.controller.start()
                
                self.is_connected = True
                logger.info(f"Connected to actuator controller on {port}")
                
                # Set initial speed
                speed = self.speed_input.value()
                self.axis.setSpeed(speed)
                
                self._update_ui_state()
                
            except Exception as e:
                self.controller = None
                self.axis = None
                self.is_connected = False
                logger.error(f"Error connecting to actuator: {str(e)}")
                QMessageBox.warning(self, "Connection Error", f"Error connecting to actuator: {str(e)}")
                self._update_ui_state()
                
    # Movement control methods
    def move_to_position(self):
        """Move to an absolute position."""
        if not self.is_connected or not self.axis:
            return
            
        try:
            position = self.position_input.value()
            self.axis.setDPOS(position)
        except Exception as e:
            logger.error(f"Error moving to position: {str(e)}")
            QMessageBox.warning(self, "Movement Error", f"Error moving to position: {str(e)}")
            
    def move_left(self):
        """Move left (negative) by the specified step."""
        if not self.is_connected or not self.axis:
            return
            
        try:
            step = -self.step_input.value()  # Negative for left
            self.axis.step(step)
        except Exception as e:
            logger.error(f"Error moving left: {str(e)}")
            QMessageBox.warning(self, "Movement Error", f"Error moving left: {str(e)}")
            
    def move_right(self):
        """Move right (positive) by the specified step."""
        if not self.is_connected or not self.axis:
            return
            
        try:
            step = self.step_input.value()  # Positive for right
            self.axis.step(step)
        except Exception as e:
            logger.error(f"Error moving right: {str(e)}")
            QMessageBox.warning(self, "Movement Error", f"Error moving right: {str(e)}")
            
    def set_speed(self):
        """Set the movement speed."""
        if not self.is_connected or not self.axis:
            return
            
        try:
            speed = self.speed_input.value()
            self.axis.setSpeed(speed)
        except Exception as e:
            logger.error(f"Error setting speed: {str(e)}")
            QMessageBox.warning(self, "Speed Error", f"Error setting speed: {str(e)}")
            
    def home(self):
        """Move to home position."""
        if not self.is_connected or not self.axis:
            return
            
        try:
            # Find the index (home position)
            self.axis.findIndex()
        except Exception as e:
            logger.error(f"Error homing: {str(e)}")
            QMessageBox.warning(self, "Homing Error", f"Error homing: {str(e)}")
            
    def stop(self):
        """Stop all movement."""
        if not self.is_connected or not self.controller:
            return
            
        try:
            self.controller.stopMovements()
        except Exception as e:
            logger.error(f"Error stopping: {str(e)}")
            QMessageBox.warning(self, "Stop Error", f"Error stopping: {str(e)}")
            
    # Sequence builder methods
    def add_step(self):
        """Add a step to the sequence."""
        try:
            # Get action type
            action_text = self.action_combo.currentText()
            action_type = None
            for at in ActionType:
                if at.value == action_text:
                    action_type = at
                    break
                    
            if not action_type:
                return
                
            # Create parameters dict based on action type
            params = {}
            
            if action_type == ActionType.MOVE_ABSOLUTE:
                params["position"] = self.pos_input.value()
                params["speed"] = self.seq_speed_input.value()
                params["unit"] = self.unit_combo.currentText()
                
            elif action_type == ActionType.MOVE_RELATIVE:
                params["distance"] = self.pos_input.value()
                params["speed"] = self.seq_speed_input.value()
                params["unit"] = self.unit_combo.currentText()
                
            elif action_type == ActionType.HOME:
                params["speed"] = self.seq_speed_input.value()
                
            elif action_type == ActionType.PAUSE:
                params["duration"] = self.dur_input.value()
                
            elif action_type == ActionType.SET_SPEED:
                params["speed"] = self.seq_speed_input.value()
                params["unit"] = self.unit_combo.currentText()
                
            elif action_type == ActionType.SCAN:
                params["speed"] = self.seq_speed_input.value()
                params["direction"] = self.dir_combo.currentText()
                params["duration"] = self.dur_input.value()
                params["unit"] = self.unit_combo.currentText()
                
            # Create step action
            step = StepAction(action_type, params)
            
            # Add to sequence
            self.current_sequence.append(step)
            
            # Update list
            self.sequence_list.addItem(str(step))
            
            # Update UI state
            self._update_ui_state()
            
        except Exception as e:
            logger.error(f"Error adding step: {str(e)}")
            QMessageBox.warning(self, "Sequence Error", f"Error adding step: {str(e)}")
            
    def delete_step(self):
        """Delete the selected step from the sequence."""
        current_row = self.sequence_list.currentRow()
        if current_row >= 0 and current_row < len(self.current_sequence):
            del self.current_sequence[current_row]
            self.sequence_list.takeItem(current_row)
            self._update_ui_state()
            
    def clear_sequence(self):
        """Clear the entire sequence."""
        self.current_sequence = []
        self.sequence_list.clear()
        self._update_ui_state()
        
    def move_step_up(self):
        """Move the selected step up in the sequence."""
        current_row = self.sequence_list.currentRow()
        if current_row > 0:
            # Swap in the sequence
            self.current_sequence[current_row], self.current_sequence[current_row-1] = \
                self.current_sequence[current_row-1], self.current_sequence[current_row]
                
            # Update the list widget
            item_text = self.sequence_list.item(current_row).text()
            self.sequence_list.takeItem(current_row)
            self.sequence_list.insertItem(current_row-1, item_text)
            self.sequence_list.setCurrentRow(current_row-1)
            
    def move_step_down(self):
        """Move the selected step down in the sequence."""
        current_row = self.sequence_list.currentRow()
        if current_row >= 0 and current_row < len(self.current_sequence) - 1:
            # Swap in the sequence
            self.current_sequence[current_row], self.current_sequence[current_row+1] = \
                self.current_sequence[current_row+1], self.current_sequence[current_row]
                
            # Update the list widget
            item_text = self.sequence_list.item(current_row).text()
            self.sequence_list.takeItem(current_row)
            self.sequence_list.insertItem(current_row+1, item_text)
            self.sequence_list.setCurrentRow(current_row+1)
            
    def run_sequence(self):
        """Run the current sequence."""
        if not self.is_connected or not self.axis or not self.current_sequence:
            return
            
        try:
            # Get loop settings
            self.loop_enabled = self.loop_check.isChecked()
            self.loop_count = self.loop_count_spin.value() if self.loop_enabled else 1
            
            # Disable UI during execution
            self.running = True
            self._update_ui_state()
            
            # Start a timer to run the sequence in the background
            self.execute_timer = QTimer()
            self.execute_timer.timeout.connect(self._execute_sequence_step)
            self.current_step_index = 0
            self.current_loop = 0
            self.execute_timer.start(100)  # Check every 100ms
            
        except Exception as e:
            logger.error(f"Error starting sequence: {str(e)}")
            QMessageBox.warning(self, "Sequence Error", f"Error starting sequence: {str(e)}")
            self.running = False
            self._update_ui_state()
            
    def _execute_sequence_step(self):
        """Execute the current step in the sequence."""
        if not self.running or not self.is_connected:
            self.execute_timer.stop()
            self.running = False
            self._update_ui_state()
            return
            
        # Check if we've completed all loops
        if self.current_loop >= self.loop_count:
            self.execute_timer.stop()
            self.running = False
            self._update_ui_state()
            return
            
        # Check if we've completed the current loop
        if self.current_step_index >= len(self.current_sequence):
            self.current_loop += 1
            self.current_step_index = 0
            
            # If we've completed all loops, stop
            if self.current_loop >= self.loop_count:
                self.execute_timer.stop()
                self.running = False
                self._update_ui_state()
                return
                
        # Get the current step
        step = self.current_sequence[self.current_step_index]
        
        # Execute the step
        try:
            self._execute_step(step)
            # Move to the next step
            self.current_step_index += 1
        except Exception as e:
            logger.error(f"Error executing step: {str(e)}")
            self.execute_timer.stop()
            self.running = False
            self._update_ui_state()
            QMessageBox.warning(self, "Sequence Error", f"Error executing step: {str(e)}")
            
    def _execute_step(self, step):
        """Execute a single step in the sequence."""
        action_type = step.action_type
        params = step.params
        
        if action_type == ActionType.MOVE_ABSOLUTE:
            position = params.get("position", 0)
            speed = params.get("speed", 1.0)
            self.axis.setSpeed(speed)
            self.axis.setDPOS(position)
            
        elif action_type == ActionType.MOVE_RELATIVE:
            distance = params.get("distance", 0)
            speed = params.get("speed", 1.0)
            self.axis.setSpeed(speed)
            self.axis.step(distance)
            
        elif action_type == ActionType.HOME:
            speed = params.get("speed", 1.0)
            self.axis.setSpeed(speed)
            self.axis.findIndex()
            
        elif action_type == ActionType.PAUSE:
            duration = params.get("duration", 1.0)
            time.sleep(duration)
            
        elif action_type == ActionType.SET_SPEED:
            speed = params.get("speed", 1.0)
            self.axis.setSpeed(speed)
            
        elif action_type == ActionType.SCAN:
            speed = params.get("speed", 1.0)
            direction = params.get("direction", "positive")
            duration = params.get("duration", 1.0)
            
            # Convert direction to numeric value (1 for positive, -1 for negative)
            dir_value = 1 if direction == "positive" else -1
            
            self.axis.setSpeed(speed)
            self.axis.startScan(dir_value, duration)
            
    def stop_sequence(self):
        """Stop the sequence execution."""
        if self.running:
            try:
                # Stop the timer
                if hasattr(self, 'execute_timer'):
                    self.execute_timer.stop()
                
                # Stop movement
                if self.controller:
                    self.controller.stopMovements()
                
                self.running = False
                self._update_ui_state()
                
            except Exception as e:
                logger.error(f"Error stopping sequence: {str(e)}")
                QMessageBox.warning(self, "Sequence Error", f"Error stopping sequence: {str(e)}")
                
    def save_sequence(self):
        """Save the current sequence to a file."""
        if not self.current_sequence:
            QMessageBox.warning(self, "Save Error", "No sequence to save")
            return
            
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Sequence", "", "JSON Files (*.json)"
            )
            
            if not file_path:
                return
                
            # Add .json extension if not present
            if not file_path.endswith('.json'):
                file_path += '.json'
                
            # Convert sequence to JSON-serializable format
            sequence_data = {
                "sequence": [step.to_dict() for step in self.current_sequence],
                "loop_enabled": self.loop_check.isChecked(),
                "loop_count": self.loop_count_spin.value()
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(sequence_data, f, indent=2)
                
            self.current_file = file_path
            logger.info(f"Sequence saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving sequence: {str(e)}")
            QMessageBox.warning(self, "Save Error", f"Error saving sequence: {str(e)}")
            
    def load_sequence(self):
        """Load a sequence from a file."""
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load Sequence", "", "JSON Files (*.json)"
            )
            
            if not file_path:
                return
                
            # Load from file
            with open(file_path, 'r') as f:
                sequence_data = json.load(f)
                
            # Clear current sequence
            self.clear_sequence()
            
            # Load sequence steps
            for step_data in sequence_data.get("sequence", []):
                step = StepAction.from_dict(step_data)
                self.current_sequence.append(step)
                self.sequence_list.addItem(str(step))
                
            # Load loop settings
            self.loop_check.setChecked(sequence_data.get("loop_enabled", False))
            self.loop_count_spin.setValue(sequence_data.get("loop_count", 1))
            
            self.current_file = file_path
            logger.info(f"Sequence loaded from {file_path}")
            self._update_ui_state()
            
        except Exception as e:
            logger.error(f"Error loading sequence: {str(e)}")
            QMessageBox.warning(self, "Load Error", f"Error loading sequence: {str(e)}")

    def _update_ui_state(self):
        """Update the UI state based on the current connection and sequence status."""
        self.status_label.setText(f"Status: {'Connected' if self.is_connected else 'Not Connected'}")
        self.status_label.setStyleSheet("color: " + ("green;" if self.is_connected else "red;"))
        self.position_label.setText(f"Position: {'N/A' if not self.axis else f'{self.axis.getEPOS():.3f} mm'}")
        self.position_label.setStyleSheet("color: " + ("green;" if self.axis else "red;"))
        
        # Check if sequence has items
        has_sequence = len(self.current_sequence) > 0
        has_file = self.current_file is not None
        
        # Set enabled states based on connection and sequence status
        self.run_seq_btn.setEnabled(self.is_connected and self.axis and has_sequence)
        self.stop_seq_btn.setEnabled(self.running)
        self.save_seq_btn.setEnabled(has_sequence)
        self.load_seq_btn.setEnabled(True)  # Always allow loading
        self.delete_step_btn.setEnabled(has_sequence)
        self.clear_seq_btn.setEnabled(has_sequence)
        self.move_up_btn.setEnabled(has_sequence)
        self.move_down_btn.setEnabled(has_sequence)
        self.loop_check.setEnabled(has_sequence)
        self.loop_count_spin.setEnabled(self.loop_check.isChecked())
        
        # The add_step_btn should be enabled when connected, not when a sequence exists
        self.add_step_btn.setEnabled(self.is_connected)
        
        # Enable/disable controls based on connection
        self.pos_input.setEnabled(self.is_connected)
        self.seq_speed_input.setEnabled(self.is_connected)
        self.unit_combo.setEnabled(self.is_connected)
        self.dir_combo.setEnabled(self.is_connected)
        self.dur_input.setEnabled(self.is_connected)
        self.speed_input.setEnabled(self.is_connected)
        self.speed_label.setEnabled(self.is_connected)
        self.set_speed_btn.setEnabled(self.is_connected)
        self.home_btn.setEnabled(self.is_connected)
        self.stop_btn.setEnabled(self.is_connected)
        self.position_input.setEnabled(self.is_connected)
        self.position_label_static.setEnabled(self.is_connected)
        self.move_to_btn.setEnabled(self.is_connected)
        self.step_input.setEnabled(self.is_connected)
        self.step_label.setEnabled(self.is_connected)
        self.move_left_btn.setEnabled(self.is_connected)
        self.move_right_btn.setEnabled(self.is_connected)
        
        # Correctly handle connection UI
        self.refresh_ports_btn.setEnabled(not self.is_connected)
        self.connect_btn.setEnabled(not self.is_connected)
        self.port_combo.setEnabled(not self.is_connected)
        self.port_label.setEnabled(not self.is_connected)
        
        # Tab widget should always be enabled
        self.tab_widget.setEnabled(True)
        
        # Keep the status timer running
        self.status_timer.start(500)
