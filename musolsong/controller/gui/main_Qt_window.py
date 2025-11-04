"""
The main application class for the MUSOLSONG Coordinator Software.        
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any


from PyQt6.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog, QMessageBox,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QLabel,QGroupBox, QLineEdit, QHBoxLayout, QGridLayout,
    QComboBox,QFormLayout, QTabWidget, QLineEdit, 
    QDoubleSpinBox, QVBoxLayout, QProgressBar
)
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtCore import QThread

from musolsong.controller.musolsong_tools.yaml_sequence_validator import YAMLSequenceValidator
from musolsong.controller.song_client_module.song_xmlrp_client import xmlrpcSONGClient as SONGClient
from musolsong.controller.logging_module.system_logger import SystemLogger
from .background_QT_processing import ProcessingWorker 

# Determine package directories dynamically to decide which musol lib to import
if os.getenv("USE_MUSOLLIB_SIMULATOR") == "1":
    from musolsong.controller.musol_lib_simulator.musol_simulator import MusolLibSimulator as MusolLib 
else:
    from musol import MusolLib

class MusolSongApp(QMainWindow, MusolLib, SONGClient, SystemLogger):
    """
    The main application class for the MUSOLSONG Coordinator Software.

    This class inherits from QMainWindow and contains the main application
    logic. It initializes the user interface components, sets up the
    menus, and connects the control buttons to their respective slots.

    It also contains the slots for the control buttons and the background
    processing thread.

    Attributes:
        musol (MusolLib): The MUSOL library  instance.
        song (SONGClient): The SONG client instance.
        logger (SystemLogger): The system logger instance.
        worker_thread (QThread): The background processing thread.
        worker (ProcessingWorker): The background processing worker.
        current_seq_data (YAMLSequenceValidator): The current sequence validated data.
        is_aborting (bool): Flag to indicate if the processing operation is being aborted.
    """

    def __init__(
        self,
        musol_lib: MusolLib,
        song_client: SONGClient,
        system_logger: SystemLogger = None
    ) -> None:

        """
        Constructor to Initialize the MUSOLSONG Coordinator Software.

        Args:
            musol_lib: The MUSOL library  instance.
            song_client: The SONG client instance.
            system_logger: Optional system logger instance for logging system
            messages. Defaults to None.
        """
        self.musol = musol_lib
        self.song = song_client        
        self.logger = system_logger
        
        self.worker_thread = None
        self.worker = None
        
        self.current_seq_data = None # Current sequence validated data (YAMLSequenceValidator) 
        self.is_aborting = False   # Flag to indicate if the processing operation is being aborted
        super().__init__()
        self.init_ui()
                   
    def init_ui(self):
        
        """
        Initialize the user interface components.
        
        This method sets the window title and size, creates the project 
        information widgets, creates the menu bar, main widget, tab widget,
        control buttons, and status bar.
        """
        self.setWindowTitle("MUSOLSONG Coordinator Software")
        self.setGeometry(100, 100, 680, 700)
        self.setMinimumSize(650, 600)

        # Create menu bar for app to load YAML file and exit.
        self.create_menu_bar()
        
        # Create project information widgets
        proj_num_layout, proj_name_layout = self.create_project_info_widgets()
  
        # Create main widget and layout for project information,
        # operations tab, and engineering tab.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        layout.addLayout(proj_num_layout)
        layout.addLayout(proj_name_layout)
        
        # Create tab widget for operations and engineering
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: lightgray;
                padding: 6px;
                border: 1px solid #999;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }

            QTabBar::tab:selected {
                background: #3498db;   /* blue highlight */
                color: white;          /* white text */
                font-weight: bold;
            }

            QTabBar::tab:!selected {
                margin-top: 2px;  /* make unselected look lower */
            }   
        """)        
        layout.addWidget(self.tab_widget)             
        
        # Create operations tab
        self.create_operations_layout()
        
        # Create engineering tab
        self.create_engineering_layout()
        
        #self.create_control_buttons(layout)
        self.status_bar = self.statusBar()
        
        # Status bar
        # Check if MUSOL Library is connected
        if not self.musol.is_connected():
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("MUSOL Library not initialized. Only Engineering tab available")
            # Set the status bar color to red
            self.status_bar.setStyleSheet("background-color: rgb(255, 0, 0);")
                  
        # Check if SONG server is connected
        if not self.song.is_connected():
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("SONG server not available. Only Engineering tab available")
            # Set the status bar color to red
            self.status_bar.setStyleSheet("background-color: rgb(255, 0, 0);")
            
        # Check if both MUSOL Library and SONG server are connected
        if self.musol.is_connected() and self.song.is_connected():
            # If both are connected, set the status bar message to "Ready"
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("Ready")
            # Set the status bar color to green
            self.status_bar.setStyleSheet("background-color: rgb(0, 255, 0);")      
        
    def create_project_info_widgets(self):
        
        """
        Create the project number and project name input widgets.

        This method creates the user interface components for the project number
        and project name input fields. The project number is a single-line text
        input field with a placeholder text of "0". The project name is a single-line
        text input field with a placeholder text of "None".

        Returns:
            tuple: A tuple containing the project number layout and the project
                name layout.
        """
        num_label = QLabel("Project Number:")
        num_label.setStyleSheet("color: blue; font-weight: bold;")
        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("Default: 0")
        
        proj_num_layout = QHBoxLayout()
        proj_num_layout.addWidget(num_label)
        proj_num_layout.addWidget(self.num_input)

        # --- Project Name ---
        name_label = QLabel("Project Name:")
        name_label.setStyleSheet("color: blue; font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Default: None")
         
        proj_name_layout = QHBoxLayout()
        proj_name_layout.addWidget(name_label)
        proj_name_layout.addWidget(self.name_input)
        
        return proj_num_layout, proj_name_layout 
     
    def create_menu_bar(self):
        """
        Create the menu bar for the application.
        
        Creates the menu bar with items "File",  "Open" and "Exit".
        The  the "Open" action opens an existing YAML file, 
        The "Exit" action closes the application.
        """
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Load sequence YAML file', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_and_display_sequence_config)
        file_menu.addAction(open_action)
        
        """save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_to_yaml)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        """
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def close(self):
        """
        Close the MUSOLSONG Coordinator Software application.

        This method closes the application and disconnects from the MUSOL
        library and the SONG server. It also logs an info message to the
        system logger indicating that the application is being closed.

        Returns:
            None
        """
        self._log_info("Closing MUSOLSONG Coordinator Software","close()")
        self.musol.close()
        self.song.disconnect()
        return super().close()
    
    def create_operations_layout(self):  
        """
        Create the Operations tab.
        
        This tab includes information about the current modulations mode, a table
        for showing modulations, a group for calibration setup, control buttons, 
        and labels for displaying the current status of each field.
        """
        op_widget = QWidget()
        op_layout = QVBoxLayout(op_widget) 
        
        # Add modulation type info
        self.mode_label = QLabel("MODE: ")
        self.mode_label.setStyleSheet("color: blue; font-weight: bold;")
        op_layout.addWidget(self.mode_label)
        
        
      # Modulations group layout
        mod_group = QGroupBox("   Modulations")
        
        mod_group.setStyleSheet("""
            QGroupBox {
                border: 3px solid #3498db;
                border-radius: 4px;
                padding: 2px 2px;
                font-size: 14px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
            }
            QGroupBox::title {
                padding: 2px 2px;
                color: darkblue;
                font-weight: bold;
            }
        """)
        mod_layout = QVBoxLayout(mod_group)
              
        # Modulations Table
        self.modulations_table = QTableWidget()
        self.modulations_table.setColumnCount(4)
        self.modulations_table.setHorizontalHeaderLabels(["Alpha \n(deg)", "Beta \n(deg)","SONG Integration\n(sec)", "    Description"])
        self.modulations_table.setColumnWidth(0, 100)
        self.modulations_table.setColumnWidth(1, 100)
        self.modulations_table.setColumnWidth(2, 150)
        self.modulations_table.setColumnWidth(3, 250)
        self.modulations_table.setAlternatingRowColors(True)

        self.modulations_table.setStyleSheet("""
            QTableWidget {
                border: 3px solid #3498db;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
                font-weight: bold;
                color: black;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }""")
        # To allow editing: self.modulations_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        # No edditing is allowed    
        self.modulations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Estimate height for 6 rows
        row_height = self.modulations_table.verticalHeader().defaultSectionSize()
        self.modulations_table.setMinimumHeight(row_height * 6 + self.modulations_table.horizontalHeader().height()) 
        
        mod_layout.addWidget(self.modulations_table)
        op_layout.addWidget(mod_group)
                
        # Calibration group
        calibration_group = QGroupBox("  Calibration Setups")
        calibration_group.setStyleSheet("""
            QGroupBox {
                border: 3px solid #3498db;
                border-radius: 4px;
                padding: 10px 10px;
                font-size: 14px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
            }
            QGroupBox::title {
                padding: 8px 8px;
                color: darkblue;
                font-weight: bold;
            }
        """)
        cal_layout = QFormLayout(calibration_group)
        
        offset_display = QLineEdit()
        offset_display.setReadOnly(True)
        offset_display.setFrame(False)
       
        offset_display.textChanged.connect(self.update_number_of_cycles)
        
        self.retarding_display = offset_display
        self.retarding_display.setStyleSheet("color: green; font-weight: bold;")
        
        # Add number of cycles  info 
        self.number_of_cycles_label = QLabel("")
        self.number_of_cycles_label.setStyleSheet("color: blue; font-weight: bold;")
        
        cal_layout.addRow("Incremental angle per cycle:", offset_display) 
        cal_layout.addRow("Number of cycles:", self.number_of_cycles_label)
        op_layout.addWidget(calibration_group)        
        
        # Add status labels
        self.status_label = QLabel("Ready to start processing")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        op_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        op_layout.addWidget(self.progress_bar)
         
        # Add control buttons
        # Inner horizontal layout for control buttons
        self.control_button_layout = QHBoxLayout()

        self.process_button = QPushButton("START Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white; border-color: white;
                    border-radius: 8px;
                    padding: 8px 70px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                """)

        #self.process_button.setDisabled(True)

        self.abort_button = QPushButton("ABORT Processing")
        self.abort_button.clicked.connect(self.abort_processing)
        self.abort_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white; border-color: white;
                    border-radius: 8px;
                    padding: 8px 70px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #f1c40f;
                }
                """)
        self.abort_button.setEnabled(False)  # Initially disabled
        self.control_button_layout.addWidget(self.process_button)
        self.control_button_layout.addWidget(self.abort_button)
        #self.control_button_layout.addStretch()
        op_layout.addLayout(self.control_button_layout)
           
    
        # Group box to hold labels
        status_group = QGroupBox("  Current Status")
        grid_layout = QGridLayout() 
           
       # Create labels for each status field
        self.labels = {
            'Modulation Cycle': QLabel("1"),
            'Modulation Step': QLabel("1"),
            'Translation Unit': QLabel("0.0"),
            'Alpha position': QLabel("0.0"),
            'Beta position': QLabel("0.0"),
            'Theta position': QLabel("0.0"),
            'SONG integration time': QLabel("0.0")
        }
        
        # Add labels to grid layout (2 columns)
        names = list(self.labels.keys())
        for index, name in enumerate(names):
            row = index % 3        # 3 rows
            col = index // 3       # 2 columns
            grid_layout.addWidget(QLabel(name + ":"), row, col * 2)
            grid_layout.addWidget(self.labels[name], row, col * 2 + 1)
        
        # Add the grid layout to the group box
        status_group.setLayout(grid_layout)
        status_group.setStyleSheet("""
            QGroupBox {
                border: 3px solid #3498db;
                border-radius: 10px;
                padding: 12px 12px;
                font-size: 14px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
            }
            QGroupBox::title {
                color: darkblue;
                font-weight: bold;
            }
        """)
        op_layout.addWidget(status_group)      
       
        op_widget.setLayout(op_layout)
               
         # Add the Operations tab        
        self.tab_widget.addTab(op_widget, "Operations")
        
    # Setter for Alpha
    def set_alpha(self, value):
        alpha_str = f"{value:.2f}"
        self.labels['Alpha position'].setText(alpha_str)

    # Setter for Beta
    def set_beta(self, value):
        beta_str = f"{value:.2f}"
        self.labels['Beta position'].setText(beta_str)
        
    # Setter for theta (Retarding plate angle) 
    def set_theta(self, value):
        theta_str = f"{value:.2f}"
        self.labels['Theta position'].setText(theta_str)
        
    # Setter for translation unit
    def set_translation_unit(self, value):
        translation_unit_str = f"{value:.2f}"
        self.labels['Translation Unit'].setText(translation_unit_str)        

    # Setter for SONG integration time
    def set_song_integration_time(self, value):
        value_str = f"{value:.2f}"
        self.labels['SONG integration time'].setText(value_str)
      
    # Create the Engineering tab      
    def create_engineering_layout(self):
        """
        Create the Engineering tab.
        
        This tab includes 2 areas of input fields for PLC configuration and SONG acquisition,
        and 2 buttons for configurePLC and AcquireSongImage.
        
        The input fields for PLC configuration will include:
        set_mode (CALIBRATION/OBSERVATION)
        alpha and beta angles in degrees for both engines
        retarder plate angle in degrees (only make sense if calibration mode is selected).
        The input fields for SONG acquisition will include:
        SONG integration time in seconds and description or comment of the acquisition
        """
        eng_widget = QWidget()
        eng_layout = QVBoxLayout()
        
        eng_layout.addWidget(QLabel("Engineering controls go here"))
        eng_widget.setLayout(eng_layout)        
            
        # Engineering tab
        eng_widget = QWidget()
        eng_layout = QVBoxLayout(eng_widget)
        
        # PLC group layout
        plc_group = QGroupBox("MUSOL PLC Configuration")
        plc_layout = QVBoxLayout(plc_group)        

        plc_group.setStyleSheet("""
            QGroupBox {
                border: 3px solid #3498db;
                border-radius: 8px;
                padding: 12px 12px;
                font-size: 14px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
                max-width: 605px;
                max-height: 210px;
            }
            QGroupBox::title {
                padding: 3px 3px;
                color: darkblue;
                font-weight: bold;
            }
        """)
    
        mode_label = QLabel("MODE")
        mode_label.setStyleSheet("color: blue; font-weight: bold;")
        
        # Select mode for PLC configuration
        self.mode_combo_box = QComboBox()
        self.mode_combo_box.addItems(["CALIBRATION", "OBSERVATION"])
        self.mode_combo_box.currentIndexChanged.connect(self.update_retarding_plate_angle_input_visibility)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo_box)   
        plc_layout.addLayout(mode_layout)
          
        # Alpha input field
        self.alpha_label = QLabel("Alpha:")
        self.alpha_label.setStyleSheet("color: blue; font-weight: bold;")
        plc_layout.addWidget(self.alpha_label)
        self.alpha_input = QDoubleSpinBox()
        self.alpha_input.setRange(-180, 180)
        self.alpha_input.setDecimals(2)
        self.alpha_input.setSingleStep(1)
        plc_layout.addWidget(self.alpha_input)
        
        # Beta input field
        
        """
        Set beta angle in degrees for both engines
        """
        beta_label = QLabel("Beta:")        
        beta_label.setStyleSheet("color: blue; font-weight: bold;")        
        plc_layout.addWidget(beta_label)        
        self.beta_input = QDoubleSpinBox()
        self.beta_input.setRange(-180, 180)
        self.beta_input.setDecimals(2)
        self.beta_input.setSingleStep(1)        
        plc_layout.addWidget(self.beta_input)      
        
        # Retarding plate angle input field
        """
        Set retarder plate angle in degrees (only make sense if calibration mode is selected)
        """
        retarder_plate_angle_label = QLabel("Retarding plate angle:")        
        retarder_plate_angle_label.setStyleSheet("color: blue; font-weight: bold;")        
        self.retarding_plate_angle_input = QDoubleSpinBox()
        self.retarding_plate_angle_input.setRange(1, 360)
        self.retarding_plate_angle_input.setSingleStep(1)        
        self.retarding_plate_angle_input.setValue(45.0)
        plc_layout.addWidget(retarder_plate_angle_label)        
        plc_layout.addWidget(self.retarding_plate_angle_input)        
        plc_layout.addStretch()  
        
        eng_layout.addWidget(plc_group)   
        
        #Add button to get_current_status from the PLC
        
        get_current_status_btn = QPushButton("Get current status from PLC")
        get_current_status_btn.setStyleSheet("""
            QPushButton {
                border: 6px solid #3498db;
                border-radius: 16px;
                padding: 12px 12px;
                font-size: 16px;
                font-weight: bold;
                color: blue;
                background-color: lightgray;
                max-width: 605px;
                max-height: 30px;
            }
            QPushButton::pressed {
                background-color: #3498db;
                color: white;
            }   
        """)
        get_current_status_btn.clicked.connect(self.getPLCCurrentStatus)
        eng_layout.addWidget(get_current_status_btn)       
                 
        
         # SONG group layout
        song_group = QGroupBox("SONG Configuration")
        song_layout = QVBoxLayout(song_group)        

        song_group.setStyleSheet("""
            QGroupBox {
                border: 3px solid #3498db;
                border-radius: 8px;
                padding: 12px 12px;
                font-size: 14px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
                max-width: 605px;
                max-height: 120px;
            }
            QGroupBox::title {
                padding: 3px 3px;
                color: darkblue;
                font-weight: bold;
            }
        """)
        
        # SONG integration time input field
        """
        Set SONG integration time in seconds
        """
        song_integration_time_label = QLabel("SONG integration time:")        
        song_integration_time_label.setStyleSheet("color: blue; font-weight: bold;")         
        
        self.song_integration_time_input = QDoubleSpinBox()
        self.song_integration_time_input.setRange(0.1, 300)
        self.song_integration_time_input.setDecimals(2)
        self.song_integration_time_input.setSingleStep(0.5)
        self.song_integration_time_input.setValue(2.0) 
           
        song_layout.addWidget(song_integration_time_label)
        song_layout.addWidget(self.song_integration_time_input)
        
        
        # Description input field
        """
        Set description or comment of the acquisition
        """
        description_label = QLabel("Description:")
        description_label.setStyleSheet("color: blue; font-weight: bold;")
        song_layout.addWidget(description_label)
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Default: MUSOL TEST")
        song_layout.addWidget(self.description_input)  
        song_layout.addStretch()  
    
        eng_layout.addWidget(song_group)
        
        """
        Add buttons for configurePLC and AcquireSongImage
        """
        btn_layout = QHBoxLayout()
        configurePLC_btn = QPushButton("Configure PLC")
        configurePLC_btn.setStyleSheet("""
            QPushButton {
                border: 6px solid #3498db;
                border-radius: 8px;
                padding: 12px 12px;
                font-size: 16px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
                max-width: 200px;
                max-height: 60px;
            }
            QPushButton::pressed {
                background-color: #3498db;
                color: white;
            }   
        """)
        
        configurePLC_btn.clicked.connect(self.configurePLC)
        btn_layout.addWidget(configurePLC_btn)
        acquireSongImage_btn = QPushButton("Acquire Song Image")
        acquireSongImage_btn.setStyleSheet("""
            QPushButton {
                border: 6px solid #3498db;
                border-radius: 8px;
                padding: 5px 5px;
                font-size: 16px;
                font-weight: bold;
                color: blue;
                background-color: lightblue;
                max-width: 200px;
                max-height: 60px;
            }
            QPushButton::pressed {
                background-color: #3498db;
                color: white;
            }   
        """)
        
        acquireSongImage_btn.clicked.connect(self.acquireSongImage)
        btn_layout.addWidget(acquireSongImage_btn)    
        eng_layout.addLayout(btn_layout)
        
        # Add the Engineering tab        
        self.tab_widget.addTab(eng_widget, "Engineering")


    def getPLCCurrentStatus(self):
        
        """
        Function to get the current status of the MUSOL PLC.

        Returns:
            tuple: A tuple containing the current status of the MUSOL PLC.
            mode (str): The current mode of the MUSOL PLC.
            alpha_position (float): The current alpha position of the MUSOL PLC.
            beta_position (float): The current beta position of the MUSOL PLC.  
            theta_position (float): The current theta position of the MUSOL PLC.
            reference_position (float): The current reference position of the MUSOL PLC.
            error_code (int): The current error code of the MUSOL PLC. 0 for success
        """
        
        if not self.musol.is_connected():
            self._log_error("Not connected to MUSOL PLC", "getPLCCurrentStatus()")
            self.status_bar.showMessage("ERROR:Not connected to MUSOL PLC...")
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            self.status_bar.repaint()
            return
        else:
            self._log_info("Getting current status of MUSOL PLC", "getPLCCurrentStatus()")
        
        retvals = self.musol.get_current_status()
        # retvals holds: mode, dt80_01, dt80_02, dt80_03, l511
        #print(f"retvals: {retvals}")
        mode = retvals[0]
        dt80_01_pos = retvals[1]
        dt80_02_pos = retvals[2]
        dt80_03_pos = retvals[3]
        l511_pos = retvals[4]
        error_var = retvals[5]   
        
        if error_var != 0: 
            self._log_critical("Returned error from PLC", "getPLCCurrentStatus()",
                                f"ERROR value: {error_var} - ERROR description: {self.musol.get_error_description(error_var)}")
            self.status_bar.clearMessage()
            self.status_bar.showMessage("ERROR: Sending get_current_status commad to PLC", 3000)
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            self.status_bar.repaint()    
            return
        else:
            metadata_msg = f"mode:{mode}, alpha:{dt80_01_pos:.3f},  beta:{dt80_02_pos:.3f},  theta:{dt80_03_pos:.3f},  linear_translator:{l511_pos:.3f}"
            self._log_info("Return from get_current_status cmd", "getPLCCurrentStatus()", metadata_msg)
            
            status_message = f"PLC status - mode:{mode}, - dt80_01:{dt80_01_pos:.2f}, dt80_02:{dt80_02_pos:.2f},  dt80_03:{dt80_03_pos:.2f},  l511:{l511_pos:.2f}"

            self.status_bar.clearMessage()  
            self.statusBar().showMessage(status_message, 50000)
            self.status_bar.setStyleSheet("background-color: rgb(0, 255, 0);")    
            self.status_bar.repaint()
            return

    
    def update_retarding_plate_angle_input_visibility(self):
        
        """
        Updates the visibility of the retarding plate angle input based on the current mode selected.
        
        If the current mode is CALIBRATION, the retarding plate angle input is shown. Otherwise, it is hidden.
        """
        if self.mode_combo_box.currentText() == "CALIBRATION":
            #print ("update_retarding_plate_angle_input_visibility 1, text_mode =", self.mode_combo_box.currentText())
            self.retarding_plate_angle_input.setVisible(True)
        else:
            self.retarding_plate_angle_input.setVisible(False)
            
        #print ("update_retarding_plate_angle_input_visibility2, text_mode =", self.mode_combo_box.currentText())
 
    def get_imageType(self):   
        """
        Retrieves the current image type based on the selected mode.

        If the current mode is CALIBRATION, returns "CALIB". Otherwise, returns "SUN".
        
        Returns:
            str: The current image type.
        """
        if self.mode_combo_box.currentText() == "CALIBRATION":
            current_imageType = "CALIB" 
        else:
            current_imageType = "SUN" 
        
        return current_imageType   
        
    def get_project_data(self):
        # Handle project_num
        """
        Retrieves project number and name from the input fields.

        Returns:
            tuple: A tuple containing the project number and name.
        """
        num_text = self.num_input.text().strip()
        project_num = int(num_text) if num_text.isdigit() else 0

        # Handle project_name
        name_text = self.name_input.text().strip()
        project_name = name_text if name_text else "NoneGiven"

        return project_num, project_name 
 
    def configurePLC(self):
        """
        Configures the PLC with the values entered in the input fields. 
        """
        if not self.musol.is_connected():
            self._log_error("Not connected to MUSOL PLC", "Engineering mode:configurePLC()")
            self.status_bar.showMessage("ERROR:Not connected to MUSOL PLC...")
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            self.status_bar.repaint()
            return
        
        
        # Retrieve the current value of the alpha, beta input fields
        alpha_deg, beta_deg, calibration_theta_deg = self.get_modulation_values()
                
        # Retrieve the current value of the mode combo box
        current_mode = self.mode_combo_box.currentText()
        
        # Set the status bar message
        self.status_bar.clearMessage()
        if self.musol.is_connected():           
            # Log the configuration   and send it to the PLC       
            self._log_info("Sending set_mode cmd to PLC ", "Engineering mode:configurePLC()",f"current_mode:{current_mode}")
            retval = self.musol.set_mode(current_mode)
            if retval != 0: 
                self._log_critical("Returned error from PLC", "Engineering mode:configurePLC()",
                             f"ERROR value: {retval} - ERROR description: {self.musol.get_error_description(retval)}")
                self.status_bar.clearMessage()
                self.status_bar.showMessage("ERROR: Sending set_mode commad to PLC", 3000)
                self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
                self.status_bar.repaint()    
                return
        else:
            self._log_error("Not connected to MUSOL PLC", "Engineering mode:configurePLC()")
            self.status_bar.showMessage("ERROR:Not connected to MUSOL PLC...")
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            self.status_bar.repaint()
            return
        
        # Call the set_modulation method        
        if self.musol.is_connected():
            self._log_info("Sending set_modulation cmd to PLC ", 
                         "Eng. mode:configurePLC()",f"alpha_value:{alpha_deg}, beta_value:{beta_deg}, retarder_plate_angle:{calibration_theta_deg}")   
            return_values = self.musol.set_modulation( alpha_deg, beta_deg, calibration_theta_deg)
            # return l511, dt80_01, dt80_02, dt80_03, result
            #print ("return values", return_values)
            alpha_pos = return_values[0]
            beta_pos = return_values[1]
            theta_pos = return_values[2]
            linear_translator_pos = return_values[3]
            error_var = return_values[4]
            if error_var != 0:
                self._log_critical("Returned error from PLC", "Engineering mode:configurePLC()",
                                f"ERROR value: {error_var} - ERROR description: {self.musol.get_error_description(error_var)}")
                self.statusBar().showMessage(f"ERROR: Sending set_modulation cmd to PLC {self.musol.get_error_description(error_var)}")
                self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);")
                self.statusBar().repaint() 
                return 
        
        else:
            self._log_error("Not connected to MUSOL PLC", "Engineering mode:configurePLC()")
            self.status_bar.showMessage("ERROR:Not connected to MUSOL PLC...")
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            self.status_bar.repaint()
            return
        
        
        
        self._log_debug("Return from set_modulation cmd", "Eng. mode:configurePLC()",
                     f"alpha:{alpha_pos:.3f}, beta:{beta_pos:.3f}, theta:{theta_pos:.3f}, linear_translator:{linear_translator_pos:.3f}, error_var:{error_var}") 
        
        status_message = f"Modulation set successfully to alpha: {alpha_pos:.2f},  beta: {beta_pos:.2f},  theta: {theta_pos:.2f},  linear_translator: {linear_translator_pos:.2f}"
        self.statusBar().showMessage(status_message, 10000)
        self.statusBar().setStyleSheet("background-color: rgb(0, 255, 0);")
        self.statusBar().repaint() 
          
    def acquireSongImage(self):
        """
        Excecute an acquisition cmd on the SONG server to acquire a SONG image and wait for the response.
        """
        if not self.song.is_connected():    
            self._log_error("Not connected to SONG server", "Engineering mode:acquireSongImage()")
            self.status_bar.showMessage("ERROR:Not connected to SONG...")
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            return
        
        # Set the status bar message
        self.status_bar.clearMessage()
        self.status_bar.showMessage("Sending commads to SONG...")
        self.status_bar.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.status_bar.repaint()

        # Retrieve the current value of the alpha, beta input fields
        proj_nr, proj_name = self.get_project_data()
        integration_time = self.song_integration_time_input.value()
        image_type = self.get_imageType()        
        alpha_deg, beta_deg, calibration_theta_deg = self.get_modulation_values()       
  
        # Log and send it to the SONG 
            
        self._log_info("Sending acquire_a_solar_image cmd to SONG ", "Engineering mode:acquireSongImage()",
                    f"proj_nr:{proj_nr}, proj_name:{proj_name},integration_time:{integration_time},imagetype:{image_type},alpha_deg:{alpha_deg},beta_deg:{beta_deg},calibration_theta_deg:{calibration_theta_deg}")    
              
        return_dic = self.song.send_acquire_cmd(proj_nr, proj_name, 
                                                integration_time , image_type, alpha_deg, beta_deg, calibration_theta_deg, 
                                                "MUSONG acquisition")   
        #print("acquisition status", return_dic)             
        status = return_dic["status"]
        message = return_dic["message"]
        if status == 0:
            timestamp = return_dic["timestamp"]
            #acquisition_id = return_dic["acquisition_id"]
            filename = return_dic["filename"]
            status_message = "Acquisition successful: " + filename
            
            self._log_debug(f"Return from acquire_a_solar_image cmd (REQUESTED_IMAGE_TYPE:{image_type})", "Engineering mode:acquireSongImage()",
                        f"status:{status}, message:{message}, timestamp:{timestamp}, filename:{filename}")       
            self.status_bar.showMessage(status_message, 9000)
            self.status_bar.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.status_bar.repaint()
              
            self._log_info("Acquisition successful", "Engineering mode:acquireSongImage()",f"status:{status}, message:{message}, timestamp:{timestamp}, filename:{filename}")
        else:
            self.status_bar.showMessage("ERROR: Acquiring image...")
            self.status_bar.setStyleSheet("background-color: rgb(255, 255, 0);")
            self._log_error("Acquisition failed", "Engineering mode:acquireSongImage()",f"status:{status}, message:{return_dic['message']}")
        
        self.status_bar.repaint()
        return        

    def get_modulation_values(self):
            
        # Retrieve the current value of the alpha, beta input fields
        """
        Retrieve the current values of the alpha, beta, and calibration theta input fields.

        Returns:
            tuple: A tuple containing the alpha, beta, and calibration theta values in degrees.
        """
        alpha_deg = self.alpha_input.value()    
        beta_deg = self.beta_input.value()   
        calibration_theta_deg = self.retarding_plate_angle_input.value() if self.retarding_plate_angle_input.isVisible() else 0.0        
        return alpha_deg, beta_deg, calibration_theta_deg             
                
    def load_and_display_sequence_config(self):
        """
        Opens a file dialog to select a YAML file containing the sequence configuration.
        Validates the selected file using a YAMLSequenceValidator. If the file is valid,
        populates the UI with the configuration data; otherwise, displays validation warnings.
        In case of an error during loading, displays a critical error message.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Sequence Definition YAML File",
            str(Path.home()),
            "YAML Files (*.yaml *.yml)"
        )
        if not file_path:
            return
        
        # Reset progress bar and status bar
        self.progress_bar.setValue(0)
        self.statusBar().clearMessage()
        try:
            sequence_data = YAMLSequenceValidator(file_path)
            self.current_file = file_path
            
            if sequence_data.validate():
                self.populate_ui_with_yaml(sequence_data)
                QMessageBox.information(
                    self, "Success", "All modulation steps are valid!"
                )
            else:
                QMessageBox.warning(
                    self, "Validation Warnings", "\n".join(sequence_data.get_errors())
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    # NOTE: This method is NOT used!!! No "save" button is available in the GUI
    # left for future use in case we want to save the data to a file
    def save_file(self):
        """
        Save the current YAML data to a file.

        If the current file path is not empty, it saves the data to the current file path.
        Otherwise, it opens a file dialog for the user to select a file path and saves the data to the selected file path.
        """
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    # NOTE: This method is NOT used!!! No "save as" button is available in the GUI
    # left for future use in case we want to save the data to a file
    def save_file_as(self):
        """
        Opens a file dialog to select a file path to save the current YAML data to a file.

        If a file path is selected, it saves the data to the selected file path. If the file path does not end with '.yaml' or '.yml', it appends '.yaml' to the file path.

        :return: None
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save YAML File", "", "YAML Files (*.yaml);;All Files (*)")
        
        if file_path:
            if not file_path.endswith(('.yaml', '.yml')):
                file_path += '.yaml'
            
            self.save_to_file(file_path)
    
    def save_to_file(self, file_path):
        """
        Save the current YAML data to a file.

        If the data is not valid, it does not save the data to a file and returns immediately.
        Otherwise, it saves the data to the specified file path. If the file path does not end with '.yaml' or '.yml', it appends '.yaml' to the file path.

        It updates the status bar and window title after successfully saving the file.

        :param file_path: The path to the file where the data will be saved
        :return: None
        """
        if not self.validate_data():
            return
        
        try:
            data = self.get_yaml_data()
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            
            self.current_file = file_path
            self.statusBar().showMessage(f"Saved: {os.path.basename(file_path)}")
            self.setWindowTitle(f"YAML MUSOLGSONG Sequence Configuration Editor - {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}") 
          
    def populate_ui_with_yaml(self, data: YAMLSequenceValidator):
        
        """
        Populate the UI tables with the data from a YAML file containing the 
        sequence configuration.
        The data is expected to have the following structure:

        {
            'modes': {
                'observation': {
                    'modulations': [
                        {'alpha': float, 'beta': float, SONG_int_time: float, 'description': str},
                        ...
                    ]
                },
                'calibration': {
                    'modulations': [
                        {'alpha': float, 'beta': float, SONG_int_time: float, 'description': str},
                        ...
                    ],
                    'retarding_plate_theta_offset': float
                }
            }
        }

        The data is not validated here. Validation should be done before calling this method.

        :param data: The data to display in the UI
        """
        try:
            modeType = data.get_mode()
            if modeType == "observation":

                self.modulations_table.setRowCount(0)
                self.mode_label.setText(f"Mode: OBSERVATION")
                self.mode_label.setStyleSheet("color: blue; font-weight: bold;")
                self.modulations_table.setRowCount(data.get_modulation_count())
                self.retarding_display.setVisible(False)
                self.number_of_cycles_label.setVisible(False)
            elif modeType == "calibration":
                self.modulations_table.setRowCount(data.get_modulation_count())
                self.mode_label.setText(f"Mode: CALIBRATION")
                self.mode_label.setStyleSheet("color: green; font-weight: bold;")                
                offsets = data.get_retarding_plate_offsets()
                self.retarding_display.setText(str(offsets))
                self.retarding_display.setVisible(True)
                   
                required_cycles = 360 // offsets
                self.number_of_cycles_label.setText(f": {required_cycles}")
                self.number_of_cycles_label.setStyleSheet("color: blue; font-weight: light;")   
                self.number_of_cycles_label.setVisible(True)       
                
            for i in range(data.get_modulation_count()):
                    params = data.get_modulation_parameters(i)
                    #print(f"Modulation {i}: {params}")
                    
                    self.modulations_table.setItem(i, 0, QTableWidgetItem(str(params["alpha"])))
                    self.modulations_table.setItem(i, 1, QTableWidgetItem(str(params["beta"])))
                    self.modulations_table.setItem(i, 2, QTableWidgetItem(str(params["SONG_int_time"])))
                    self.modulations_table.setItem(i, 3, QTableWidgetItem(str(params["description"])))
                    
        
            for r in range(self.modulations_table.rowCount()):
                self.modulations_table.setVerticalHeaderItem(r, QTableWidgetItem(str(r + 1)))
        
            self.current_seq_data = data  
            modulations = data.get_modulations()
            self.modulations = modulations
            #print("Modulations:", self.modulations)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate UI:\n{str(e)}")
            
            
    # NOTE: This method is NOT used!!!
    def save_to_yaml(self):
      if self.current_seq_data is not None:
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Sequence Definition YAML File",
            str(Path.home()),
            "YAML Files (*.yaml *.yml)"
        )
        if save_path:
          with open(save_path, 'w') as f:
            yaml.dump(self.current_seq_data, f)
      return

    def start_processing(self):
        #check if SONG is connected
        """
        Start the processing of the modulation data.

        This method is called when the start button is pressed. It will check if
        the SONG and MUSOL PLC are connected, and if the sequence configuration
        is loaded. If all conditions are met, it will start the processing of the
        modulation data.

        :return: None
        """  
        
        #check if SONG is connected
        if not self.song.is_connected():
            self._log_critical("Can not process. Not connected to SONG server", "start_processing()")
            self.statusBar().showMessage("ERROR:Can not process!! Not connected to SONG. Must re-start the application...",10000)
            self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);")
            self.statusBar().repaint()
            return
               
        #check if MUSOL is connected, both should be connected
        if not self.musol.is_connected():
            self._log_critical("Can not process. Not connected to MUSOL PLC", "start_processing()")
            self.statusBar().showMessage("ERROR:Can not process!! Not connected to MUSOL PLC. Must re-start the application...",10000)
            self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);")
            self.statusBar().repaint()
            return
        
        if self.current_seq_data is None:
            self._log_critical("Can not process. No sequence configuration loaded", "start_processing()")
            self.statusBar().showMessage("ERROR:Can not process!! No sequence configuration loaded...",10000)
            self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);")
            self.statusBar().repaint()
            return
        
        self.menuBar().setEnabled(False)
        self.process_button.setEnabled(False)
        self.abort_button.setEnabled(True)
        self.tab_widget.widget(1).setEnabled(False)   # disable Engineering tab content
        
        
        self.statusBar().showMessage(f"Processing file: {self.current_file} started")
        self.statusBar().setStyleSheet("background-color: rgb(0, 255, 0);")
        self.statusBar().repaint()
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        #Prepare the data for processing
        initial_data =self.prepare_data_for_processing()  
        #print ("*****IN MAIN QT WINDOW********")
        #print(initial_data)
        #print ("*************")

        # Create worker and thread
        self.worker = ProcessingWorker(initial_data)
        self.worker_thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)        
        
        
        # Connect worker signals   
        # Connect signals
        self.worker_thread.started.connect(self.worker.process_modulation_data)
        self.worker.progress_updated.connect(self.on_update_status_labels)
        self.worker.status_updated.connect(self.status_label.setText)
        self.worker.processing_finished.connect(self.on_processing_finished)
        
        # Clean up when thread finishes
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.processing_finished.connect(self.worker_thread.quit)
        
        # Start the thread
        self.worker_thread.start()
        
    def on_update_status_labels(self,received_status):
           
        """
        Update the status labels in the UI based on the received status from the worker thread.

        This method is called whenever the worker thread sends an update signal with the current status.

        Parameters
        ----------
        received_status : dict
            A dictionary containing the current status of the modulation sequence processing.

        Returns
        -------
        None
        """
        percentage_done = received_status['percetage_done']
        self.progress_bar.setValue(percentage_done)
        
        current_cycle = received_status['current_cycle']
        total_cycles = received_status['number_of_cycles']
        value = f"{current_cycle}/{total_cycles}"
        self.labels['Modulation Cycle'].setText(str(value))
        
        current_step = received_status['current_step'] 
               
        alpha_str = f"{received_status['alpha']:.2f}"
        beta_str = f"{received_status['beta']:.2f}"
        theta_str = f"{received_status['theta']:.2f}"
        translation_unit_str = f"{received_status['translation_unit']:.2f}"
        SONG_int_time = received_status['SONG_int_time'] 
        
        
        header_item = self.modulations_table.verticalHeaderItem(current_step-1)
        header_item.setBackground(QColor("#f9e79f"))  # light yellow    
        self.labels['Modulation Step'].setText(str(current_step))    
        self.labels['Translation Unit'].setText(str(translation_unit_str))
        self.labels['Alpha position'].setText(str(alpha_str))    
        self.labels['Beta position'].setText(str(beta_str))    
        self.labels['Theta position'].setText(str(theta_str))    
        self.labels['SONG integration time'].setText(str(SONG_int_time))
        
        #print("*********")
        #print(f"current_cycle: {current_cycle}, total_cycles: {total_cycles}, current_step: {current_step}, self.modulations_table.rowCount(): {self.modulations_table.rowCount()}" )#  current_cycle, total_cycles, current_step, self.modulations_table.rowCount()) 
        #print("*********")
        if (current_step == self.modulations_table.rowCount()):
            self.reset_table_index_hihlighting()
        
        return
     
    def reset_table_index_hihlighting(self):
        for i in range(self.modulations_table.rowCount()):   
            header_item = self.modulations_table.verticalHeaderItem(i)  
            header_item.setBackground(QColor("white"))  # light white    
        return
       
    def prepare_data_for_processing(self):
        
        """
        Prepare the data for processing. This method is called when the start button is pressed.
        
        It will check if the sequence configuration is loaded and if the number of cycles is set.
        If not, it will set the number of cycles to 1 and the offset angle to 0.
        
        It will then prepare a dictionary with the initial data for processing and return it.
        
        :return: dict
            A dictionary containing the initial data for processing.
        """
        if self.current_seq_data is None:
            self._log_critical("Can not process. No sequence configuration loaded", "start_processing()")
            self.statusBar().showMessage("ERROR:Can not process!! No sequence configuration loaded...",8000)
            self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);")
            return
        
        if self.current_seq_data.get_number_of_cycles() == None:
            number_of_cycles = 1
            offset_angle = 0
        else:
            number_of_cycles = self.current_seq_data.get_number_of_cycles()
            offset_angle = self.current_seq_data.get_retarding_plate_offsets()
        
        
        proj_nr, proj_name = self.get_project_data()    
        initial_data = {
            'modulations': self.current_seq_data.get_modulations(),
            'op_mode': self.current_seq_data.get_mode().upper(),
            'modulations_count': self.current_seq_data.get_modulation_count(),
            'number_of_cycles': number_of_cycles,
            'offset_angle': offset_angle,
            'proj_number': proj_nr,
            'proj_name': proj_name,
            'musol_connector': self.musol,
            'song_connector': self.song,
            'logger': self.logger
        }
        
        #print("Initial data:", initial_data)
        return initial_data
    
        
    def abort_processing(self):
        """Abort the background processing"""
        if self.worker:
            
            self.statusBar().showMessage("Aborting processing...",10000)
            self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);")
            self.statusBar().repaint()            
            self.worker.abort()
       
    def on_processing_finished(self, completed):
        """Handle processing completion or abortion"""
        # Re-enable start button and disable abort button
        
        self.process_button.setEnabled(True)
        self.abort_button.setEnabled(False)
        self.menuBar().setEnabled(True)
        self.tab_widget.widget(1).setEnabled(True) # enable Engineering tab content

        
        self.reset_table_index_hihlighting()
        
        if completed:
            self.statusBar().clearMessage()
            self.progress_bar.setValue(100)
        else:
            # An error or aborted. Reset progress bar
            if self.worker.is_aborted():
                self.statusBar().showMessage("Process terminated due ABORT requested...",10000)
            else:
                self.statusBar().showMessage("Process terminated due to error...",10000)
                
            self.statusBar().setStyleSheet("background-color: rgb(255, 255, 0);") 
            self.statusBar().repaint()
            self.progress_bar.setValue(0)
            pass
        
        # Clean up
        if self.worker_thread:
            #print(f"cleanning up completed: {completed}")

            self.worker_thread.quit()
            self.worker_thread.wait()  # Wait for thread to finish
            self.worker_thread = None
            self.worker = None    
    
    def closeEvent(self, event):
        """Handle window closing - make sure to clean up threads"""
        if self.worker_thread and self.worker_thread.isRunning():
            if self.worker:
                self.worker.abort()
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()
    
    def abort_processing1(self):
        """
        Aborts the current processing cycle. This function is called when the user 
        clicks the "Abort" button. It sets the is_aborting flag to True and updates 
        the status bar to show that the processing has been aborted.

        Returns:
            None
        """
        self.is_aborting = True
        self.statusBar().showMessage("Processing aborted")
        self.statusBar().setStyleSheet("background-color: rgb(255, 69, 0);")
        return 
    
    def update_number_of_cycles(self):
        """
        Updates the number of cycles required for the current retarding plate theta offset.
        
        The number of cycles is calculated as 360 divided by the theta offset.
        If the theta offset is not in the allowed values, the label is set to red
        with an error message. Otherwise, the label is set to blue with the
        calculated number of cycles.
        """
        ALLOWED_THETA_ANGLE_VALUES = [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 60, 72, 90, 120, 180, 360]
        offset = self.retarding_display.text()        
        if (offset not in ALLOWED_THETA_ANGLE_VALUES):
            self.number_of_cycles_label.setText(f"Invalid Incremetal angle per cycle: {offset}")
            self.number_of_cycles_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            required_cycles = 360 // offset
            self.number_of_cycles_label.setText(f": {required_cycles}")
            self.number_of_cycles_label.setStyleSheet("color: blue; font-weight: bold;")       
        return       
 
    def _log_debug(self, message: str, component: str = "system", 
                 metadata: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        if self.logger:
            self.logger.log_debug(message, component, metadata)
        else:
            print(f"DEBUG: {message}")
    def _log_info(self, message: str, component: str = "system", 
                 metadata: Optional[Dict[str, Any]] = None):
        """Log info message"""
        if self.logger:
            self.logger.log_info(message, component, metadata)
        else:
            print(f"INFO: {message}")
    
    def _log_critical(self, message: str, component: str = "system", 
                 metadata: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        if self.logger:
            self.logger.log_critical(message, component, metadata)
        else:
            print(f"CRITICAL: {message}")
    def _log_error(self, message: str, component: str = "system", 
                 metadata: Optional[Dict[str, Any]] = None):
        """Log error message"""
        if self.logger:
            self.logger.log_error(message, component, metadata)
        else:
            print(f"ERROR: {message}")