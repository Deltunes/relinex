import os
import subprocess
from datetime import datetime
import numpy as np

def concatFilelistRNX(fileDir: str, outputPath="."):

    outputFilepath = f"{outputPath}/{fileDir}/concat"
    rnxFileDir = f"{outputPath}/{fileDir}/rinex"
    azielevFileDir = f"{outputPath}/{fileDir}/azielev"

    rnxFileDict, azielevFileDict = getFilelistRNX(rnxFileDir, azielevFileDir)

    rnxFileTupleSorted = sorted(rnxFileDict.items())
    rnxFilelist = []
    epochList = []
    for tuple in rnxFileTupleSorted:
         epochList.append(tuple[0])
         rnxFilelist.append(tuple[1])

    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])

    for i in range(0, len(epochList)):
        print(f"{(i+1):5}) {epochList[i]}\t", end = "")
        if i % 3 == 2:
            print()
    print()
    print()
    print(f"First Recorded Epoch - {epochList[0]}\tLast Recorded Epoch - {epochList[-1]}")
    print()
    while True:
        print(f"Select Epoch Range to Concatenate (1-{len(epochList)})")
        print("\tFirst - ", end="")
        first = input()
        print("\tLast - ", end="")
        last = input()
        try:
            first = int(first)
            last = int(last)
            break
        except:
            print("Invalid input. Try again.")
            print()
    print()
    
    print(f"First - {epochList[first-1]}\tLast - {epochList[last-1]}")

    rnxFilelist = rnxFilelist[first-1:last]
    azielevFilelist = azielevFilelist[first-1:last]
    
    # RINEX CONCAT
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for rnxFilepath in rnxFilelist:
        RNXformatEdit(rnxFilepath)
        rnxFilename = rnxFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(rnxFilename.split("_")[1:])

        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        elif epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(rnxFilepath)

    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/rinex/success_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

    # AZIMUTH & ELEVATION CONCAT
    azielevConcat = open(f"{outputFilepath}/azielev/azielev_{epochFirstAll}-{epochLastAll}.txt", "w", encoding="utf-8")
    azielevConcat.write("")
    azielevConcat.close()
    for azielevFilepath in azielevFilelist:
        azielevFile = open(azielevFilepath, "r", encoding="utf-8")
        azielevData = azielevFile.read()
        azielevFile.close()

        azielevConcat = open(f"{outputFilepath}/azielev/azielev_{epochFirstAll}-{epochLastAll}.txt", "a", encoding="utf-8")
        azielevConcat.write(azielevData)
        azielevConcat.close()

def concatFilelistOBSNAV(fileDir: str, siteno: int, outputPath="."):
    outputFilepath = f"{outputPath}/{fileDir}/site{siteno}/concat"
    obsFileDir = f"{outputPath}/{fileDir}/site{siteno}/obs"
    navFileDir = f"{outputPath}/{fileDir}/site{siteno}/nav"

    print(outputFilepath)
    print(obsFileDir)
    print(navFileDir)

    obsFileDict, navFileDict = getFilelistOBSNAV(obsFileDir, navFileDir)

    obsFileTupleSorted = sorted(obsFileDict.items())
    obsFilelist = []
    epochList = []
    for tuple in obsFileTupleSorted:
         epochList.append(tuple[0])
         obsFilelist.append(tuple[1])

    navFileTupleSorted = sorted(navFileDict.items())
    navFilelist = []
    for tuple in navFileTupleSorted:
         navFilelist.append(tuple[1])

    for i in range(0, len(epochList)):
        print(f"{(i+1):5}) {epochList[i]}\t", end = "")
        if i % 3 == 2:
            print()
    print()
    print()
    print(f"First Recorded Epoch - {epochList[0]}\tLast Recorded Epoch - {epochList[-1]}")
    print()
    while True:
        print(f"Select Epoch Range to Concatenate (1-{len(epochList)})")
        print("\tFirst - ", end="")
        first = input()
        print("\tLast - ", end="")
        last = input()
        try:
            first = int(first)
            last = int(last)
            break
        except:
            print("Invalid input. Try again.")
            print()
    print()
    
    print(f"First - {epochList[first-1]}\tLast - {epochList[last-1]}")

    obsFilelist = obsFilelist[first-1:last]
    navFilelist = navFilelist[first-1:last]
    
    # OBS CONCAT
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for obsFilepath in obsFilelist:
        RNXformatEdit(obsFilepath)
        obsFilename = obsFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(obsFilename.split("_")[3:])
        
        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        if epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(obsFilepath)

    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/obs/success_obs_site{siteno}_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")
    
    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for navFilepath in navFilelist:
        RNXformatEdit(navFilepath)
        navFilename = navFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(navFilename.split("_")[3:])
        
        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        elif epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(navFilepath)

    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/nav/success_nav_site{siteno}_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

def getFilelistRNX(rnxfiledir: str, azielevfiledir: str):
    rnxFileDict = dict()
    azielevFileDict = dict()
    for filepath in os.listdir(rnxfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:1])
            filenameEpochRange = "_".join(filename.split("_")[1:])
            print(filenamePrefix)
            if extension == "rnx" and filenamePrefix == "success":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                rnxFileDict[firstDatetime] = f"{rnxfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    for filepath in os.listdir(azielevfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:1])
            filenameEpochRange = "_".join(filename.split("_")[1:])
            if extension == "txt" and filenamePrefix == "azielev":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                azielevFileDict[firstDatetime] = f"{azielevfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    return rnxFileDict, azielevFileDict

def getFilelistOBSNAV(obsfiledir: str, navfiledir: str):
    obsFileDict = dict()
    navFileDict = dict()
    for filepath in os.listdir(obsfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:2])
            filenameEpochRange = "_".join(filename.split("_")[3:])
            if extension == "rnx" and filenamePrefix == "success_obs":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                obsFileDict[firstDatetime] = f"{obsfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    for filepath in os.listdir(navfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:2])
            filenameEpochRange = "_".join(filename.split("_")[3:])
            if extension == "rnx" and filenamePrefix == "success_nav":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                navFileDict[firstDatetime] = f"{navfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    return obsFileDict, navFileDict

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