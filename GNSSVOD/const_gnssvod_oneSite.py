import gnssvod as gv
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection

def RNXtoIMG(rnxFilepath):
	# Get name of file, no format
	rnxFilename = rnxFilepath.split("/")[-1].split(".")[0]

	# Preprocess RINEX data to netCDF file
	pattern = {'rnxfile1':f'{rnxFilepath}'}
	outputdir = {'rnxfile1':'GNSSVOD/nc/'}
	keepvars = ['S?','S??']
	gv.preprocess(pattern, interval='1s', keepvars=keepvars, outputdir=outputdir, overwrite=True)

	# Open and sort netCDF file
	print("Opening nc dataset")
	ds = xr.open_mfdataset(f"GNSSVOD/nc/{rnxFilename}.nc",combine='nested',concat_dim='Epoch',join='outer')
	df = ds.to_dataframe().dropna(how='all').sort_index()

	# Plotting netCDF data
	# ALL SATELLITES, ONE SITE
	print("Plotting Data")
	station_name = 'rnxfile1'
	
	# initialize figure with polar axes
	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))

	# polar plots need a radius and theta direction in radians
	radius = 90-df.Elevation
	theta = np.deg2rad(df.Azimuth)
		
	# plot each measurement and color by signal to noise ratio
	for j in df.columns.tolist():
		if j[0] == 'S':
			hs = ax.scatter(theta,radius,c=df[j])
	ax.set_rlim([0,90])
	ax.set_theta_zero_location("N")

	plt.colorbar(hs, shrink=0.5, label='SNR (L1)')
	plt.title(station_name)
	
	#plt.savefig(f"IMAGE_SUCCESS/scatter/plot_oneSite.png")
	plt.savefig("IMAGE_SUCCESS/plot_oneSite.png")
	plt.savefig(f"IMAGE_SUCCESS/scatter/plot_oneSite_{rnxFilename}.png")

	hemi = gv.hemibuild(4)
	patches = hemi.patches()

	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))
	pc = PatchCollection(patches.values,facecolor='none',linewidth=1)

	ax.add_collection(pc)
	ax.set_rlim([0,90])
	ax.set_theta_zero_location("N")

	newdf = hemi.add_CellID(df)

	hemi_average = newdf.groupby('CellID').mean()

	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))

	# associate the mean values to the patches, join inner will drop patches with no data, making plotting slightly faster
	ipatches = pd.concat([patches,hemi_average],join='inner',axis=1)

	# plotting with colored patches
	Sfreq = []
	for k in df.columns.tolist():
		if k[0] == 'S':
			Sfreq.append(k)
	df['SNR_mean'] = Sfreq.mean(axis=1)

	pc = PatchCollection(ipatches.Patches,array=ipatches['SNR_mean'],edgecolor='face',linewidth=1)
	
	pc.set_clim([25,50])
	ax.add_collection(pc)
	ax.set_rlim([0,90])
	ax.set_theta_zero_location("N")
	ax.set_title(station_name)
	plt.colorbar(pc, ax=ax, location='bottom', shrink=0.5, pad=0.05, label='SNR (L1)')

	#plt.savefig('IMAGE_SUCCESS/hemi/plot_oneSite_hemi.png',facecolor='white',transparent=False,bbox_inches='tight')
	plt.savefig("IMAGE_SUCCESS/plot_oneSite_hemi.png",facecolor='white',transparent=False,bbox_inches='tight')
	plt.savefig(f"IMAGE_SUCCESS/hemi/plot_oneSite_hemi_{rnxFilename}.png",facecolor='white',transparent=False,bbox_inches='tight')
	plt.close()
