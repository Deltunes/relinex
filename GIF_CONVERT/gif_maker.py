import os
import subprocess

# Scale scatter plots for GIF conversion
fileno = 1
imgPath = f"IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}.png"
print("Scaling scatter plot images")
while os.path.exists(imgPath):
    #print(f"Scatter {fileno}")
    scaleCMD = f"ffmpeg -hide_banner -loglevel error -i IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}.png -vf scale=600:600 IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}S.png -y"
    delCMD = f"rm IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}.png"
    renameCMD = f"mv IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}S.png IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}.png"

    scaleCMD = scaleCMD.split(" ")
    delCMD = delCMD.split(" ")
    renameCMD = renameCMD.split(" ")

    subprocess.run(scaleCMD)
    subprocess.run(delCMD)
    subprocess.run(renameCMD)

    fileno += 1
    imgPath = f"IMAGE_SUCCESS/scatter/plot_oneSite_success{fileno}.png"

# Scale hemi plots for GIF conversion
fileno = 1
imgPath = f"IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}.png"
print("Scaling hemi plot images")
while os.path.exists(imgPath):
    #print(f"Hemi {fileno}")
    scaleCMD = f"ffmpeg -hide_banner -loglevel error -i IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}.png -vf scale=600:600 IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}S.png -y"
    delCMD = f"rm IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}.png"
    renameCMD = f"mv IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}S.png IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}.png"

    scaleCMD = scaleCMD.split(" ")
    delCMD = delCMD.split(" ")
    renameCMD = renameCMD.split(" ")

    subprocess.run(scaleCMD)
    subprocess.run(delCMD)
    subprocess.run(renameCMD)

    fileno += 1
    imgPath = f"IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success{fileno}.png"


scatterPaletteCMD = "ffmpeg -hide_banner -loglevel error -i IMAGE_SUCCESS/scatter/plot_oneSite_success%d.png -vf palettegen GIF_SUCCESS/palettes/palette_oneSite_scatter.png -y"
hemiPaletteCMD = "ffmpeg -hide_banner -loglevel error -i IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success%d.png -vf palettegen GIF_SUCCESS/palettes/palette_oneSite_hemi.png -y"
scatterGIFCMD = "ffmpeg -hide_banner -loglevel error -framerate 8 -i IMAGE_SUCCESS/scatter/plot_oneSite_success%d.png -i GIF_SUCCESS/palettes/palette_oneSite_scatter.png -filter_complex paletteuse GIF_SUCCESS/gifs/plot_oneSite_scatter.gif -y"
hemiGIFCMD = "ffmpeg -hide_banner -loglevel error -framerate 8 -i IMAGE_SUCCESS/hemi/plot_oneSite_hemi_success%d.png -i GIF_SUCCESS/palettes/palette_oneSite_hemi.png -filter_complex paletteuse GIF_SUCCESS/gifs/plot_oneSite_hemi.gif -y"

scatterPaletteCMD = scatterPaletteCMD.split(" ")
hemiPaletteCMD = hemiPaletteCMD.split(" ")
scatterGIFCMD = scatterGIFCMD.split(" ")
hemiGIFCMD = hemiGIFCMD.split(" ")

print("Creating scatter plot palette")
subprocess.run(scatterPaletteCMD)
print("Creating hemi plot palette")
subprocess.run(hemiPaletteCMD)
print("Creating scatter plot GIF")
subprocess.run(scatterGIFCMD)
print("Creating hemi plot GIF")
subprocess.run(hemiGIFCMD)

print("Program complete! GIFs made.")