"""
Laser Device Controller Module

This module provides an interface for communicating with and controlling
a laser device via serial communication.
"""

import time
import logging
import serial
from serial.tools import list_ports

logger = logging.getLogger(__name__)

class LaserController:
    """
    Controller class for interfacing with a laser device over serial connection.
    
    This class provides methods to connect to, configure, and control a laser device.
    It handles the communication protocol, command formatting, and response parsing.
    """
    
    def __init__(self, port=None, baudrate=9600, timeout=1):
        """
        Initialize the laser controller.
        
        Args:
            port (str, optional): Serial port to connect to. If None, will attempt auto-detection.
            baudrate (int, optional): Baud rate for serial communication. Defaults to 9600.
            timeout (float, optional): Read timeout in seconds. Defaults to 1.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.connected = False
        self.device_info = {}
        
    def list_available_ports(self):
        """
        List all available serial ports on the system.
        
        Returns:
            list: List of available serial port names.
        """
        available_ports = list_ports.comports()
        return [port.device for port in available_ports]
    
    def connect(self, port=None):
        """
        Connect to the laser device.
        
        Args:
            port (str, optional): Serial port to use. If None, uses the instance port
                or attempts to auto-detect.
                
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        if port is not None:
            self.port = port
            
        # Auto-detect port if not specified
        if self.port is None:
            available_ports = self.list_available_ports()
            if not available_ports:
                logger.error("No serial ports found")
                return False
            
            # TODO: Implement heuristics to identify the correct laser device port
            # For now, just use the first available port
            self.port = available_ports[0]
            
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Verify connection by sending a test command and checking response
            if self._verify_connection():
                self.connected = True
                logger.info(f"Connected to laser device on {self.port}")
                self._get_device_info()
                return True
            else:
                self.connection.close()
                self.connection = None
                logger.error(f"Failed to verify laser device on {self.port}")
                return False
                
        except serial.SerialException as e:
            logger.error(f"Failed to connect to port {self.port}: {str(e)}")
            self.connection = None
            return False
    
    def disconnect(self):
        """
        Disconnect from the laser device.
        
        Returns:
            bool: True if disconnection was successful, False otherwise.
        """
        if self.connection is not None:
            try:
                self.connection.close()
                self.connection = None
                self.connected = False
                logger.info("Disconnected from laser device")
                return True
            except serial.SerialException as e:
                logger.error(f"Error during disconnection: {str(e)}")
                return False
        return True  # Already disconnected
    
    def is_connected(self):
        """
        Check if the controller is currently connected to a device.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self.connected and self.connection is not None and self.connection.is_open
    
    def send_command(self, command, wait_for_response=True, timeout=1.0):
        """
        Send a command to the laser device.
        
        Args:
            command (str): Command to send.
            wait_for_response (bool, optional): Whether to wait for a response. Defaults to True.
            timeout (float, optional): Response timeout in seconds. Defaults to 1.0.
            
        Returns:
            str or None: Response from the device, or None if no response or error.
        """
        if not self.is_connected():
            logger.error("Cannot send command: Not connected to device")
            return None
            
        try:
            # Convert command to bytes and add termination if needed
            if not command.endswith('\r\n'):
                command += '\r\n'
            
            # Send the command
            self.connection.write(command.encode('utf-8'))
            logger.debug(f"Sent command: {command.strip()}")
            
            # Wait for and return the response if requested
            if wait_for_response:
                return self._read_response(timeout)
            return None
            
        except serial.SerialException as e:
            logger.error(f"Error sending command: {str(e)}")
            self.connected = False
            return None
    
    def set_power(self, power_level):
        """
        Set the laser power level.
        
        Args:
            power_level (float): Power level to set (0.0 to 100.0).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # Ensure power_level is within valid range
        power_level = max(0.0, min(100.0, power_level))
        
        # Format depends on the specific laser protocol
        # Modify this command according to your laser device's protocol
        command = f"POWER {power_level:.1f}"
        
        response = self.send_command(command)
        if response and "OK" in response:
            logger.info(f"Set laser power to {power_level}%")
            return True
        else:
            logger.error(f"Failed to set laser power to {power_level}%")
            return False
    
    def enable_laser(self, enable=True):
        """
        Enable or disable the laser output.
        
        Args:
            enable (bool, optional): True to enable, False to disable. Defaults to True.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        command = "ENABLE" if enable else "DISABLE"
        
        response = self.send_command(command)
        if response and "OK" in response:
            status = "enabled" if enable else "disabled"
            logger.info(f"Laser {status}")
            return True
        else:
            action = "enable" if enable else "disable"
            logger.error(f"Failed to {action} laser")
            return False
    
    def get_status(self):
        """
        Get the current status of the laser device.
        
        Returns:
            dict: Dictionary containing status information, or None if failed.
        """
        response = self.send_command("STATUS")
        if not response:
            logger.error("Failed to get laser status")
            return None
            
        # Parse the response into a status dictionary
        # This parsing depends on the specific protocol of your laser device
        status = {
            'connected': self.is_connected(),
            'power': 0.0,
            'enabled': False,
            'temperature': 0.0,
            'error': None
        }
        
        # Example parsing - modify according to your device's response format
        try:
            for line in response.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'power':
                        status['power'] = float(value)
                    elif key == 'enabled':
                        status['enabled'] = value.lower() == 'true'
                    elif key == 'temp':
                        status['temperature'] = float(value)
                    elif key == 'error':
                        status['error'] = value if value != 'none' else None
        except Exception as e:
            logger.error(f"Error parsing status response: {str(e)}")
            return None
            
        return status
    
    def _verify_connection(self):
        """
        Verify that we are connected to a valid laser device.
        
        Returns:
            bool: True if verification succeeded, False otherwise.
        """
        # Send a simple command that any compliant laser device should respond to
        # Modify this according to your laser device's protocol
        response = self._read_response(timeout=0.5)  # Clear any pending data first
        
        response = self.send_command("*IDN?")
        # Verify the response contains expected identification info
        # This validation depends on your specific laser device
        return response is not None and len(response) > 0
    
    def _get_device_info(self):
        """
        Retrieve and store device information.
        
        Returns:
            dict: Dictionary of device information.
        """
        # Retrieve basic device information using appropriate commands
        # This depends on your specific laser device's protocol
        response = self.send_command("*IDN?")
        
        if response:
            # Parse the identification string
            # Format depends on your device - modify accordingly
            parts = response.strip().split(',')
            if len(parts) >= 3:
                self.device_info = {
                    'manufacturer': parts[0].strip(),
                    'model': parts[1].strip(),
                    'serial': parts[2].strip(),
                    'firmware': parts[3].strip() if len(parts) > 3 else None
                }
            else:
                self.device_info = {'raw_response': response.strip()}
                
        return self.device_info
    
    def _read_response(self, timeout=1.0):
        """
        Read a response from the device.
        
        Args:
            timeout (float, optional): Response timeout in seconds. Defaults to 1.0.
            
        Returns:
            str or None: Response string, or None if timeout or error.
        """
        if not self.is_connected():
            return None
            
        try:
            # Set the timeout for this read operation
            original_timeout = self.connection.timeout
            self.connection.timeout = timeout
            
            # Read until we get a complete response
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.connection.in_waiting > 0:
                    chunk = self.connection.readline().decode('utf-8', errors='replace')
                    response += chunk
                    if chunk.endswith('\n'):  # Got a complete line
                        break
                time.sleep(0.01)  # Short sleep to prevent CPU hogging
                
            # Restore original timeout
            self.connection.timeout = original_timeout
            
            if response:
                logger.debug(f"Received response: {response.strip()}")
                return response
            else:
                logger.debug("No response received (timeout)")
                return None
                
        except serial.SerialException as e:
            logger.error(f"Error reading response: {str(e)}")
            self.connected = False
            return None 