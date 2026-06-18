import sys
import os
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
from constUBXtoRNXconv import UBXtoRNX, mkconv
from const_gnssvod_oneSite import RNXtoIMG
from collections import deque

# Variables
i = 1
quit = False
conv = mkconv()
rnxDeleteQ = deque()
azielevDeleteQ = deque()

# Take command line args as input for waitTime and epochInterval
if len(sys.argv) > 2:
	waitTime = int(sys.argv[1])
	epochInterval = int(sys.argv[2])
elif len(sys.argv) > 1:
	waitTime = int(sys.argv[1])
else:
	waitTime = 60
	epochInterval = 10

while not quit:
	# Process GNSS data and convert to RINEX format + extra Azimuth/Elevation data
	rnxFilepath = ""
	azielevFilepath = ""

	rnxFilepath, azielevFilepath, conv, quit = UBXtoRNX(conv, i, waitTime=waitTime, epochInterval=epochInterval)
	rnxDeleteQ.append(rnxFilepath)
	azielevDeleteQ.append(azielevFilepath)
	i += 1

	# If program is quit during UBXtoRNX, end while loop
	if quit:
		break

	# Plot RINEX file
	RNXtoIMG(rnxFilepath)
	
	# AFTER FIRST TURN ONLY
	# Delete previous RINEX file to save space
	# NEED TO ADD .nc FILE DELETION TOO!!!!!
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
			print(f"Deleting AZIELEV file at: {rnxNetCDF}")
			os.remove(rnxNetCDF)
		else:
			print(f"Warning: AZIELEV file to DELETE could not be found at {rnxNetCDF}")
