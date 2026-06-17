import sys
import os
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
from constUBXtoRNXconv import UBXtoRNX, mkconv
from const_gnssvod_oneSite_copy import RNXtoIMG
from collections import deque

i = 1
quit = False
conv = mkconv()
rnxDeleteQ = deque()
azielevDeleteQ = deque()

if len(sys.argv) > 2:
	waitTime = int(sys.argv[1])
	epochInterval = int(sys.argv[2])
elif len(sys.argv) > 1:
	waitTime = int(sys.argv[1])
else:
	waitTime = 60
	epochInterval = 10

while not quit:
	rnxFilename = ""
	azielevFilename = ""

	rnxFilename, azielevFilename, conv, quit = UBXtoRNX(conv, i, waitTime=waitTime, epochInterval=epochInterval)
	rnxDeleteQ.append(rnxFilename)
	azielevDeleteQ.append(azielevFilename)
	i += 1

	RNXtoIMG(rnxFilename)
	
	# AFTER FIRST TURN ONLY
	if i > 1:
		rnxDelete = rnxDeleteQ.popleft()
		azielevDelete = azielevDeleteQ.popleft()
		
		print(f"Deleting RINEX file at: {rnxDelete}")
		print(f"Deleting AZIELEV file at: {azielevDelete}")
		
		if os.path.exists(rnxDelete):
			os.remove(rnxDelete)
		else:
			print(f"Warning: RINEX file to DELETE could not be found at {rnxDelete}")

		if os.path.exists(azielevDelete):
			os.remove(azielevDelete)
		else:
			print(f"Warning: AZIELEV file to DELETE could not be found at {azielevDelete}")
	
