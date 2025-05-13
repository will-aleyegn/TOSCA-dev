"""
Xeryon Sequence Builder
A tool for creating, saving, loading, and running sequences of stage movements.
"""

from Xeryon import *
import time
import json
import os
import matplotlib.pyplot as plt
from enum import Enum
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ActionType(Enum):
    MOVE_ABSOLUTE = "Move Absolute"
    MOVE_RELATIVE = "Move Relative"
    HOME = "Home"
    PAUSE = "Pause"
    SET_SPEED = "Set Speed"
    SCAN = "Scan"

class StepAction:
    def __init__(self, action_type, params=None):
        self.action_type = action_type
        self.params = params or {}
    
    def to_dict(self):
        return {
            "action_type": self.action_type.name,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            ActionType[data["action_type"]],
            data["params"]
        )
    
    def __str__(self):
        if self.action_type == ActionType.MOVE_ABSOLUTE:
            return f"Move to {self.params.get('position', 0)} {self.params.get('unit', 'mm')}"
        elif self.action_type == ActionType.MOVE_RELATIVE:
            return f"Move {self.params.get('distance', 0)} {self.params.get('unit', 'mm')}"
        elif self.action_type == ActionType.HOME:
            return "Move to Home"
        elif self.action_type == ActionType.PAUSE:
            return f"Pause for {self.params.get('duration', 0)} seconds"
        elif self.action_type == ActionType.SET_SPEED:
            return f"Set Speed to {self.params.get('speed', 0)} {self.params.get('unit', 'mm')}/s"
        elif self.action_type == ActionType.SCAN:
            return f"Scan {self.params.get('direction', 'positive')} for {self.params.get('duration', 0)} seconds"
        return str(self.action_type)

class SequenceBuilder:
    def __init__(self, master):
        self.master = master
        self.master.title("Xeryon Sequence Builder")
        self.master.geometry("800x600")
        
        # Controller and axis variables
        self.controller = None
        self.axis = None
        self.is_connected = False
        self.current_sequence = []
        self.current_file = None
        self.loop_enabled = False
        self.loop_count = 1
        
        self.create_gui()
    
    def create_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.com_var = tk.StringVar()
        self.com_entry = ttk.Entry(conn_frame, textvariable=self.com_var, width=10)
        self.com_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.com_var.set("COM3")
        
        self.refresh_btn = ttk.Button(conn_frame, text="Refresh Ports", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect)
        self.connect_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Not Connected")
        ttk.Label(conn_frame, textvariable=self.status_var).grid(row=0, column=4, padx=5, pady=5)
        
        # Parameter frame
        param_frame = ttk.LabelFrame(main_frame, text="Action Parameters", padding="5")
        param_frame.pack(fill=tk.X, pady=5)
        
        # Action type selection
        ttk.Label(param_frame, text="Action Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.action_var = tk.StringVar()
        self.action_combobox = ttk.Combobox(param_frame, textvariable=self.action_var, 
                                           values=[a.value for a in ActionType], state="readonly", width=15)
        self.action_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.action_combobox.current(0)
        self.action_combobox.bind("<<ComboboxSelected>>", self.update_param_frame)
        
        # Speed
        ttk.Label(param_frame, text="Speed (mm/s):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_entry = ttk.Entry(param_frame, textvariable=self.speed_var, width=10)
        self.speed_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Position/Distance
        self.pos_label = ttk.Label(param_frame, text="Position (mm):")
        self.pos_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.pos_var = tk.DoubleVar(value=0.0)
        self.pos_entry = ttk.Entry(param_frame, textvariable=self.pos_var, width=10)
        self.pos_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Direction
        ttk.Label(param_frame, text="Direction:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_var = tk.StringVar(value="positive")
        self.dir_combobox = ttk.Combobox(param_frame, textvariable=self.dir_var, 
                                        values=["positive", "negative"], state="readonly", width=10)
        self.dir_combobox.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Duration
        ttk.Label(param_frame, text="Duration (s):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.dur_var = tk.DoubleVar(value=1.0)
        self.dur_entry = ttk.Entry(param_frame, textvariable=self.dur_var, width=10)
        self.dur_entry.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Units
        ttk.Label(param_frame, text="Units:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.unit_var = tk.StringVar(value="mm")
        self.unit_combobox = ttk.Combobox(param_frame, textvariable=self.unit_var, 
                                         values=["mm", "mu", "nm"], state="readonly", width=10)
        self.unit_combobox.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Add step button
        self.add_btn = ttk.Button(param_frame, text="Add Step", command=self.add_step)
        self.add_btn.grid(row=6, column=0, padx=5, pady=5, columnspan=2, sticky=tk.EW)
        
        # Sequence frame
        seq_frame = ttk.LabelFrame(main_frame, text="Sequence", padding="5")
        seq_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Sequence list
        self.sequence_listbox = tk.Listbox(seq_frame, width=70, height=10)
        self.sequence_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(seq_frame, orient="vertical", command=self.sequence_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sequence_listbox.config(yscrollcommand=scrollbar.set)
        
        # Button frame for sequence operations
        button_frame = ttk.Frame(seq_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.delete_btn = ttk.Button(button_frame, text="Delete Step", command=self.delete_step)
        self.delete_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.clear_btn = ttk.Button(button_frame, text="Clear All", command=self.clear_sequence)
        self.clear_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.move_up_btn = ttk.Button(button_frame, text="Move Up", command=self.move_step_up)
        self.move_up_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.move_down_btn = ttk.Button(button_frame, text="Move Down", command=self.move_step_down)
        self.move_down_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Loop control
        loop_frame = ttk.LabelFrame(main_frame, text="Loop Control", padding="5")
        loop_frame.pack(fill=tk.X, pady=5)
        
        self.loop_var = tk.BooleanVar(value=False)
        self.loop_check = ttk.Checkbutton(loop_frame, text="Loop Sequence", variable=self.loop_var)
        self.loop_check.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(loop_frame, text="Loop Count:").grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.loop_count_var = tk.IntVar(value=1)
        self.loop_count_entry = ttk.Entry(loop_frame, textvariable=self.loop_count_var, width=5)
        self.loop_count_entry.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Execution and file operations
        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(fill=tk.X, pady=5)
        
        self.run_btn = ttk.Button(exec_frame, text="Run Sequence", command=self.run_sequence)
        self.run_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(exec_frame, text="Stop", command=self.stop_sequence)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_btn = ttk.Button(exec_frame, text="Save Sequence", command=self.save_sequence)
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.load_btn = ttk.Button(exec_frame, text="Load Sequence", command=self.load_sequence)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Initial UI state
        self.update_param_frame()
        self.update_ui_state()
        
        # Refresh ports at startup
        self.refresh_ports()
    
    def update_param_frame(self, event=None):
        action_type = self.get_selected_action_type()
        
        # Hide all fields first
        for widget in [self.pos_label, self.pos_entry, self.speed_entry, 
                      self.dir_combobox, self.dur_entry, self.unit_combobox]:
            widget.grid_remove()
        
        # Show fields based on action type
        if action_type == ActionType.MOVE_ABSOLUTE:
            self.pos_label.config(text="Position (mm):")
            self.pos_label.grid()
            self.pos_entry.grid()
            self.speed_entry.grid()
            self.unit_combobox.grid()
        
        elif action_type == ActionType.MOVE_RELATIVE:
            self.pos_label.config(text="Distance (mm):")
            self.pos_label.grid()
            self.pos_entry.grid()
            self.speed_entry.grid()
            self.unit_combobox.grid()
        
        elif action_type == ActionType.HOME:
            self.speed_entry.grid()
        
        elif action_type == ActionType.PAUSE:
            self.dur_entry.grid()
        
        elif action_type == ActionType.SET_SPEED:
            self.speed_entry.grid()
            self.unit_combobox.grid()
        
        elif action_type == ActionType.SCAN:
            self.speed_entry.grid()
            self.dir_combobox.grid()
            self.dur_entry.grid()
            self.unit_combobox.grid()
    
    def update_ui_state(self):
        connected = self.is_connected
        
        # Connection controls
        self.com_entry.config(state="normal" if not connected else "disabled")
        self.connect_btn.config(text="Disconnect" if connected else "Connect")
        
        # Action controls
        for widget in [self.action_combobox, self.speed_entry, self.pos_entry, 
                       self.dir_combobox, self.dur_entry, self.unit_combobox,
                       self.add_btn]:
            widget.config(state="normal" if connected else "disabled")
        
        # Sequence controls
        for widget in [self.delete_btn, self.clear_btn, self.move_up_btn, 
                       self.move_down_btn, self.run_btn, self.stop_btn]:
            widget.config(state="normal" if connected else "disabled")
    
    def refresh_ports(self):
        """Refresh the list of available COM ports"""
        ports = list(serial.tools.list_ports.comports())
        port_names = [port.device for port in ports]
        
        if port_names:
            self.com_var.set(port_names[0])
            print(f"Available ports: {', '.join(port_names)}")
        else:
            print("No COM ports found")
    
    def connect(self):
        """Connect or disconnect from the controller"""
        if not self.is_connected:
            try:
                com_port = self.com_var.get()
                print(f"Connecting to {com_port}...")
                
                # Create controller and axis
                self.controller = Xeryon(com_port, 115200)
                self.axis = self.controller.addAxis(Stage.XLS_312, "X")
                self.controller.start()
                
                # Try to find index
                try:
                    self.axis.findIndex()
                    print("Index found successfully")
                except Exception as e:
                    print(f"Warning during index finding: {e}")
                
                self.is_connected = True
                self.status_var.set("Connected")
                print(f"Connected to controller on {com_port}")
                
                # Set units to mm
                self.axis.setUnits(Units.mm)
                
                # Update UI
                self.update_ui_state()
                
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
                print(f"Connection error: {e}")
        else:
            # Disconnect
            try:
                if self.controller:
                    self.controller.stop()
                    self.controller = None
                    self.axis = None
                
                self.is_connected = False
                self.status_var.set("Not Connected")
                print("Disconnected from controller")
                
                # Update UI
                self.update_ui_state()
                
            except Exception as e:
                messagebox.showerror("Disconnection Error", f"Error during disconnection: {str(e)}")
                print(f"Disconnection error: {e}")
    
    def get_selected_action_type(self):
        """Get the currently selected action type from the UI"""
        action_str = self.action_var.get()
        for action_type in ActionType:
            if action_type.value == action_str:
                return action_type
        return ActionType.MOVE_ABSOLUTE
    
    def add_step(self):
        """Add a step to the current sequence"""
        action_type = self.get_selected_action_type()
        params = {}
        
        # Collect parameters based on action type
        if action_type == ActionType.MOVE_ABSOLUTE:
            params = {
                "position": self.pos_var.get(),
                "speed": self.speed_var.get(),
                "unit": self.unit_var.get()
            }
        
        elif action_type == ActionType.MOVE_RELATIVE:
            params = {
                "distance": self.pos_var.get(),
                "speed": self.speed_var.get(),
                "unit": self.unit_var.get()
            }
        
        elif action_type == ActionType.HOME:
            params = {
                "speed": self.speed_var.get()
            }
        
        elif action_type == ActionType.PAUSE:
            params = {
                "duration": self.dur_var.get()
            }
        
        elif action_type == ActionType.SET_SPEED:
            params = {
                "speed": self.speed_var.get(),
                "unit": self.unit_var.get()
            }
        
        elif action_type == ActionType.SCAN:
            params = {
                "speed": self.speed_var.get(),
                "direction": self.dir_var.get(),
                "duration": self.dur_var.get(),
                "unit": self.unit_var.get()
            }
        
        # Create the step and add to sequence
        step = StepAction(action_type, params)
        self.current_sequence.append(step)
        
        # Update the listbox
        self.sequence_listbox.insert(tk.END, f"{len(self.current_sequence)}. {step}")
        print(f"Added step: {step}")
    
    def delete_step(self):
        """Delete the selected step from the sequence"""
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a step to delete.")
            return
        
        index = selection[0]
        if 0 <= index < len(self.current_sequence):
            del self.current_sequence[index]
            
            # Update the listbox
            self.sequence_listbox.delete(0, tk.END)
            for i, step in enumerate(self.current_sequence):
                self.sequence_listbox.insert(tk.END, f"{i+1}. {step}")
            
            print(f"Deleted step at position {index+1}")
    
    def clear_sequence(self):
        """Clear the entire sequence"""
        if messagebox.askyesno("Clear Sequence", "Are you sure you want to clear the entire sequence?"):
            self.current_sequence = []
            self.sequence_listbox.delete(0, tk.END)
            print("Sequence cleared")
    
    def move_step_up(self):
        """Move the selected step up in the sequence"""
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a step to move.")
            return
        
        index = selection[0]
        if index > 0:
            # Swap steps
            self.current_sequence[index], self.current_sequence[index-1] = \
                self.current_sequence[index-1], self.current_sequence[index]
            
            # Update the listbox
            self.sequence_listbox.delete(0, tk.END)
            for i, step in enumerate(self.current_sequence):
                self.sequence_listbox.insert(tk.END, f"{i+1}. {step}")
            
            # Update selection
            self.sequence_listbox.selection_set(index-1)
            print(f"Moved step from position {index+1} to {index}")
    
    def move_step_down(self):
        """Move the selected step down in the sequence"""
        selection = self.sequence_listbox.curselection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a step to move.")
            return
        
        index = selection[0]
        if index < len(self.current_sequence) - 1:
            # Swap steps
            self.current_sequence[index], self.current_sequence[index+1] = \
                self.current_sequence[index+1], self.current_sequence[index]
            
            # Update the listbox
            self.sequence_listbox.delete(0, tk.END)
            for i, step in enumerate(self.current_sequence):
                self.sequence_listbox.insert(tk.END, f"{i+1}. {step}")
            
            # Update selection
            self.sequence_listbox.selection_set(index+1)
            print(f"Moved step from position {index+1} to {index+2}")
    
    def run_sequence(self):
        """Run the current sequence"""
        if not self.current_sequence:
            messagebox.showinfo("Empty Sequence", "The sequence is empty. Please add steps first.")
            return
        
        loop_enabled = self.loop_var.get()
        loop_count = self.loop_count_var.get() if loop_enabled else 1
        
        # Disable UI during execution
        for widget in [self.add_btn, self.delete_btn, self.clear_btn, 
                      self.move_up_btn, self.move_down_btn, self.run_btn]:
            widget.config(state="disabled")
        
        # Start execution in a separate thread
        threading.Thread(target=self._execute_sequence, args=(loop_count,), daemon=True).start()
    
    def _execute_sequence(self, loop_count):
        """Execute the sequence (run in a separate thread)"""
        self.is_running = True
        
        try:
            for loop in range(loop_count):
                if not self.is_running:
                    break
                
                if loop_count > 1:
                    print(f"\nStarting loop {loop+1}/{loop_count}")
                
                for i, step in enumerate(self.current_sequence):
                    if not self.is_running:
                        break
                    
                    # Update UI to show current step
                    self.master.after(0, lambda idx=i: self.sequence_listbox.selection_clear(0, tk.END))
                    self.master.after(0, lambda idx=i: self.sequence_listbox.selection_set(idx))
                    self.master.after(0, lambda idx=i: self.sequence_listbox.see(idx))
                    
                    print(f"Executing step {i+1}: {step}")
                    self._execute_step(step)
            
            print("Sequence execution completed")
        
        except Exception as e:
            print(f"Error during sequence execution: {e}")
            self.master.after(0, lambda: messagebox.showerror("Execution Error", 
                                                            f"Error during sequence execution: {str(e)}"))
        
        finally:
            self.is_running = False
            # Re-enable UI
            self.master.after(0, self._enable_ui_after_run)
    
    def _enable_ui_after_run(self):
        """Re-enable UI controls after sequence execution"""
        for widget in [self.add_btn, self.delete_btn, self.clear_btn, 
                      self.move_up_btn, self.move_down_btn, self.run_btn]:
            widget.config(state="normal")
    
    def _execute_step(self, step):
        """Execute a single step in the sequence"""
        action_type = step.action_type
        params = step.params
        
        # Set appropriate units
        if "unit" in params:
            unit_str = params["unit"]
            if unit_str == "mm":
                self.axis.setUnits(Units.mm)
            elif unit_str == "mu":
                self.axis.setUnits(Units.mu)
            elif unit_str == "nm":
                self.axis.setUnits(Units.nm)
        
        # Execute based on action type
        if action_type == ActionType.MOVE_ABSOLUTE:
            self.axis.setSpeed(params.get("speed", 1.0))
            self.axis.setDPOS(params.get("position", 0))
        
        elif action_type == ActionType.MOVE_RELATIVE:
            self.axis.setSpeed(params.get("speed", 1.0))
            current_pos = self.axis.getEPOS()
            target_pos = current_pos + params.get("distance", 0)
            self.axis.setDPOS(target_pos)
        
        elif action_type == ActionType.HOME:
            self.axis.setSpeed(params.get("speed", 1.0))
            self.axis.setDPOS(0)
        
        elif action_type == ActionType.PAUSE:
            duration = params.get("duration", 1.0)
            print(f"Pausing for {duration} seconds...")
            time.sleep(duration)
        
        elif action_type == ActionType.SET_SPEED:
            self.axis.setSpeed(params.get("speed", 1.0))
        
        elif action_type == ActionType.SCAN:
            self.axis.setSpeed(params.get("speed", 1.0))
            direction = 1 if params.get("direction", "positive") == "positive" else -1
            duration = params.get("duration", 1.0)
            
            if duration > 0:
                self.axis.startScan(direction, duration)
            else:
                self.axis.startScan(direction)
                time.sleep(1.0)  # Default duration
                self.axis.stopScan()
    
    def stop_sequence(self):
        """Stop the currently running sequence"""
        self.is_running = False
        
        # Stop any ongoing movement
        if self.controller and self.axis:
            try:
                self.axis.stopScan()
                self.controller.stopMovements()
            except Exception as e:
                print(f"Error stopping movements: {e}")
        
        print("Sequence execution stopped")
    
    def save_sequence(self):
        """Save the current sequence to a JSON file"""
        if not self.current_sequence:
            messagebox.showinfo("Empty Sequence", "The sequence is empty. Nothing to save.")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Sequence"
            )
            
            if not filename:
                return  # User cancelled
            
            # Convert sequence to JSON-serializable format
            sequence_data = {
                "steps": [step.to_dict() for step in self.current_sequence],
                "loop_enabled": self.loop_var.get(),
                "loop_count": self.loop_count_var.get()
            }
            
            with open(filename, 'w') as f:
                json.dump(sequence_data, f, indent=2)
            
            self.current_file = filename
            print(f"Sequence saved to {filename}")
            messagebox.showinfo("Save Successful", f"Sequence saved to {filename}")
            
        except Exception as e:
            print(f"Error saving sequence: {e}")
            messagebox.showerror("Save Error", f"Error saving sequence: {str(e)}")
    
    def load_sequence(self):
        """Load a sequence from a JSON file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Sequence"
            )
            
            if not filename:
                return  # User cancelled
            
            with open(filename, 'r') as f:
                sequence_data = json.load(f)
            
            # Convert JSON data back to sequence objects
            self.current_sequence = [StepAction.from_dict(step_data) 
                                    for step_data in sequence_data.get("steps", [])]
            
            # Update loop settings if available
            if "loop_enabled" in sequence_data:
                self.loop_var.set(sequence_data["loop_enabled"])
            
            if "loop_count" in sequence_data:
                self.loop_count_var.set(sequence_data["loop_count"])
            
            # Update the listbox
            self.sequence_listbox.delete(0, tk.END)
            for i, step in enumerate(self.current_sequence):
                self.sequence_listbox.insert(tk.END, f"{i+1}. {step}")
            
            self.current_file = filename
            print(f"Sequence loaded from {filename}")
            messagebox.showinfo("Load Successful", f"Sequence loaded from {filename}")
            
        except Exception as e:
            print(f"Error loading sequence: {e}")
            messagebox.showerror("Load Error", f"Error loading sequence: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = SequenceBuilder(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}") 