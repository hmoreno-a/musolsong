import logging
import json
import time
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import os
import sys


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    PERFORMANCE = "performance"
    ERROR = "error"
    HEALTH_CHECK = "health_check"
    CUSTOM = "custom"


@dataclass
class LogEvent:
    timestamp: datetime
    level: LogLevel
    event_type: EventType
    message: str
    component: str
    metadata: Dict[str, Any]
    error_details: Optional[Dict[str, Any]] = None



class SystemLogger:
    """
    Centralized logging system for system events and errors.
    Handles structured logging with metadata and error tracking.
    """
    
    def __init__(self, 
                 log_level: LogLevel = LogLevel.INFO,
                 max_events: int = 10000,
                 log_file: Optional[str] = None,
                 enable_console: bool = True):
        
        """
        Initialize the SystemLogger.
        
        Args:
            log_level (LogLevel): Level of detail to log. Defaults to LogLevel.INFO.
            max_events (int): Maximum number of events to store. Defaults to 10000.
            log_file (str, optional): File to log to. Defaults to None.
            enable_console (bool, optional): Whether to log to the console. Defaults to True.
        """
        self.log_level = log_level
        self.max_events = max_events
        
        # Event storage
        self.events: deque = deque(maxlen=max_events)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.component_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Threading
        self._lock = threading.Lock()
        
        # Setup logging
        self._setup_logger(log_file, enable_console)
    
    def _setup_logger(self, log_file: Optional[str], enable_console: bool):
        """Setup the underlying Python logger"""
        self.logger = logging.getLogger("MSLogger")
        self.logger.setLevel(getattr(logging, self.log_level.value))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_format = logging.Formatter(
            #    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                '%(asctime)s - %(levelname)s - %(message)s'   # do not print name of logger
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
        else:
            print ("\n\t******There will be no console output: NONE SPECIFIED*****\n")
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        else:
            print ("\n\t******There will be no logs file: NONE SPECIFIED*****\n")
    
    def log_event(self, 
                  level: LogLevel, 
                  message: str, 
                  component: str = "system",
                  event_type: EventType = EventType.CUSTOM,
                  metadata: Optional[Dict[str, Any]] = None,
                  error_details: Optional[Dict[str, Any]] = None):
        """Log a system event with metadata"""
        
        if metadata is None:
            metadata = {}
        
        event = LogEvent(
            timestamp=datetime.now(),
            level=level,
            event_type=event_type,
            message=message,
            component=component,
            metadata=metadata,
            error_details=error_details
        )
        
        """
        Append a new event to the event deque and update component statistics.
        
        Locks the event deque and component statistics to ensure thread safety.
        """
        with self._lock:
            self.events.append(event)
            
            # Update component stats
            # If this is the first event for the component, initialize its stats
            if component not in self.component_stats:
                self.component_stats[component] = {
                    'event_count': 0,
                    'error_count': 0,
                    'last_activity': None
                }
            
            # Increment event count and last activity
            self.component_stats[component]['event_count'] += 1
            self.component_stats[component]['last_activity'] = datetime.now()
            
            # If this is an error or critical event, increment error count
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self.error_counts[component] += 1
                self.component_stats[component]['error_count'] += 1
        
        # Log to underlying logger
        log_data = {
            'comp': component,
            #'event_type': event_type.value,
            'metadata': metadata
        }
        
        if error_details:
            log_data['error_details'] = error_details
        
        # Use getattr to dynamically call the log method based on the level value
        # getattr(self.logger, level.value.lower()) will return the method of the logger
        # that corresponds to the level value. For example, if the level value is 'INFO',
        # getattr(self.logger, level.value.lower()) will return the self.logger.info method.
        # The method is then called with the message and log_data as arguments.
        getattr(self.logger, level.value.lower())(
            f"{message} | {json.dumps(log_data)}"
        )
    
    def log_error(self, 
                  message: str, 
                  component: str = "system",
                  exception: Optional[Exception] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """Log an error with exception details"""
        
        error_details = {}
        if exception:
            error_details = {
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        self.log_event(
            level=LogLevel.ERROR,
            message=message,
            component=component,
            event_type=EventType.ERROR,
            metadata=metadata or {},
            error_details=error_details
        )
    
    def log_performance(self, 
                       component: str,
                       operation: str,
                       duration_ms: float,
                       metadata: Optional[Dict[str, Any]] = None):
        """Log performance metrics
        
        This function logs a performance metric event. It takes the component name, the operation name, the duration in milliseconds, and optional metadata.
        
        The performance metric event is logged with the INFO log level, the PERFORMANCE event type, and the component name.
        
        The event message is a formatted string containing the operation name and duration in milliseconds.
        
        The event metadata is a dictionary containing the operation name, duration in milliseconds, and optional user-provided metadata.
        """
        
        perf_metadata = {
            'operation': operation,
            'duration_ms': duration_ms,
            **(metadata or {})
        }
        
        self.log_event(
            level=LogLevel.INFO,
            message=f"Performance: {operation} completed in {duration_ms:.2f}ms",
            component=component,
            event_type=EventType.PERFORMANCE,
            metadata=perf_metadata
        )
    
    def log_info(self, message: str, component: str = "system", 
                 metadata: Optional[Dict[str, Any]] = None):
        """Log an info message"""
        
        self.log_event(LogLevel.INFO, message, component, EventType.CUSTOM, metadata)

    def log_warning(self, message: str, component: str = "system", 
                    metadata: Optional[Dict[str, Any]] = None):
        """Log a warning message"""
     
        self.log_event(LogLevel.WARNING, message, component, EventType.CUSTOM, metadata)

    def log_debug(self, message: str, component: str = "system", 
                  metadata: Optional[Dict[str, Any]] = None):
        """Log a debug message"""
        
        self.log_event(LogLevel.DEBUG, message, component, EventType.CUSTOM, metadata)
   
    def log_critical(self, message: str, component: str = "system", 
                     metadata: Optional[Dict[str, Any]] = None):
        """Log a critical message"""
       
        self.log_event(LogLevel.CRITICAL, message, component, EventType.CUSTOM, metadata)

    def get_events(self, 
                   component: Optional[str] = None,
                   level: Optional[LogLevel] = None,
                   event_type: Optional[EventType] = None,
                   since: Optional[datetime] = None,
                   limit: Optional[int] = None) -> List[LogEvent]:
        """
        Retrieve filtered events

        Filter events by component, log level, event type, and timestamp (since).
        Optionally limit the number of events returned.
        """
        
        with self._lock:
            # Get a copy of the events list
            events = list(self.events)
        
        # Apply filters
        if component:
            # Filter by component
            events = [e for e in events if e.component == component]
        
        if level:
            # Filter by log level
            events = [e for e in events if e.level == level]
        
        if event_type:
            # Filter by event type
            events = [e for e in events if e.event_type == event_type]
        
        if since:
            # Filter by timestamp (newest first)
            events = [e for e in events if e.timestamp > since]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            # Limit the number of events returned
            events = events[:limit]
        
        return events
    
    def get_component_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all components"""
        with self._lock:
            return dict(self.component_stats)
    
    def get_error_counts(self) -> Dict[str, int]:
        """Get error counts by component"""
        with self._lock:
            return dict(self.error_counts)
    
    def get_recent_errors(self, minutes: int = 60, limit: int = 50) -> List[LogEvent]:
        """Get recent errors within specified time window"""
        since = datetime.now() - timedelta(minutes=minutes)
        return self.get_events(level=LogLevel.ERROR, since=since, limit=limit)
    
    def clear_events(self):
        """Clear all stored events"""
        with self._lock:
            self.events.clear()
            self.error_counts.clear()
            self.component_stats.clear()
    
    def export_events(self, filename: str, format: str = 'json'):
        """
        Export events to file

        The events are exported in the format specified by the format parameter.
        The events are dumped to the file specified by the filename parameter.
        """
        with self._lock:
            events_data = [asdict(event) for event in self.events]
        
        # Convert datetime objects to strings
        # We need to do this because JSON doesn't support datetime objects
        for event in events_data:
            event['timestamp'] = event['timestamp'].isoformat()
        
        if format.lower() == 'json':
            # Dump the events to the file in JSON format
            with open(filename, 'w') as f:
                json.dump(events_data, f, indent=2)
        
        # Log the event
        self.log_event(
            LogLevel.INFO,
            f"Events exported to {filename}",
            metadata={'event_count': len(events_data), 'format': format}
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of logging statistics
        
        This method returns a dictionary containing the total number of events,
        the distribution of events by log level, the distribution of events by
        component, the count of errors per component, and statistics for each
        component.
        """
        with self._lock:
            total_events = len(self.events)
            # Count the number of events per log level
            level_counts = defaultdict(int)
            for event in self.events:
                level_counts[event.level.value] += 1
            
            # Count the number of events per component
            component_counts = defaultdict(int)
            for event in self.events:
                component_counts[event.component] += 1
            
            # Get the error counts per component
            error_counts = dict(self.error_counts)
            
            # Get the statistics for each component
            component_stats = dict(self.component_stats)
            
            return {
                'total_events': total_events,
                'level_distribution': dict(level_counts),
                'component_distribution': dict(component_counts),
                'error_counts': error_counts,
                'component_stats': component_stats
            }




def example_standalone_usage():
    """Example showing how to use the classes independently"""
    
    # Use logger independently
    logger = SystemLogger(log_level=LogLevel.DEBUG)
    logger.log_info("Standalone logger test", "test")
    
    return logger


if __name__ == "__main__":
    
    print("\n=== Standalone Usage ===")
    logger2 = example_standalone_usage()
    
    # Keep running for a bit to see monitoring in action
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    
