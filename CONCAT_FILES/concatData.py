import os
import subprocess

def concatFilelist(rnxFileDir: str, azielevFileDir: str):

    outputFilepath = "RNX_SUCCESS/concat"

    rnxFilelist, azielevFilelist = getFilelist(rnxFileDir, azielevFileDir)

    # RINEX CONCAT
    cmdstr = []
    cmdstr.append("./CONCAT_FILES/gfzrnx")
    cmdstr.append("-finp")

    filenoFirst = 0
    filenoLast = 0
    for rnxFilepath in rnxFilelist:
        RNXformatEdit(rnxFilepath)

        rnxFilename = rnxFilepath.split("/")[-1].split(".")[0]
        
        fileno=""
        digits="0123456789"
        for char in rnxFilename:
            if char in digits:
                fileno+=char

        if int(fileno) < filenoFirst or filenoFirst == 0:
            filenoFirst = int(fileno)
        elif int(fileno) > filenoLast or filenoLast == 0:
            filenoLast = int(fileno)


        cmdstr.append(rnxFilepath)

    cmdstr.append("-fout")
    cmdstr.append(f"RNX_SUCCESS/concat/success{filenoFirst}-{filenoLast}.rnx")
    print(f"first - {filenoFirst}")
    print(f"last - {filenoLast}")
    subprocess.run(cmdstr)
    #subprocess.run(["./concat/gfzrnx", "-finp", f"{rnxFilepath1}", f"{rnxFilepath2}", "-fout", f"concat/success{filerange}.rnx"])

    # AZIMUTH & ELEVATION CONCAT
    azielevConcat = open(f"{outputFilepath}/azimuth&elevation{filenoFirst}-{filenoLast}.txt", "w", encoding="utf-8")
    azielevConcat.write("")
    azielevConcat.close()
    for azielevFilepath in azielevFilelist:
        azielevFile = open(azielevFilepath, "r", encoding="utf-8")
        azielevData = azielevFile.read()
        azielevFile.close()

        azielevConcat = open(f"{outputFilepath}/azimuth&elevation{filenoFirst}-{filenoLast}.txt", "a", encoding="utf-8")
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

    for filename in os.listdir(azielevfiledir):
        filenameSplit = filename.split(".")
        extension = filenameSplit[-1]
        if extension == "txt" and filenameSplit[0][0:17] == "azimuth&elevation":
            #print(f"{azielevfiledir}/{filename}")
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