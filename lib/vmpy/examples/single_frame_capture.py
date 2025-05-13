#!/usr/bin/env python3
"""
Single Frame Capture Example for VmbPy

This example demonstrates how to capture a single frame from a camera using VmbPy.
"""

import sys
import cv2
try:
    import vmbpy
except ImportError:
    print("VmbPy module not found. Please install it first.")
    sys.exit(1)

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
                print("Camera ID:", cam.get_id())
                print("Camera Name:", cam.get_name())
                
                # Try to adjust some camera settings
                try:
                    cam.get_feature_by_name("ExposureAuto").set_value("Off")
                    cam.get_feature_by_name("ExposureTime").set_value(20000)  # 20ms
                    print("Set exposure to 20ms")
                except (AttributeError, vmbpy.VmbFeatureError) as e:
                    print(f"Could not set exposure: {str(e)}")
                
                # Capture a single frame
                print("Capturing a single frame...")
                frame = cam.get_frame()
                print(f"Frame captured - ID: {frame.get_id()}")
                
                # Convert frame to OpenCV format
                try:
                    # Convert frame to numpy array (requires numpy extra)
                    if hasattr(frame, 'as_opencv_image'):
                        image = frame.as_opencv_image()
                    else:
                        image = frame.as_numpy_array()
                    
                    # Save image to file
                    filename = "captured_frame.png"
                    cv2.imwrite(filename, image)
                    print(f"Image saved to {filename}")
                    
                    # Display the image
                    cv2.imshow("Captured Frame", image)
                    print("Press any key to exit...")
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    
                except Exception as e:
                    print(f"Error processing frame: {str(e)}")
        
        except Exception as e:
            print(f"Error accessing cameras: {str(e)}")
            
if __name__ == "__main__":
    main() 