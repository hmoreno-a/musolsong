#!/usr/bin/env python3
import pyads
import platform
import socket

# create some constants for connection
#TARGET_IP = "161.72.209.222"  #PLC IP ojo este numero podria cambiar, el nombre musol-plc es fijo
TARGET_AMS_ID = "5.110.208.2.1.1"  # PLC AMS NetID
TARGET_NAME = "musol-plc"
TARGET_USERNAME = "Administrator"
TARGET_PASSWORD = "1"
ROUTE_NAME = "musolsong"

# Check if the script is running on Linux
if platform.system() == "Linux":
    print("\n*************************************************")
    print("\tRunning on Linux")
    # Get Target_IP
    target_IP = socket.gethostbyname(TARGET_NAME)
    print("\tTARGET_NAME:", TARGET_NAME)
    print("\tTARGET_IP:", target_IP)
    # Get the hostname and IP address
    hostname = socket.gethostname()
    print("\tHostname:", hostname)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Google's public DNS server
    client_IP = s.getsockname()[0]
    print("\tLocal IP address:", client_IP)
    client_NETID = ".".join(client_IP.split(".")[0:4] + ["1.1"])    
    print("\tLocal NETID:", client_NETID)
    print("*************************************************\n")
    s.close()   
else:
    print("Running on Windows - This script is only for Linux")
    exit

# Open the ADS port
pyads.open_port()
"""
Add a new route to the target PLC

The route is added automatically to client on Linux, 
but on Windows use the TwinCAT router to add the route.
"""
print("***Add new route to PLC - add_route_to_plc......\n")
print(f"*****Route Name: {ROUTE_NAME}")
print(f"*****Client NETID: {client_NETID}")
print(f"*****Client IP: {client_IP}")    
print(f"*****Target IP: {target_IP}")    
print(f"*****Target AMS NetID: {TARGET_AMS_ID}")    
print(f"*****Target Username: {TARGET_USERNAME}\n")   
retval =pyads.add_route_to_plc(
    client_NETID, client_IP, target_IP, TARGET_USERNAME, TARGET_PASSWORD,
    route_name=ROUTE_NAME
)
print(f"***Route added to PLC - return value from add_route_to_plc: {retval}\n")
print("*************************************************\n")
# Close the ADS port
pyads.close_port()

"""
Try to connect to the PLC using TwinCAT3.

The connection is established using the TARGET_AMS_ID, TARGET_IP, 
and the TwinCAT3 port number (851).

Raises:
    Exception: If the connection to the PLC cannot be established.
"""
try:
    print ("***Connect to plc......\n")
    print (f"***TwinCAT3 AMS ID: {TARGET_AMS_ID}")
    print (f"***TwinCAT3 IP: {target_IP}")    
    print (f"***TwinCAT3 port number: {pyads.PORT_TC3PLC1}\n")
    #pyads.PORT_TC3PLC1 is por 851 
    plc = pyads.Connection(
        TARGET_AMS_ID, pyads.PORT_TC3PLC1, target_IP
    )
    print(f"***Successful connected to plc\n") 
    print("*************************************************\n")
   
except Exception as e:
    print(f"Failed to connect: {e}")
    
try:
    plc.open()
except Exception as e:
    print(f"Failed to open connection: {e}")
    exit()
    
print(f"***Successful open connection to plc\n")


print("*************************************************\n")
print ("***Check PLC-Read State -  plc.read_state" )

try:
    """
    Read the state of the PLC.

    The state of the PLC is read from the PLC using the read_state method.
    The state is returned as a retval object.

    Raises:
        Exception: If the read_state method fails.
    """
    retval = plc.read_state()
    print(f" return value from read_state: {retval} ")

except Exception as e:
    """
    Failed to read the state of the PLC.

    The exception is raised if the read_state method fails.
    """
    print(f"Failed to read_state: {e}")
    

print("*************************************************\n")
print ("***Check PLC-Read .bEmergencyStop - plc.read_by_name" )
# read a well known bool value by name 
try:
    i = plc.read_by_name(".bEmergencyStop", pyads.PLCTYPE_BOOL)
    print (f"return value from read_by_name .bEmergencyStop:  {i}")
except Exception as e:
    print(f"Failed to read_state: .bEmergencyStop: {e}")

print("*************************************************\n")    
        
"""
Try to read the CPU load from the PLC.

The CPU load is read from the PLC using the read_by_name method,
with the name "_SystemInfo.CpuLoad" and the data type pyads.PLCTYPE_REAL.

Raises:
    Exception: If the connection to the PLC cannot be established or if the
    read_by_name method fails.
"""
print ("***Check PLC-Read _SystemInfo.CpuLoad - plc.read_by_name" )
try:
    # Read the CPU load from the PLC
    cpu_load = plc.read_by_name("_SystemInfo.CpuLoad", pyads.PLCTYPE_REAL)
    print(f"CPU load: {cpu_load:.2f}%")
except Exception as e:
    """
    Failed to read the CPU load from the PLC.

    The exception is raised if the read_by_name method fails.
    """
    print(f"***Failed to read_by_name _SystemInfo.CpuLoad: {e}")
print("*************************************************\n") 

# close connection
try:
    plc.close()
except pyads.ADSError as e:
    print(f"ADS/AMS connection failed: {e}")
