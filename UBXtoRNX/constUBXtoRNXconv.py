from datetime import datetime, timezone
import time
from serial import Serial
from pyubx2 import UBXReader
from pygnssutils.rinex_conv import RinexConverter
from pygnssutils.rinex_globals import OBS, EPOCHMIN
import subprocess
import sys

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

def writeAzimElev(conv, currEpoch, azimelevFile, azimelevDict):
	newEpoch = conv.get_current_epoch("O")

	if newEpoch == EPOCHMIN:
		return currEpoch
	
	if currEpoch != newEpoch:
			currEpoch = newEpoch
			azimelevFile.write("> ")
			azimelevFile.write(str(currEpoch))
			azimelevFile.write("\n")
			for k in azimelevDict:
				azimelevFile.write(str(k))
				azimelevFile.write("/")
				azimelevFile.write(f"{str(azimelevDict[k][0])}/{str(azimelevDict[k][1])}")
				azimelevFile.write("\n")
	return currEpoch

def RNXformatEdit(rnxFilename):
	# Reformat RINEX file to work with GNSSVODs
	rplcRNX = open(rnxFilename, "r", encoding="utf-8")
	rplcData = rplcRNX.read()
	rplcRNX.close()
	
	rplcData = rplcData.replace("\n→","")
	rplcData = rplcData.replace("END OF FILE                                                 COMMENT\n","")
	
	rplcRNX = open(rnxFilename, "w", encoding="utf-8")
	rplcRNX.write(rplcData)
	rplcRNX.close()

def correctAzimElev(rnxFilename, azimElevFilename):
	# Open RINEX file to read
	rnxFile = open(rnxFilename, "r", encoding="utf-8")
	rnxData = rnxFile.readlines()
	rnxFile.close()

	# Open Azimuth/Elevation file to read
	azimElevFile = open(azimElevFilename, "r", encoding="utf-8")
	azimElevData = azimElevFile.readlines()
	azimElevFile.close()

	# Increment till satellites
	for line in range(len(rnxData)-1):
		if rnxData[line][0] == ">":
			rnxData = rnxData[line:]
			break

	# Get satellite IDs
	currEpochLine = ""
	currEpochLineSplit = rnxData[0].strip()
	satIDs = {}
	for line in rnxData:
		if line[0] == ">":
			currEpochSplit = line.strip().split()
			currEpochSplit = currEpochSplit[0:7]
			currEpochSplit[2] = f"{int(currEpochSplit[2]):02d}"
			currEpochSplit[3] = f"{int(currEpochSplit[3]):02d}"
			currEpochSplit[4] = f"{int(currEpochSplit[4]):02d}"
			currEpochSplit[5] = f"{int(currEpochSplit[5]):02d}"
			currEpochSplit[6] = f"{float(currEpochSplit[6]):09f}"
			currEpochLine = "/".join(currEpochSplit)
			currEpochLine = currEpochLine[:-7]
		else:
			if currEpochLine not in satIDs:
				satIDs[currEpochLine] = set()
			satIDs[currEpochLine].add(line[0:3])


	# Write ONLY lines with satellite IDs that are in the RINEX file
	correctedAzimElev = ""
	currEpochKey = ""
	for line in azimElevData:
		if line[0] == ">":
			azimelevEpoch = line.replace("-", " ").replace(":", " ").replace("+"," ")
			azimelevEpoch = azimelevEpoch.split(" ")
			azimelevEpoch = azimelevEpoch[0:7]
			azimelevEpoch[6] = (azimelevEpoch[6])[0:2]
			currEpochKey = "/".join(azimelevEpoch)
			correctedAzimElev += (currEpochKey + "\n")
		else:
			currSatID = line[0:3]
			if currSatID in satIDs[currEpochKey]:
				correctedAzimElev += line

	azimElevFile = open(azimElevFilename, "w", encoding="utf-8")
	azimElevFile.write(correctedAzimElev)

def UBXtoRNX(conv, fileno, waitTime=60, epochInterval=10):
	stream = Serial(COMPORT, 9600, timeout=10)
	ubr = UBXReader(stream)
		
	print(f"RINEX FILE LENGTH: {waitTime} second(s)")
	print(f"EPOCH INTERVAL: {epochInterval} second(s)")

	try:
		#while True:
		if True:
			i = fileno
			print(f"RNX FILE: {i}")
			
			currEpoch = EPOCHMIN
			rnxFilename = f"RNX_SUCCESS/rinex/success{i}.rnx"
			azimelevFilename = f"RNX_SUCCESS/azielev/azimuth&elevation{i}.txt"
			conv._outputs[OBS]["fnm"] = rnxFilename
			conv._outputs[OBS]["stm"] = open(rnxFilename, "w", encoding="utf-8")
			azimelevFile = open(azimelevFilename, "w", encoding="utf-8")

			currIntTime = waitTime

			end_time = time.time() + waitTime
			while time.time() < end_time:

				countdown = int(end_time - time.time())
				if countdown < int(currIntTime):
					print(f"\r\t\t{countdown}\t\t", end="")
					currIntTime = countdown

				raw, msg = ubr.read()
				
				if msg == None:
					continue
					
				if (msg.identity == "RXM-RAWX"):
					currSec = int(msg.rcvTow)
					if ((currSec % epochInterval) == 0):
						input_prc = conv._outputs[OBS]["hnd"].process_input_data(msg)
					else:
						input_prc = 0
				else:
					input_prc = conv._outputs[OBS]["hnd"].process_input_data(msg)

				if (msg.identity == "NAV-SAT"):
					azimelevDict = {}
					for j in range(1, msg.numSvs):
						azimelev = (getattr(msg, f"azim_{j:02d}"), getattr(msg, f"elev_{j:02d}"))
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
						azimelevDict[id] = azimelev
						
					currEpoch = writeAzimElev(conv, currEpoch, azimelevFile, azimelevDict)

				conv._outputs[OBS]["prc"] += input_prc
				
			currEpoch = writeAzimElev(conv, currEpoch, azimelevFile, azimelevDict)

			# Output RINEX file
			conv.process_output_data(["O"])
			conv._outputs[OBS]["stm"].close()
			azimelevFile.close()

			RNXformatEdit(rnxFilename)
			correctAzimElev(rnxFilename, azimelevFilename)
			#subprocess.run(["sudo", "shutdown", "-h", "now"])

			print()
			quit = False
			return rnxFilename, azimelevFilename, conv, quit

	except KeyboardInterrupt:
		if (conv._outputs[OBS]["stm"].closed == False):
			conv.process_output_data(["O"])
			conv._outputs[OBS]["stm"].close()

			RNXformatEdit(rnxFilename)
			correctAzimElev(rnxFilename, azimelevFilename)

		if (azimelevFile.closed == False):
			currEpoch = writeAzimElev(conv, currEpoch, azimelevFile, azimelevDict)
			azimelevFile.close()
			correctAzimElev(rnxFilename, azimelevFilename)
		
		print()
		quit = True
		return rnxFilename, azimelevFilename, conv, quit
