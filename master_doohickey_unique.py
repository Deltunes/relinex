import sys
import os
import subprocess
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
sys.path.insert(1, 'AWS_UPLOAD')
from UBXtoRNXconv import UBXtoRNX, mkconv
from aws_upload import aws_upload

# Variables
i = 1
quit = False
conv = mkconv()
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

        rnxFilepath, azielevFilepath, quit = UBXtoRNX(fileno=i, waitTime=waitTime, epochInterval=epochInterval)
        i += 1

        subprocess.run(["vcgencmd","get_throttled"])
        subprocess.run(["vcgencmd","measure_temp"])
        subprocess.run(["free","-h"])

        # If program is quit during UBXtoRNX, end while loop
        if quit:
            print("Quitting...")
            break

        print("Uploading RINEX and plots to AWS storage")
        try:
            aws_fileset = aws_upload(1, aws_fileset)
        except:
            print("Upload failed!")
        
except KeyboardInterrupt:
    print("Keyboard Interrupt! Quitting...")

