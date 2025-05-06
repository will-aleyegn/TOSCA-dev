# VmbPy SDK and API Summary

This document summarizes key information about the VmbPy SDK (the Python API for Vimba X), based on the provided `docs/vmpy/README.md` and the official [Python API Manual](https://docs.alliedvision.com/Vimba_X/Vimba_X_DeveloperGuide/pythonAPIManual.html).

## Overview

*   **VmbPy:** The official Python API (wrapper) for Allied Vision's Vimba X SDK, built upon the VmbC API.
*   **Purpose:** Allows control of Allied Vision cameras using Python. Recommended for quick prototyping, getting started with machine vision, and easy interfacing with libraries like OpenCV and NumPy.
*   **Based on:** VmbC (the C API of Vimba X).
*   **Design:** Aims for a pythonic interface using context managers and standard Python practices. Structure is similar to VmbCPP to ease potential migration for performance-critical applications.
*   **GenICam Compliant:** Fully supports the GenICam standard.
*   **Detailed Reference:** For a complete function and class reference, see the HTML documentation within the `docs/VmbPy_Function_Reference` directory.

## Compatibility

*   **Operating Systems:** See Vimba X Release Notes for supported OS.
*   **Python:** Version >= 3.7.x required (64-bit interpreter recommended for 64-bit OS).

## Installation

*   **Prerequisites:**
    *   Python >= 3.7 installed.
    *   `pip` package installer available.
    *   Vimba X SDK installed (provides Transport Layers, drivers, and potentially the required VmbC version). Check VmbPy/Vimba X compatibility.
    *   (Windows) Visual C++ Redistributable might be required if Vimba X SDK is not fully installed.
*   **Package:** VmbPy is provided as a `.whl` file within the Vimba X installation directory (recommended source) or downloadable from [GitHub](https://github.com/alliedvision/VmbPy/releases).
*   **Installation Command:** `pip install /path/to/vmbpy-X.Y.Z*.whl` (use `python -m pip` or `pip3` if needed).
*   **Wheel Types:**
    *   **With VmbC libs (Recommended, platform-specific tag like `win_amd64`):** Includes necessary VmbC libraries. Still requires Vimba X installation or manual setup for Transport Layers (TLs) and drivers.
    *   **Without VmbC libs (`any` platform tag):** Requires a full Vimba X installation on the system for VmbC libraries.
*   **Optional Dependencies (Extras):** Install using `pip install '/path/to/vmbpy*.whl[extra1,extra2]'`
    *   `numpy`: For converting `Frame` objects to NumPy arrays (`frame.as_numpy_ndarray()`).
    *   `opencv`: Ensures NumPy arrays are valid OpenCV images (`frame.as_opencv_image()`, requires `numpy`).
    *   `test`: Development tools (`flake8`, `mypy`, `coverage`) for running the full test suite.
*   **Important Note:** Updating the Vimba X SDK does *not* automatically update VmbPy. Reinstall the VmbPy `.whl` manually after SDK updates, especially if encountering an "Invalid VmbC Version" error.

## Core Concepts & Usage

*   **Entry Point:** `VmbSystem` singleton. Get via `vmbpy.VmbSystem.get_instance()`.
*   **Context Managers (`with` statement):** **Crucial** for resource management. Used for `VmbSystem` (API init/shutdown), `Camera` (open/close, feature discovery), `Stream`, `Interface`, `FeatureContainer`, etc. *Always* interact with these objects within their `with` scope.
    ```python
    from vmbpy import *
    with VmbSystem.get_instance() as vmb: # Initialize Vimba X
        cams = vmb.get_all_cameras()
        if cams:
            with cams[0] as cam: # Open camera, load features
                # Access features, start/stop streaming
                pass # Camera automatically closed
        # Vimba X automatically shut down
    ```
*   **Listing Devices:**
    *   `vmb.get_all_cameras()`
    *   `vmb.get_all_interfaces()`
*   **Accessing Features:** Access camera features (GenICam nodes) by name within the `Camera` context.
    ```python
    with cam:
        # Get feature object
        exposure = cam.get_feature_by_name('ExposureTime')
        # Set value
        exposure.set(10000)
        # Get value
        current_exp = exposure.get()
        print(f"Current exposure: {current_exp} µs")

        # Check available enum values
        pixel_format = cam.get_feature_by_name('PixelFormat')
        if pixel_format.is_readable(): # Check if readable first
           print(f"Available formats: {pixel_format.get_available_values()}")
        # Set enum value (string)
        # NOTE: For PixelFormat, use cam.set_pixel_format() instead (see below)
        # pixel_format.set('Mono8')
    ```
*   **Pixel Format Handling:** *Do not* set via the `PixelFormat` feature directly. Use `Camera` methods:
    *   `cam.get_pixel_formats()`: Returns tuple of supported `PixelFormat` enum members.
    *   `cam.get_pixel_format()`: Returns current `PixelFormat` enum member.
    *   `cam.set_pixel_format(PixelFormat.Mono8)`: Sets the camera's pixel format *before* streaming.
    *   `frame.convert_pixel_format(PixelFormat.Mono8)`: Converts an already acquired `Frame` object's pixel data to a different format (if supported by ImageTransform library).
*   **Image Acquisition (Streaming):**
    *   **Asynchronous (Recommended for GUI/continuous):**
        *   Define a callback function: `def frame_handler(cam: Camera, stream: Stream, frame: Frame): ...`
        *   **Inside callback:** Process the `frame`, then **must queue it back**: `cam.queue_frame(frame)`.
        *   Start: `cam.start_streaming(handler=frame_handler, buffer_count=N)`
        *   Stop: `cam.stop_streaming()`
    *   **Synchronous:**
        *   Single frame: `frame = cam.get_frame(timeout_ms=1000)`
        *   Multiple frames (generator): `for frame in cam.get_frame_generator(limit=10, timeout_ms=1000): ...`
*   **Frame Object:**
    *   Contains image data (`frame.get_buffer()`) and metadata.
    *   Convert to NumPy: `numpy_array = frame.as_numpy_ndarray()` (requires `numpy` extra).
    *   Convert to OpenCV: `opencv_image = frame.as_opencv_image()` (requires `opencv` extra).
    *   Access Chunk Data (if enabled on camera): `frame.access_chunk_data(chunk_callback_func)`.
*   **Chunk Data:** Access image metadata embedded in the frame (e.g., timestamp, exposure). Requires enabling Chunk Mode on the camera first.
*   **User Sets:** Load/save camera settings to/from the camera's non-volatile memory using `UserSetSelector`, `UserSetLoad`, `UserSetSave` features.
*   **Settings Files (XML):** Load/save camera settings to/from an XML file on the host PC using `cam.load_settings('path/to/settings.xml')` and `cam.save_settings('path/to/settings.xml')`.
*   **Software Trigger:**
    *   Set trigger source: `cam.TriggerSource.set('Software')`
    *   Set trigger selector (e.g., FrameStart): `cam.TriggerSelector.set('FrameStart')`
    *   Enable trigger mode: `cam.TriggerMode.set('On')`
    *   Execute trigger: `cam.TriggerSoftware.run()`
*   **Trigger over Ethernet (ToE):** Use Action Commands for synchronized triggering of multiple GigE cameras (see Application Note).

## Configuration

*   **Transport Layers (TLs):** VmbPy finds TLs (`.cti` files) via:
    *   `GENICAM_GENTL64_PATH` (64-bit) / `GENICAM_GENTL32_PATH` (32-bit) environment variable (points to dir containing `.cti`, e.g., `<VimbaX_Install>/VimbaTL/CTI`). This is the standard method.
    *   Advanced configuration via `VmbC.xml` (location depends on `.whl` type) or `VmbSystem.set_path_configuration`.

## Key Classes (Examples)

*   `VmbSystem`: Singleton API entry point.
*   `Camera`: Represents a camera device; access features, control streaming.
*   `Stream`: Represents the data stream from a camera.
*   `Interface`: Represents a system interface (e.g., network card).
*   `Feature`: Represents a camera setting (GenICam node).
*   `Frame`: Contains acquired image data and metadata.
*   `PixelFormat`: Enum for pixel formats.
*   `Log`: Access logging configuration.

## Examples

Code examples are available in `docs/vmpy/examples/` and referenced in the official manual.

## Troubleshooting & Logging

*   **Common Issues:**
    *   `GENICAM_GENTL..._PATH` not set or points to wrong directory.
    *   VmbPy version incompatible with installed Vimba X SDK C API version (`VmbSystem.get_version()` to check). Reinstall VmbPy `.whl` after SDK updates.
    *   Trying to set `PixelFormat` feature directly instead of using `cam.set_pixel_format()`.
*   **Logging:** Useful for debugging and understanding API calls.
    *   Enable: `vmb.enable_log(LOG_CONFIG_...)` (e.g., `LOG_CONFIG_WARNING_CONSOLE_ONLY`, `LOG_CONFIG_INFO_FILE_ONLY`, `LOG_CONFIG_TRACE_FILE_ONLY`).
    *   Disable: `vmb.disable_log()`.
    *   Get logger instance: `log = Log.get_instance()` (to manually log messages: `log.info(...)`, `log.warning(...)`, etc.).
    *   Decorators:
        *   `@TraceEnable()`: Logs entry/exit of decorated function (level Trace).
        *   `@ScopedLogEnable(LOG_CONFIG_...)`: Enables specific logging level only for the duration of the decorated function call.

---
*Source: [Allied Vision VmbPy Documentation](https://docs.alliedvision.com/Vimba_X/Vimba_X_DeveloperGuide/pythonAPIManual.html)* 