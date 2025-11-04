#!/usr/bin/env python3
"""
SONG Spectrograph Server Simulator

This server simulates the SONG  spectrograph system
for solar observations. It handles XML-RPC requests from clients for image acquisition.

The server implements the acquire_a_solar_image method that accepts parameters for
solar observations including project info, exposure settings, and MUSOL polarimetry angles.
"""

import sys
import time
import random
import logging
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from datetime import datetime
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('song_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SONGSpectrographSimulator:
    """
    Simulator for the SONG spectrograph system.
    Handles solar image acquisition requests with various parameters.
    """
    
    def __init__(self):
        self.is_busy = False
        self.observation_count = 0
        self.start_time = datetime.now()
        
        # Valid parameter ranges and values
        self.valid_imagetypes = ["SUN", "CALIB"]
        self.max_exptime = 300.0  # Maximum exposure time in seconds
        self.min_exptime = 0.01   # Minimum exposure time in seconds
        
        logger.info("SONG Spectrograph Simulator initialized")
    
    def is_alive(self):
     
        return 1  # Always return 1 (True) to indicate "SONG Spectrograph Simulator is alive" )
    
    def acquire_a_solar_image(self, proj_nr: int, proj_name: str, exptime: float, imagetype: str, 
                              alpha_deg: float, beta_deg: float, calibration_theta_deg: float, comment: str=" "):
        
        
        # Log the incoming request
        """
        Simulate the acquisition of an image using the SONG spectrograph system.

        Args:
            proj_nr (int): Project number defined by SONG Science team
            proj_name (str): Project name defined by SONG Science team
            exptime (float): Exposure time in seconds
            imagetype (str): Type of observation ["SUN", "CALIB"]
            alpha_deg (float): MUSOL Quarter-wave plate angle in degrees
            beta_deg (float): MUSOL Half-wave plate angle in degrees
            calibration_theta_deg (float): MUSOL Calibration rotating retarding angle in degrees
            comment (str): Additional comment for the observation

        Returns:
            dict: Status information about the acquisition attempt
                'status' (int): 0 if acquisition was successful, 1 if there was an error
                'message' (str): Success message or error message
                'timestamp' (str): Timestamp when the acquisition was attempted
                'filename' (str): Name of the FITS file containing the acquired image
        """
        logger.info(f"Acquisition request received:")
        logger.info(f"  Project: {proj_nr} - {proj_name}")
        logger.info(f"  Exposure time: {exptime}s")
        logger.info(f"  Image type: {imagetype}")
        logger.info(f"  MUSOL angles - Alpha: {alpha_deg}°, Beta: {beta_deg}°, Theta: {calibration_theta_deg}°")
        logger.info(f"  Comment: {comment}")
        print(f"\n   **************************\n")

        # Check if system is busy
        if self.is_busy:
            error_msg = "System is currently busy with another acquisition"
            logger.warning(error_msg)
            return {
                'status': 1,
                'message': error_msg,
                'timestamp': datetime.now().isoformat(),
                'acquisition_id': None
            }
        
        # Validate parameters
        validation_result = self._validate_parameters(
            proj_nr, proj_name, exptime, imagetype, 
            alpha_deg, beta_deg, calibration_theta_deg
        )
        
        if validation_result['status'] != 0:
            logger.error(f"Parameter validation failed: {validation_result['message']}")
            return validation_result
        
        # Simulate acquisition process
        try:
            self.is_busy = True
            acquisition_id = f"SONG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.observation_count:04d}"
            
            logger.info(f"Starting acquisition {acquisition_id}")
            
            # Simulate acquisition time (exposure time + overhead)
            overhead_time = random.uniform(2.0, 5.0)  # Random overhead between 2-5 seconds
            total_time = exptime + overhead_time
            
            # Simulate the acquisition process with progress updates
            steps = 5
            step_time = total_time / steps
            
            for step in range(steps):
                time.sleep(step_time)
                progress = (step + 1) * 20
                logger.info(f"Acquisition {acquisition_id} progress: {progress}%")
            
            # Simulate random success/failure (95% success rate)
            #success = random.random() > 0.05
            success = True
            print(f"\n   *****************Acquisition {acquisition_id} completed sucess= {success}")
            if success == True:
                self.observation_count += 1
                result = {
                    'status': 0,
                    'message': 'Acquisition completed successfully',
                    'timestamp': datetime.now().isoformat(),
                    'filename': f"{acquisition_id}_{imagetype}.fits"
                }
                logger.info(f"Acquisition {acquisition_id} completed successfully")
                
            else:
                print(f"\n   *****************Acquisition failed: {success}")
                error_reasons = [
                    "CCD temperature too high",
                    "Weather conditions deteriorated",
                    "Mechanical shutter failure",
                    "Network timeout during readout",
                    "Insufficient disk space"
                ]
                error_msg = random.choice(error_reasons)
                
                result = {
                    'status': 1,
                    'message': f'Acquisition failed: {error_msg}',
                    'timestamp': datetime.now().isoformat(),
                    'acquisition_id': acquisition_id,
                }
                logger.error(f"Acquisition {acquisition_id} failed: {error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error during acquisition: {str(e)}"
            logger.error(error_msg)
            result = {
                'status': 1,
                'message': error_msg,
                'timestamp': datetime.now().isoformat(),
                'filename': None
            }
        
        finally:
            self.is_busy = False
        
        return result
    
    def _validate_parameters(self, proj_nr, proj_name, exptime, imagetype, 
                           alpha_deg, beta_deg, calibration_theta_deg):
        
        # Check project number
        """
        Validate parameters for an acquisition request.

        Args:
            proj_nr (int): Project number defined by SONG Science team
            proj_name (str): Project name defined by SONG Science team
            exptime (float): Exposure time in seconds
            imagetype (str): Type of observation ["SUN", "CALIB"]
            alpha_deg (float): MUSOL Quarter-wave plate angle in degrees
            beta_deg (float): MUSOL Half-wave plate angle in degrees
            calibration_theta_deg (float): MUSOL Calibration rotating retarding angle in degrees

        Returns:
            dict: Status information about the validation attempt
                'status' (int): 0 if parameters are valid, 1 if there are errors
                'message' (str): Error message if there are errors
                'timestamp' (str): Timestamp when the validation was attempted
                'acquisition_id' (str): None if there are errors, otherwise a unique identifier for the acquisition
        """
        if not isinstance(proj_nr, int) or proj_nr < 0:
            return {
                'status': 1,
                'message': 'Invalid project number: must be a non-negative integer',
                'timestamp': datetime.now().isoformat(),
                'acquisition_id': None
            }
        
        # Check project name
        if not isinstance(proj_name, str) or len(proj_name.strip()) == 0:
            return {
                'status': 1,
                'message': 'Invalid project name: must be a non-empty string',
                'timestamp': datetime.now().isoformat(),
                'acquisition_id': None
            }
        
        # Check exposure time
        if not isinstance(exptime, (int, float)) or exptime < self.min_exptime or exptime > self.max_exptime:
            return {
                'status': 1,
                'message': f'Invalid exposure time: must be between {self.min_exptime} and {self.max_exptime} seconds',
                'timestamp': datetime.now().isoformat(),
                'acquisition_id': None
            }
        
        # Check image type
        if imagetype not in self.valid_imagetypes:
            return {
                'status': 1,
                'message': f'Invalid image type: must be one of {self.valid_imagetypes}',
                'timestamp': datetime.now().isoformat(),
                'acquisition_id': None
            }
        
        # Check angle parameters (should be valid floats, angles can be any value)
        angles = [alpha_deg, beta_deg, calibration_theta_deg]
        angle_names = ['alpha_deg', 'beta_deg', 'calibration_theta_deg']
        
        for angle, name in zip(angles, angle_names):
            if not isinstance(angle, (int, float)):
                return {
                    'status': 1,
                    'message': f'Invalid {name}: must be a number',
                    'timestamp': datetime.now().isoformat(),
                    'acquisition_id': None
                }
        
        return {'status': 0, 'message': 'Parameters valid'}
    
    def get_status(self):
        """Get current system status."""
        uptime = datetime.now() - self.start_time
        
        return {
            'system_status': 'busy' if self.is_busy else 'ready',
            'uptime_seconds': int(uptime.total_seconds()),
            'total_observations': self.observation_count,
            'server_time': datetime.now().isoformat()
        }
    
    def get_capabilities(self):
        """Get system capabilities and configuration."""
        return {
            'valid_imagetypes': self.valid_imagetypes,
            'exptime_range': [self.min_exptime, self.max_exptime],
            'detector_type': 'CCD',
            'polarimetry_enabled': True,
            'server_version': '1.0.0'
        }


class RequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler for logging."""
    
    def log_request(self, code='-', size='-'):
        """Log incoming requests."""
        logger.info(f"XML-RPC request from {self.client_address[0]}:{self.client_address[1]} - {code}")


def main():
    """Main server function."""
    
    # Server configuration
    HOST = "0.0.0.0"  # Listen on all interfaces
    PORT = 8050
    
    print("=" * 70)
    print("SONG Spectrograph Server Simulator")
    print("=" * 70)
    print(f"Starting server on {HOST}:{PORT}")
    print("Available methods:")
    print("  - acquire_a_solar_image(proj_nr, proj_name, exptime, imagetype,")
    print("                         alpha_deg, beta_deg, calibration_theta_deg, comment)")
    print("  - ping()")
    print("  - get_status()")
    print("  - get_capabilities()")
    print("=" * 70)
    
    # Create the server
    try:
        server = SimpleXMLRPCServer(
            (HOST, PORT),
            requestHandler=RequestHandler,
            allow_none=True
        )
        
        # Create detector instance
        detector = SONGSpectrographSimulator()
        
        # Register methods
        server.register_instance(detector)
        server.register_introspection_functions()
        
        logger.info(f"Server started successfully on {HOST}:{PORT}")
        logger.info("Waiting for client connections...")
        
        # Start serving
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Server stopped")
        print("\nServer stopped")


if __name__ == "__main__":
    main()
