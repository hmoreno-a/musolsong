"""MUSOLGSONG Coordinator Software System"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QApplication


from musolsong.controller.cli.sequence_processor import MusolsongCLI
from musolsong.controller.gui.main_Qt_window import MusolSongApp
from musolsong.controller.musolsong_tools.yaml_system_config_reader import SystemConfigReader
from musolsong.controller.logging_module.system_logger import SystemLogger, LogLevel
from musolsong.controller.song_client_module.song_xmlrp_client import xmlrpcSONGClient as SONGClient

# Determine the MUSOL library to use
if os.getenv("USE_MUSOLLIB_SIMULATOR") == "1":
    from musolsong.controller.musol_lib_simulator.musol_simulator import MusolLibSimulator as MusolLib 
else:
    from musol import MusolLib

# Determine package directories dynamically
PACKAGE_ROOT = Path(__file__).parent.parent.parent
CONTROLLER_DIR = Path(__file__).parent
ETC_DIR = CONTROLLER_DIR / "etc"

def expand_path(path):
    """Expand environment variables and user home directory in paths"""
    if path and path != "NONE":
        return os.path.expandvars(os.path.expanduser(path))
    return path

def setup_system_components(system_config_reader, logger=None):
    """
    Setup common system components (PLC and SONG clients)
    Returns: (plc_client, song_client_connector, is_plc_available, is_song_available)
    """
    # Connect to the MUSOL PLC
    plc_client = MusolLib()
    plc_ams_net_id = system_config_reader.get_plc_ams_net_id()
    plc_logs_enabled = system_config_reader.get_plc_logs_enabled()
    
    # First expand environment variables, then expand ~ (user home)
    expanded = os.path.expandvars(system_config_reader.get_plc_logs_path())
    plc_logs_path = os.path.expanduser(expanded)
    
    is_plc_available = False
    
    if logger is not None:
        logger.log_info("Connecting to MUSOL PLC", "main.setup_system_components()", {
            "plc_ams_net_id": plc_ams_net_id,
            "plc_logs_enabled": plc_logs_enabled,
            "plc_logs_path": plc_logs_path,
        })
    
    # Connect to the MUSOL PLC
    connection_result = plc_client.connect(plc_ams_net_id, plc_logs_enabled, plc_logs_path)
    
    # Check the connection result
    if connection_result == plc_client.SUCCESS:
        is_plc_available = True
    else:
        if logger is not None:
            logger.log_error(f"Failed to connect to MUSOL PLC: {plc_client.get_error_description(connection_result)}",
                "main.setup_system_components()", "")
    
    # Initialize the PLC
    if is_plc_available:    
        if logger is not None:
            logger.log_info("Initializing MUSOL PLC - Sending initialize command", "main.setup_system_components()", "")
        
        connection_result = plc_client.initialize()
        if connection_result == plc_client.SUCCESS:
            if logger is not None:
                logger.log_info("MUSOL PLC successfully initialized", "main.setup_system_components()", "")
        else:
            is_plc_available = False
            if logger is not None:
                logger.log_error(f"Failed to initialize MUSOL PLC: {plc_client.get_error_description(connection_result)}",
                    "main.setup_system_components()", "")
                    
    # Initialize the spectrograph client
    song_host = system_config_reader.get_spectrograph_host()
    song_port = system_config_reader.get_spectrograph_port()
    song_connection_timeout = system_config_reader.get_spectrograph_timeout()
    is_song_available = True
        
    if logger is not None:
        logger.log_info("Connecting to SONG server (test)", "main.setup_system_components()",
                f"song_host:{song_host} song_port:{song_port}")
    
    # Connect to the SONG server
    try:    
        song_client_connector = SONGClient(song_host, song_port, song_connection_timeout)
    except Exception as e:
        is_song_available = False
        if logger is not None:
            logger.log_error("Failed to connect to SONG server", "main.setup_system_components()", str(e),
                    f"song_host:{song_host} song_port:{song_port}")
    else:
        # Check if the connection was successful
        retval, error_description = song_client_connector.connect()
        if retval == True:
            if logger is not None:
                logger.log_info("Successfully connected to SONG server", "main.setup_system_components()") 
        else:
            is_song_available = False
            if logger is not None:
                logger.log_error("Failed to connect to SONG server", "main.setup_system_components()", error_description,
                        f"song_host:{song_host} song_port:{song_port}")

    return plc_client, song_client_connector, is_plc_available, is_song_available

def run_cli_mode(system_config_reader, logger, sequence_yaml_file, project_name, project_number, args):
    """
    Run MUSOLSONG in CLI mode
    """
    
    """
    print("=" * 70)
    print("\tMUSOLGSONG Coordinator - CLI Mode")
    print("\t**Selected library for MUSOL PLC:", MusolLib.__name__)
    print("=" * 70)
    """
    
    if logger is not None:
        logger.log_info("MUSOLSONG Coordinator running in CLI mode", "main.run_cli_mode")
        musol_lib_msg = f"**Selected library for MUSOL PLC: {MusolLib.__name__}"
        logger.log_info(musol_lib_msg , "main.run_cli_mode")
    
    
    if args.validate_only:
        logger.log_info("Validation only selected", "main.run_cli_mode()")
        plc_client = None
        song_client = None
    else:
        logger.log_info("Processing mode selected", "main.run_cli_mode()")
        # Setup system components
        plc_client, song_client, is_plc_available, is_song_available = setup_system_components(
                system_config_reader, logger
        )
        # Check if both PLC and SONG are unavailable
        if not is_plc_available and not is_song_available:
            if logger is not None:
                logger.log_error("Failed to connect to PLC and SONG server. Cannot proceed.", "main.run_cli_mode()")
            return 1
    
    # Initialize CLI processor
    try:
        # Initialize CLI processor
        cli_processor = MusolsongCLI(
            plc_client=plc_client,
            song_client=song_client,
            logger=logger
        )
        logger.log_debug("Calling process_sequence_file()", "main.run_cli_mode()", {
            "sequence_yaml_file": sequence_yaml_file,
            "project_name": project_name,
            "project_number": project_number    
        })
        # Process the project YAML
        success = cli_processor.process_sequence_file(
            sequence_yaml_file=sequence_yaml_file,
            project_name=project_name,
            project_number=project_number,
            validate_only=args.validate_only,
            verbose=args.verbose            
        )
        
        if success:
            if logger is not None:
                logger.log_info("CLI processing completed successfully", "main.run_cli_mode()")
            else:
                print("CLI processing completed successfully")
            if args.verbose  == False:
                print("CLI processing completed successfully")
            return 0
        else:
            if logger is not None:
                logger.log_error("CLI processing failed", "main.run_cli_mode()")
            else:
                print("CLI processing failed. Consult log file for details.")
            if args.verbose  == False:
                print("CLI processing failed. Consult log file for details.")
            return 1
            
    except Exception as e:
        if logger is not None:
            logger.log_error(f"CLI processing error: {str(e)}", "main.run_cli_mode()")
            #print(f"Error: {str(e)}")
        else:
            print(f"CLI processing error: {str(e)}")
        return 1
    
    except KeyboardInterrupt:
        
        if logger is not None:
            logger.log_critical(f"CLI processing aborted: Detected Ctrl+C — exiting gracefully.", "main.run_cli_mode()")
        else:
            print("\nDetected Ctrl+C — exiting gracefully.")
        
        # Close the MUSOL and SONG connections
        if cli_processor is not None:
            cli_processor.abort_processing()
        return 1

def run_gui_mode(system_config_reader, logger):
    """
    Run MUSOLSONG in GUI mode (original functionality)
    """   
    if logger is not None:
        logger.log_info("MUSOLSONG Coordinator running in GUI mode", "main.run_gui_mode()")
        musol_lib_msg = f"**Selected library for MUSOL PLC: {MusolLib.__name__}"
        logger.log_info(musol_lib_msg , "main.run_gui_mode()") 
    else:
        print("=" * 70)
        print("\tMUSOLGSONG Coordinator Software System")
        print("\t**Selected library for MUSOL PLC:", MusolLib.__name__)
        print("=" * 70)
        print("Initializing MUSOLGSONG Coordinator System ...")       
        
          
    
    # Setup system components
    plc_client, song_client_connector, is_plc_available, is_song_available = setup_system_components(
        system_config_reader, logger
    )
    
    # If both PLC and SONG server connections failed, exit the program
    if not is_plc_available and not is_song_available and logger is not None: 
        logger.log_error("*******Failed to connect to PLC and to song server. EXITING NOW.*******", "main.run_gui_mode()")
        return 1
    
    # Create and display the main window
    if logger is not None:
        logger.log_info("Initializing MUSOLSONG GUI", "main.run_gui_mode()",
            f"is SONG server available: {(str(is_song_available).upper())} , is PLC available: {(str(is_plc_available).upper())}")
        
    # Create an instance of QApplication
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 
               
    if app is None:
        if logger is not None:
            logger.log_error("Failed to create QApplication instance", "main.run_gui_mode()")
        return 1
        
    # Create an instance of the main application window
    main_window = MusolSongApp(plc_client, song_client_connector, logger)
    
    if main_window is None:
        if logger is not None:
            logger.log_error("Failed to create MusolSongApp instance", "main.run_gui_mode()")
        return 1
        
    # Show the main application window
    try:
        main_window.show()
    except Exception as e:
        if logger is not None:
            logger.log_error("Failed to show main window", "main.run_gui_mode", str(e))
        return 1
        
    # The application event loop
    try:
        return app.exec()
    except Exception as e:
        if logger is not None:
            logger.log_error("Failed to run application event loop", "main.run_gui_mode", str(e))
        return 1

def parse_arguments():
    """
    Parse command line arguments
    Returns: argparse.Namespace or None if no arguments provided
    """
    parser = argparse.ArgumentParser(
        description='MUSOLGSONG Coordinator - Run in GUI or CLI mode',
        add_help=False  # We'll handle help manually to avoid conflicts
    )
    
    # CLI mode arguments
    cli_group = parser.add_argument_group('CLI Mode Arguments')
    cli_group.add_argument(
        '--sequence-yaml',
        type=str,
        help='Path to sequence YAML modulations file (enables CLI mode)'
    )
    cli_group.add_argument(
        '--project-name', '-n',
        type=str,
        help='Project name (required for CLI mode)'
    )
    cli_group.add_argument(
        '--project-number', '-p',
        type=int,
        help='Project number (required for CLI mode)'
    )
    cli_group.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate the YAML file without processing (CLI mode)'
    )
    cli_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output (CLI mode)'
    )
    
    # Help argument
    parser.add_argument(
        '--help', '-h',
        action='store_true',
        help='Show this help message and exit'
    )
    
    # Parse arguments
    args, unknown = parser.parse_known_args()
    
    # Show help if requested
    if args.help:
        parser.print_help()
        print("\nGUI Mode:")
        print("  Run without arguments to start the graphical interface")
        print("\nExamples:")
        print("  GUI Mode: musolsong-controller")
        print("  CLI Mode: musolsong-controller --sequence-yaml config.yaml --project-name \"My Project\" --project-number 123")
        print("  CLI Validate Only: musolsong-controller --sequence-yaml config.yaml -n \"Test\" -p 456 --validate-only")
        sys.exit(0)
    
    # Check if we should run in CLI mode
    if args.sequence_yaml is not None:
        # Validate required CLI arguments
        if args.project_name is None or args.project_number is None:
            print("Error: --project-name and --project-number are required for CLI mode")
            print("Use --help for more information")
            sys.exit(1)
        return args
    
    # No CLI arguments provided, run GUI mode
    return None

def initialize_system_logger(system_config_reader,verbose="FILE"):
    """
    Initialize the system logger based on configuration
    Returns: SystemLogger instance or None if logging is disabled
    """
    system_logs_enabled = system_config_reader.get_system_logs_enabled()
    if not system_logs_enabled:
        print("*******System logging is disabled")
        print("=" * 70)
        return None
    
    datestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    expanded = os.path.expandvars(system_config_reader.get_system_logs_path())
    log_dir = os.path.expanduser(expanded)
    
    if log_dir == "NONE":
        log_file_abs_path = None
    else:
        os.makedirs(log_dir, exist_ok=True)
        file_name = f"MUSOLSONG_{datestamp}.log"
        log_file_abs_path = os.path.join(log_dir, file_name)
    
    log_level_str = system_config_reader.get_system_logs_level()
    enable_console = system_config_reader.get_system_console_logs_enabled()
    
    # Over pass enable console flag for CLI mode.Use verbose
    if verbose == "FILE":
        # use whatever is on the file (GUI mode)
        enable_console = system_config_reader.get_system_console_logs_enabled()
    # CLI Mode do whatever is on verbose variable
    if verbose == "TRUE":
        enable_console = True
    if verbose == "FALSE":
        enable_console = False
    
    """
    print(f"Log level: {log_level_str}")
    print(f"Log file: {log_file_abs_path}")
    print(f"Enable console: {enable_console}")
    """
    logger = SystemLogger(
        log_level=LogLevel[log_level_str],
        log_file=log_file_abs_path,
        enable_console=enable_console
    )
       
    logger.log_info("System logger initialized", "main",
            f"log_level:{log_level_str}  log_file:{log_file_abs_path} enable_console:{enable_console}")
    
    return logger

def main():
    """
    Main entry point of the MUSOLGSONG Coordinator Software System.
    Supports both GUI and CLI modes.
    """  

    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Use the dynamic ETC_DIR to find the config file
        config_file_path = ETC_DIR / 'systemConfig.yaml'
        print(f"Loading configuration file from: {config_file_path}")
        
        # Retrieve configurations from systemConfig.yaml file
        system_config_reader = SystemConfigReader(str(config_file_path))
        musol_song_config = system_config_reader.get_MUSOLSONG_config()
        plc_config = system_config_reader.get_plc_config()
        spectrograph_config = system_config_reader.get_spectrograph_config()
        
    except Exception as e:
        print(f"*******Failed to retrieve configurations from systemConfig.yaml: {str(e)}")
        sys.exit(1)
    
    if not all((musol_song_config, plc_config, spectrograph_config)):
        print("*******Failed to retrieve configurations from systemConfig.yaml.*******")
        sys.exit(1)
    
    # Initialize the system logger
    # note: that  args.verbose is ony set for the CLI mode.
    # This is used to override the enable_console flag in
    # the systemConfig.yaml. 
    # For CLI mode if verose is true, console logging is enabled
    # otherwise it is disabled
    if args is not None:
        if args.verbose== True:
            verbose = "TRUE"
        else:
            verbose = "FALSE"   
    else:
        verbose = "FILE"   # GUI mode
    logger = initialize_system_logger(system_config_reader, verbose)
    try:
        # Run in appropriate mode
        if args is not None:
            # CLI Mode
            return run_cli_mode(
                system_config_reader=system_config_reader,
                logger=logger,
                sequence_yaml_file=args.sequence_yaml,
                project_name=args.project_name,
                project_number=args.project_number,
                args=args
            )
        else:
            # GUI Mode
            return run_gui_mode(system_config_reader, logger)

    except Exception as e:
        print(f"*******Failed to run MUSOLSONG: {str(e)}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\nDetected Ctrl+C — exiting gracefully.")
       
    return 0
        
if __name__ == "__main__":
    sys.exit(main())