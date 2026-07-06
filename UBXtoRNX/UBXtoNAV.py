import time
from serial import Serial
from pyubx2 import UBXReader
from pygnssutils.rinex_conv import RinexConverter
from pygnssutils.rinex_globals import NAV, EPOCHMIN
import sys

#   Lists serial ports to determine COMPORT
#   Uncomment if needed
#import serial.tools.list_ports
#ports = serial.tools.list_ports.comports()
#for port in ports:
#    print(f"{port.device} - {port.description}")

COMPORT = '/dev/ttyACM0'

def mkconv():
    return RinexConverter(
        app=None,
        rinex_version="3.05",
        rinex_types=["O","N"],
        gnssfilter=[""],
        obsfilter=[""],
        timecorr=True,
        ionocorr=True,
        eopcorr=True,
        datasource=["U"],
        starttime="",
        minobs=0,
        marker=["UNKN", "", "NONE"],
        antenna=["", ""],
        antennahed=[0.0, 0.0, 0.0],
        receiver=["", "", ""],
        observer="",
        comments=[],
    )

def UBXtoNAV(fileno, waitTime=60, epochInterval=10):
    # Connect to Sparkfun chip through COMPORT
    stream = Serial(COMPORT, 9600, timeout=10)
    ubr = UBXReader(stream)
        
    print(f"NAVIGATION FILE LENGTH: {waitTime} second(s)")
    print(f"EPOCH INTERVAL: {epochInterval} second(s)")

    try:
        conv = mkconv()

        print(f"NAV FILE: {fileno}")
        
        # Set default invalid epoch value
        currEpoch = EPOCHMIN

        # Set RINEX and AZIELEV filenames
        rnxFilepath = f"NAV_SUCCESS/rinex/success_nav_{fileno}.rnx"

        # Set up file stream for RINEX file output
        conv._outputs[NAV]["fnm"] = rnxFilepath
        conv._outputs[NAV]["stm"] = open(rnxFilepath, "w", encoding="utf-8")

        # Countdown setup
        currIntTime = waitTime
        end_time = time.time() + waitTime

        while time.time() < end_time:

            # Countdown to end of epoch interval
            countdown = int(end_time - time.time())
            if countdown < int(currIntTime):
                print(f"\r\t\t{countdown}\t\t", end="")
                currIntTime = countdown
            
            # Read UBXMessage from Sparkfun chip
            _, msg = ubr.read()
            
            # If no UBXMessage was received, just continue to next loop
            #if msg == None:
            #   continue

            # RXM-RAWX is received every second
            if (msg.identity == "RXM-RAWX"):
                # only process epoch input every (epochInterval) seconds
                currSec = int(msg.rcvTow)
                if ((currSec % epochInterval) == 0):
                    input_prc = conv._outputs[NAV]["hnd"].process_input_data(msg)
                else:
                    input_prc = 0
            else:
                # process any other message identity
                input_prc = conv._outputs[NAV]["hnd"].process_input_data(msg)
            
            conv._outputs[NAV]["prc"] += input_prc

        # Output files
        conv.process_output_data(["O"])
        conv._outputs[NAV]["stm"].close()

        return rnxFilepath

    # IF PROGRAM IS EXITED BEFORE COMPLETION
    except KeyboardInterrupt:
        # Write incomplete RINEX data
        if (conv._outputs[NAV]["stm"].closed == False):
            conv.process_output_data(["N"])
            conv._outputs[NAV]["stm"].close()

        return rnxFilepath

i = 1
while True:
    UBXtoNAV(i)
    i += 1
