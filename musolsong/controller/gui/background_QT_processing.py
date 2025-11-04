
from PyQt6.QtCore import  QObject, pyqtSignal, QMutex, QMutexLocker
import time


class ProcessingWorker(QObject):
    """
    A worker class that runs in a separate thread.
    
    This class provides a way to run a long-running task in a separate thread
    and communicate with the main thread to update the UI.
    """
    
    # Signals to communicate with the main thread
    progress_updated = pyqtSignal(dict)   # Dict with data to update the UI
    status_updated = pyqtSignal(str)
    processing_finished = pyqtSignal(bool)  # True if completed, False if aborted or error
    
    def __init__(self, input_data=None):
        """
        Constructor for the ProcessingWorker class.
        Initializes the ProcessingWorker.
        """
        super().__init__()
        self._abort_flag = False
        self._mutex = QMutex()
        self.input_data = input_data  # Store data passed during initialization
    
    def abort(self):
        """Thread-safe method to set abort flag"""
        with QMutexLocker(self._mutex):
            self._abort_flag = True
    
    def is_aborted(self):
        """Thread-safe method to check abort flag"""
        with QMutexLocker(self._mutex):
            return self._abort_flag
    
    def reset(self):
        """Reset the abort flag for a new processing session"""
        with QMutexLocker(self._mutex):
            self._abort_flag = False
    
    

    def process_modulation_data(self):
        
        """
        Process the modulations data. It will set the mode of the PLC and process the modulations
        according to the mode. If the mode is OBSERVATION, the modulations will
        be processed once. If the mode is CALIBRATION, the modulations will be
        processed in a loop, with the theta angle increasing by the offset angle
        each cycle.

        :return: None
        """
        #print("*****************Processing started in thread********************")
        #print (self.input_data)
        #print ("**********************************")
        if self.input_data:
            self.status_updated.emit("Processing started...")

        
        #get data for processing
        modulations = self.input_data["modulations"]
        mode_uppercase = self.input_data["op_mode"]
        number_of_cycles = self.input_data["number_of_cycles"]
        offset_angle = self.input_data["offset_angle"]
        self.musol = self.input_data["musol_connector"]
        self.song = self.input_data["song_connector"]
        self.logger = self.input_data["logger"]
        current_theta = 0.0
        current_cycle = 0
        
        #set mode
        retval = self.musol.set_mode(mode_uppercase)
        if retval == 0:
            if mode_uppercase == "OBSERVATION":
                current_cycle = 1                
                #If error or aborted , notify main thread that processing is finished and return
                if(self.process_modulations(current_cycle,modulations,current_theta=999)) == 1:
                    #print(f"is_aborted = {self.is_aborted()}")                    
                    self.processing_finished.emit(False)
                    return
            else:
                # CALIBRATION MODE
                current_theta = 0.0
                for i in range(number_of_cycles):
                    current_cycle = i + 1
                    #print("=" * 70)
                    #print(f"Processing cycle {current_cycle}/{number_of_cycles}: Current Theta: {current_theta}")
                    self.logger.log_info(f"***Processing cycle {current_cycle}/{number_of_cycles}: Theta: {current_theta}",
                            "ProcessingWorker.process_modulation_data()",
                       f"Current cycle: {current_cycle}/{number_of_cycles} - Theta: {current_theta} - Number of modulations: {len(modulations)}")
                    
                    #self.set_modulation_cycle(current_cycle, number_of_cycles)
                    
                    #If error or aborted, notify main thread that processing is finished and return
                    if (self.process_modulations(current_cycle,modulations, current_theta))==1: 
                        #print(f"is_aborted = {self.is_aborted()}")
                        self.processing_finished.emit(False)
                        return
                        
                    current_theta += offset_angle                    
        else:
            # Error sending set_mode command
            self.logger.log_critical("ERROR sending set_mode cmd to PLC", "ProcessingWorker.process_modulation_data()",
                       f"ERROR value: {retval} - ERROR description: {self.musol.get_error_description(retval)}")

            text_msg =  f"PLC Set mode failed!- ERROR value: {retval} - {self.musol.get_error_description(retval)}"
            self.status_updated.emit(text_msg)
            #Notify main thread that processing is finished  due to error and return
            self.processing_finished.emit(False)
            return
               
         # Processing completed successfully
        self.status_updated.emit("Processing completed successfully!")
        self.processing_finished.emit(True)                        
        return  

    def process_modulations(self, cycle, modulations, current_theta=999)-> int:   
        
        """
        Process all modulations in a cycle of the sequence configuration.

        This function is responsible for sending the set_modulation command to the
        MUSOL PLC and the acquire_an_solar_image command to the SONG spectrograph
        for each modulation in the sequence configuration.

        If the process is aborted (by calling abort_modulation_sequence()), this
        function will return 1. If any of the commands sent to the PLC or SONG
        fail, this function will also return 1.

        :param cycle: The number of the cycle to process (1-indexed)
        :param modulations: A list of dictionaries, where each dictionary contains
            the following keys:
            - alpha: float, the alpha angle in degrees
            - beta: float, the beta angle in degrees
            - SONG_int_time: float, the integration time in seconds
            - description: str, an optional description of the modulation
        :param current_theta: The value of the current theta angle in degrees.
            If this is None, the theta angle will not be sent to the PLC.
        :return: 0 if the sequence was processed successfully, 1 if the process
            was aborted or if any of the commands sent to the PLC or SONG failed
        """
        
        modulations_count = self.input_data["modulations_count"]
        number_of_cycles = self.input_data["number_of_cycles"]
        
        if current_theta != 999:
            theta_deg_for_PLC = current_theta
            theta_deg_for_SONG = current_theta
            image_type = "CALIB"
        else:
            theta_deg_for_PLC = None
            theta_deg_for_SONG = current_theta
            image_type = "SUN"
                   
        for i in range(modulations_count):
            step = i + 1
            
            if self.is_aborted():
                text_msg =  f"Aborted at setp {step} of cycle {cycle}/{number_of_cycles}"               
                self.status_updated.emit(f"Aborted at setp: {step} of cycle {cycle}/{number_of_cycles}")               
                self.logger.log_info(text_msg,"ProcessingWorker.process_modulations()"," ")
                #El proceso se detiene aqui. self.processing_finished.emit(False) es llamado en el process_modulation_data
                return(1)  
            
            modulation = modulations[i]
            #print(f"*****Processing modulation {step}/{modulations_count}")       
            #process modulation
            alpha_deg = modulation.alpha
            beta_deg = modulation.beta            
            SONG_int_time = modulation.SONG_int_time            
            description = modulation.description
            if description is None or description == "":
                description = " "
                
            self.logger.log_info("Sending set_modulation cmd to PLC ", 
                         "ProcessingWorker.process_modulations()",
                         f"alpha_value:{alpha_deg}, beta_value:{beta_deg}, retarder_plate_angle:{theta_deg_for_PLC}")   
                   
            #print(f"alpha: {alpha_deg}, beta: {beta_deg}, SONG_int_time: {SONG_int_time}, description: {description}")  
            self.status_updated.emit(f"Sending modulation commnad to MUSOL PLC...")

            return_PLC_values = self.musol.set_modulation( alpha_deg,
                                                          beta_deg,
                                                          theta_deg_for_PLC,)
            #print(f"return_values from MUSOL PLC: {return_PLC_values}")
  
            error_var = return_PLC_values[4]
            if error_var != 0: 
                text_msg =  f"PLC Set modulation failed! - Stop at step {step} of cycle {cycle}/{number_of_cycles}"
                self.status_updated.emit(f"{text_msg} ERROR: {self.musol.get_error_description(error_var)}")
                
                self.logger.log_critical(text_msg, "ProcessingWorker.process_modulations()", 
                            f"ERROR: {error_var} - {self.musol.get_error_description(error_var)}")

                #El proceso se detiene aqui. self.processing_finished.emit(False) es llamado en el process_modulation_data
                return(1)
            else:
                
                self.logger.log_debug(f"Return from set_modulation cmd",
                            "ProcessingWorker.process_modulations()",
                               f"alpha:{return_PLC_values[0]:.2f}, beta:{return_PLC_values[1]:.2f}, theta:{return_PLC_values[2]:.2f}, translation_unit:{return_PLC_values[3]:.2f}, status:{return_PLC_values[4]}, message:{self.musol.get_error_description(error_var)}") 
                #update labels status widgets on the GUI
                # Note: NBthe set_modulation_cycle will always be updated, 
                # evethough it does not change for each modulation.
                # this is done to keep the GUI up to date at one place
                status_updated_dict = self.prepare_updated_data_for_GUI(modulations_count,number_of_cycles,
                                                cycle, step, 
                                                return_PLC_values[0], #PLC alpha
                                                return_PLC_values[1], #PLC beta
                                                return_PLC_values[2], #PLC theta
                                                return_PLC_values[3], #PLC_translation_unit
                                                SONG_int_time  #user defined SONG integration time
                                                ) 
                
                #print(f"status_updated_dict: {status_updated_dict}") 
                self.progress_updated.emit(status_updated_dict)
                
                #print(f"Sending commads to SONG...")
                self.status_updated.emit(f"Sending acquire_an_solar_image commad to SONG...")

                # Retrieve the current value of the alpha, beta input fields
                proj_nr, proj_name = self.input_data["proj_number"], self.input_data["proj_name"]

                self.logger.log_info("Sending acquire_an_solar_image cmd to SONG ",
                        "ProcessingWorker.process_modulations()",
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
                    #acquisition_id = return_dic["acquisition_id"]
                    filename = return_dic["filename"]
                    
                    self.logger.log_debug(f"Returned values from acquire_an_solar_image cmd (REQUESTED_IMAGE_TYPE:{image_type})",
                            "ProcessingWorker.process_modulations()",
                               f"status:{status}, message:{message}, timestamp:{timestamp}, filename:{filename}")       
                                   
                    status_message = "Acquisition successful: " + filename
                    self.status_updated.emit(status_message)         
                    
                    self.logger.log_info("Acquisition successful",
                                    "process_modulations()",
                                    f"status:{status}, message:{message}, timestamp:{timestamp}, filename:{filename}")
                else:
                    text_msg =  f"SONG Acquisition failed!- Stop at step: {step} of cycle {cycle}/{number_of_cycles}"
                    self.status_updated.emit(text_msg) 
  
                    self.logger.log_error(text_msg, 
                                   "ProcessingWorker.process_modulations()",
                                    f"status:{status}, message:{return_dic['message']}")
                    #El proceso se detiene aqui. self.processing_finished.emit(False) es llamado en el process_modulation_data
                    return(1)
            # end of for loop    
        return (0)
    
    def prepare_updated_data_for_GUI(self, modulations_count ,number_of_cycles,
                                        cycle, step, 
                                        alpha,  beta, theta,
                                        translation_unit,
                                        SONG_int_time ): 
   
        #print(f"prepare_updated_data_for_GUI: {modulations_count}, {number_of_cycles}, {cycle}, {step}, {alpha}, {beta}, {theta}, {translation_unit}, {SONG_int_time}")    
        """
        Prepare a dictionary containing the updated status data of the
        modulation sequence processing.

        Parameters
        ----------
        modulations_count : int
            The number of modulations in the sequence configuration
        number_of_cycles : int
            The number of cycles in the sequence configuration
        cycle : int
            The current cycle number
        step : int
            The current step number
        alpha : float
            The alpha angle in degrees
        beta : float
            The beta angle in degrees
        theta : float
            The theta angle in degrees
        translation_unit : str
            The current position  of the translation unit
        SONG_int_time : float
            The integration time in seconds

        Returns
        -------
        updated_status_data : dict
            A dictionary containing the updated status data of the modulation sequence processing.
        """
        total_steps = modulations_count
        total_modulations_to_be_processed = total_steps * number_of_cycles
        modulations_sofar_processsed = ((cycle -1) * total_steps) + step -1

        percentage_done = int(modulations_sofar_processsed / total_modulations_to_be_processed * 100)
         
        # Note:NB the currentmodulation cycle will always be updated on the GUi, therefore
        # this is done to keep the GUI up to date at one place 
        updated_status_data = {
            'percetage_done': percentage_done,
            'number_of_cycles': number_of_cycles,
            'current_cycle': cycle, 
            'current_step': step,   
            'alpha': alpha, 
            'beta': beta,   
            'theta': theta, 
            'translation_unit': translation_unit,   
            'SONG_int_time': SONG_int_time
        }
        
        return updated_status_data