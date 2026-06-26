import sys
import os
import subprocess
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
sys.path.insert(1, 'AWS_UPLOAD')
from constUBXtoRNXconv import UBXtoRNX, mkconv
from const_gnssvod_oneSite import RNXtoIMG
from aws_upload import aws_upload
from collections import deque

# Variables
i = 1
quit = False
conv = mkconv()
rnxDeleteQ = deque()
azielevDeleteQ = deque()
aws_fileset = set()

# Make any missing directories
os.makedirs("RNX_SUCCESS/rinex", exist_ok=True)
os.makedirs("RNX_SUCCESS/azielev", exist_ok=True)
os.makedirs("IMAGE_SUCCESS/scatter", exist_ok=True)
os.makedirs("IMAGE_SUCCESS/hemi", exist_ok=True)

# Take command line args as input for waitTime and epochInterval
if len(sys.argv) > 2:
    waitTime = int(sys.argv[1])
    epochInterval = int(sys.argv[2])
elif len(sys.argv) > 1:
    waitTime = int(sys.argv[1])
else:
    waitTime = 60
    epochInterval = 10

try:
    while not quit:
        # Process GNSS data and convert to RINEX format + extra Azimuth/Elevation data
        rnxFilepath = ""
        azielevFilepath = ""

        rnxFilepath, azielevFilepath, _, quit = UBXtoRNX(fileno=i, waitTime=waitTime, epochInterval=epochInterval)
        rnxDeleteQ.append(rnxFilepath)
        azielevDeleteQ.append(azielevFilepath)
        i += 1

        subprocess.run(["vcgencmd","get_throttled"])
        subprocess.run(["vcgencmd","measure_temp"])
        subprocess.run(["free","-h"])

        # If program is quit during UBXtoRNX, end while loop
        if quit:
            print("Quitting...")
            break

        # Plot RINEX file
        RNXtoIMG(rnxFilepath)
        
        # AFTER FIRST TURN ONLY
        # Delete unnecessary files to save space
        if i > 2:
            rnxDelete = rnxDeleteQ.popleft()
            azielevDelete = azielevDeleteQ.popleft()
            rnxNetCDF = f"GNSSVOD/nc/{rnxDelete.split("/")[-1].split(".")[0]}.nc"
            
            if os.path.exists(rnxDelete):
                print(f"Deleting RINEX file at: {rnxDelete}")
                os.remove(rnxDelete)
            else:
                print(f"Warning: RINEX file to DELETE could not be found at {rnxDelete}")

            if os.path.exists(azielevDelete):
                print(f"Deleting AZIELEV file at: {azielevDelete}")
                os.remove(azielevDelete)
            else:
                print(f"Warning: AZIELEV file to DELETE could not be found at {azielevDelete}")

            if os.path.exists(rnxNetCDF):
                print(f"Deleting NETCDF file at: {rnxNetCDF}")
                os.remove(rnxNetCDF)
            else:
                print(f"Warning: NETCDF file to DELETE could not be found at {rnxNetCDF}")

        #if i % 6 == 0:
        print("Uploading RINEX and plots to AWS storage")
        try:
            aws_fileset = aws_upload(aws_fileset)
        except:
            print("Upload failed!")
        
except KeyboardInterrupt:
    print("Keyboard Interrupt! Quitting...")

