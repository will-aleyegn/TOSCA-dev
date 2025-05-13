# Allied Vision VmbPy SDK Documentation and Examples Summary

## Overview

VmbPy is the Python API of the Allied Vision Vimba X SDK. It provides a pythonic interface to access the full functionality of the Vimba X SDK, which is the successor to the Vimba SDK. VmbPy is fully GenICam compliant, allowing for rapid development of camera control applications.

## Installation Requirements

- Python 3.7 or higher
- Installation via provided `.whl` file from either:
  - Vimba X installation package
  - Allied Vision GitHub release page
- Two `.whl` types available:
  - Recommended: With included VmbC libs (platform tag e.g., `win_amd64`)
  - Alternative: Without included VmbC libs (platform tag `any`) - requires pre-existing Vimba X installation

## Optional Dependencies

VmbPy defines several optional dependency packages:
- **numpy**: Enables conversion of `VmbPy.Frame` objects to NumPy arrays
- **opencv**: Ensures NumPy arrays are valid OpenCV images
- **test**: Tools for executing the test suite (flake8, mypy, coverage)

## Usage Principles

VmbPy follows these design principles:
1. Uses Python context managers for setup and teardown
2. Resembles VmbCPP design for easy migration
3. Manages resources correctly, even when errors occur

### Basic Usage Example

```python
import vmbpy

vmb = vmbpy.VmbSystem.get_instance()
with vmb:
    cams = vmb.get_all_cameras()
    for cam in cams:
        print(cam)
```

## Configuration

- Uses the `VmbC.xml` configuration file
- Default configuration loads Transport Layers from the `GENICAM_GENTL64_PATH` environment variable
- Configuration location:
  - For `.whl` with included libs: `/site-packages/vmbpy/c_binding/lib`
  - For `.whl` without included libs: `/api/bin` in Vimba X installation
- Custom configuration possible via `VmbSystem.set_path_configuration`

## SDK Examples

### 1. Single Frame Capture (`single_frame_capture.py`)

Demonstrates how to:
- Connect to a camera
- Configure basic settings (exposure)
- Capture a single frame
- Convert the frame to OpenCV format
- Save and display the captured image

Key functions:
- `vmb.get_all_cameras()` - Lists available cameras
- `camera.get_frame()` - Captures a single frame
- `frame.as_opencv_image()` - Converts to OpenCV format

### 2. Continuous Streaming (`streaming_example.py`)

Demonstrates how to:
- Configure camera settings (exposure, gain)
- Set up continuous streaming with a callback
- Handle frames in real-time
- Display the live video feed

Key components:
- Frame callback function with the signature: `frame_handler(camera, stream, frame)`
- Frame queue management with `cam.queue_frame(frame)`
- Stream control with `start_streaming()` and `stop_streaming()`

### 3. Camera Features Access (`camera_features.py`)

Shows how to:
- Access camera features (parameters)
- Get information about feature types, ranges, and available values
- Read current values
- Modify camera settings
- Handle camera-specific feature variations

Feature types demonstrated:
- Integer features (with min, max, increment)
- Float features (with min, max)
- Enumeration features (with available options)

## Best Practices

1. Always use context managers (`with` statements) for proper resource management
2. Queue frames back to the camera during streaming
3. Handle exceptions appropriately for camera-specific features
4. Check feature availability before attempting to access or modify
5. Consider camera feature dependencies when setting parameters

## Testing

The SDK includes a comprehensive test suite that can be run using:
- Python's unittest discovery mechanism
- The provided `run_tests.py` script

## Compatibility

VmbPy is the successor to VimbaPython, with some significant differences. A migration guide is available in the Vimba X SDK documentation.

## Note for Production Use

- VmbPy aims to be performant but may not be fast enough for performance-critical applications
- For high-performance requirements, consider migrating to VmbCPP
- Beta versions are available for testing but not recommended for production 