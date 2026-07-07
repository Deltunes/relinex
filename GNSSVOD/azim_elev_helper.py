import pandas as pd

def azim_elev_fromFile(epochRange):
	masterOutputFile = open("masterOutputPath.txt", "r", encoding="utf-8")
	masterOutputPath = masterOutputFile.readline()
	masterOutputFile.close()
	azimElevFilename = f"{masterOutputPath}/RNX_SUCCESS/concat/azimuth&elevation_{epochRange}.txt"
	azimElevFile = open(azimElevFilename, "r", encoding="utf-8")
	azimElevData = azimElevFile.readlines()
	azimElevFile.close()

	epochs = []

	for line in azimElevData:
		if line[0] == ">":
			epoch = ""
			epochSplit = line.strip("\n").split("/")
			epoch = f"{epochSplit[1]}-{epochSplit[2]}-{epochSplit[3]} {epochSplit[4]}:{epochSplit[5]}:{epochSplit[6]}"
		else:
			info = line.strip().split("/")
			sv = info[0]
			azim = float(info[1])
			elev = float(info[2])
			
			epochs.append(
				{
					'Epoch': pd.Timestamp(epoch),
					'SV': sv,
					'Azimuth': azim,
					'Elevation': elev
				}
			)
	azimElevDataframe = pd.DataFrame(epochs).set_index(['Epoch', 'SV'])
	return azimElevDataframe
