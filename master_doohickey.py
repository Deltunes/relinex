import sys
import asyncio
sys.path.insert(1, 'UBXtoRNX')
sys.path.insert(2, 'GNSSVOD')
#from constUBXtoRNXconv import UBXtoRNX
from constUBXtoRNXconv import UBXtoRNX, mkconv
from const_gnssvod_oneSite import RNXtoIMG

i = 1
quit = False
conv = mkconv()

if len(sys.argv) > 2:
	waitTime = int(sys.argv[1])
	epochInterval = int(sys.argv[2])
elif len(sys.argv) > 1:
	waitTime = int(sys.argv[1])
else:
	waitTime = 60
	epochInterval = 10

#rnxFilename, azimelevFilename, conv, quit = UBXtoRNX(i, waitTime=waitTime, epochInterval=epochInterval)

while not quit:
    rnxFilename, azimelevFilename, conv, quit = UBXtoRNX(conv, i, waitTime=waitTime, epochInterval=epochInterval)
    i += 1

    RNXtoIMG(rnxFilename, azimelevFilename)
    
