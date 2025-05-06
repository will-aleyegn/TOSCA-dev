"""
Actuator Controller Module

This module provides an interface for controlling the motion actuator 
on the TOSCA laser device.
"""

import time
import logging
import serial
import threading

logger = logging.getLogger(__name__)

class ActuatorController:
    """
    Controller class for interfacing with the TOSCA device actuator.
    
    This class provides methods to initialize, move, and control the position
    of the mechanical actuator on the TOSCA laser device.
    """
    
    # Actuator movement constants
    MAX_SPEED = 100.0  # Maximum speed in percentage
    HOME_POSITION = (0, 0, 0)  # Default home position (x, y, z)
    
    def __init__(self, port=None, baudrate=115200, timeout=1.0):
        """
        Initialize the actuator controller.
        
        Args:
            port (str, optional): Serial port for actuator communication. None for auto-detect.
            baudrate (int): Baud rate for serial communication
            timeout (float): Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.connected = False
        self.current_position = None
        self.is_moving = False
        self.motion_lock = threading.Lock()
        
    def connect(self, port=None):
        """
        Connect to the actuator controller.
        
        Args:
            port (str, optional): Serial port to use. If None, uses instance port or auto-detects.
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if port is not None:
            self.port = port
            
        # Use the provided port or auto-detect
        if self.port is None:
            # Try to auto-detect the actuator port
            # This implementation depends on specific characteristics of the TOSCA actuator
            # You will need to modify this for your specific device
            from serial.tools import list_ports
            
            available_ports = list(list_ports.comports())
            for port_info in available_ports:
                # Look for identifying information that would indicate this is the actuator
                # For example, check the hardware ID, description, or other attributes
                if "TOSCA_ACTUATOR" in port_info.description or "ACTUATOR" in port_info.description:
                    self.port = port_info.device
                    logger.info(f"Auto-detected actuator on port {self.port}")
                    break
                    
            if self.port is None:
                logger.error("Failed to auto-detect actuator port")
                return False
                
        try:
            # Establish serial connection
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Verify connection by sending a test command
            if self._verify_connection():
                self.connected = True
                logger.info(f"Connected to actuator on {self.port}")
                
                # Get the current position
                self.current_position = self.get_position()
                return True
            else:
                if self.connection:
                    self.connection.close()
                self.connection = None
                logger.error(f"Failed to verify actuator on {self.port}")
                return False
                
        except serial.SerialException as e:
            logger.error(f"Error connecting to actuator: {str(e)}")
            if self.connection:
                self.connection.close()
            self.connection = None
            return False
    
    def disconnect(self):
        """
        Disconnect from the actuator.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if not self.connection:
            return True  # Already disconnected
            
        try:
            # Stop any ongoing movement
            if self.is_moving:
                self.stop()
                
            # Close the connection
            self.connection.close()
            self.connection = None
            self.connected = False
            logger.info("Disconnected from actuator")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from actuator: {str(e)}")
            return False
    
    def is_connected(self):
        """
        Check if the controller is connected to the actuator.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected and self.connection is not None and self.connection.is_open
    
    def home(self):
        """
        Move the actuator to its home position.
        
        Returns:
            bool: True if homing was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot home: Not connected to actuator")
            return False
            
        try:
            with self.motion_lock:
                self.is_moving = True
                
                # Send the home command
                response = self._send_command("HOME")
                
                if response and "OK" in response:
                    # Wait for the homing to complete
                    wait_start_time = time.time()
                    max_wait_sec = 30 # Example: 30 seconds max wait for homing
                    while self._is_actuator_busy():
                        time.sleep(0.1)
                        if time.time() - wait_start_time > max_wait_sec:
                            logger.error(f"Homing timeout after {max_wait_sec} seconds. Actuator might be stuck.")
                            self.is_moving = False
                            return False # Or raise an exception
                            
                    # Update current position
                    self.current_position = self.HOME_POSITION
                    self.is_moving = False
                    logger.info("Actuator homed successfully")
                    return True
                else:
                    self.is_moving = False
                    logger.error("Failed to home actuator")
                    return False
                    
        except Exception as e:
            self.is_moving = False
            logger.error(f"Error during homing: {str(e)}")
            return False
    
    def move_to(self, x=None, y=None, z=None, speed=50.0):
        """
        Move the actuator to an absolute position.
        
        Args:
            x (float, optional): X-axis position (units depend on the actuator)
            y (float, optional): Y-axis position (units depend on the actuator)
            z (float, optional): Z-axis position (units depend on the actuator)
            speed (float): Movement speed as percentage of maximum speed (0-100)
        
        Returns:
            bool: True if movement was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot move: Not connected to actuator")
            return False
            
        # Check if any position is provided
        if x is None and y is None and z is None:
            logger.error("No position specified for movement")
            return False
            
        # Clamp speed to valid range
        speed = max(0.0, min(100.0, speed))
        
        try:
            with self.motion_lock:
                self.is_moving = True
                
                # Get current position for any unspecified axes
                if self.current_position is None:
                    self.current_position = self.get_position()
                    if self.current_position is None:
                        self.is_moving = False
                        return False
                        
                current_x, current_y, current_z = self.current_position
                
                # Use current position for any unspecified axis
                target_x = x if x is not None else current_x
                target_y = y if y is not None else current_y
                target_z = z if z is not None else current_z
                
                # Send the move command
                command = f"MOVE X{target_x:.2f} Y{target_y:.2f} Z{target_z:.2f} S{speed:.1f}"
                response = self._send_command(command)
                
                if response and "OK" in response:
                    # Wait for the movement to complete
                    wait_start_time = time.time()
                    max_wait_sec = 60 # Example: 60 seconds max wait for movement
                    while self._is_actuator_busy():
                        time.sleep(0.1)
                        if time.time() - wait_start_time > max_wait_sec:
                            logger.error(f"Movement timeout after {max_wait_sec} seconds. Actuator might be stuck.")
                            self.is_moving = False
                            return False # Or raise an exception
                            
                    # Update current position
                    self.current_position = (target_x, target_y, target_z)
                    self.is_moving = False
                    logger.info(f"Actuator moved to position: X={target_x}, Y={target_y}, Z={target_z}")
                    return True
                else:
                    self.is_moving = False
                    logger.error(f"Failed to move actuator to X={target_x}, Y={target_y}, Z={target_z}")
                    return False
                    
        except Exception as e:
            self.is_moving = False
            logger.error(f"Error during movement: {str(e)}")
            return False
    
    def move_relative(self, dx=0, dy=0, dz=0, speed=50.0):
        """
        Move the actuator by a relative distance.
        
        Args:
            dx (float): Relative movement along X-axis
            dy (float): Relative movement along Y-axis
            dz (float): Relative movement along Z-axis
            speed (float): Movement speed as percentage of maximum speed (0-100)
        
        Returns:
            bool: True if movement was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot move: Not connected to actuator")
            return False
            
        # Check if any movement is requested
        if dx == 0 and dy == 0 and dz == 0:
            logger.info("No movement specified")
            return True
            
        # Get current position
        if self.current_position is None:
            self.current_position = self.get_position()
            if self.current_position is None:
                return False
                
        # Calculate target position
        current_x, current_y, current_z = self.current_position
        target_x = current_x + dx
        target_y = current_y + dy
        target_z = current_z + dz
        
        # Perform the move
        return self.move_to(target_x, target_y, target_z, speed)
    
    def stop(self):
        """
        Stop any ongoing actuator movement immediately.
        
        Returns:
            bool: True if stop command was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot stop: Not connected to actuator")
            return False
            
        try:
            # Send the stop command
            response = self._send_command("STOP", timeout=0.5)
            
            # Update status
            self.is_moving = False
            
            if response and "OK" in response:
                logger.info("Actuator stopped")
                
                # Update position after stopping
                self.current_position = self.get_position()
                return True
            else:
                logger.error("Failed to stop actuator")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping actuator: {str(e)}")
            return False
    
    def get_position(self):
        """
        Get the current position of the actuator.
        
        Returns:
            tuple or None: (x, y, z) position or None if failed
        """
        if not self.is_connected():
            logger.error("Cannot get position: Not connected to actuator")
            return None
            
        try:
            # Request the current position
            response = self._send_command("GET_POS")
            
            if not response:
                logger.error("Failed to get actuator position")
                return None
                
            # Parse the position from the response
            # Example response format: "POS X:10.00 Y:20.00 Z:5.00"
            # Modify this parsing according to your actuator's response format
            try:
                # Look for X, Y, Z values in the response
                x = y = z = 0.0
                
                for part in response.strip().split():
                    if part.startswith("X:"):
                        x = float(part.split(":")[1])
                    elif part.startswith("Y:"):
                        y = float(part.split(":")[1])
                    elif part.startswith("Z:"):
                        z = float(part.split(":")[1])
                        
                self.current_position = (x, y, z)
                return (x, y, z)
                
            except Exception as e:
                logger.error(f"Error parsing position response: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting actuator position: {str(e)}")
            return None
    
    def get_status(self):
        """
        Get the current status of the actuator.
        
        Returns:
            dict or None: Status information dict or None if failed
        """
        if not self.is_connected():
            logger.error("Cannot get status: Not connected to actuator")
            return None
            
        try:
            # Request the status
            response = self._send_command("STATUS")
            
            if not response:
                logger.error("Failed to get actuator status")
                return None
                
            # Parse the status from the response
            # Modify this parsing according to your actuator's response format
            status = {
                'connected': self.is_connected(),
                'moving': self.is_moving,
                'position': self.current_position,
                'error': None
            }
            
            # Example parsing for status response
            for line in response.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'error':
                        status['error'] = value if value != 'none' else None
                    elif key == 'state':
                        status['moving'] = value.lower() == 'moving'
                        
            return status
            
        except Exception as e:
            logger.error(f"Error getting actuator status: {str(e)}")
            return None
    
    def _send_command(self, command, timeout=None):
        """
        Send a command to the actuator and get the response.
        
        Args:
            command (str): Command to send
            timeout (float, optional): Custom timeout for this command
            
        Returns:
            str or None: Response string or None if failed
        """
        if not self.is_connected():
            return None
            
        try:
            # Set custom timeout if specified
            original_timeout = None
            if timeout is not None and self.connection:
                original_timeout = self.connection.timeout
                self.connection.timeout = timeout
                
            # Add command termination if needed
            if not command.endswith('\r\n'):
                command += '\r\n'
                
            # Send the command
            self.connection.write(command.encode('utf-8'))
            logger.debug(f"Sent command to actuator: {command.strip()}")
            
            # Read the response
            response = ""
            start_time = time.time()
            max_time = start_time + (timeout if timeout is not None else self.timeout)
            
            while time.time() < max_time:
                if self.connection.in_waiting > 0:
                    chunk = self.connection.readline().decode('utf-8', errors='replace')
                    response += chunk
                    if chunk.endswith('\n'):  # End of response
                        break
                time.sleep(0.01)
                
            # Restore original timeout
            if original_timeout is not None:
                self.connection.timeout = original_timeout
                
            if response:
                logger.debug(f"Received response from actuator: {response.strip()}")
                return response.strip()
            else:
                logger.debug("No response received from actuator (timeout)")
                return None
                
        except Exception as e:
            logger.error(f"Error sending command to actuator: {str(e)}")
            return None
    
    def _verify_connection(self):
        """
        Verify that we're connected to the actuator.
        
        Returns:
            bool: True if verified, False otherwise
        """
        # Send a simple command that the actuator should respond to
        # Example: query version or status
        response = self._send_command("*IDN?")
        
        # Check for expected response indicating this is the TOSCA actuator
        # Modify this check according to your actuator's response format
        return response is not None and "TOSCA" in response
    
    def _is_actuator_busy(self):
        """
        Check if the actuator is currently moving.
        
        Returns:
            bool: True if busy/moving, False if idle
        """
        response = self._send_command("IS_BUSY?")
        
        # Modify this check according to your actuator's response format
        if response and "BUSY" in response.upper():
            return True
        elif response and "IDLE" in response.upper():
            return False
        else:
            # If we can't determine the state, assume it's not busy
            return False 