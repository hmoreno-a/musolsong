import sys
import yaml
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QGroupBox, QFormLayout,
                            QLineEdit, QDoubleSpinBox,QSpinBox, QPushButton,
                            QTableWidget, QHeaderView,
                            QFileDialog, QMessageBox, QCheckBox,QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import os

ALLOWED_THETA_ANGLE_VALUES = [1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 60, 72, 90, 120, 180, 360]
class ModulationTableWidget(QTableWidget):
    def __init__(self, parent: QWidget = None) -> None:
        """
        Initialize ModulationTableWidget instance.

        :param parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """
        Set up the UI for the modulation table widget.

        This method initializes the table with four columns: 'Alpha', 'Beta', 
        'Integration Time', and 'Description'. It also configures the header 
        sections, setting the resize mode for each column and specifying fixed 
        widths for the first three columns. An initial 2 empty rows are added to 
        the table.
        """

        self.setColumnCount(4)
        self.setHorizontalHeaderLabels([
            'Alpha \n(-180°..180°)', 'Beta \n(-180°..180°)', 'Integration Time (sec)', 'Description'
        ])

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.setColumnWidth(0, 120)
        self.setColumnWidth(1, 120)
        self.setColumnWidth(2, 165)

        self.add_row()
        self.add_row()
    
    def add_row(self):
        """
        Add a new row to the modulation table.

        This method inserts a new row at the end of the table with the following widgets:
        - A QDoubleSpinBox for the alpha angle, ranging from -180 to 180 degrees, with
        2 decimal places and a step size of 1 degree.
        - A QDoubleSpinBox for the beta angle, ranging from -180 to 180 degrees, with
        2 decimal places and a step size of 1 degree, initialized to -45 degrees.
        - A QDoubleSpinBox for the integration time, ranging from 0.1 to 300 seconds,
        with 2 decimal places and a step size of 0.5 seconds, initialized to 2.0 seconds.
        - A QLineEdit for an optional description, with a placeholder text of "Optional description...".
        """

        row = self.rowCount()
        self.insertRow(row)
        
        # Alpha spinbox
        alpha_spin = QDoubleSpinBox()
        alpha_spin.setRange(-180, 180)
        alpha_spin.setDecimals(2)
        alpha_spin.setSingleStep(1)
        self.setCellWidget(row, 0, alpha_spin)
        
        # Beta spinbox
        beta_spin = QDoubleSpinBox()
        beta_spin.setMaximum(180)
        beta_spin.setMinimum(-180)    
        beta_spin.setDecimals(2)
        beta_spin.setSingleStep(1)
        beta_spin.setValue(-45)
        self.setCellWidget(row, 1, beta_spin)
        
        # Integration time spinbox
        int_time_spin = QDoubleSpinBox()
        int_time_spin.setRange(0.1, 300)
        int_time_spin.setDecimals(2)
        int_time_spin.setSingleStep(0.5)
        int_time_spin.setValue(2.0)
        self.setCellWidget(row, 2, int_time_spin)
        
        # Description line edit
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Optional description...")
        self.setCellWidget(row, 3, desc_edit)
        
    
    def remove_selected_row(self):
        current_row = self.currentRow()
        if current_row >= 0 and self.rowCount() > 1:
            self.removeRow(current_row)
    
    def get_modulations(self):
        """
        Return a list of modulations from the table data.
        
        Each modulation is a dictionary with the following keys:
        
        - alpha: float, the alpha angle in degrees
        - beta: float, the beta angle in degrees
        - SONG_int_time: float, the integration time in seconds
        - description: str, an optional description of the modulation
        
        Modulations are only included in the returned list if all of the above
        values are valid (i.e. they are not NaN or None).
        """
        modulations = []
        for row in range(self.rowCount()):
            alpha_widget = self.cellWidget(row, 0)
            beta_widget = self.cellWidget(row, 1)
            int_time_widget = self.cellWidget(row, 2)
            desc_widget = self.cellWidget(row, 3)

            
            if alpha_widget and beta_widget and int_time_widget:
                modulation = {
                    'alpha': alpha_widget.value(),
                    'beta': beta_widget.value(),
                    'SONG_int_time': int_time_widget.value()
                }
                
                if desc_widget and desc_widget.text().strip():
                    modulation['description'] = desc_widget.text().strip()
                
                modulations.append(modulation)
        
        return modulations
    
    def set_modulations(self, modulations):
        # Clear existing rows
        """
        Populate the modulation table with the given modulations.

        The modulations argument should be a list of dictionaries, where each
        dictionary represents a modulation with the following keys:

        - alpha: float, the alpha angle in degrees
        - beta: float, the beta angle in degrees
        - SONG_int_time: float, the integration time in seconds
        - description: str, an optional description of the modulation

        The table will be cleared and the modulations will be added in the
        order they are given in the list. If the list is empty, a single empty
        row will be added to the table.
        """
        self.setRowCount(0)
        
        # Add rows for each modulation
        for mod in modulations:
            self.add_row()
            row = self.rowCount() - 1
            
            # Set values
            alpha_widget = self.cellWidget(row, 0)
            beta_widget = self.cellWidget(row, 1)
            int_time_widget = self.cellWidget(row, 2)
            desc_widget = self.cellWidget(row, 3)
            
            if alpha_widget:
                alpha_widget.setValue(mod.get('alpha', 0.0))
            if beta_widget:
                beta_widget.setValue(mod.get('beta', 0.0))
            if int_time_widget:
                int_time_widget.setValue(mod.get('SONG_int_time', 1.0))       
            if desc_widget:
                desc_widget.setText(mod.get('description', ''))
        
        # Ensure at least one row exists
        if self.rowCount() == 0:
            self.add_row()

class YAMLEditorGUI(QMainWindow):
    def __init__(self):
        """
        Initialize the YAMLEditorGUI instance.

        This constructor sets up the main window by initializing necessary attributes
        such as the current file, and calls the method to set up the user interface.
        """

        super().__init__()
        self.current_file = None
        self.init_ui()
    
    def init_ui(self):
        """
        Initialize the user interface components.
        
        This method sets the window title and size, creates the menu bar,
        main widget, tab widget, control buttons, and status bar.
        """
        self.setWindowTitle("YAML MUSOLGSONG Sequence Configuration Editor")
        self.setGeometry(100, 100, 900, 700)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
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
        
        # Create tabs
        self.create_calibration_tab()
        self.create_observation_tab()
        
        # Add control buttons
        self.create_control_buttons(layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("background-color: rgb(0, 255, 0);")
    
    def create_menu_bar(self):
        """
        Create the menu bar for the application.
        
        Creates the menu bar with items "File", "New", "Open", "Save", "Save As...",
        and "Exit". The "New" action creates a new untitled YAML file, the "Open"
        action opens an existing YAML file, the "Save" action saves the current file
        with its current name, the "Save As..." action saves the current file with
        a new name, and the "Exit" action closes the application.
        """
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def create_calibration_tab(self):
        # Calibration tab
        """
        Create the calibration tab.

        This method creates the calibration tab, which contains the enable
        calibration checkbox, the retarding plate offset spinbox, and the
        modulation table. The modulation table is a table that allows the user
        to add and remove modulations for the calibration mode. The number of
        cycles is also displayed based on the value of the retarding plate offset
        spinbox.

        :return: None
        """
        cal_widget = QWidget()
        cal_layout = QVBoxLayout(cal_widget)
        
        # Enable calibration checkbox
        self.cal_enabled = QCheckBox("Enable Calibration Mode")
        self.cal_enabled.setChecked(False)
        self.cal_enabled.toggled.connect(self.toggle_calibration_mode)
        cal_layout.addWidget(self.cal_enabled)
        
        # Calibration content widget
        self.cal_content = QWidget()
        cal_content_layout = QVBoxLayout(self.cal_content)
        
        # Retarding plate offsets
        offset_group = QGroupBox("Retarding Plate Offsets")
        offset_layout = QFormLayout(offset_group)
        
        self.retarding_plate_offsets = QSpinBox()
        self.retarding_plate_offsets.setRange(1, 360)
        self.retarding_plate_offsets.setKeyboardTracking(False)
        self.retarding_plate_offsets.setSingleStep(1)
        self.retarding_plate_offsets.setSuffix(" degrees")
        self.retarding_plate_offsets.setValue(5)  # Default to 5 degrees
        self.retarding_plate_offsets.valueChanged.connect(self.update_number_of_cycles)
        offset_layout.addRow("Incremental angle per cycle:", self.retarding_plate_offsets)
        
        # Add validation info label
        info_label = QLabel("Must be a factor of 360 (e.g., 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30, 36, 40, 45, 60, 72, 90, 120, 180, 360)")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        offset_layout.addRow("Valid values:", info_label)
        

        # Add number of cycles  info
        self.number_of_cycles_label = QLabel("Number of cycles: 72 ")
        self.number_of_cycles_label.setStyleSheet("color: blue; font-weight: bold;")
        offset_layout.addRow("", self.number_of_cycles_label)
        
        cal_content_layout.addWidget(offset_group)
        
        # Modulations
        mod_group = QGroupBox("Modulations")
        mod_layout = QVBoxLayout(mod_group)
        
        self.cal_modulations = ModulationTableWidget()
        mod_layout.addWidget(self.cal_modulations)
        
        # Modulation control buttons
        mod_btn_layout = QHBoxLayout()
        
        add_cal_btn = QPushButton("Add Modulation")
        add_cal_btn.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                border: 2px solid #999;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2ecc71;  /* highlight if toggle/checked */
                color: white;
            }
        """)
        add_cal_btn.clicked.connect(self.add_calibration_modulation)
        mod_btn_layout.addWidget(add_cal_btn)
        
        remove_cal_btn = QPushButton("Remove Selected")
        remove_cal_btn.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                border: 2px solid #999;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2ecc71;  /* highlight if toggle/checked */
                color: white;
            }
        """)

        remove_cal_btn.clicked.connect(self.remove_calibration_modulation)
        mod_btn_layout.addWidget(remove_cal_btn)   
        mod_btn_layout.addStretch()  
        mod_layout.addLayout(mod_btn_layout)
        
        cal_content_layout.addWidget(mod_group)
        
        cal_layout.addWidget(self.cal_content)
        self.tab_widget.addTab(cal_widget, "Calibration")
    
    def create_observation_tab(self):
        # Observation tab
        """
        Create the Observation tab.
        
        This tab includes a checkbox to enable Observation mode,
        a table for adding Observation modulations, and buttons to add and remove modulations.
        """
        
        obs_widget = QWidget()
        obs_layout = QVBoxLayout(obs_widget)
        
        # Enable observation checkbox
        self.obs_enabled = QCheckBox("Enable Observation Mode")
        self.obs_enabled.setChecked(False)
        self.obs_enabled.toggled.connect(self.toggle_observation_mode)
        obs_layout.addWidget(self.obs_enabled)
        
        # Observation content widget
        self.obs_content = QWidget()
        obs_content_layout = QVBoxLayout(self.obs_content)
        
        # Modulations
        mod_group = QGroupBox("Modulations")
        mod_layout = QVBoxLayout(mod_group)
        
        self.obs_modulations = ModulationTableWidget()
        mod_layout.addWidget(self.obs_modulations)
        
        # Modulation control buttons
        mod_btn_layout = QHBoxLayout()
        
        add_obs_btn = QPushButton("Add Modulation")
        add_obs_btn.clicked.connect(self.obs_modulations.add_row)
        mod_btn_layout.addWidget(add_obs_btn)
        
        remove_obs_btn = QPushButton("Remove Selected")
        remove_obs_btn.clicked.connect(self.obs_modulations.remove_selected_row)
        mod_btn_layout.addWidget(remove_obs_btn)
        
        mod_btn_layout.addStretch()
        mod_layout.addLayout(mod_btn_layout)
        
        obs_content_layout.addWidget(mod_group)
        
        obs_layout.addWidget(self.obs_content)
        self.tab_widget.addTab(obs_widget, "Observation")
    
    def create_control_buttons(self, layout):
        """
        Create control buttons (Validate and Preview YAML) and add them to the given layout.
        
        The Validate button triggers the validate_data slot, and the Preview YAML button
        triggers the preview_yaml slot.
        """
        btn_layout = QHBoxLayout()
        
        validate_btn = QPushButton("Validate")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                border: 2px solid #999;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2ecc71;  /* highlight if toggle/checked */
                color: white;
            }
        """)
        validate_btn.clicked.connect(self.validate_data)
        btn_layout.addWidget(validate_btn)
        
        preview_btn = QPushButton("Preview YAML")
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                border: 2px solid #999;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2ecc71;  /* highlight if toggle/checked */
                color: white;
            }
        """)
        preview_btn.clicked.connect(self.preview_yaml)
        btn_layout.addWidget(preview_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def update_number_of_cycles(self):
        """
        Update the number of cycles required for the current retarding plate theta offset.
        
        The number of cycles is calculated as 360 divided by the theta offset.
        If the theta offset is not in the allowed values, the label is set to red
        with an error message. Otherwise, the label is set to blue with the
        calculated number of cycles.
        """
        offset = int(self.retarding_plate_offsets.value())
        if (offset not in ALLOWED_THETA_ANGLE_VALUES):
            self.number_of_cycles_label.setText(f"Invalid Retarding plate theta offset: {offset}")
            self.number_of_cycles_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            required_cycles = 360 // offset
            self.number_of_cycles_label.setText(f"Number of cycles: {required_cycles}")
            self.number_of_cycles_label.setStyleSheet("color: blue; font-weight: bold;")

    
    def add_calibration_modulation(self):
        """Add a modulation and update count"""
        self.cal_modulations.add_row()
    
    def remove_calibration_modulation(self):
        """Remove selected modulation and update count"""
        self.cal_modulations.remove_selected_row()
    
    
    def toggle_calibration_mode(self, checked):
        self.cal_content.setEnabled(checked)
        
    
    def toggle_observation_mode(self, checked):
        self.obs_content.setEnabled(checked)
    
    def is_factor_of_360(self, value):
        """Check if a value is a factor of 360"""
        if value <= 0 or value > 360:
            return False
        return 360 % value == 0
    
    def get_factors_of_360(self):
        """Get all factors of 360 in the range [1, 360]"""
        factors = []
        for i in range(1, 361):
            if 360 % i == 0:
                factors.append(i)
        return factors
    
    def validate_data(self):
        """
        Validate the data in the YAML editor.
        
        This method checks that at least one mode (Calibration or Observation) is enabled,
        and that each enabled mode has at least one modulation. It also checks that the
        retarding plate offset in the Calibration mode is a factor of 360.
        
        If there are any errors, a warning box is displayed with a list of errors.
        If all data is valid, a success box is displayed.
        
        Returns:
            bool: True if all data is valid, False otherwise.
        """
        errors = []
        
        # Check that at least one mode is enabled
        if not self.cal_enabled.isChecked() and not self.obs_enabled.isChecked():
            errors.append("At least one mode (Calibration/Observation) must be enabled.")
            
        #  Allow only one mode to be enabled at a time.
        if self.cal_enabled.isChecked() and self.obs_enabled.isChecked():
            errors.append("Only one mode (Calibration/Observation) can be enabled at a time.")
        
        # Validate calibration mode
        if self.cal_enabled.isChecked():
            cal_mods = self.cal_modulations.get_modulations()
            if not cal_mods:
                errors.append("Calibration mode requires at least one modulation.")
            
            # Validate retarding plate offsets
            # Check that the value is a factor of 360
            offset_value = int(self.retarding_plate_offsets.value())
            if not self.is_factor_of_360(offset_value):
                valid_factors = self.get_factors_of_360()
                errors.append(f"Retarding plate offset ({offset_value}°) must be a factor of 360°.\n"
                             f"Valid values: {', '.join(map(str, valid_factors))}")
            
        
        # Validate observation mode
        if self.obs_enabled.isChecked():
            obs_mods = self.obs_modulations.get_modulations()
            if not obs_mods:
                errors.append("Observation mode requires at least one modulation.")
        
        if errors:
            error_message = "\n".join(errors)
            QMessageBox.warning(self, "Validation Errors", error_message)
            return False

        QMessageBox.information(self, "Validation", "All modulations are valid!")
        return True
    
    def get_yaml_data(self):
        """
        Get the YAML data from the editor.

        This method creates a YAML data structure based on the current state of the editor.
        It checks which modes are enabled, and populates the data structure with the relevant modulation data.

        Returns:
            dict: The YAML data structure.
        """
        data = {'modes': {}}
        
        # Add calibration mode if enabled
        if self.cal_enabled.isChecked():
            cal_data = {
                # Retarding plate offset in degrees
                'retarding_plate_offsets': int(self.retarding_plate_offsets.value()),
                # List of modulations for calibration mode
                'modulations': self.cal_modulations.get_modulations()
            }
            data['modes']['calibration'] = cal_data
        
        # Add observation mode if enabled
        if self.obs_enabled.isChecked():
            obs_data = {
                # List of modulations for observation mode
                'modulations': self.obs_modulations.get_modulations()
            }
            data['modes']['observation'] = obs_data
        
        return data
    
    def set_yaml_data(self, data):
        # Clear existing data
        """
        Populate the editor with YAML data.

        :param data: The YAML data to display in the editor.
        :type data: dict
        """
        self.cal_enabled.setChecked(False)
        self.obs_enabled.setChecked(False)
        
        modes = data.get('modes', {})
        
        # Load calibration mode
        if 'calibration' in modes:
            self.cal_enabled.setChecked(True)
            cal_data = modes['calibration']
            
            # Set retarding plate offsets
            self.retarding_plate_offsets.setValue(
                cal_data.get('retarding_plate_offsets', 0)
            )
            
            # Set modulations
            self.cal_modulations.set_modulations(
                cal_data.get('modulations', [])
            )
        
        # Load observation mode
        if 'observation' in modes:
            self.obs_enabled.setChecked(True)
            obs_data = modes['observation']
            
            # Set modulations
            self.obs_modulations.set_modulations(
                obs_data.get('modulations', [])
            )
    
    def preview_yaml(self):
        """
        Preview the YAML data in a dialog box.

        This method first validates the YAML data in the editor. If the data is valid,
        it generates the YAML string and displays it in a message box for preview.

        The preview dialog provides an overview of the generated YAML and allows the
        user to see the data structure before saving or further processing.
        """

        if self.validate_data():
            data = self.get_yaml_data()
            yaml_text = yaml.dump(data, default_flow_style=False, indent=2)
            
            # Create preview dialog
            preview_dialog = QMessageBox(self)
            preview_dialog.setMinimumSize(600, 600);  # Set dialog size to 600x600
            preview_dialog.setDetailedText(yaml_text)
            preview_dialog.setWindowTitle("YAML Preview")
            preview_dialog.setText("Generated YAML:")
            preview_dialog.setStyleSheet("QLabel{min-width: 300px; min-height: 70px; font-size: 12pt;}");           
            preview_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            preview_dialog.exec()
    
    def new_file(self):
        # Reset to default state
        """
        Reset the editor to its default state, clearing any existing data and 
        preparing for a new file to be created.
        """
        self.current_file = None
        self.cal_enabled.setChecked(False)
        self.obs_enabled.setChecked(False)
        self.retarding_plate_offsets.setValue(1)
        
        # Clear modulation tables
        self.cal_modulations.set_modulations([])
        self.obs_modulations.set_modulations([])
        
        # Update calibration modulations count
        self.update_number_of_cycles()
        
        self.statusBar().showMessage("New file created")
        
        self.setWindowTitle("YAML MUSOLGSONG Sequence Configuration Editor - New File")
    
    def open_file(self):
        """
        Open an existing YAML file using a file dialog.

        This method opens a file dialog for the user to select a YAML file. If a file is selected,
        it loads the YAML data and populates the editor with the configuration data. If the file
        is valid, it updates the UI with the configuration data; otherwise, it displays errors
        in a message box. In case of an error during loading, it displays a critical error message.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open YAML File", "", "YAML Files (*.yaml *.yml);;All Files (*)")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                
                self.set_yaml_data(data)
                self.current_file = file_path
                self.statusBar().showMessage(f"Opened: {os.path.basename(file_path)}")
                self.setWindowTitle(f"YAML MUSOLGSONG Sequence Configuration Editor - {os.path.basename(file_path)}")
                
                # Update calibration modulations count after loading
                if self.cal_enabled.isChecked():
                    self.update_number_of_cycles()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
    
    def save_file(self):
        """
        Save the current YAML data to a file.

        If the current file path is not empty, it saves the data to the current file path.
        Otherwise, it opens a file dialog for the user to select a file path and saves the data to the selected file path.
        :return: None
        """
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """
        Open a file dialog for the user to select a file path to save the current YAML data to a file.

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
