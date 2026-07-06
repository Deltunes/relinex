import os
import subprocess
import sys
from datetime import datetime
import numpy as np

sys.path.insert(1, 'GNSSVOD')
from gnssvod_oneSite import RNXtoIMG

def concatFilelist(rnxFileDir: str, azielevFileDir: str):

    outputFilepath = "RNX_SUCCESS/concat"

    rnxFileDict, azielevFileDict = getFilelist(rnxFileDir, azielevFileDir)

    rnxFileTupleSorted = sorted(rnxFileDict.items())
    rnxFilelist = []
    for tuple in rnxFileTupleSorted:
         rnxFilelist.append(tuple[1])

    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])
         
    prevRNXOutput = None
    prevAzielevOutput = None
    for i in range(len(rnxFilelist)):
        subprocess.run(["vcgencmd","get_throttled"])
        subprocess.run(["vcgencmd","measure_temp"])
        subprocess.run(["free","-h"])
        
        rnxFileNew = rnxFilelist[i]

        # RINEX CONCAT
        epochFirst = datetime.max
        epochLast = datetime.min
        
        RNXformatEdit(rnxFileNew)

        rnxFilename = rnxFileNew.split("/")[-1].split(".")[0]

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

        epochFirst = epochFirst.strftime("%Y_%m_%d_%H_%M_%S")
        epochLast = epochLast.strftime("%Y_%m_%d_%H_%M_%S")
        outputFilepathRNX = f"{outputFilepath}/success_{epochFirst}-{epochLast}.rnx"

        cmdstr = []
        cmdstr.append("./CONCAT_FILES/gfzrnx")
        cmdstr.append("-finp")
        if prevRNXOutput:
             cmdstr.append(prevRNXOutput)
        cmdstr.append(rnxFileNew)
        cmdstr.append("-fout")
        cmdstr.append(outputFilepathRNX)

        print(f"first - {epochFirst}")
        print(f"last - {epochLast}")
        subprocess.run(cmdstr)

        prevRNXOutput = outputFilepathRNX

        # AZIMUTH & ELEVATION CONCAT
        """outputFilepathAzielev = f"{outputFilepath}/azimuth&elevation_{epochFirst}-{epochLast}.txt"
        azielevConcat = open(outputFilepathAzielev, "w", encoding="utf-8")
        azielevConcat.write("")
        azielevConcat.close()
        for azielevFilepath in azielevFilelist:
            azielevFile = open(azielevFilepath, "r", encoding="utf-8")
            azielevData = azielevFile.read()
            azielevFile.close()

            azielevConcat = open(outputFilepathAzielev, "a", encoding="utf-8")
            azielevConcat.write(azielevData)
            azielevConcat.close()"""

        outputFilepathAzielev = f"{outputFilepath}/azimuth&elevation_{epochFirst}-{epochLast}.txt"
        azielevOutput = open(outputFilepathAzielev, "w", encoding="utf-8")

        if prevAzielevOutput:
            prev = open(prevAzielevOutput, "r", encoding="utf-8")
            for line in prev:
                azielevOutput.write(line)
            prev.close()

        new = open(azielevFilelist[i], "r", encoding="utf-8")
        for line in new:
            azielevOutput.write(line)
        new.close()

        azielevOutput.close()
        prevAzielevOutput = outputFilepathAzielev

        RNXtoIMG(outputFilepathRNX)

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