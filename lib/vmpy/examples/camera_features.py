#!/usr/bin/env python3
"""
Camera Features Example for VmbPy

This example demonstrates how to access and modify camera features using VmbPy.
"""

import sys
try:
    import vmbpy
except ImportError:
    print("VmbPy module not found. Please install it first.")
    sys.exit(1)

def print_feature_info(feature):
    """Print information about a camera feature."""
    print(f"Feature: {feature.get_name()}")
    print(f"  Display Name: {feature.get_display_name()}")
    print(f"  Type: {feature.get_type().name}")
    print(f"  Access Mode: {feature.get_access_mode().name}")
    
    try:
        if feature.get_type() in (vmbpy.VmbFeatureType.Integer, vmbpy.VmbFeatureType.Float, 
                                vmbpy.VmbFeatureType.Enumeration):
            print(f"  Current Value: {feature.get_value()}")
            
        if feature.get_type() == vmbpy.VmbFeatureType.Integer:
            print(f"  Min: {feature.get_range()[0]}, Max: {feature.get_range()[1]}, Inc: {feature.get_increment()}")
        elif feature.get_type() == vmbpy.VmbFeatureType.Float:
            print(f"  Min: {feature.get_range()[0]}, Max: {feature.get_range()[1]}")
        elif feature.get_type() == vmbpy.VmbFeatureType.Enumeration:
            print("  Available values:")
            for entry in feature.get_entries():
                print(f"    - {entry.name} ({entry.value})")
    except (AttributeError, vmbpy.VmbFeatureError) as e:
        print(f"  Could not read value/range: {str(e)}")
    
    print()

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
                print(f"\nCamera Info for {cam.get_id()}:")
                print("========================")
                print(f"Name: {cam.get_name()}")
                print(f"Model: {cam.get_model()}")
                print(f"Serial: {cam.get_serial()}")
                print(f"Interface ID: {cam.get_interface_id()}")
                print()
                
                # Get and print important features
                print("Important Camera Features:")
                print("=========================")
                important_features = [
                    "Width", "Height", "PixelFormat", 
                    "ExposureAuto", "ExposureTime", 
                    "GainAuto", "Gain"
                ]
                
                for feature_name in important_features:
                    try:
                        feature = cam.get_feature_by_name(feature_name)
                        print_feature_info(feature)
                    except (AttributeError, vmbpy.VmbFeatureError) as e:
                        print(f"Feature '{feature_name}' not available: {str(e)}")
                        print()
                
                # Example of setting features
                print("Setting some features:")
                print("=====================")
                
                # Try to set pixel format to Mono8
                try:
                    pixel_format = cam.get_feature_by_name("PixelFormat")
                    original_format = pixel_format.get_value()
                    print(f"Original pixel format: {original_format}")
                    
                    # Try to set to Mono8 if available
                    available_formats = [entry.name for entry in pixel_format.get_entries()]
                    if "Mono8" in available_formats:
                        pixel_format.set_value("Mono8")
                        print(f"Set pixel format to: Mono8")
                    else:
                        print(f"Mono8 not available. Available formats: {available_formats}")
                        
                    # Read back the value to confirm
                    current_format = pixel_format.get_value()
                    print(f"Current pixel format: {current_format}")
                    
                    # Return to original format
                    pixel_format.set_value(original_format)
                    print(f"Restored pixel format to: {original_format}")
                    
                except (AttributeError, vmbpy.VmbFeatureError) as e:
                    print(f"Could not set pixel format: {str(e)}")
                
                print()
                
                # Get all features (optional, can be a lot of output)
                print("Do you want to list all camera features? (y/n)")
                choice = input().strip().lower()
                if choice == 'y':
                    print("\nAll Camera Features:")
                    print("===================")
                    for feature in cam.get_all_features():
                        print_feature_info(feature)
        
        except Exception as e:
            print(f"Error accessing cameras: {str(e)}")
            
if __name__ == "__main__":
    main() 