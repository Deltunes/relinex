import os
import subprocess
from datetime import datetime

def concatFilelist(rnxFileDir: str, azielevFileDir: str):

    outputFilepath = "RNX_SUCCESS/concat"

    rnxFilelist, azielevFilelist = getFilelist(rnxFileDir, azielevFileDir)

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
    cmdstr.append(f"RNX_SUCCESS/concat/success_{epochFirst}-{epochLast}.rnx")
    print(f"first - {epochFirst}")
    print(f"last - {epochLast}")
    subprocess.run(cmdstr)
    #subprocess.run(["./concat/gfzrnx", "-finp", f"{rnxFilepath1}", f"{rnxFilepath2}", "-fout", f"concat/success{filerange}.rnx"])

    # AZIMUTH & ELEVATION CONCAT
    azielevConcat = open(f"{outputFilepath}/azimuth&elevation_{epochFirst}-{epochLast}.txt", "w", encoding="utf-8")
    azielevConcat.write("")
    azielevConcat.close()
    for azielevFilepath in azielevFilelist:
        azielevFile = open(azielevFilepath, "r", encoding="utf-8")
        azielevData = azielevFile.read()
        print(azielevData)
        azielevFile.close()

        azielevConcat = open(f"{outputFilepath}/azimuth&elevation{epochFirst}-{epochLast}.txt", "a", encoding="utf-8")
        azielevConcat.write(azielevData)
        azielevConcat.close()

def getFilelist(rnxfiledir: str, azielevfiledir: str):
    rnxFilelist = set()
    azielevFilelist = set()
    for filename in os.listdir(rnxfiledir):
        filenameSplit = filename.split(".")
        extension = filenameSplit[-1]
        if extension == "rnx" and filenameSplit[0][0:7] == "success":
            #print(filenameSplit[0][7:])
            #print(f"{rnxfiledir}/{filename}")
            rnxFilelist.add(f"{rnxfiledir}/{filename}")

    print("TEST????")
    print(os.listdir(azielevfiledir))
    for filename in os.listdir(azielevfiledir):
        print(filename)
        filenameSplit = filename.split(".")
        extension = filenameSplit[-1]
        if extension == "txt" and filenameSplit[0][0:17] == "azimuth&elevation":
            print(f"{azielevfiledir}/{filename}")
            azielevFilelist.add(f"{azielevfiledir}/{filename}")
    
    return rnxFilelist, azielevFilelist

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


concatFilelist("RNX_SUCCESS/rinex", "RNX_SUCCESS/azielev")