import os
import time
import random
from typing import Tuple, Optional
from datetime import datetime

class MusolLibSimulator:
    """
    Simulator for the MUSOL library with ADS connection capabilities.
    This class simulates the behavior of a real MUSOL system for testing purposes.
    """
    
    # Error codes
    SUCCESS = 0
    ERR_CONNECTION_FAILED = 1
    ERR_DIR_NOT_FOUND = 2
    ERR_INVALID_LENGTH = 3
    ERR_INVALID_MODE = 4
    ERR_INVALID_ANGLE = 5
    ERR_INVALID_POSITION = 6
    ERR_PLC_COMM_FAILURE = 7
    ERR_PLC_FAILURE = 8
    ERR_TIMEOUT = 9
    ERR_UNEXPECTED_CONDITION = 10
    ERR_EMERGENCY_STOP_ACTIVE = 11
    ERR_AXIS_NOT_READY = 12
    ERR_AXIS_NOT_CALIBRATED = 13
    
    
    # Valid modes
    VALID_MODES = ["CALIBRATION", "OBSERVATION"]
    
    def __init__(self):
        """Initialize the simulator with default values."""
        self.connected = False
        self.is_initialized = False
        self.current_mode = None
        self.logs_enabled = False
        self.logs_dir_path = None
        self.emergency_stop_active = False
        
        # Current positions (simulated)
        self.l511_position = 0.0
        self.dt80_01_position = 0.0
        self.dt80_02_position = 0.0
        self.dt80_03_position = 0.0
        
        # Angle limits (degrees)
        self.alpha_min, self.alpha_max = -180.0, 180.0
        self.beta_min, self.beta_max = -180.0, 180.0
        self.theta_min, self.theta_max = -360.0, 360.0
    
    def is_connected(self):
        """
        Check if the client is currently connected to the PLC.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def enable_axes(self) -> int:
        """Enable the axes on the PLC."""
        return self.SUCCESS
    
    def disable_axes(self) -> int:
        """Disable the axes on the PLC."""
        return self.SUCCESS
    
    def _log_message(self, message: str) -> None:
        
        """
        Write a log message if logs are enabled and a logs directory path is set.

        Args:
            message (str): The log message to write.

        """
        if self.logs_enabled and self.logs_dir_path:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            try:
                log_file = os.path.join(self.logs_dir_path, "musol_simulator.log")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except Exception as e:
                print(f"Failed to write log: {e}")
    
    def _simulate_communication_delay(self) -> None:
        """Simulate communication delay with random timing."""
        time.sleep(random.uniform(0.01, 0.05))
    
    def _simulate_random_failure(self, failure_rate: float = 0.05) -> bool:
        """Simulate random system failures for testing."""
        return random.random() < failure_rate
    
    def connect(self, plc_ams_net_id: str, logs: bool, logs_dir_path: str) -> int:
        """
        Establish ADS connection and activate/deactivate logs.
        
        Args:
            plc_ams_net_id: AMS Net ID of the PLC
            logs: Enable/disable logging
            logs_dir_path: Directory path for log files
            
        Returns:
            SUCCESS/ERR_CONNECTION_FAILED/ERR_DIR_NOT_FOUND
        """
        self._log_message(f"Attempting connection to PLC: {plc_ams_net_id}")
        
        # Validate logs directory if logging is enabled
        if logs and not os.path.exists(logs_dir_path):
            self._log_message(f"Log directory not found: {logs_dir_path}")
            return self.ERR_DIR_NOT_FOUND
        
        # Simulate connection delay
        self._simulate_communication_delay()
        
        # Simulate connection failure
        if self._simulate_random_failure(0.1):  # 10% failure rate
            self._log_message("Connection failed")
            return self.ERR_CONNECTION_FAILED
        
        # Successfully connected
        self.connected = True
        self.logs_enabled = logs
        self.logs_dir_path = logs_dir_path
        
        self._log_message(f"Successfully connected to PLC: {plc_ams_net_id}")
        return self.SUCCESS
    
    def initialize(self) -> int:
        """
        Homing procedure (all axes).
        
        Returns:
            SUCCESS/ERR_TIMEOUT/ERR_PLC_FAILURE
        """
        if not self.connected:
            return self.ERR_PLC_FAILURE
        
        self._log_message("Starting homing procedure")
        
        # Simulate homing time
        time.sleep(random.uniform(0.5, 1.5))
        
        # Simulate communication timeout
        if self._simulate_random_failure(0.05):
            self._log_message("Communication timeout during homing")
            return self.ERR_TIMEOUT
        
        # Simulate PLC failure
        if self._simulate_random_failure(0.03):
            self._log_message("PLC failure during homing")
            return self.ERR_PLC_FAILURE
        
        # Successful homing - reset positions to home
        self.l511_position = 0.0
        self.dt80_01_position = 0.0
        self.dt80_02_position = 0.0
        self.dt80_03_position = 0.0
        self.is_initialized = True
        self.emergency_stop_active = False
        
        self._log_message("Homing procedure completed successfully")
        return self.SUCCESS
    
    def set_mode(self, mode: str) -> int:
        """
        Set operational mode.
        
        Args:
            mode: Operational mode (CALIBRATION/OBSERVATION)
            
        Returns:
            SUCCESS/ERR_TIMEOUT/ERR_INVALID_MODE/ERR_PLC_FAILURE
        """
        if not self.connected:
            return self.ERR_PLC_FAILURE
        
        if not self.is_initialized:
            return self.ERR_PLC_FAILURE
        
        if mode not in self.VALID_MODES:
            self._log_message(f"Invalid mode: {mode}")
            return self.ERR_INVALID_MODE
        
        self._simulate_communication_delay()
        
        # Simulate communication timeout
        if self._simulate_random_failure(0.05):
            self._log_message("Communication timeout while setting mode")
            return self.ERR_TIMEOUT
        
        # Simulate PLC failure
        if self._simulate_random_failure(0.0):
            self._log_message("PLC failure while setting mode")
            return self.ERR_PLC_FAILURE
        
        self.current_mode = mode
        self._log_message(f"Mode set to: {mode}")
        return self.SUCCESS
    
    def set_modulation(self, alpha_angle: float, beta_angle: float, 
                      calibration_theta_angle: Optional[float] = None) -> Tuple[float, float, float, float, int]:
        """
        Move the motors and return current positions.
        
        Args:
            alpha_angle: Alpha angle in degrees
            beta_angle: Beta angle in degrees
            calibration_theta_angle: Calibration theta angle in degrees (optional)
            
        Returns:
            Tuple of (L-511, DT80-01, DT80-02, DT80-03, error_code)
        """
        time.sleep(6)

        #print("set_modulation in musol_simulator:", alpha_angle, beta_angle, calibration_theta_angle)
        if not self.connected or not self.is_initialized:
            return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_PLC_FAILURE
        
        if self.emergency_stop_active:
            return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_PLC_FAILURE
        
        # Validate angles
        if not (self.alpha_min <= alpha_angle <= self.alpha_max):
            self._log_message(f"Invalid alpha angle: {alpha_angle}")
            return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_INVALID_ANGLE
        
        if not (self.beta_min <= beta_angle <= self.beta_max):
            self._log_message(f"Invalid beta angle: {beta_angle}")
            return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_INVALID_ANGLE
        
        if calibration_theta_angle is not None:
            if not (self.theta_min <= calibration_theta_angle <= self.theta_max):
                self._log_message(f"Invalid theta angle: {calibration_theta_angle}")
                return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_INVALID_ANGLE
        
        # Simulate movement time
        time.sleep(random.uniform(0.2, 0.8))
        
        # Simulate communication timeout
        if self._simulate_random_failure(0.05):
            self._log_message("Communication timeout during modulation")
            return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_TIMEOUT
        
        # Simulate PLC failure
        if self._simulate_random_failure(0.0):
            self._log_message("PLC failure during modulation")
            return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.ERR_PLC_FAILURE
        
        # Update positions based on angles (simplified simulation)
        self.l511_position = alpha_angle * 0.5 + beta_angle * 0.3
        self.dt80_01_position = alpha_angle * 0.8 + random.uniform(-0.1, 0.1)
        self.dt80_02_position = beta_angle * 0.7 + random.uniform(-0.1, 0.1)
        
        if calibration_theta_angle is not None:
            self.dt80_03_position = calibration_theta_angle * 0.6 + random.uniform(-0.1, 0.1)
        else:
            self.dt80_03_position = (alpha_angle + beta_angle) * 0.4 + random.uniform(-0.1, 0.1)
        
        self._log_message(f"Modulation set - Alpha: {alpha_angle}, Beta: {beta_angle}, Theta: {calibration_theta_angle}")
        return self.l511_position, self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.SUCCESS
    
    def get_current_status(self) -> Tuple[str, float, float, float, float, int]:
        """
        Get current status and positions.
        
        Returns:
            Tuple of (mode, DT80-01, DT80-02, DT80-03, L-511, error_code)
        """
        if not self.connected:
            return "UNKNOWN", 0.0, 0.0, 0.0, 0.0, self.ERR_PLC_FAILURE
        
        self._simulate_communication_delay()
        
        # Simulate communication timeout
        if self._simulate_random_failure(0.05):
            self._log_message("Communication timeout while getting status")
            return self.current_mode or "UNKNOWN", self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.l511_position, self.ERR_TIMEOUT
        
        # Simulate PLC failure
        if self._simulate_random_failure(0.03):
            self._log_message("PLC failure while getting status")
            return self.current_mode or "UNKNOWN", self.dt80_01_position, self.dt80_02_position, self.dt80_03_position, self.l511_position, self.ERR_PLC_FAILURE
        
        # Add small random variations to positions (simulate sensor noise)
        l511_current = self.l511_position + random.uniform(-0.01, 0.01)
        dt80_01_current = self.dt80_01_position + random.uniform(-0.01, 0.01)
        dt80_02_current = self.dt80_02_position + random.uniform(-0.01, 0.01)
        dt80_03_current = self.dt80_03_position + random.uniform(-0.01, 0.01)
        
        current_mode = self.current_mode or "NOT_SET"
        
        return current_mode, dt80_01_current, dt80_02_current, dt80_03_current, l511_current, self.SUCCESS
 
    
    def close(self) -> None:
        """Terminate connection."""
        if self.connected:
            self._log_message("Closing connection")
            self.connected = False
            self.is_initialized = False
            self.current_mode = None
            self.emergency_stop_active = False
        
    def simulate_emergency_stop(self) -> None:
        """Simulate emergency stop activation (for testing purposes)."""
        self.emergency_stop_active = True
        self._log_message("Emergency stop activated")
    
    def get_error_description(self, error_code: int) -> str:
        """Get human-readable error description."""
        error_descriptions = {
            self.SUCCESS: "Operation successful",
            self.ERR_CONNECTION_FAILED: "Connection to PLC failed",
            self.ERR_DIR_NOT_FOUND: "Log directory not found",
            self.ERR_INVALID_LENGTH: "Invalid length parameter",
            self.ERR_INVALID_MODE: "Invalid operational mode",
            self.ERR_INVALID_ANGLE: "Invalid angle parameter",
            self.ERR_INVALID_POSITION: "Invalid position parameter",
            self.ERR_PLC_COMM_FAILURE: "PLC communication failure",
            self.ERR_PLC_FAILURE: "PLC failure or not connected",
            self.ERR_TIMEOUT: "Communication timeout",
            self.ERR_UNEXPECTED_CONDITION: "Unexpected condition",
            self.ERR_EMERGENCY_STOP_ACTIVE: "Emergency stop active",
            self.ERR_AXIS_NOT_READY: "Axis not ready",
            self.ERR_AXIS_NOT_CALIBRATED: "Axis not calibrated"
        }
        return error_descriptions.get(error_code, "Unknown error")
        

# Example usage
if __name__ == "__main__":
    # Create simulator instance
    simulator = MusolLibSimulator()
    
    # Connect to PLC
    result = simulator.connect("192.168.1.100.1.1", logs=True, logs_dir_path="./../logs")
    
    print(f"Connection result: {simulator.get_error_description(result)}")
    
    if result == simulator.SUCCESS:
        # Initialize system
        result = simulator.initialize()
        print(f"Initialization result: {simulator.get_error_description(result)}")
        
        if result == simulator.SUCCESS:
            # Set mode
            result = simulator.set_mode("CALIBRATION")
            print(f"Set mode result: {simulator.get_error_description(result)}")
            
            # Set modulation
            l511, dt80_01, dt80_02, dt80_03, result = simulator.set_modulation(45.0, 30.0, 90.0)
            print(f"Set modulation result: {simulator.get_error_description(result)}")
            print(f"Positions - L511: {l511:.2f}, DT80-01: {dt80_01:.2f}, DT80-02: {dt80_02:.2f}, DT80-03: {dt80_03:.2f}")
            
            # Get current status
            mode, l511, dt80_01, dt80_02, dt80_03, result = simulator.get_current_status()
            print(f"Current status - Mode: {mode}, L511: {l511:.2f}, DT80-01: {dt80_01:.2f}, DT80-02: {dt80_02:.2f}, DT80-03: {dt80_03:.2f}")
            print(f"Status result: {simulator.get_error_description(result)}")
        
        # Close connection
        simulator.close()
        print("Connection closed")
