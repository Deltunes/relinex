import time
from serial import Serial
from pyubx2 import UBXReader
from pygnssutils.rinex_conv import RinexConverter
from pygnssutils.rinex_globals import OBS, NAV, EPOCHMIN
import subprocess
import sys
import os

COMPORT = None

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

# Reformat RINEX file so that GNSS-VOD can read it
def RNXformatEdit(rnxFilepath):
    # Reformat RINEX file to work with GNSSVODs
    rplcRNX = open(rnxFilepath, "r", encoding="utf-8")
    rplcData = rplcRNX.read()
    rplcRNX.close()
    
    rplcData = rplcData.replace("\n→","")
    rplcData = rplcData.replace("END OF FILE                                                 COMMENT\n","")
    
    rplcRNX = open(rnxFilepath, "w", encoding="utf-8")
    rplcRNX.write(rplcData)
    rplcRNX.close()

def renameFilesWithEpoch(rnxFilepath, firstEpoch, lastEpoch):
    firstEpoch = firstEpoch.strftime("%Y_%m_%d_%H_%M_%S")
    lastEpoch = lastEpoch.strftime("%Y_%m_%d_%H_%M_%S")
    rnxFileSplit = rnxFilepath.split("/")
    rnxFileSplit[-1] = f"{rnxFileSplit[-1][:12]}{firstEpoch}-{lastEpoch}.rnx"
    rnxFilepathNew = "/".join(rnxFileSplit)
    os.rename(f"{rnxFilepath}", f"{rnxFilepathNew}")

def getEpoch(conv, currEpoch):
    newEpoch = conv.get_current_epoch("O")

    # If epoch returns as default, just use last valid epoch
    if newEpoch == EPOCHMIN:
        return currEpoch
    
    # If epoch has changed since last check
    if currEpoch != newEpoch:
        return newEpoch

def UBXtoNAVOBS(fileno, waitTime=60, epochInterval=10, outputPath=".", comport=None):
    COMPORT = comport
    # Connect to Sparkfun chip through COMPORT
    try:
        stream = Serial(COMPORT, 9600, timeout=10)
        ubr = UBXReader(stream)
    except:
        print(f"Could not connect to Sparkfun chip at COMPORT: {COMPORT}")
        quit = True
        return quit
        
    print(f"RINEX FILE LENGTH: {waitTime} second(s)")
    print(f"EPOCH INTERVAL: {epochInterval} second(s)")

    try:
        conv = mkconv()

        print(f"RNX FILE: {fileno}")
        
        # Set default invalid epoch value
        currEpoch = EPOCHMIN
        firstEpoch = None
        lastEpoch = None

        # Set RINEX and AZIELEV filenames
        rnxFilepathOBS = f"{outputPath}/NAV_SUCCESS/success_obs_{fileno}.rnx"
        rnxFilepathNAV = f"{outputPath}/NAV_SUCCESS/success_nav_{fileno}.rnx"

        # Set up file stream for RINEX file output
        conv._outputs[OBS]["fnm"] = rnxFilepathOBS
        conv._outputs[OBS]["stm"] = open(rnxFilepathOBS, "w", encoding="utf-8")
        conv._outputs[NAV]["fnm"] = rnxFilepathNAV
        conv._outputs[NAV]["stm"] = open(rnxFilepathNAV, "w", encoding="utf-8")

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
            if msg == None:
                continue

            # RXM-RAWX is received every second
            if (msg.identity == "RXM-RAWX"):
                # only process epoch input every (epochInterval) seconds
                currSec = int(msg.rcvTow)
                if ((currSec % epochInterval) == 0):
                    input_prcOBS = conv._outputs[OBS]["hnd"].process_input_data(msg)
                    input_prcNAV = conv._outputs[NAV]["hnd"].process_input_data(msg)
                else:
                    input_prcOBS = 0
                    input_prcNAV = 0
            else:
                # process any other message identity
                input_prcOBS = conv._outputs[OBS]["hnd"].process_input_data(msg)
                input_prcNAV = conv._outputs[NAV]["hnd"].process_input_data(msg)

            conv._outputs[OBS]["prc"] += input_prcOBS
            conv._outputs[NAV]["prc"] += input_prcNAV
            
            if firstEpoch == None or firstEpoch == EPOCHMIN:
                firstEpoch = getEpoch(conv, currEpoch)
            
        # Output files
        conv.process_output_data(["O"])
        conv.process_output_data(["N"])
        conv._outputs[OBS]["stm"].close()
        conv._outputs[NAV]["stm"].close()

        if lastEpoch == None:
            lastEpoch = getEpoch(conv, currEpoch)
        
        RNXformatEdit(rnxFilepathOBS)

        renameFilesWithEpoch(rnxFilepathOBS, firstEpoch, lastEpoch)
        renameFilesWithEpoch(rnxFilepathNAV, firstEpoch, lastEpoch)

        print()
        quit = False
        return quit

    # IF PROGRAM IS EXITED BEFORE COMPLETION
    except KeyboardInterrupt:
        # Write incomplete RINEX data
        if (conv._outputs[OBS]["stm"].closed == False):
            conv.process_output_data(["O"])
            conv._outputs[OBS]["stm"].close()
            RNXformatEdit(rnxFilepathOBS)
        if (conv._outputs[NAV]["stm"].closed == False):
            conv.process_output_data(["N"])
            conv._outputs[NAV]["stm"].close()
            RNXformatEdit(rnxFilepathNAV)

        # Write incomplete AZIELEV data
        #renameFilesWithEpoch(rnxFilepathOBS, firstEpoch, lastEpoch)
        #renameFilesWithEpoch(rnxFilepathNAV, firstEpoch, lastEpoch)

        print()
        quit = True
        return quit

# Run UBXtoRNX, pass arguments
if __name__ == "__main__":
    i = 1
    while True:
        if len(sys.argv) > 2:
            UBXtoNAVOBS(i, int(sys.argv[1]),int(sys.argv[2]))
        elif len(sys.argv) > 1:
            UBXtoNAVOBS(i, int(sys.argv[1]))
        else:
            UBXtoNAVOBS(i)
        i += 1
