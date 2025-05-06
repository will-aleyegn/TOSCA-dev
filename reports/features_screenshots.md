# TOSCA Features Screenshots

This document provides screenshots of the key features of the TOSCA Laser Control System. These visual references help users understand the application's functionality and user interface.

## Installation Requirements

To use the screenshot tool, you'll need to install PyAutoGUI:

```bash
pip install pyautogui
```

Then you can run the screenshot tool while the TOSCA application is open:

```bash
python screenshot_tool.py --all
```

## Main Application Window

![Main Window](../screenshots/main_window.png)

This screenshot shows the main application window with:
- Tabbed interface for navigation between different modules
- Status bar showing connected devices and current patient
- Emergency stop button at the bottom right
- Menu bar with File, Hardware, Camera, and Help menus

## Patient Management

### Patient Information Form

![Patient Form](../screenshots/patient_form.png)

This screenshot shows the patient information form with:
- Fields for patient personal information (name, DOB, gender)
- Contact information section
- Medical history section
- Notes section
- Save/Load/Export buttons

### Patient Selection Dialog

![Patient Selection](../screenshots/patient_selection.png)

This screenshot shows the patient selection dialog with:
- List of patients in the database
- Search/filter functionality
- Options to create a new patient or open selected patient

## Treatment Session Management

### Treatment Session Form

![Treatment Session](../screenshots/treatment_session.png)

This screenshot shows the treatment session management interface with:
- List of treatment sessions for the current patient (left panel)
- Session details form (right panel)
- Device settings section
- Session notes section
- Images associated with the session
- Controls to add/view images

## Camera Control

### Camera Display

![Camera Display](../screenshots/camera_display.png)

This screenshot shows the camera control interface with:
- Live video feed from the connected camera
- Camera connection controls
- Stream start/stop controls
- Image capture button
- Camera settings (exposure, gain controls)
- Status indicators

## Laser Control

![Laser Control](../screenshots/laser_control.png)

This screenshot shows the laser control interface with:
- Laser power controls
- Safety interlocks
- Treatment parameter settings
- Treatment application controls
- Status indicators

## Data Integration

### Image Added to Session Prompt

![Image Added to Session](../screenshots/image_added.png)

This screenshot shows the prompt that appears when capturing an image with a patient selected:
- Dialog asking if the user wants to add the image to the current treatment session
- Options to add to session or cancel

### Patient-Specific Image Directory

![Patient Image Directory](../screenshots/patient_images.png)

This screenshot shows the file explorer view of a patient's image directory:
- Organization of images by patient ID
- Naming convention for images including patient information and capture parameters
- "Latest" image for quick reference

## Taking Screenshots

To capture specific features or interactions in the TOSCA application:

1. Run the TOSCA application and navigate to the screen you want to capture
2. Open a command prompt and run:
   ```bash
   python screenshot_tool.py --name feature_name
   ```
3. Replace `feature_name` with a descriptive name for the screenshot
4. The script will capture the current screen after a brief delay
5. Screenshots are saved in the `docs/screenshots` directory with timestamps

You can also use the interactive mode to capture all main screens:
```bash
python screenshot_tool.py --all
``` 