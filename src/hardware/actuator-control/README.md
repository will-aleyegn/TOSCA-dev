# Xeryon Stage Control Tools

This repository contains tools for controlling Xeryon piezoelectric stages using the Xeryon Python library.

## Prerequisites

- Python 3.6 or higher
- Xeryon controller connected via USB
- Required packages: `pyserial`, `matplotlib`, `tkinter`

Install required packages:
```
pip install pyserial matplotlib
```
(tkinter is included with standard Python installations)

## Available Tools

### 1. Basic Demo (xeryon_demo.py)

A simple demo script that demonstrates basic functionality of the Xeryon Python library:
- Connecting to the controller
- Moving to absolute positions
- Making relative movements
- Scanning
- Data logging and visualization

Run the demo:
```
python xeryon_demo.py
```

### 2. Sequence Builder (xeryon_sequence_builder.py)

A GUI application for creating, saving, loading, and running sequences of stage movements:

Features:
- Connect to any available COM port
- Create step-by-step movement sequences
- Set speed, position, direction, and timing
- Save and load sequences
- Loop sequences multiple times
- Real-time sequence execution

Run the Sequence Builder:
```
python xeryon_sequence_builder.py
```

## Usage of Sequence Builder

1. **Connect to Controller**
   - Select the COM port from the dropdown
   - Click "Connect"
   - The system will attempt to find the index position

2. **Create a Sequence**
   - Select an action type (Move Absolute, Move Relative, Home, etc.)
   - Set parameters (position, speed, duration, etc.)
   - Click "Add Step"
   - Repeat to build your sequence

3. **Edit Your Sequence**
   - Select a step and use "Delete Step" to remove it
   - Use "Move Up" and "Move Down" to reorder steps
   - Use "Clear All" to start over

4. **Run Your Sequence**
   - Enable/disable looping and set loop count if needed
   - Click "Run Sequence" to execute
   - Click "Stop" to interrupt execution

5. **Save and Load Sequences**
   - Save your sequences for later use with "Save Sequence"
   - Load previously saved sequences with "Load Sequence"

## Troubleshooting

If you encounter thermal protection errors:
1. Power cycle the hardware (unplug for 30+ seconds)
2. Check for physical obstructions
3. Contact Xeryon support (support@xeryon.com)

## Resources

- Xeryon Documentation: [https://xeryon.com/software/xeryon-python-library/](https://xeryon.com/software/xeryon-python-library/)
- Check the Manuals directory for detailed information about your controller 