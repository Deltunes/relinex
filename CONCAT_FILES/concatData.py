import os
import subprocess
from datetime import datetime
import numpy as np

def concatFilelistOBS(fileDir: str, siteno: int, outputPath="."):
    # Create filepaths
    outputFilepath = f"{outputPath}/{fileDir}/site{siteno}/concat"
    obsFileDir = f"{outputPath}/{fileDir}/site{siteno}/obs"
    azielevFileDir = f"{outputPath}/{fileDir}/site{siteno}/azielev"

    # Get file dict, key is first datetime, item is filepath
    obsFileDict, azielevFileDict = getFilelistOBS(obsFileDir, azielevFileDir, siteno)

    # Sort file dictionaries into sorted epoch list and sorted file list
    obsFileTupleSorted = sorted(obsFileDict.items())
    obsFilelist = []
    epochList = []
    for tuple in obsFileTupleSorted:
         epochList.append(tuple[0])
         obsFilelist.append(tuple[1])

    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])

    # Print all epochs
    for i in range(0, len(epochList)):
        print(f"{(i+1):5}) {epochList[i]}\t", end = "")
        if i % 3 == 2:
            print()
    print()
    print()
    print(f"First Recorded Epoch - {epochList[0]}\tLast Recorded Epoch - {epochList[-1]}")
    print()

    # Choose epoch range
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

    # Restrict filelists to epoch range
    obsFilelist = obsFilelist[first-1:last]
    azielevFilelist = azielevFilelist[first-1:last]
    
    # Concatenate observation files
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    # Intialize epoch
    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for obsFilepath in obsFilelist:
        # Prepare obs file, get filename and epoch range
        formatOBS(obsFilepath)
        obsFilename = obsFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(obsFilename.split("_")[2:])

        # Get first and last epoch from epoch range
        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        # Change overall epoch range
        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        elif epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(obsFilepath)

    # Convert overall epoch range to str
    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/obs/obs_site{siteno}_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

    # Concat azimuth/elevation files
    azielevConcat = open(f"{outputFilepath}/azielev/azielev_site{siteno}_{epochFirstAll}-{epochLastAll}.txt", "w", encoding="utf-8")
    azielevConcat.write("")
    azielevConcat.close()
    for azielevFilepath in azielevFilelist:
        azielevFile = open(azielevFilepath, "r", encoding="utf-8")
        azielevData = azielevFile.read()
        azielevFile.close()

        azielevConcat = open(f"{outputFilepath}/azielev/azielev_site{siteno}_{epochFirstAll}-{epochLastAll}.txt", "a", encoding="utf-8")
        azielevConcat.write(azielevData)
        azielevConcat.close()


def concatFilelistNAV(fileDir: str, siteno: int, outputPath="."):
    # Create filepaths
    outputFilepath = f"{outputPath}/{fileDir}/site{siteno}/concat"
    navFileDir = f"{outputPath}/{fileDir}/site{siteno}/nav"

    # Get file dict, key is first datetime, item is filepath
    navFileDict = getFilelistNAV(navFileDir, siteno)

    # Sort file dictionaries into sorted epoch list and sorted file list
    navFileTupleSorted = sorted(navFileDict.items())
    epochList = []
    navFilelist = []
    for tuple in navFileTupleSorted:
         epochList.append(tuple[0])
         navFilelist.append(tuple[1])

    # Print all epochs
    for i in range(0, len(epochList)):
        print(f"{(i+1):5}) {epochList[i]}\t", end = "")
        if i % 3 == 2:
            print()
    print()
    print()
    print(f"First Recorded Epoch - {epochList[0]}\tLast Recorded Epoch - {epochList[-1]}")
    print()

    # Choose epoch range
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

    # Restrict filelist to epoch range
    navFilelist = navFilelist[first-1:last]

    # Concatenate navigation files
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    # Intialize epoch
    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for navFilepath in navFilelist:
        # Get filename and epoch range
        navFilename = navFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(navFilename.split("_")[2:])

        # Get first and last epoch from epoch range
        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        # Change overall epoch range
        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        elif epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(navFilepath)

    # Convert overall epoch range to str
    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/nav/nav_site{siteno}_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

def concatFilelistOBSNAV(fileDir: str, siteno: int, outputPath="."):
    # Create filepaths
    outputFilepath = f"{outputPath}/{fileDir}/site{siteno}/concat"
    obsFileDir = f"{outputPath}/{fileDir}/site{siteno}/obs"
    navFileDir = f"{outputPath}/{fileDir}/site{siteno}/nav"
    azielevFileDir = f"{outputPath}/{fileDir}/site{siteno}/azielev"

    # Get file dict, key is first datetime, item is filepath
    obsFileDict, navFileDict, azielevFileDict = getFilelistOBSNAV(obsFileDir, navFileDir, azielevFileDir, siteno)

    # Sort file dictionaries into sorted epoch list and sorted file list
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
        
    azielevFileTupleSorted = sorted(azielevFileDict.items())
    azielevFilelist = []
    for tuple in azielevFileTupleSorted:
         azielevFilelist.append(tuple[1])

    # Print all epochs
    for i in range(0, len(epochList)):
        print(f"{(i+1):5}) {epochList[i]}\t", end = "")
        if i % 3 == 2:
            print()
    print()
    print()
    print(f"First Recorded Epoch - {epochList[0]}\tLast Recorded Epoch - {epochList[-1]}")
    print()

    # Choose epoch range
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

    # Restrict filelists to epoch range
    obsFilelist = obsFilelist[first-1:last]
    navFilelist = navFilelist[first-1:last]
    azielevFilelist = azielevFilelist[first-1:last]

    # OBSERVATION FILES
    # Concatenate observation files
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    # Intialize epoch
    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for obsFilepath in obsFilelist:
        # Prepare obs file, get filename and epoch range
        formatOBS(obsFilepath)
        obsFilename = obsFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(obsFilename.split("_")[2:])

        # Get first and last epoch from epoch range
        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        # Change overall epoch range
        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        if epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(obsFilepath)

    # Convert overall epoch range to str
    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/obs/obs_site{siteno}_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

    # NAVIGATION FILES
    # Concatenate observation files
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    # Intialize epoch
    epochFirstAll = datetime.max
    epochLastAll = datetime.min
    for navFilepath in navFilelist:
        # Get filename and epoch range
        navFilename = navFilepath.split("/")[-1].split(".")[0]
        epochRange = "_".join(navFilename.split("_")[2:])

        # Get first and last epoch from epoch range
        epochSplit = epochRange.split("-")
        epochFirst = datetime.strptime(epochSplit[0], "%Y_%m_%d_%H_%M_%S")
        epochLast = datetime.strptime(epochSplit[1], "%Y_%m_%d_%H_%M_%S")

        # Change overall epoch range
        if epochFirst < epochFirstAll:
            epochFirstAll = epochFirst
        elif epochLast > epochLastAll:
            epochLastAll = epochLast

        cmdstr.append(navFilepath)

    # Convert overall epoch range to str
    epochFirstAll = epochFirstAll.strftime("%Y_%m_%d_%H_%M_%S")
    epochLastAll = epochLastAll.strftime("%Y_%m_%d_%H_%M_%S")

    cmdstr.append("-fout")
    cmdstr.append(f"{outputFilepath}/nav/nav_site{siteno}_{epochFirstAll}-{epochLastAll}.rnx")
    cmdstr.append("-f")
    subprocess.run(cmdstr)

    # AZIMUTH & ELEVATION
    # Concat azimuth/elevation files
    azielevConcat = open(f"{outputFilepath}/azielev/azielev_site{siteno}_{epochFirstAll}-{epochLastAll}.txt", "w", encoding="utf-8")
    azielevConcat.write("")
    azielevConcat.close()
    for azielevFilepath in azielevFilelist:
        azielevFile = open(azielevFilepath, "r", encoding="utf-8")
        azielevData = azielevFile.read()
        azielevFile.close()

        azielevConcat = open(f"{outputFilepath}/azielev/azielev_site{siteno}_{epochFirstAll}-{epochLastAll}.txt", "a", encoding="utf-8")
        azielevConcat.write(azielevData)
        azielevConcat.close()

def getFilelistOBS(obsfiledir: str, azielevfiledir: str, siteno: int):
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

def getFilelistNAV(navfiledir: str, siteno: str):
    navFileDict = dict()

    for filepath in os.listdir(navfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:2])
            filenameEpochRange = "_".join(filename.split("_")[2:])
            if extension == "rnx" and filenamePrefix == f"nav_site{siteno}":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                navFileDict[firstDatetime] = f"{navfiledir}/{filepath}"
        except:
            print(f"Invalid file: {filepath}. Skipping...")

    return navFileDict

def getFilelistOBSNAV(obsfiledir: str, navfiledir: str, azielevfiledir: str, siteno: str):
    obsFileDict = dict()
    navFileDict = dict()
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

    for filepath in os.listdir(navfiledir):
        try:
            filenameSplit = filepath.split(".")
            extension = filenameSplit[-1]
            filename = filenameSplit[0]
            filenamePrefix = "_".join(filename.split("_")[0:2])
            filenameEpochRange = "_".join(filename.split("_")[2:])
            if extension == "rnx" and filenamePrefix == f"nav_site{siteno}":
                firstDatetimeStr = filenameEpochRange.split("-")[0]
                firstDatetime = datetime.strptime(firstDatetimeStr, "%Y_%m_%d_%H_%M_%S")
                navFileDict[firstDatetime] = f"{navfiledir}/{filepath}"
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

    return obsFileDict, navFileDict, azielevFileDict

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