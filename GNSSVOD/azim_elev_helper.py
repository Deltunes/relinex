import pandas as pd

def azim_elev_fromFile(epochRange, filepath):
	# Open azimuth/elevation file from epoch range
	azimElevFilename = f"{filepath}/azielev/azielev_{epochRange}.txt"
	azimElevFile = open(azimElevFilename, "r", encoding="utf-8")
	azimElevData = azimElevFile.readlines()
	azimElevFile.close()


	epochs = []
	for line in azimElevData:
		# Find lines with epoch
		if line[0] == ">":
			epoch = ""
			epochSplit = line.strip("\n").split("/")
			epoch = f"{epochSplit[1]}-{epochSplit[2]}-{epochSplit[3]} {epochSplit[4]}:{epochSplit[5]}:{epochSplit[6]}"
		else:
			# Satellite data lines
			info = line.strip().split("/")
			sv = info[0]
			azim = float(info[1])
			elev = float(info[2])

			# add data to epoch
			epochs.append(
				{
					'Epoch': pd.Timestamp(epoch),
					'SV': sv,
					'Azimuth': azim,
					'Elevation': elev
				}
			)

	# output azimuth/elevation data to GNSSVOD
	azimElevDataframe = pd.DataFrame(epochs).set_index(['Epoch', 'SV'])
	return azimElevDataframe
