#!/usr/bin/env python3
import pyads
import socket
# create some constants for connection
TARGET_AMS_ID = "5.110.208.2.1.1"  # PLC AMS NetID
TARGET_NAME = "musol-plc"
TARGET_USERNAME = "Administrator"
TARGET_PASSWORD = "1"
ROUTE_NAME = "musolsong"

"""
Try to connect to the PLC using TwinCAT3.

The connection is established using the TARGET_AMS_ID, TARGET_IP, 
and the TwinCAT3 port number (851).

Raises:
    Exception: If the connection to the PLC cannot be established.
"""
try:
    # Get Target_IP
    target_IP = socket.gethostbyname(TARGET_NAME)

    print ("***Connect to plc......\n")
    print (f"***TwinCAT3 AMS ID: {TARGET_AMS_ID}")
    print("\tTARGET_NAME:", TARGET_NAME)
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
    print("Opening connection")
    plc.open()
    print("Connection opened")
    
    #current_timeout = plc.get_timeout()
    #print(f"Timeout actual: {current_timeout} ms")
    print("Setting timeout to 15 seconds")
    plc.timeout = 15_000  # 15 seconds
    current_timeout = plc.set_timeout(plc.timeout)
    #print(f"Timeout actual: {current_timeout} ms")
    plc.close()
    print("Connection closed")  

except Exception as e:
    print(f"Error: {e}")

