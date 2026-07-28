import os
import sys
import subprocess
from datetime import datetime
sys.path.insert(1, 'CONCAT_FILES')
from concatData_gif import concatFilelist

# Collect filelist at image file directory
def getFilelist(imgfiledir: str):
    fileset = dict()
    for filepath in os.listdir(imgfiledir):
        # Collect filenames in dict with second epoch as key
        if filepath != ".gitkeep":
            filenameSplit = filepath.split(".")
            filename = filenameSplit[0]
            filenameEpochRange = "_".join(filename.split("_")[2:])
            lastDatetime = datetime.strptime(filenameEpochRange.split("-")[1], "%Y_%m_%d_%H_%M_%S")
            fileset[lastDatetime] = filename.split(".")[0]

    # Sort directory into list of filenames sorted by datetime
    sortedFileset = []
    for tuple in sorted(fileset.items()):
        sortedFileset.append(tuple[1])

    return sortedFileset

def makeGIF(siteno, dir, outputPath="."):
    # Concat files before PNG conversion
    concatFilelist(siteno, f"{outputPath}/{dir}/site{siteno}", outputPath)

    # Scale scatter plots for GIF conversion
    scatterFilepath = f"{outputPath}/IMAGE_SUCCESS/site{siteno}/scatter"
    fileset = getFilelist(scatterFilepath)

    # Scale images
    print("Scaling scatter plot images")
    for filename in fileset:
        scaleCMD = f"ffmpeg -hide_banner -loglevel error -i {scatterFilepath}/{filename}.png -vf scale=600:600 {scatterFilepath}/{filename}S.png -y"
        delCMD = f"rm {scatterFilepath}/{filename}.png"
        renameCMD = f"mv {scatterFilepath}/{filename}S.png {scatterFilepath}/{filename}.png"

        scaleCMD = scaleCMD.split(" ")
        delCMD = delCMD.split(" ")
        renameCMD = renameCMD.split(" ")

        subprocess.run(scaleCMD)
        subprocess.run(delCMD)
        subprocess.run(renameCMD)

    # Scale hemi plots for GIF conversion
    hemiFilepath = f"{outputPath}/IMAGE_SUCCESS/site{siteno}/hemi"
    fileset = getFilelist(hemiFilepath)

    print("Scaling hemi plot images")
    for filename in fileset:
        print(filename)
        scaleCMD = f"ffmpeg -hide_banner -loglevel error -i {hemiFilepath}/{filename}.png -vf scale=600:600 {hemiFilepath}/{filename}S.png -y"
        delCMD = f"rm {hemiFilepath}/{filename}.png"
        renameCMD = f"mv {hemiFilepath}/{filename}S.png {hemiFilepath}/{filename}.png"

        scaleCMD = scaleCMD.split(" ")
        delCMD = delCMD.split(" ")
        renameCMD = renameCMD.split(" ")

        subprocess.run(scaleCMD)
        subprocess.run(delCMD)
        subprocess.run(renameCMD)

    # Create palettes for GIF conversion
    scatterPaletteCMD = f'ffmpeg -hide_banner -loglevel error -pattern_type glob -i "{scatterFilepath}/plot_oneSite_*.png" -vf palettegen {outputPath}/GIF_SUCCESS/site{siteno}/palettes/palette_oneSite_scatter.png -y'
    hemiPaletteCMD = f'ffmpeg -hide_banner -loglevel error -pattern_type glob -i "{hemiFilepath}/plot_oneSite_hemi_*.png" -vf palettegen {outputPath}/GIF_SUCCESS/site{siteno}/palettes/palette_oneSite_hemi.png -y'

    print("Creating scatter plot palette")
    subprocess.run(scatterPaletteCMD, shell=True)
    print("Creating hemi plot palette")
    subprocess.run(hemiPaletteCMD, shell=True)

    # Create GIFs with images and image palette
    scatterGIFCMD = f'ffmpeg -hide_banner -loglevel error -framerate 8 -pattern_type glob -i "{scatterFilepath}/plot_oneSite_*.png" -i {outputPath}/GIF_SUCCESS/site{siteno}/palettes/palette_oneSite_scatter.png -filter_complex paletteuse {outputPath}/GIF_SUCCESS/site{siteno}/gifs/plot_oneSite_scatter.gif -y'
    hemiGIFCMD = f'ffmpeg -hide_banner -loglevel error -framerate 8 -pattern_type glob -i "{hemiFilepath}/plot_oneSite_hemi_*.png" -i {outputPath}/GIF_SUCCESS/site{siteno}/palettes/palette_oneSite_hemi.png -filter_complex paletteuse {outputPath}/GIF_SUCCESS/site{siteno}/gifs/plot_oneSite_hemi.gif -y'

    print("Creating scatter plot GIF")
    subprocess.run(scatterGIFCMD, shell=True)
    print("Creating hemi plot GIF")
    subprocess.run(hemiGIFCMD, shell=True)

    print("Program complete! GIFs made.")
    print()
