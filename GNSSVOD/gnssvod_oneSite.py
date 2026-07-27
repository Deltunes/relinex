import gnssvod as gv
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection

def RNXtoIMG(obsFilepath, siteno, outputPath="."):
	# Get name of file, no format
	obsFilename = obsFilepath.split("/")[-1].split(".")[0]
	obsEpochRange = "_".join(obsFilename.split("_")[2:])

	# Preprocess RINEX data to netCDF file
	pattern = {'obsfile1':f'{obsFilepath}'}
	outputdir = {'obsfile1':f'GNSSVOD/nc/'}
	keepvars = ['S?','S??']
	gv.preprocess(pattern, interval='1s', keepvars=keepvars, outputdir=outputdir, overwrite=True)

	# Open and sort netCDF file
	print("Opening nc dataset")
	ds = xr.open_mfdataset(f"GNSSVOD/nc/{obsFilename}.nc",combine='nested',concat_dim='Epoch',join='outer')
	df = ds.to_dataframe().dropna(how='all').sort_index()

	# Plotting netCDF data
	# ALL SATELLITES, ONE SITE
	print("Plotting Data")
	
	# initialize figure with polar axes
	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))

	# polar plots need a radius and theta direction in radians
	radius = 90-df.Elevation
	theta = np.deg2rad(df.Azimuth)
		
	# plot each measurement and color by signal to noise ratio
	for j in df.columns.tolist():
		if j[0] == 'S':
			hs = ax.scatter(theta,radius,c=df[j],vmin=0,vmax=50)
	ax.set_rlim([0,90])
	ax.set_theta_zero_location("N")
	plt.title(obsEpochRange)
	plt.colorbar(hs, ax=ax, location='bottom', shrink=0.5, pad=0.05)
	
	plt.savefig(f"{outputPath}/IMAGE_SUCCESS/site{siteno}/plot_oneSite.png",bbox_inches='tight')
	plt.savefig(f"{outputPath}/IMAGE_SUCCESS/site{siteno}/scatter/plot_oneSite_{obsEpochRange}.png",bbox_inches='tight')
	plt.close(fig)

	hemi = gv.hemibuild(4)
	patches = hemi.patches()

	Sfreq = []
	for k in df.columns.tolist():
		if k[0] == 'S':
			Sfreq.append(k)
	df['SNR_mean'] = df[Sfreq].mean(axis=1)

	newdf = hemi.add_CellID(df)

	hemi_average = newdf.groupby('CellID').mean()

	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))

	# associate the mean values to the patches, join inner will drop patches with no data, making plotting slightly faster
	ipatches = pd.concat([patches,hemi_average],join='inner',axis=1)

	# plotting with colored patches
	pc = PatchCollection(ipatches.Patches,array=ipatches['SNR_mean'],edgecolor='face',linewidth=1)
	
	pc.set_clim([0,50])
	ax.add_collection(pc)
	
	ax.set_rlim([0,90])
	ax.set_theta_zero_location("N")
	ax.set_title(obsEpochRange)
	plt.colorbar(pc, ax=ax, location='bottom', shrink=0.5, pad=0.05)

	plt.savefig(f"{outputPath}/IMAGE_SUCCESS/site{siteno}/plot_oneSite_hemi.png",facecolor='white',transparent=False,bbox_inches='tight')
	plt.savefig(f"{outputPath}/IMAGE_SUCCESS/site{siteno}/hemi/plot_oneSite_hemi_{obsEpochRange}.png",facecolor='white',transparent=False,bbox_inches='tight')
	plt.close(fig)