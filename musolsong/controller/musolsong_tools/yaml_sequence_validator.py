import yaml
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ModeType(Enum):
    OBSERVATION = "observation"
    CALIBRATION = "calibration"


@dataclass
class Modulation:
    """Data class for modulation parameters"""
    alpha: float
    beta: float
    SONG_int_time: float
    description: Optional[str] = None


class YAMLSequenceValidator:
    """
    Validates YAML files according to the specified schema for observation/calibration modes.
    """
    
    def __init__(self, yaml_file_path: Optional[str] = None, yaml_content: Optional[str] = None):
        """
        Initialize the validator with either a file path or YAML content string.
        
        Args:
            yaml_file_path: Path to the YAML file to validate
            yaml_content: YAML content as a string
        """
        self.yaml_file_path = yaml_file_path
        self.yaml_content = yaml_content
        self.data: Optional[Dict] = None
        self.errors: List[str] = []
        self.is_valid_flag = False
        self.mode_type: Optional[ModeType] = None
        self.modulations: List[Modulation] = []
        self.retarding_plate_offsets: Optional[int] = None
        
        if yaml_file_path or yaml_content:
            self.validate()
    
    def _load_yaml(self) -> Dict:
        
        """
        Load YAML data from a file or a string.

        This method attempts to load YAML data either from a file specified by
        `yaml_file_path` or from a string provided in `yaml_content`. If neither 
        is available, a ValidationError is raised. If the YAML format is invalid,
        or if the file does not exist, corresponding ValidationErrors are raised.

        Returns:
            Dict: Parsed YAML data as a dictionary.

        Raises:
            ValidationError: If no YAML source is provided, if the YAML format is
            invalid, or if the file is not found.
        """

        try:
            if self.yaml_file_path:
                with open(self.yaml_file_path, 'r') as file:
                    return yaml.safe_load(file)
            elif self.yaml_content:
                return yaml.safe_load(self.yaml_content)
            else:
                raise ValidationError("No YAML file path or content provided")
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML format: {e}")
        except FileNotFoundError:
            raise ValidationError(f"File not found: {self.yaml_file_path}")
    
    def _validate_angle(self, angle: Union[int, float], angle_name: str) -> bool:
        """Validate angle is within -180 to 180 degrees"""
        if not isinstance(angle, (int, float)):
            self.errors.append(f"{angle_name} must be a number, got {type(angle).__name__}")
            return False
        
        if not (-180 <= angle <= 180):
            self.errors.append(f"{angle_name} must be between -180 and 180 degrees, got {angle}")
            return False
        
        return True
    
    def _validate_integration_time(self, int_time: Union[int, float]) -> bool:
        """Validate SONG_int_time is within 0.1 to 300 seconds"""
        if not isinstance(int_time, (int, float)):
            self.errors.append(f"SONG_int_time must be a number, got {type(int_time).__name__}")
            return False
        
        if not (0.1 <= int_time <= 300):
            self.errors.append(f"SONG_int_time must be between 0.1 and 300 seconds, got {int_time}")
            return False
        
        return True
    
    def _validate_retarding_plate_offsets(self, offsets: Union[int, float]) -> bool:
        """Validate retarding_plate_offsets is a factor of 360 in range 1-360"""
        if not isinstance(offsets, (int, float)):
            self.errors.append(f"retarding_plate_offsets must be a number, got {type(offsets).__name__}")
            return False
        
        if not (1 <= offsets <= 360):
            self.errors.append(f"retarding_plate_offsets must be between 1 and 360 degrees, got {offsets}")
            return False
        
        if 360 % offsets != 0:
            self.errors.append(f"retarding_plate_offsets must be a factor of 360, got {offsets}")
            return False
        
        return True
    
    def _validate_modulation(self, modulation: Dict, index: int) -> Optional[Modulation]:
        """Validate a single modulation entry"""
        if not isinstance(modulation, dict):
            self.errors.append(f"Modulation {index} must be a dictionary")
            return None
        
        # Check required fields
        required_fields = ['alpha', 'beta', 'SONG_int_time']
        for field in required_fields:
            if field not in modulation:
                self.errors.append(f"Modulation {index} missing required field: {field}")
                return None
        
        # Validate alpha
        alpha_valid = self._validate_angle(modulation['alpha'], f"Modulation {index} alpha")
        
        # Validate beta
        beta_valid = self._validate_angle(modulation['beta'], f"Modulation {index} beta")
        
        # Validate SONG_int_time
        int_time_valid = self._validate_integration_time(modulation['SONG_int_time'])
        
        # Validate description if present
        description = modulation.get('description')
        if description is not None and not isinstance(description, str):
            self.errors.append(f"Modulation {index} description must be a string")
            return None
        
        if alpha_valid and beta_valid and int_time_valid:
            return Modulation(
                alpha=float(modulation['alpha']),
                beta=float(modulation['beta']),
                SONG_int_time=float(modulation['SONG_int_time']),
                description=description
            )
        
        return None
    
    def _validate_mode(self, mode_name: str, mode_data: Dict) -> bool:
        """Validate a specific mode (observation or calibration)"""
        if not isinstance(mode_data, dict):
            self.errors.append(f"Mode '{mode_name}' must be a dictionary")
            return False
        
        # Check for modulations
        if 'modulations' not in mode_data:
            self.errors.append(f"Mode '{mode_name}' missing required field: modulations")
            return False
        
        modulations = mode_data['modulations']
        if not isinstance(modulations, list):
            self.errors.append(f"Mode '{mode_name}' modulations must be a list")
            return False
        
        if len(modulations) == 0:
            self.errors.append(f"Mode '{mode_name}' must have at least one modulation")
            return False
        
        # Validate each modulation
        valid_modulations = []
        for i, modulation in enumerate(modulations):
            validated_mod = self._validate_modulation(modulation, i)
            if validated_mod:
                valid_modulations.append(validated_mod)
        
        if not valid_modulations:
            return False
        
        self.modulations = valid_modulations
        
        # For calibration mode, validate retarding_plate_offsets
        if mode_name == 'calibration':
            if 'retarding_plate_offsets' not in mode_data:
                self.errors.append("Calibration mode missing required field: retarding_plate_offsets")
                return False
            
            if not self._validate_retarding_plate_offsets(mode_data['retarding_plate_offsets']):
                return False
            
            self.retarding_plate_offsets = int(mode_data['retarding_plate_offsets'])
        
        return True
    
    def validate(self) -> bool:
        """
        Validate the YAML file according to the schema.
        
        Returns:
            bool: True if valid, False otherwise
        """
        self.errors = []
        self.is_valid_flag = False
        self.mode_type = None
        self.modulations = []
        self.retarding_plate_offsets = None
        
        try:
            self.data = self._load_yaml()
        except ValidationError as e:
            self.errors.append(str(e))
            return False
        
        if not isinstance(self.data, dict):
            self.errors.append("YAML root must be a dictionary")
            return False
        
        
        modes = self.data['modes']
        if not isinstance(modes, dict):
            self.errors.append("'modes' must be a dictionary")
            return False
        
        # Check that exactly one mode is present
        valid_modes = ['observation', 'calibration']
        present_modes = [mode for mode in valid_modes if mode in modes]
        
        if len(present_modes) == 0:
            self.errors.append("At least one mode (observation or calibration) must be present")
            return False
        
        if len(present_modes) > 1:
            self.errors.append("Only one mode (observation or calibration) can be present")
            return False
        # Validate the present mode
        mode_name = present_modes[0]
        self.mode_type = ModeType(mode_name)
        
        if not self._validate_mode(mode_name, modes[mode_name]):
            return False
        
        self.is_valid_flag = True
        return True
    
    def is_valid(self) -> bool:
        """
        Get the validation status of the YAML file.
        
        Returns:
            bool: True if the YAML file is valid, False otherwise.
        """
        return self.errors.copy()
    
    def get_mode(self) -> Optional[str]:
        """Get the mode type (observation or calibration)"""
        return self.mode_type.value if self.mode_type else None
    
    def get_modulations(self) -> List[Modulation]:
        """
        Retrieve a copy of the list of modulations.

        Returns:
            List[Modulation]: A list of Modulation instances representing the
            modulations in the current mode.
        """
        return self.modulations.copy()
    
    def get_modulation(self, index: int) -> Optional[Modulation]:
        
        """
        Get a specific modulation by its index.

        Args:
            index (int): Index of the modulation to get (0-based).

        Returns:
            Optional[Modulation]: The Modulation object at the given index, or None if out of range.
        """
        if 0 <= index < len(self.modulations):
            return self.modulations[index]
        return None
    
    def get_modulation_count(self) -> int:
        """Get the number of modulations"""
        return len(self.modulations)
    
    def get_retarding_plate_offsets(self) -> Optional[float]:
        """Get retarding_plate_offsets value (only for calibration mode)"""
        return self.retarding_plate_offsets
    
    def get_number_of_cycles(self) -> Optional[int]:
        """
        Get the number of cycles for calibration mode.
        Calculated as 360 divided by retarding_plate_offsets.
        Returns None if not in calibration mode.
        """
        if self.retarding_plate_offsets is not None:
            return int(360 / self.retarding_plate_offsets)
        return None
    
    def get_modulation_parameters(self, index: int) -> Optional[Dict[str, Union[float, str]]]:
        """Get individual modulation parameters as a dictionary"""
        modulation = self.get_modulation(index)
        if modulation:
            return {
                'alpha': modulation.alpha,
                'beta': modulation.beta,
                'SONG_int_time': modulation.SONG_int_time,
                'description': modulation.description
            }
        return None
    def get_errors(self):
        return self.errors
    
    def load_from_file(self, yaml_file_path: str) -> bool:
        """Load and validate from a new file"""
        self.yaml_file_path = yaml_file_path
        self.yaml_content = None
        return self.validate()
    
    def load_from_string(self, yaml_content: str) -> bool:
        """Load and validate from a YAML string"""
        self.yaml_content = yaml_content
        self.yaml_file_path = None
        return self.validate()


# Example usage and testing
if __name__ == "__main__":
    # Example YAML content for testing
    observation_yaml = """
modes:
  observation:
    modulations:
      - alpha: 45.0
        beta: 90.0
        SONG_int_time: 1.5
        description: "First observation step"
      - alpha: -30.0
        beta: 60.0
        SONG_int_time: 2.0
        description: "Second observation step"
"""

    calibration_yaml = """
modes:
  calibration:
    retarding_plate_offsets: 45.0
    modulations:
      - alpha: 0.0
        beta: 0.0
        SONG_int_time: 1.0
        description: "Calibration step"
"""

    # Test observation mode
    print("Testing observation mode:")
    validator = YAMLSequenceValidator(yaml_content=observation_yaml)
    print(f"Valid: {validator.is_valid()}")
    print(f"Mode: {validator.get_mode()}")
    print(f"Modulations count: {validator.get_modulation_count()}")
    
    for i in range(validator.get_modulation_count()):
        params = validator.get_modulation_parameters(i)
        print(f"Modulation {i}: {params}")
    
    print("\nTesting calibration mode:")
    validator = YAMLSequenceValidator(yaml_content=calibration_yaml)
    print(f"Valid: {validator.is_valid()}")
    print(f"Mode: {validator.get_mode()}")
    print(f"Retarding plate offsets: {validator.get_retarding_plate_offsets()}")
    print(f"Number of cycles: {validator.get_number_of_cycles()}")
    
    # Test invalid case
    print("\nTesting invalid YAML:")
    invalid_yaml = """
modes:
  observation:
    modulations:
      - alpha: 200.0  # Invalid angle
        beta: 90.0
        SONG_int_time: 1.5
"""
    
    validator = YAMLSequenceValidator(yaml_content=invalid_yaml)
    print(f"Valid: {validator.is_valid()}")
    print(f"Errors: {validator.get_errors()}")
