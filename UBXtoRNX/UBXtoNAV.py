from pyubx2 import UBXReader, UBXMessage, SET_LAYER_RAM, SET_LAYER_BBR
from pygnssutils.rinex_conv import RinexConverter
from pygnssutils.rinex_globals import OBS, NAV, EPOCHMIN, GPS, GAL, QZS
from serial import Serial
import time
import os

COMPORT = None

def mkconv():
    return RinexConverter(
        app=None,
        rinex_version="3.05",
        rinex_types=["O","N"],
        gnssfilter=[GPS, GAL, QZS],
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

def formatNAV(navFilepath):
    # Reformat RINEX file to work with GNSSVODs
    navFile = open(navFilepath, "r", encoding="utf-8")
    navLines = navFile.readlines()
    navFile.close()
    
    navFile = open(navFilepath, "w", encoding="utf-8")
    for line in navLines:
        if "LEAPSECONDS" not in line:
            navFile.write(line)
    navFile.close()

def renameFilesWithEpoch(navFilepath, firstEpoch, lastEpoch):
    firstEpoch = firstEpoch.strftime("%Y_%m_%d_%H_%M_%S")
    lastEpoch = lastEpoch.strftime("%Y_%m_%d_%H_%M_%S")

    navFileSplit = navFilepath.split("/")
    navFilename = navFileSplit[-1]
    navFilePrefix = "_".join(navFilename.split("_")[:-1])
    navFileSplit[-1] = f"{navFilePrefix}_{firstEpoch}-{lastEpoch}.rnx"
    navFilepathNew = "/".join(navFileSplit)

    os.rename(f"{navFilepath}", f"{navFilepathNew}")

def getEpoch(conv, currEpoch):
    newEpoch = conv.get_current_epoch("N")

    # If epoch returns as default, just use last valid epoch
    if newEpoch == EPOCHMIN:
        return currEpoch
    
    return newEpoch

def UBXtoNAV(fileno, siteno, waitTime=60, epochInterval=10, outputPath=".", comport=None):
    COMPORT = comport
    # Connect to Sparkfun chip through COMPORT
    try:
        stream = Serial(COMPORT, 115200, timeout=10)
        ubr = UBXReader(stream)
        
        cfg_data = [
            ("CFG_MSGOUT_UBX_RXM_RAWX_USB", 1),
            ("CFG_MSGOUT_UBX_RXM_SFRBX_USB", 1),
            ("CFG_MSGOUT_UBX_NAV_SAT_USB", 1),
        ]
        msg = UBXMessage.config_set(SET_LAYER_RAM | SET_LAYER_BBR, 0, cfg_data)
        stream.write(msg.serialize())
    except:
        print(f"Could not connect to Sparkfun chip at COMPORT: {COMPORT}")
        quit = True
        return quit
        
    print(f"NAVIGATION FILE LENGTH: {waitTime} second(s)")
    print(f"EPOCH INTERVAL: {epochInterval} second(s)")

    try:
        conv = mkconv()

        print(f"RNX FILE: {fileno}")
        
        # Set default invalid epoch value
        currEpoch = EPOCHMIN
        firstEpoch = None
        lastEpoch = None

        # Set RINEX and AZIELEV filenames
        navFilepath = f"{outputPath}/NAV_SUCCESS/site{siteno}/nav/nav_site{siteno}_{fileno}.rnx"

        # Set up file stream for RINEX file output
        conv._outputs[NAV]["fnm"] = navFilepath
        conv._outputs[NAV]["stm"] = open(navFilepath, "w", encoding="utf-8")

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
               print("No UBXMessage received.")
               continue

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

            if firstEpoch == None or firstEpoch == EPOCHMIN:
                firstEpoch = getEpoch(conv, currEpoch)

        # Output files
        conv.process_output_data(["N"])
        conv._outputs[NAV]["stm"].close()

        while lastEpoch == None or lastEpoch == EPOCHMIN:
            lastEpoch = getEpoch(conv, currEpoch)

        formatNAV(navFilepath)
        renameFilesWithEpoch(navFilepath, firstEpoch, lastEpoch)

        print()
        quit = False
        return quit

    # IF PROGRAM IS EXITED BEFORE COMPLETION
    except KeyboardInterrupt:
        # Write incomplete RINEX data
        if (conv._outputs[NAV]["stm"].closed == False):
            conv.process_output_data(["N"])
            conv._outputs[NAV]["stm"].close()
            formatNAV(navFilepath)

        if lastEpoch == None:
            lastEpoch = getEpoch(conv, currEpoch)
        renameFilesWithEpoch(navFilepath, firstEpoch, lastEpoch)

        print()
        quit = True
        return quit

"""if __name__ == "__main__":
    i = 1
    while True:
        if len(sys.argv) > 2:
            UBXtoNAV(i, int(sys.argv[1]),int(sys.argv[2]))
        elif len(sys.argv) > 1:
            UBXtoNAV(i, int(sys.argv[1]))
        else:
            UBXtoNAV(i)
        i += 1"""
