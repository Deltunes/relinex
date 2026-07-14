import os
import subprocess
import sys
from datetime import datetime
import numpy as np

sys.path.insert(1, 'GNSSVOD')
from gnssvod_oneSite import RNXtoIMG

def concatFilelist(rnxFileDir: str, azielevFileDir: str, outputPath="."):
    outputFilepath = f"{outputPath}/OBS_SUCCESS/concat/gif_data"

    rnxFileDict, azielevFileDict = getFilelist(rnxFileDir, azielevFileDir)

    rnxFileTupleSorted = sorted(rnxFileDict.items())
    rnxFilelist = []
    for tuple in rnxFileTupleSorted:
         rnxFilelist.append(tuple[1])

    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])

    print(len(rnxFilelist))
    print(len(azielevFilelist))
         
    prevRNXOutput = None
    prevAzielevOutput = None

    epochFirst = datetime.max
    epochLast = datetime.min

    delRNX = None
    delAzielev = None
    for i in range(len(rnxFilelist)):
        rnxFileNew = rnxFilelist[i]
        rnxFilename = rnxFileNew.split("/")[-1].split(".")[0]
        RNXformatEdit(rnxFileNew)

        epochRange = ""
        epochNums = False
        for char in rnxFilename:
            if char == ".":
                break
            if epochNums == True:
                epochRange += char
            elif char == "_" and epochNums == False:
                epochNums = True
        
        epochSplit = epochRange.split("-")
        epoch1 = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epoch2 = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        if epoch1 < epochFirst or epochFirst == datetime.max:
            epochFirst = epoch1
        if epoch2 > epochLast or epochLast == datetime.min:
            epochLast = epoch2

        epochFirstStr = epochFirst.strftime("%Y_%m_%d_%H_%M_%S")
        epochLastStr = epochLast.strftime("%Y_%m_%d_%H_%M_%S")
        newRNXFilename = f"success_{epochFirstStr}-{epochLastStr}.rnx"
        outputFilepathRNX = f"{outputFilepath}/rinex/{newRNXFilename}"

        cmdstr = []
        cmdstr.append(f"CONCAT_FILES/gfzrnx")
        cmdstr.append("-finp")
        if prevRNXOutput:
             cmdstr.append(prevRNXOutput)
             delRNX = prevRNXOutput
        cmdstr.append(rnxFileNew)
        cmdstr.append("-fout")
        cmdstr.append(outputFilepathRNX)

        print(f"first - {epochFirstStr}")
        print(f"last - {epochLastStr}")
        subprocess.run(cmdstr, capture_output=True)

        prevRNXOutput = outputFilepathRNX

        # AZIMUTH & ELEVATION CONCAT
        newAzielevFilename = f"azielev_{epochFirstStr}-{epochLastStr}.txt"
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

        RNXtoIMG(outputFilepathRNX, outputPath)
        if delRNX != None and delAzielev != None:
            delNC = f"GNSSVOD/nc/{f"{newRNXFilename.split(".")[0]}.nc"}"
            os.remove(delRNX)
            os.remove(delAzielev)
            os.remove(delNC)
            
        print()

def getFilelist(rnxfiledir: str, azielevfiledir: str):
    rnxFileDict = dict()
    azielevFileDict = dict()
    for filename in os.listdir(rnxfiledir):
        filenameSplit = filename.split(".")
        extension = filenameSplit[-1]
        if extension == "rnx" and filenameSplit[0][0:7] == "success":
            firstDatetimeStr = filenameSplit[0][8:].split("-")[0]
            firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
            rnxFileDict[firstDatetime] = f"{rnxfiledir}/{filename}"
            #print(f"{rnxfiledir}/{filename}")

    for filename in os.listdir(azielevfiledir):
        filenameSplit = filename.split(".")
        extension = filenameSplit[-1]
        if extension == "txt" and filenameSplit[0][0:7] == "azielev":
            firstDatetimeStr = filenameSplit[0][8:].split("-")[0]
            firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
            azielevFileDict[firstDatetime] = f"{azielevfiledir}/{filename}"
            #print(f"{azielevfiledir}/{filename}")

    return rnxFileDict, azielevFileDict

def RNXformatEdit(rnxFilepath):
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