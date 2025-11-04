
"""
This module provides a class to read and manage the MUSOLSONG system 
configuration from a YAML file.
"""
import yaml
from typing import Optional, Union
import os  # The main needs it 

class SystemConfigReader:
    """
    A class to read and manage system configuration from a YAML file.
    """
    def __init__(self, config_file_path: str):
        """
        Initialize the configuration reader with a YAML file path.
        
        Args:
            config_file_path (str): Path to the YAML configuration file
        """
        self.config_file_path = config_file_path
        self.config_data = {}
    
    def __init__(self, config_file_path: str):
        """
        Initialize the configuration reader with a YAML file path.
        
        Args:
            config_file_path (str): Path to the YAML configuration file
        """
        self.config_file_path = config_file_path
        self.config_data = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load and parse the YAML configuration file.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If there's an error parsing the YAML file
        """
        try:
            with open(self.config_file_path, 'r') as file:
                self.config_data = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file: {e}")
    
    def reload_config(self) -> None:
        """
        Reload the configuration from the file.
        Useful if the configuration file has been modified.
        """
        self._load_config()
    
    # PLC MUSOL Configuration Getters
    def get_plc_ams_net_id(self) -> Optional[str]:
        """
        Get the PLC AMS Net ID.
        
        Returns:
            str: The AMS Net ID or None if not found
        """
        return self.config_data.get('plc_MUSOL', {}).get('ams_net_id')
    
    def get_plc_logs_enabled(self) -> Optional[bool]:
        """
        Get the PLC logs enabled status.
        
        Returns:
            bool: True if logs are enabled, False otherwise, or None if not found
        """
        return self.config_data.get('plc_MUSOL', {}).get('logs_enabled')
    
    def get_plc_logs_path(self) -> Optional[str]:
        
        """
        Get the expanded PLC logs directory path.

        The path may contain environment variables which will be
        expanded before returning.

        Returns:
            str: The expanded logs directory path or None if not found
        """
        logs_path_to_expand = self.config_data.get('plc_MUSOL', {}).get('logs_path')
        return os.path.expandvars(logs_path_to_expand)  
    
    # Spectrograph SONG Configuration Getters
    def get_spectrograph_host(self) -> Optional[str]:
        """
        Get the spectrograph TCP server IP address.
        
        Returns:
            str: The host IP address or None if not found
        """
        return self.config_data.get('spectrograph_SONG', {}).get('host')
    
    def get_spectrograph_port(self) -> Optional[int]:
        """
        Get the spectrograph port number.
        
        Returns:
            int: The port number or None if not found
        """
        return self.config_data.get('spectrograph_SONG', {}).get('port')
    
    def get_spectrograph_timeout(self) -> Optional[int]:
        """
        Get the spectrograph timeout value in seconds.
        
        Returns:
            int: The timeout value in seconds or None if not found
        """
        return self.config_data.get('spectrograph_SONG', {}).get('timeout')
 
    def get_system_logs_enabled(self) -> Optional[bool]:
        """
        Get the MUSOLSONG system logs enabled status.
        
        Returns:
            bool: True if logs are enabled, False otherwise, or None if not found
        """

        return self.config_data.get('MUSOLSONG_system', {}).get('logs_enabled')
 
    def get_system_logs_path(self) -> Optional[str]:
        """
        Get the expanded system logs directory path.

        The path may contain environment variables which will be
        expanded before returning.

        Returns:
            str: The expanded logs directory path or None if not found
        """
        logs_path_to_expand = self.config_data.get('MUSOLSONG_system', {}).get('logs_path')
        #print(logs_path_to_expand)
        return os.path.expandvars(logs_path_to_expand)
 
    def get_system_logs_level(self) -> Optional[str]:
        """
        Get the MUSOLSONG system log level.
        
        Returns:
            str: The log level or None if not found
        """
        return self.config_data.get('MUSOLSONG_system', {}).get('logs_level')    
    
    def get_system_console_logs_enabled(self) -> Optional[bool]:
        """
        Get the MUSOLSONG system console logs enabled status.
        
        Returns:
            bool: True if console logs are enabled, False otherwise, or None if not found
        """
        return self.config_data.get('MUSOLSONG_system', {}).get('logs_console_enabled') 
    
    def get_plc_config(self) -> dict:
        """
        Get the entire PLC configuration section.
        
        Returns:
            dict: The PLC configuration dictionary
        """
        return self.config_data.get('plc_MUSOL', {})
    
    def get_spectrograph_config(self) -> dict:
        """
        Get the entire spectrograph configuration section.
        
        Returns:
            dict: The spectrograph configuration dictionary
        """
        return self.config_data.get('spectrograph_SONG', {})

    def get_MUSOLSONG_config(self) -> dict:    
        """
        Get the entire MUSOLSONG system configuration section.
        
        Returns:
            dict: The MUSOLSONG system configuration dictionary
        """
        return self.config_data.get('MUSOLSONG_system', {})
    
    def get_all_config(self) -> dict:
        """
        Get the entire configuration data.
        
        Returns:
            dict: The complete configuration dictionary
        """
        return self.config_data
    
    def __str__(self) -> str:
        """
        String representation of the configuration.
        
        Returns:
            str: YAML formatted string of the configuration
        """
        return yaml.dump(self.config_data, default_flow_style=False)


# Example usage
if __name__ == "__main__":
    # Create an instance of the configuration reader
    file_path = os.environ.get('MY_MUSOLSONG_ETC') + '/systemConfig.yaml'
    print (f"Config file path: {file_path}")
    config = SystemConfigReader(file_path)
    
    # Access PLC configuration
    print("PLC Configuration:")
    print(f"  AMS Net ID: {config.get_plc_ams_net_id()}")
    print(f"  Logs Enabled: {config.get_plc_logs_enabled()}")
    print(f"  Logs Path: {config.get_plc_logs_path()}")
    
    # Access Spectrograph configuration
    print("\nSpectrograph Configuration:")
    print(f"  Host: {config.get_spectrograph_host()}")
    print(f"  Port: {config.get_spectrograph_port()}")
    print(f"  Timeout: {config.get_spectrograph_timeout()}")
    
    # Access MUSOLSONG configuration
    print("\nMUSOLSONG System Configuration:")
    print(f"  Logs Enabled: {config.get_system_logs_enabled()}")
    print(f"  Logs Path: {config.get_system_logs_path()}")
    print(f"  Logs Console Enabled: {config.get_system_console_logs_enabled()}")
    
    
    # Get entire sections
    print("\nComplete PLC Config:")
    print(config.get_plc_config())
    
    print("\nComplete Spectrograph Config:")
    print(config.get_spectrograph_config())
    
    print("\nComplete MUSOLSONG Config:")
    print(config.get_MUSOLSONG_config())
    
    print("\nComplete Config:")
    print(config.get_all_config())  
    
    # Print the entire configuration
    print("\nComplete Configuration:")
    print(config)
    
    # Print the entire configuration as a dictionary
    #print("\nComplete Configuration as Dictionary:")
    #print(config.config_data)