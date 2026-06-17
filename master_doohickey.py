import sys
import os
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
from constUBXtoRNXconv import UBXtoRNX, mkconv
from const_gnssvod_oneSite import RNXtoIMG

i = 1
quit = False
conv = mkconv()
rnxDeleteQ = []
azielevDeleteQ = []

if len(sys.argv) > 2:
	waitTime = int(sys.argv[1])
	epochInterval = int(sys.argv[2])
elif len(sys.argv) > 1:
	waitTime = int(sys.argv[1])
else:
	waitTime = 60
	epochInterval = 10

#rnxFilename, azielevFilename, conv, quit = UBXtoRNX(i, waitTime=waitTime, epochInterval=epochInterval)

while not quit:
	rnxFilename = ["",""]
	azielevFilename = ["",""]

	rnxFilename[0], azielevFilename[0], conv, quit = UBXtoRNX(conv, i, waitTime=waitTime, epochInterval=epochInterval)
	rnxDeleteQ.append(rnxFilename[0])
	azielevDeleteQ.append(azielevFilename[0])
	i += 1

	rnxFilename[1], azielevFilename[1], conv, quit = UBXtoRNX(conv, i, waitTime=waitTime, epochInterval=epochInterval)
	rnxDeleteQ.append(rnxFilename[1])
	azielevDeleteQ.append(azielevFilename[1])
	i += 1
	
	if i > 6:
		rnxDelete = rnxDeleteQ.pop()
		azielevDelete = azielevDeleteQ.pop()
		if os.path.exists(rnxDelete):
			os.remove(rnxDelete)
		else:
			print(f"Warning: RINEX file to DELETE could not be found at {rnxDelete}")

		if os.path.exists(azielevDelete):
			os.remove(azielevDelete)
		else:
			print(f"Warning: AZIELEV file to DELETE could not be found at {azielevDelete}")

	RNXtoIMG(rnxFilename, azielevFilename)
	
