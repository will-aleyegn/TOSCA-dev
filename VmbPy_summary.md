# VmbPy SDK Summary

## Overview
VmbPy is the Python API for Vimba X SDK, providing access to Allied Vision cameras in a Pythonic way.

## Installation
- Requires Python 3.7+
- Install using provided `.whl` file: `pip install docs/vmpy/vmbpy-1.1.0-py3-none-win_amd64.whl`
- Two types of wheel files:
  - With VmbC libs (platform tag e.g., `win_amd64`): No need for pre-existing Vimba installation
  - Without libs (platform tag `any`): Requires pre-existing Vimba X installation
- Optional dependencies can be installed: `pip install 'file.whl[numpy,opencv]'`

## Basic Usage
```python
import vmbpy

vmb = vmbpy.VmbSystem.get_instance()
with vmb:
    cams = vmb.get_all_cameras()
    for cam in cams:
        print(cam)
```

## Important Concepts
1. **Context Managers**: VmbPy relies on context managers for setup/teardown
2. **Exception Handling**: Main exception types:
   - `vmbpy.VmbFeatureError`: For feature-related errors
   - Regular Python exceptions are used (no VmbCError exists)
3. **Camera Interface**: Accessed through context managers

## Camera Control Examples

### Finding and Connecting to a Camera
```python
import vmbpy

try:
    # Get Vimba instance
    vmb = vmbpy.VmbSystem.get_instance()
    with vmb:
        # List available cameras
        cameras = vmb.get_all_cameras()
        if not cameras:
            print("No cameras found")
            exit(1)
            
        # Access first camera
        with cameras[0] as cam:
            # Get camera ID
            print(f"Using camera: {cam.get_id()}")
            
            # Set features
            try:
                cam.get_feature_by_name("ExposureTime").set_value(10000)  # 10ms
            except Exception as e:
                print(f"Could not set exposure: {str(e)}")
                
            # Capture a frame
            frame = cam.get_frame()
            print(f"Got frame: {frame}")
            
except Exception as e:
    print(f"Error: {str(e)}")
```

### Continuous Frame Acquisition
```python
import vmbpy
import time

def frame_handler(cam, frame):
    print(f"Got frame: {frame}")
    
    # Important: Queue the frame back to the camera
    cam.queue_frame(frame)

try:
    with vmbpy.VmbSystem.get_instance() as vmb:
        with vmb.get_all_cameras()[0] as cam:
            # Start streaming with the frame handler
            cam.start_streaming(frame_handler)
            
            # Stream for 10 seconds
            time.sleep(10)
            
            # Stop streaming
            cam.stop_streaming()
            
except Exception as e:
    print(f"Error: {str(e)}")
```

## Exception Handling Tips
1. Always use context managers to ensure proper resource cleanup
2. Handle expected exceptions specifically
3. Use a catch-all Exception handler for unexpected issues
4. Common exceptions:
   - Feature setting errors (invalid values, unsupported features)
   - Frame errors (timeout, buffer underruns)
   - Connection issues (camera disconnection, transport layer errors)

## Useful Debugging
- Set up proper logging
- VmbPy outputs logs with the logger name 'vmbpyLog'
- Check for transport layer errors at startup

## Common Issues
1. Transport Layer errors: Make sure Vimba X is installed with proper drivers
2. Camera not found: Check camera connection and power
3. Frame errors: Ensure frames are always queued back to the camera
4. Feature errors: Check feature names and valid value ranges

## Important Methods on Camera objects
- `get_id()`: Get camera identifier
- `get_name()`: Get camera name
- `get_feature_by_name()`: Access camera features
- `get_frame()`: Capture a single frame
- `start_streaming()`: Begin continuous acquisition
- `stop_streaming()`: End continuous acquisition
- `queue_frame()`: Required in continuous acquisition to return frames to camera 