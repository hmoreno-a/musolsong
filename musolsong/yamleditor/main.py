"""MUSOLGSONG YAML Configuration Editor Software System"""

import sys

from PyQt6.QtWidgets import QApplication

from musolsong.yamleditor.yaml_editor_gui.yaml_sequences_editor_gui import YAMLEditorGUI
def main():
    """
    Main function to start the application.

    Initializes the application with the command line arguments, sets the
    application style to 'Fusion', creates an instance of the YAMLEditorGUI
    class, shows the window, and starts the application event loop.
    """
    print("=" * 70)
    print("\tMUSOLGSONG Configuration Editor Software System")
    print("=" * 70)
    print("Initializing MUSOLGSONG Configuration Editor Software System ...")
        
    """
    Create an instance of QApplication
    
    QApplication is the main application object in PyQt6. It is responsible for
    handling the application event loop and processing GUI events.
    """   
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()    
    
    """
    Check if the QApplication instance was successfully created
    """
    if app is None:
        print("Failed to create QApplication instance", "main")
        sys.exit(1)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = YAMLEditorGUI()
    if window is None:
        # If the instance was not created, log an error and exit the program
        print("Failed to create YAMLEditorGUI instance", "main")
        sys.exit(1)
        
    """
    Show the main application window
    
    This will make the window visible to the user
    """
    try:
        window.show()
    except Exception as e:
        # If there was an error while trying to show the window,
        #  exit the program
        print("Failed to show main window", "main", str(e))
        sys.exit(1)
            
    #sys.exit(app.exec())
    """
    The application event loop will be executed next
    
    The event loop is responsible for handling GUI events and
    processing them accordingly
    """
    try:
        sys.exit(app.exec())
    except Exception as e:
        print("Failed to run application event loop", "main", str(e))
        sys.exit(1)
        
if __name__ == '__main__':
    main()
