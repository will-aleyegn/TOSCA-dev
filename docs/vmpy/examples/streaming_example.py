#!/usr/bin/env python3
"""
Streaming Example for VmbPy

This example demonstrates how to capture continuous frames from a camera using VmbPy.
It uses the proper frame callback introduced in VmbPy 1.1.0 that requires
three parameters: camera, stream, and frame.
"""

import sys
import time
import cv2
import numpy as np
try:
    import vmbpy
except ImportError:
    print("VmbPy module not found. Please install it first.")
    sys.exit(1)

def print_camera_info(cam):
    """Print out camera information."""
    print("Camera ID: ", cam.get_id())
    print("Camera Name: ", cam.get_name())
    print("Camera Model: ", cam.get_model())
    print("Camera Serial: ", cam.get_serial())
    print("Camera Interface ID: ", cam.get_interface_id())

def frame_handler(cam, stream, frame):
    """
    This is the callback function that will be executed for each acquired frame.
    
    Args:
        cam: The Camera object
        stream: The Stream object
        frame: The Frame object containing the image data
    """
    print(f"Frame received - ID: {frame.get_id()}")
    
    # Convert frame to a displayable format
    try:
        # Convert frame to numpy array (requires numpy extra)
        if hasattr(frame, 'as_opencv_image'):
            image = frame.as_opencv_image()
        else:
            image = frame.as_numpy_array()
            
        # Display the image (rescale for visibility)
        display_image = cv2.resize(image, (800, 600))
        cv2.imshow("VmbPy Streaming Demo", display_image)
        cv2.waitKey(1)
        
    except Exception as e:
        print(f"Error converting frame: {str(e)}")
    
    # Important: Queue the frame back to the camera for reuse
    try:
        cam.queue_frame(frame)
    except Exception as e:
        print(f"Error queuing frame: {str(e)}")

def main():
    with vmbpy.VmbSystem.get_instance() as vmb:
        # Print API version
        print("VmbPy version:", vmbpy.__version__)
        
        # Get all connected cameras
        try:
            cameras = vmb.get_all_cameras()
            if not cameras:
                print("No cameras found!")
                return
            
            print(f"Found {len(cameras)} camera(s)")
            for i, cam in enumerate(cameras):
                print(f"Camera {i}: {cam.get_id()}")
                
            # Connect to the first camera
            with cameras[0] as cam:
                # Print camera info
                print_camera_info(cam)
                
                try:
                    # Try to adjust some camera settings (exposure, gain)
                    try:
                        cam.get_feature_by_name("ExposureAuto").set_value("Off")
                        cam.get_feature_by_name("ExposureTime").set_value(30000)  # 30ms
                    except (AttributeError, vmbpy.VmbFeatureError) as e:
                        print(f"Could not set exposure: {str(e)}")
                        
                    try:
                        cam.get_feature_by_name("GainAuto").set_value("Off")
                        cam.get_feature_by_name("Gain").set_value(10.0)
                    except (AttributeError, vmbpy.VmbFeatureError) as e:
                        print(f"Could not set gain: {str(e)}")
                        
                    # Create frames for streaming
                    frame_count = 5
                    frames = [cam.get_frame() for _ in range(frame_count)]
                    print(f"Created {frame_count} frames for streaming")
                    
                    # Queue frames to camera
                    for frame in frames:
                        cam.queue_frame(frame)
                    
                    # Start streaming with our frame handler
                    print("Starting continuous image acquisition...")
                    cam.start_streaming(frame_handler)
                    
                    # Stream for some time
                    stream_duration_sec = 30
                    print(f"Streaming for {stream_duration_sec} seconds. Press Ctrl+C to stop earlier.")
                    try:
                        time.sleep(stream_duration_sec)
                    except KeyboardInterrupt:
                        print("Streaming stopped by user.")
                    
                    # Stop streaming
                    cam.stop_streaming()
                    cv2.destroyAllWindows()
                    
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
        
        except Exception as e:
            print(f"Error accessing cameras: {str(e)}")
            
if __name__ == "__main__":
    main() 