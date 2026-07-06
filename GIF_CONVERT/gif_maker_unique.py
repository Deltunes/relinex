import os
import sys
import subprocess
from datetime import datetime
#import glob
sys.path.insert(1, 'CONCAT_FILES')
from concatData_gif_copy import concatFilelist

def getFilelist(imgfiledir: str):
    fileset = dict()
    for filename in os.listdir(imgfiledir):
        if filename != ".gitkeep":
            filenameEpochRange = filename.split(".")[0][-39:].split("-")
            lastDatetime = datetime.strptime(filenameEpochRange[1], "%Y_%m_%d_%H_%M_%S")
            fileset[lastDatetime] = filename.split(".")[0]
    
    sortedFileset = []
    for tuple in sorted(fileset.items()):
        sortedFileset.append(tuple[1])

    return sortedFileset

def makeGIF():
    # Scale scatter plots for GIF conversion
    fileset = getFilelist("IMAGE_SUCCESS/scatter/")

    print("Scaling scatter plot images")
    for filename in fileset:
        print(filename)
        scaleCMD = f"ffmpeg -hide_banner -loglevel error -i IMAGE_SUCCESS/scatter/{filename}.png -vf scale=600:600 IMAGE_SUCCESS/scatter/{filename}S.png -y"
        delCMD = f"rm IMAGE_SUCCESS/scatter/{filename}.png"
        renameCMD = f"mv IMAGE_SUCCESS/scatter/{filename}S.png IMAGE_SUCCESS/scatter/{filename}.png"

        scaleCMD = scaleCMD.split(" ")
        delCMD = delCMD.split(" ")
        renameCMD = renameCMD.split(" ")

        subprocess.run(scaleCMD)
        subprocess.run(delCMD)
        subprocess.run(renameCMD)

    # Scale hemi plots for GIF conversion
    fileset = getFilelist("IMAGE_SUCCESS/hemi/")

    print("Scaling hemi plot images")
    for filename in fileset:
        print(filename)
        scaleCMD = f"ffmpeg -hide_banner -loglevel error -i IMAGE_SUCCESS/hemi/{filename}.png -vf scale=600:600 IMAGE_SUCCESS/hemi/{filename}S.png -y"
        delCMD = f"rm IMAGE_SUCCESS/hemi/{filename}.png"
        renameCMD = f"mv IMAGE_SUCCESS/hemi/{filename}S.png IMAGE_SUCCESS/hemi/{filename}.png"

        scaleCMD = scaleCMD.split(" ")
        delCMD = delCMD.split(" ")
        renameCMD = renameCMD.split(" ")

        subprocess.run(scaleCMD)
        subprocess.run(delCMD)
        subprocess.run(renameCMD)

    scatterPaletteCMD = 'ffmpeg -hide_banner -loglevel error -pattern_type glob -i "IMAGE_SUCCESS/scatter/plot_oneSite_success_*.png" -vf palettegen GIF_SUCCESS/palettes/palette_oneSite_scatter.png -y'
    hemiPaletteCMD = 'ffmpeg -hide_banner -loglevel error -pattern_type glob -i "IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success_*.png" -vf palettegen GIF_SUCCESS/palettes/palette_oneSite_hemi.png -y'
    scatterGIFCMD = 'ffmpeg -hide_banner -loglevel error -framerate 8 -pattern_type glob -i "IMAGE_SUCCESS/scatter/plot_oneSite_success_*.png" -i GIF_SUCCESS/palettes/palette_oneSite_scatter.png -filter_complex paletteuse GIF_SUCCESS/gifs/plot_oneSite_scatter.gif -y'
    hemiGIFCMD = 'ffmpeg -hide_banner -loglevel error -framerate 8 -pattern_type glob -i "IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success_*.png" -i GIF_SUCCESS/palettes/palette_oneSite_hemi.png -filter_complex paletteuse GIF_SUCCESS/gifs/plot_oneSite_hemi.gif -y'

    print("Creating scatter plot palette")
    subprocess.run(scatterPaletteCMD, shell=True)
    print("Creating hemi plot palette")
    subprocess.run(hemiPaletteCMD, shell=True)
    print("Creating scatter plot GIF")
    subprocess.run(scatterGIFCMD, shell=True)
    print("Creating hemi plot GIF")
    subprocess.run(hemiGIFCMD, shell=True)

    print("Program complete! GIFs made.")

concatFilelist("RNX_SUCCESS/rinex", "RNX_SUCCESS/azielev")
makeGIF()