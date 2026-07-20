import os
import subprocess
import sys
from datetime import datetime
import numpy as np

sys.path.insert(1, 'GNSSVOD')
from gnssvod_oneSite import RNXtoIMG

def concatFilelist(siteno: int, fileDir: str, outputPath="."):
    outputFilepath = f"{fileDir}/concat/gif_data"
    obsFileDir = f"{fileDir}/obs"
    azielevFileDir = f"{fileDir}/azielev"

    obsFileDict, azielevFileDict = getFilelistOBS(siteno, obsFileDir, azielevFileDir)

    obsFileTupleSorted = sorted(obsFileDict.items())
    obsFilelist = []
    for tuple in obsFileTupleSorted:
         obsFilelist.append(tuple[1])

    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])
         
    prevRNXOutput = None
    prevAzielevOutput = None

    epochFirstAll = datetime.max
    epochLastAll = datetime.min

    delRNX = None
    delAzielev = None
    for i in range(len(obsFilelist)):
        obsFileNew = obsFilelist[i]
        obsFilename = obsFileNew.split("/")[-1].split(".")[0]
        epochRange = "_".join(obsFilename.split("_")[2:])
        formatOBS(obsFileNew)

        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        if epochFirst < epochFirstAll or epochFirstAll == datetime.max:
            epochFirstAll = epochFirst
        if epochLast > epochLastAll or epochLastAll == datetime.min:
            epochLastAll = epochLast

        epochFirstStr = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
        epochLastStr = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")
        newRNXFilename = f"obs_site{siteno}_{epochFirstStr}-{epochLastStr}.rnx"
        outputFilepathRNX = f"{outputFilepath}/obs/{newRNXFilename}"

        cmdstr = []
        cmdstr.append(f"CONCAT_FILES/gfzrnx")
        cmdstr.append("-finp")
        if prevRNXOutput:
             cmdstr.append(prevRNXOutput)
             delRNX = prevRNXOutput
        cmdstr.append(obsFileNew)
        cmdstr.append("-fout")
        cmdstr.append(outputFilepathRNX)

        subprocess.run(cmdstr, capture_output=True)

        prevRNXOutput = outputFilepathRNX

        # AZIMUTH & ELEVATION CONCAT
        newAzielevFilename = f"azielev_site{siteno}_{epochFirstStr}-{epochLastStr}.txt"
        outputFilepathAzielev = f"{outputFilepath}/azielev/{newAzielevFilename}"
        azielevOutput = open(outputFilepathAzielev, "w", encoding="utf-8")

        if prevAzielevOutput:
            prev = open(prevAzielevOutput, "r", encoding="utf-8")
            for line in prev:
                azielevOutput.write(line)
            prev.close()
            delAzielev = prevAzielevOutput

        new = open(azielevFilelist[i], "r", encoding="utf-8")
        for line in new:
            azielevOutput.write(line)
        new.close()

        azielevOutput.close()
        prevAzielevOutput = outputFilepathAzielev

        RNXtoIMG(outputFilepathRNX, siteno, outputPath)
        if delRNX != None and delAzielev != None:
            delNC = f"GNSSVOD/nc/{f"{newRNXFilename.split(".")[0]}.nc"}"
            os.remove(delRNX)
            os.remove(delAzielev)
            os.remove(delNC)
            
        print()

def getFilelistOBS(siteno: int, obsfiledir: str, azielevfiledir: str):
    obsFileDict = dict()
    azielevFileDict = dict()

    for filepath in os.listdir(obsfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:2])
            filenameEpochRange = "_".join(filename.split("_")[2:])
            if extension == "rnx" and filenamePrefix == f"obs_site{siteno}":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                obsFileDict[firstDatetime] = f"{obsfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    for filepath in os.listdir(azielevfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:2])
            filenameEpochRange = "_".join(filename.split("_")[2:])
            if extension == "txt" and filenamePrefix == f"azielev_site{siteno}":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                azielevFileDict[firstDatetime] = f"{azielevfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    return obsFileDict, azielevFileDict

def formatOBS(rnxFilepath):
	# Reformat RINEX file to work with GNSSVODs
	rplcRNX = open(rnxFilepath, "r", encoding="utf-8")
	rplcData = rplcRNX.readlines()
	rplcRNX.close()
	
	rplcRNX = open(rnxFilepath, "w", encoding="utf-8")
	for line in rplcData:
		if ("GLONASS SLOT / FRQ" in line) or ("LEAPSECONDS" in line):
			continue
		else:
			rplcRNX.write(line)
	rplcRNX.close()