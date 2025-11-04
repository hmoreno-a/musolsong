"""
MusolsongCLI class
Handles YAML sequence modulation file processing
"""

from pathlib import Path
from typing import Dict, Any, Optional

from musolsong.controller.musolsong_tools.yaml_sequence_validator import YAMLSequenceValidator

class MusolsongCLI:
    def __init__(self, plc_client, song_client, logger):
        """
        Initializes a MusolsongCLI instance with a PLC client, a SONG client, and a logger.
        
        Args:
            plc_client (MusolLib): The PLC client instance.
            song_client (SONGClient): The SONG client instance.
            logger (SystemLogger): The system logger instance.
        """
        self.plc_client = plc_client
        self.song_client = song_client
        self.logger = logger
        
        self.current_seq_data = None # Current sequence validated data (YAMLSequenceValidator) 
        self.is_aborting = False   # Flag to indicate if the processing operation is being aborted

    def process_sequence_file(self, sequence_yaml_file: str, project_name: str, 
                       project_number: int, validate_only: bool = False,verbose: bool = False) -> bool:
        
        # Validate YAML file
        """
        Processes a YAML sequence modulation file
        
        Args:
            sequence_yaml_file (str): Path to the YAML sequence modulation file
            project_name (str): Name of the project
            project_number (int): Number of the project
            validate_only (bool, optional): If True, only validates the YAML file and does not process the modulation data. Defaults to False.
            verbose (bool, optional): If True, displays more detailed logging information. Defaults to False.
        
        Returns:
            bool: True if the YAML file was successfully validated and processed, False otherwise
        """
        if not self.validate_project_yaml(sequence_yaml_file):
            return False
            
        self._log_info("Project YAML validation successful")
            
        if validate_only:
            self._log_info("Validation completed - no processing was selected", "process_sequence_file()")
            return True
        
         #check if SONG is connected
        if not self.song_client.is_connected():
            self._log_critical("Can not process. Not connected to SONG server", "process_sequence_file()")
            return False
               
        #check if MUSOL is connected, both should be connected
        if not self.plc_client.is_connected():
            self._log_critical("Can not process. Not connected to MUSOL PLC", "process_sequence_file()")
            return False
        
        if self.current_seq_data is None:
            self._log_critical("Can not process. No sequence configuration loaded", "process_sequence_file()")
            return False
          
        # Process the modulation data
        try:
               
            self._log_info(f"Starting sequence modulation file processing: {project_name} (#{project_number})",
                       "process_sequence_file")     
                
            #Prepare the data for processing
            initial_data = self.prepare_data_for_processing(project_name, project_number)
            
            if( self.process_modulation_data(initial_data)):           
                self._log_debug(f"Project '{project_name}' succesfully processed ", "process_sequence_file()")
                return True
            else:
                return False    
            
        except Exception as e:
            self._log_error(f"Sequence modulation processing failed: {e}", "process_sequence_file()")
            return False
        
    def validate_project_yaml(self, file_path: str) -> bool:
        """
        Validate a project YAML file.

        Args:
            file_path: The path to the YAML file to validate

        Returns:
            bool: True if the YAML file is valid, False otherwise

        Raises:
            Exception: If an error occurs while reading the YAML file
        """
        path = Path(file_path)
           
        self._log_info(f"Validating sequence file: {path}", "validate_project_yaml")
        if not path.exists():
            self._log_error(f"Project YAML file '{file_path}' does not exist","validate_project_yaml()")
            return False
            
        if not path.is_file():
            self._log_error(f"'{file_path}' is not a file", "validate_project_yaml()")
            return False
            
        try:            
            sequence_data = YAMLSequenceValidator(file_path)
            self.current_file = file_path    
            if sequence_data.validate():
                self._log_info("Sequence YAML file validation successful", "validate_project_yaml()")
                self.current_seq_data = sequence_data
                return True
            else:
                self._log_error("\n".join(sequence_data.get_errors()), "validate_project_yaml()")
                return False
        except Exception as e:
            self._log_error(f"Error reading sequence YAML file : {e}", "validate_project_yaml()")
            return False
    
 
    def prepare_data_for_processing(self, project_name: str, 
                       project_number: int) -> dict:
        
        """
        Prepare the data for processing. 
        
        It will check if the sequence configuration is loaded and if the number of cycles is set.
        If not, it will set the number of cycles to 1 and the offset angle to 0.
        
        It will then prepare a dictionary with the initial data for processing and return it.
        
        :return: dict
            A dictionary containing the initial data for processing.
        """
        
        if self.current_seq_data.get_number_of_cycles() == None:
            number_of_cycles = 1
            offset_angle = 0
        else:
            number_of_cycles = self.current_seq_data.get_number_of_cycles()
            offset_angle = self.current_seq_data.get_retarding_plate_offsets()
  
        initial_data = {
            'modulations': self.current_seq_data.get_modulations(),
            'op_mode': self.current_seq_data.get_mode().upper(),
            'modulations_count': self.current_seq_data.get_modulation_count(),
            'number_of_cycles': number_of_cycles,
            'offset_angle': offset_angle,
            'proj_number': project_number,
            'proj_name': project_name,
            'musol_connector': self.plc_client,
            'song_connector': self.song_client,
            'logger': self.logger
        }
        return initial_data
    
    
    def process_modulation_data(self,input_data: dict) -> bool:
        
        """
        Process the modulation data.
        
        Args:
            input_data (dict): A dictionary containing the initial data for processing.
        Returns:
            bool: True if the modulation data was successfully processed, False otherwise
        """
        #get data for processing    
        mod_data = {
            'modulations': input_data["modulations"],
            'mode_uppercase': input_data["op_mode"],
            'modulations_count': input_data["modulations_count"],
            'number_of_cycles': input_data["number_of_cycles"],
            'offset_angle': input_data["offset_angle"],
            'proj_number': input_data["proj_number"], 
            'proj_name': input_data["proj_name"],       
        }
        self.musol = input_data["musol_connector"]
        self.song = input_data["song_connector"]
        self.logger = input_data["logger"]
        current_theta = 0.0
        current_cycle = 0
        
        self._log_info(f"Sequence modulation process started", "sequence_processor.process_modulation_data()") 
        self._log_info(f"Processing mode: {mod_data['mode_uppercase']}", "sequence_processor.process_modulation_data()")
        
        """
        print("=" * 70)
        print(f"Processing mode: {mod_data['mode_uppercase']}", "sequence_processor.process_modulation_data()")
        print("=" * 70)
        """
        #set mode
        mode_status = self.musol.set_mode(mod_data["mode_uppercase"])
        if mode_status != 0:
            self._log_critical(
                f"ERROR sending set_mode cmd to PLC: {self.musol.get_error_description(mode_status)}",
                "sequence_processor.process_modulation_data()"
            )
            return False
        else:
            if mod_data["mode_uppercase"] == "OBSERVATION":
                current_cycle = 1                
                #If error or aborted return
                if(self.process_modulations(mod_data, current_cycle,current_theta=999)) >= 1:
                    print(f"is_aborted = {self.is_aborted()}") 
                    self._log_error(f"Sequence modulation process failed", "sequence_processor.process_modulation_data()")                   
                    #self.processing_finished.emit(False)
                    return False
            else:
                # CALIBRATION MODE
                current_theta = 0.0
                for i in range(mod_data["number_of_cycles"]):
                    current_cycle = i + 1      
                    print("=" * 80)
                    #print(f"Processing cycle {current_cycle}/{mod_data['number_of_cycles']}: Current Theta: {current_theta}")
                    self._log_info(f"***Processing cycle {current_cycle}/{mod_data['number_of_cycles']}: Theta: {current_theta}",
                            "sequence_processor.process_modulation_data()",
                       f"Current cycle: {current_cycle}/{mod_data['number_of_cycles']} - Theta: {current_theta} - Number of modulations: {len(mod_data['modulations'])}")
                    
                    
                    #If error or aborted return
                    if (self.process_modulations(mod_data, current_cycle, current_theta)) >= 1: 
                        print(f"is_aborted = {self.is_aborted()}")
                        self._log_error(f"Sequence modulation process failed", "sequence_processor.process_modulation_data()")
                        #self.processing_finished.emit(False)
                        return False
                        
                    current_theta += mod_data["offset_angle"]
               
         # Processing completed successfully
        self._log_debug("Sequence modulation process completed successfully", "sequence_processor.process_modulation_data()")                       
        return True

    def process_modulations(self, mod_data, current_cycle, current_theta=999)-> int:   
        
        """
        Process all modulations in a cycle of the sequence configuration.

        This function is responsible for sending the set_modulation command to the
        MUSOL PLC and the acquire_an_solar_image command to the SONG spectrograph
        for each modulation in the sequence configuration.

        If the process is aborted (by user click of CRL-C) , this
        function will return 2. 
        If any of the commands sent to the PLC or SONG fail, 
        this function will also return 1.

        :param current_cycle: The number of the cycle to process (1-indexed)
        :param mod_data: A list of dictionaries, where each dictionary contains
            the following keys:
            'modulations': 
              - alpha: float, the alpha angle in degrees
              - beta: float, the beta angle in degrees
              - SONG_int_time: float, the integration time in seconds
              - description: str, an optional description of the modulation
            'mode_uppercase': operation mode in uppercase 
            'modulations_count': Number of modulations defined in the sequence 
            'number_of_cycles': total number of cycles to reapeat the modulations
            'offset_angle': 
            'proj_number': 
            'proj_name':    
            
        :param current_theta: The value of the current theta angle in degrees.
            If this is None, the theta angle will not be sent to the PLC.
            
        :return: 0 if the sequence was processed successfully, 1 if any of the
        commands sent to the PLC or SONG failed and 2 if the process
            was aborted but the user (by click CRL-C )
        """
        
        if current_theta != 999:
            theta_deg_for_PLC = current_theta
            theta_deg_for_SONG = current_theta
            image_type = "CALIB"
        else:
            theta_deg_for_PLC = None
            theta_deg_for_SONG = current_theta
            image_type = "SUN"
                   
        for i in range(mod_data["modulations_count"]):
            step = i + 1
            
            if self.is_aborted():
                text_msg =  f"Aborted at setp {step} of cycle {current_cycle}/{mod_data['number_of_cycles']}"               
                self._log_info(text_msg,"sequence_processor.process_modulations()"," ")
                #El proceso se detiene aqui. self.processing_finished.emit(False) es llamado en el process_modulation_data
                return(2)  
            
            modulation = mod_data["modulations"][i]
            #print(f"*****Processing modulation {step}/{modulations_count}") 
            self._log_info(f"***Processing modulation {step}/{mod_data['modulations_count']}",
                           "sequence_processor.process_modulations()"," ")
      
            #process modulation
            alpha_deg = modulation.alpha
            beta_deg = modulation.beta            
            SONG_int_time = modulation.SONG_int_time            
            description = modulation.description
            if description is None or description == "":
                description = " "
                
            self._log_info("Sending set_modulation cmd to PLC ", 
                         "sequence_processor.process_modulations()",
                         f"alpha_value:{alpha_deg}, beta_value:{beta_deg}, retarder_plate_angle:{theta_deg_for_PLC}")   

            return_PLC_values = self.musol.set_modulation( alpha_deg,
                                                          beta_deg,
                                                          theta_deg_for_PLC,)  
            error_var = return_PLC_values[4]
            if error_var != 0: 
                text_msg =  f"PLC Set modulation failed! - Stop at step {step} of cycle {current_cycle}/{mod_data['number_of_cycles']}"
                
                self._log_critical(text_msg, "sequence_processor.process_modulations()", 
                            f"ERROR: {error_var} - {self.musol.get_error_description(error_var)}")
                return(1)
            else:
                
                self._log_info(f"PLC Set modulation successful",
                            "sequence_processor.process_modulations()",
                               f"alpha:{return_PLC_values[0]:.2f}, beta:{return_PLC_values[1]:.2f}, theta:{return_PLC_values[2]:.2f}, translation_unit:{return_PLC_values[3]:.2f}, status:{return_PLC_values[4]}, message:{self.musol.get_error_description(error_var)}") 
                
                #acquire image
                proj_nr, proj_name = mod_data["proj_number"], mod_data["proj_name"]
                self._log_info("Sending acquire_an_solar_image cmd to SONG ",
                        "sequence_processor.process_modulations()",
                       f"proj_nr:{proj_nr}, proj_name:{proj_name}, integration_time:{SONG_int_time}, imagetype:{image_type}, alpha_deg:{alpha_deg}, beta_deg:{beta_deg}, calibration_theta_deg:{theta_deg_for_SONG}")
              
                return_dic = self.song.send_acquire_cmd(proj_nr, proj_name, 
                                    SONG_int_time , image_type,
                                    alpha_deg, beta_deg, theta_deg_for_SONG, 
                                    description)   
                #print("acquisition status", return_dic)             
                status = return_dic["status"]
                message = return_dic["message"]
                if status == 0:
                    timestamp = return_dic["timestamp"]
                    filename = return_dic["filename"]              
                    
                    self._log_info("Acquisition successful",
                                    "sequence_processor.process_modulations()",
                                    f"status:{status}, message:{message}, timestamp:{timestamp}, filename:{filename}")
                else:
                    text_msg =  f"SONG Acquisition failed!-  Stop at step {step} of cycle {current_cycle}/{mod_data['number_of_cycles']}"  
                    self._log_error(text_msg, 
                                   "sequence_processor.process_modulations()",
                                    f"status:{status}, message:{return_dic['message']}")
                    #El proceso se detiene aqui. 
                    return(1)
            # end of for loop    
        return (0)
    def abort_processing(self):
        """
        Aborts the current processing cycle. This function is called when the user 
        clicks Cntrl-C. It closes the MUSOL and SONG connections and sets the 
        is_aborting flag to True for future use in the processing loop.

        Returns:
            None
        """
        self.is_aborting = True
        self.musol.close()
        self.song.disconnect()
        self._log_critical("Processing aborted by user", "sequence_processor.abort_processing()")
        return
    
    #TODO implementar mecanismo de semaforo parael abort
    def is_aborted(self):
            return self.is_aborting
        
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
