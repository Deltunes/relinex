import time
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, SET_LAYER_RAM, SET_LAYER_BBR
from pygnssutils.rinex_conv import RinexConverter
from pygnssutils.rinex_globals import OBS, EPOCHMIN
import subprocess
import sys

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

# Write Azimuth and Elevation to .txt file
def writeazielev(conv, currEpoch, azielevFile, azielevDict):
	# Get epoch from RinexConverter
	newEpoch = conv.get_current_epoch("O")

	# If epoch returns as default, just use last valid epoch
	if newEpoch == EPOCHMIN:
		return currEpoch
	
	# If epoch has changed since last check
	if currEpoch != newEpoch:
			currEpoch = newEpoch

			# Format epoch with "/" between to read later
			azielevEpoch = str(currEpoch).replace("-", " ").replace(":", " ").replace("+"," ")
			azielevEpoch = azielevEpoch.split(" ")
			azielevEpoch = azielevEpoch[0:6]
			azielevEpoch[5] = (azielevEpoch[5])[0:2]
			currEpochLine = "/".join(azielevEpoch)

			# Write epoch and all sattelite data for epoch
			azielevFile.write(f">/{currEpochLine}\n")
			for k in azielevDict:
				azielevFile.write(str(k))
				azielevFile.write("/")
				azielevFile.write(f"{str(azielevDict[k][0])}/{str(azielevDict[k][1])}")
				azielevFile.write("\n")
	return currEpoch

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

def correctazielev(rnxFilepath, azielevFilepath):
	# 	DATA RETRIEVAL FROM FILES
	# Open RINEX file to read
	rnxFile = open(rnxFilepath, "r", encoding="utf-8")
	rnxData = rnxFile.readlines()
	rnxFile.close()

	# Open Azimuth/Elevation file to read
	azielevFile = open(azielevFilepath, "r", encoding="utf-8")
	azielevData = azielevFile.readlines()
	azielevFile.close()

	# Increment past header until satellites
	for line in range(len(rnxData)-1):
		if rnxData[line][0] == ">":
			rnxData = rnxData[line:]
			break

	# Get satellite IDs
	currEpochLine = ""
	satIDs = {}
	for line in rnxData:
		# If line is epoch
		if line[0] == ">":
			# Reformat epoch line to match azielev format
			currEpochSplit = line.strip().split()
			currEpochSplit = currEpochSplit[0:7]
			currEpochSplit[2] = f"{int(currEpochSplit[2]):02d}"
			currEpochSplit[3] = f"{int(currEpochSplit[3]):02d}"
			currEpochSplit[4] = f"{int(currEpochSplit[4]):02d}"
			currEpochSplit[5] = f"{int(currEpochSplit[5]):02d}"
			currEpochSplit[6] = f"{float(currEpochSplit[6]):09f}"
			currEpochLine = "/".join(currEpochSplit)
			currEpochLine = currEpochLine[:-7]
		# Else line is satellite data
		else:
			# If a new epoch was reached, initialize the set for that key
			# Then, add the satellite ID to the set for that key
			if currEpochLine not in satIDs:
				satIDs[currEpochLine] = set()
			satIDs[currEpochLine].add(line[0:3])

	# 	COMPARE RINEX AND AZIELEV SATELLITE IDs
	# 	WRITE ONLY MATCHES TO AZIELEV FILE
	correctedazielev = ""
	currEpochKey = ""
	for line in azielevData:
		if line[0] == ">":
			currEpochKey = line.strip()
			correctedazielev += line
		else:
			currSatID = line[0:3]
			if currSatID in satIDs[currEpochKey]:
				correctedazielev += line

	#	WRITE CORRECTED AZIMUTH/ELEVATION DATA
	azielevFile = open(azielevFilepath, "w", encoding="utf-8")
	azielevFile.write(correctedazielev)
	azielevFile.close()

def renameFilesWithEpoch(rnxFilepath, azielevFilepath):
	azielevFile = open(azielevFilepath, "r", encoding="utf-8")
	azielevData = azielevFile.readlines()
	azielevFile.close()

	epochLines = []
	for line in range(len(azielevData)-1):
		if azielevData[line][0] == ">":
			epochLines.append(azielevData[line])

	firstEpoch = epochLines[0][2:].replace('\n','').replace("/","_")
	lastEpoch = epochLines[-1][2:].replace('\n','').replace("/","_")

	rnxFileSplit = rnxFilepath.split("/")
	rnxFileSplit[-1] = f"success_{firstEpoch}-{lastEpoch}.rnx"
	rnxFilepathNew = "/".join(rnxFileSplit)
	subprocess.run(["mv", f"{rnxFilepath}", f"{rnxFilepathNew}"])

	azielevFileSplit = azielevFilepath.split("/")
	azielevFileSplit[-1] = f"azielev_{firstEpoch}-{lastEpoch}.txt"
	azielevFilepathNew = "/".join(azielevFileSplit)
	subprocess.run(["mv", f"{azielevFilepath}", f"{azielevFilepathNew}"])

def UBXtoRNX(fileno, waitTime=60, epochInterval=10, outputPath=".", comport=None):
	COMPORT = comport
	# Connect to Sparkfun chip through COMPORT
	try:
		stream = Serial(COMPORT, 9600, timeout=10)
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
		
	print(f"RINEX FILE LENGTH: {waitTime} second(s)")
	print(f"EPOCH INTERVAL: {epochInterval} second(s)")

	try:
		conv = mkconv()

		print(f"RNX FILE: {fileno}")
		
		# Set default invalid epoch value
		currEpoch = EPOCHMIN

		# Set RINEX and AZIELEV filenames
		rnxFilepath = f"{outputPath}/RNX_SUCCESS/rinex/success{fileno}.rnx"
		azielevFilepath = f"{outputPath}/RNX_SUCCESS/azielev/azielev{fileno}.txt"
		azielevFile = open(azielevFilepath, "w", encoding="utf-8")
		azielevFile.write("")
		azielevFile.close()

		# Set up file stream for RINEX file output
		conv._outputs[OBS]["fnm"] = rnxFilepath
		conv._outputs[OBS]["stm"] = open(rnxFilepath, "w", encoding="utf-8")

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
			
			print(msg.identity)

			# If no UBXMessage was received, just continue to next loop
			if msg == None:
				continue
			
			# Azimuth/Elevation data is received from NAV-SAT messages
			# Collect azielev data from msg
			if (msg.identity == "NAV-SAT"):
				azielevDict = {}
				for j in range(1, msg.numSvs):
					azielev = (getattr(msg, f"azim_{j:02d}"), getattr(msg, f"elev_{j:02d}"))
					id = ""
					match (getattr(msg, f"gnssId_{j:02d}")):
						case 0:
							id = f"G{getattr(msg, f"svId_{j:02d}"):02d}"
						case 1:
							id = f"S{(getattr(msg, f"svId_{j:02d}") - 100):02d}"
						case 2:
							id = f"E{getattr(msg, f"svId_{j:02d}"):02d}"
						case 3:
							id = f"C{getattr(msg, f"svId_{j:02d}"):02d}"
						case 6:
							id = f"R{getattr(msg, f"svId_{j:02d}"):02d}"
						case _:
							id = "???"
					azielevDict[id] = azielev
				
				# Write azielev data w/ current epoch
				azielevFile = open(azielevFilepath, "a", encoding="utf-8")
				currEpoch = writeazielev(conv, currEpoch, azielevFile, azielevDict)
				azielevFile.close()

			# RXM-RAWX is received every second
			if (msg.identity == "RXM-RAWX"):
				# only process epoch input every (epochInterval) seconds
				currSec = int(msg.rcvTow)
				if ((currSec % epochInterval) == 0):
					input_prc = conv._outputs[OBS]["hnd"].process_input_data(msg)
				else:
					input_prc = 0
			else:
				# process any other message identity
				input_prc = conv._outputs[OBS]["hnd"].process_input_data(msg)

			conv._outputs[OBS]["prc"] += input_prc

		# Output files
		conv.process_output_data(["O"])
		conv._outputs[OBS]["stm"].close()
		RNXformatEdit(rnxFilepath)
		correctazielev(rnxFilepath, azielevFilepath)
		renameFilesWithEpoch(rnxFilepath, azielevFilepath)

		print()
		quit = False
		return quit

	# IF PROGRAM IS EXITED BEFORE COMPLETION
	except KeyboardInterrupt:
		# Write incomplete RINEX data
		if (conv._outputs[OBS]["stm"].closed == False):
			conv.process_output_data(["O"])
			conv._outputs[OBS]["stm"].close()
			RNXformatEdit(rnxFilepath)

		# Write incomplete AZIELEV data
		if (azielevFile.closed == False):
			currEpoch = writeazielev(conv, currEpoch, azielevFile, azielevDict)
			azielevFile.close()
		correctazielev(rnxFilepath, azielevFilepath)
		renameFilesWithEpoch(rnxFilepath, azielevFilepath)

		print()
		quit = True
		return quit

# Run UBXtoRNX, pass arguments
if __name__ == "__main__":
	i = 1
	while True:
		if len(sys.argv) > 2:
			UBXtoRNX(i, int(sys.argv[1]),int(sys.argv[2]))
		elif len(sys.argv) > 1:
			UBXtoRNX(i, int(sys.argv[1]))
		else:
			UBXtoRNX(i)
		i += 1