import os
import subprocess
from datetime import datetime
import numpy as np

def concatFilelist(rnxFileDir: str, azielevFileDir: str, outputPath="."):

    outputFilepath = f"{outputPath}/RNX_SUCCESS/concat"

    rnxFileDict, azielevFileDict = getFilelist(rnxFileDir, azielevFileDir)

    rnxFileTupleSorted = sorted(rnxFileDict.items())
    rnxFilelist = []
    for tuple in rnxFileTupleSorted:
         rnxFilelist.append(tuple[1])

    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])
         
    # RINEX CONCAT
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    epochFirst = datetime.max
    epochLast = datetime.min
    for rnxFilepath in rnxFilelist:
        RNXformatEdit(rnxFilepath)

        rnxFilename = rnxFilepath.split("/")[-1].split(".")[0]

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

        if epoch1 < epochFirst:
            epochFirst = epoch1
        elif epoch2 > epochLast:
            epochLast = epoch2

        cmdstr.append(rnxFilepath)

    epochFirst = epochFirst.strftime("%Y_%m_%d_%H_%M_%S")
    epochLast = epochLast.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/success_{epochFirst}-{epochLast}.rnx")
    print(f"first - {epochFirst}")
    print(f"last - {epochLast}")
    subprocess.run(cmdstr)

    # AZIMUTH & ELEVATION CONCAT
    azielevConcat = open(f"{outputFilepath}/azimuth&elevation_{epochFirst}-{epochLast}.txt", "w", encoding="utf-8")
    azielevConcat.write("")
    azielevConcat.close()
    for azielevFilepath in azielevFilelist:
        azielevFile = open(azielevFilepath, "r", encoding="utf-8")
        azielevData = azielevFile.read()
        azielevFile.close()

        azielevConcat = open(f"{outputFilepath}/azimuth&elevation_{epochFirst}-{epochLast}.txt", "a", encoding="utf-8")
        azielevConcat.write(azielevData)
        azielevConcat.close()

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
        if extension == "txt" and filenameSplit[0][0:17] == "azimuth&elevation":
            firstDatetimeStr = filenameSplit[0][18:].split("-")[0]
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