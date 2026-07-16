from pynmeagps.nmeahelpers import wnotow2utc
from datetime import datetime
import os

azielevData = open("azielev.txt", "w", encoding="utf-8")
azielevData.write("")
azielevData.close()

elevationData = open("sat_elevation_test3.csv", "r", encoding="utf-8")
elevationLines = elevationData.readlines()
elevationData.close()

prev_wnotow = datetime.min
epochFirst = datetime.max
epochLast = datetime.min
for line in elevationLines[1:]:
    lineSplit = line.split(",")
    wno = int(lineSplit[0])
    tow = int(lineSplit[1])
    satID = lineSplit[2]
    azi = int(float(lineSplit[3]))
    elev = int(float(lineSplit[4]))

    wnotow = wnotow2utc(wno, tow, autoroll=True, modwno=True).replace(tzinfo=None)

    if wnotow < epochFirst:
        epochFirst = wnotow
    if wnotow > epochLast:
        epochLast = wnotow

    azielevData = open("azielev.txt", "a", encoding="utf-8")
    if (wnotow > prev_wnotow):
        prev_wnotow = wnotow
        azielevData.write(f">/{wnotow.strftime("%Y/%m/%d/%H/%M/%S")}\n")
    azielevData.write(f"{satID}/{azi}/{elev}\n")
    azielevData.close()

epochFirst = epochFirst.strftime("%Y_%m_%d_%H_%M_%S")
epochLast = epochLast.strftime("%Y_%m_%d_%H_%M_%S")

os.rename("azielev.txt", f"azielev_{epochFirst}-{epochLast}.txt")
