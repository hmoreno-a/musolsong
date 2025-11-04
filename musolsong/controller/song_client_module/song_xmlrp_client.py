#!/usr/bin/python
"""
SONG Detector XML-RPC Client Class

This class provides a convenient interface for connecting to and communicating
with the SONG detector server via XML-RPC.

Example usage:
    client = xmlrpcSONGClient("192.168.1.100", 8050)
    if client.connect():
        result = client.send_acquire_cmd(
            proj_nr=0,
            proj_name="MUSOL",
            exptime=0.5,
            imagetype="SUN",
            alpha_deg=45.0,
            beta_deg=90.0,
            calibration_theta_deg=0.0,
            comment="Commissioning of the polarimeter"
        )
        print(result)
"""

import xmlrpc.client as xmlrpclib


class xmlrpcSONGClient:
    """
    XML-RPC client for the SONG detector system.
    
    This class handles connection management and command sending to the SONG
    detector server for solar observations and calibrations.
    """
    
    def __init__(self, serverhost="127.0.0.1", serverport=8050, connection_timeout=5.0):
        """
        Initialize the SONG client.
        
        Args:
            serverhost (str): The IP address of the SONG server (default: "127.0.0.1")
            serverport (int): The port number of the SONG server (default: 8050)
        """
        self.serverhost = serverhost
        self.serverport = serverport
        self.connection_timeout = connection_timeout
        self.server = None
        self.connected = False
    
    def connect(self):
        """
        Establish connection to the SONG server.
        
        Returns:
            bool: True if connection was successful, False otherwise
            error: Error message    
        """
        try:
            # TODO 
            # see if connection_timeout is used in Mads server and if needed
            server_url = f'http://{self.serverhost}:{self.serverport}'
            self.server = xmlrpclib.ServerProxy(server_url)
                         
            # Send is_alive  command to the server
            if not self.server.is_alive():
                #print(f"song_xmlrp_client.py: Failed to connect to SONG server at {server_url}")
                self.connected = False
                error_message = f"song_xmlrp_client.py: Failed to connect to SONG server at {server_url}"
                return False, error_message
            self.connected = True
            #print(f"song_xmlrp_client.py: Successfully connected to SONG server at {server_url}")
            return True, "None"
            
        except Exception as e:
            print(f"song_xmlrp_client.py: Failed to connect to SONG server: {e}")
            self.connected = False
            self.server = None
            error_message = f"song_xmlrp_client.py: Failed to connect to SONG server: {e}"
            return False, error_message
    
    def send_acquire_cmd(self, proj_nr: int, proj_name: str, exptime: float, imagetype: str, 
                        alpha_deg: float, beta_deg: float, calibration_theta_deg: float = 999.9, comment: str=" "):
        """
        Send an acquisition command to the SONG detector.
        
        Args:
            proj_nr (int): The project number defined in the soda.phys.au.dk by the SONG Sci. team
            proj_name (str): The project name defined in the soda.phys.au.dk by the SONG Sci. team
            exptime (float): The exposure time in seconds
            imagetype (str): What kind of observations: [SUN, CALIB]
            alpha_deg (float): MUSOL Quarter-wave plate angle
            beta_deg (float): MUSOL Half-wave plate angle
            calibration_theta_deg (float): MUSOL Calibration rotating retarding angle
            comment (str): Optional comment for the acquisition (default: "")
        
        Returns:
            dict: Status information about the acquisition attempt
                'status' (int): 0 if acquisition was successful, 1 if there was an error
                'message' (str): Success or error message
                'timestamp' (str): Timestamp when the acquisition was attempted
                'filename' (str): Name of the FITS file containing the acquired image
        """
        if not self.connected or self.server is None:
            #print("song_xmlrp_client.py: Error: Not connected to SONG server. Call connect() first.")
            error_msg = "song_xmlrp_client.py: Error: Not connected to SONG server. Call connect() first."
            result = {
                'status': 1,
                'message': error_msg}
            return result
        
        try:
            # Send the acquisition command to the server
            result = self.server.acquire_a_solar_image(
                proj_nr, 
                proj_name, 
                exptime, 
                imagetype, 
                alpha_deg, 
                beta_deg, 
                calibration_theta_deg, 
                comment
            )
            return result
            
        except Exception as e:
            #print(f"song_xmlrp_client.py: Error sending acquisition command: {str(e)}")
            error_msg = f"song_xmlrp_client.py: Unspected Error sending acquisition command: {str(e)}"
            result = {
                'status': 1,
                'message': error_msg}
            return result
    
    def disconnect(self):
        """
        Disconnect from the SONG server.
        """
        self.server = None
        self.connected = False
        #print("song_xmlrp_client.py: Disconnected from SONG server")
    
    def is_connected(self):
        """
        Check if the client is currently connected to the server.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected


# Example usage
if __name__ == "__main__":
    # Create client instance
    client = xmlrpcSONGClient("0.0.0.0", 8050)
    
    # Connect to server
    if client.connect():
        # Send acquisition command
        result = client.send_acquire_cmd(
            proj_nr=0,
            proj_name="MUSOL",
            exptime=0.5,
            imagetype="SUN",
            alpha_deg=45.0,
            beta_deg=90.0,
            calibration_theta_deg=0.0,
            comment="Commissioning of the polarimeter"
        )
        
        if result:
            print("song_xmlrp_client.py: Acquisition result:", result)
        
        # Disconnect when done
        client.disconnect()
    else:
        print("song_xmlrp_client.py: Failed to connect to SONG server")