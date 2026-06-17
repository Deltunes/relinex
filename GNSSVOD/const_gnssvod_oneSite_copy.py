import gnssvod as gv
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.dates as mdates
import datetime

def RNXtoIMG(rnxFilepath):
	rnxFilename = rnxFilepath.split("/")[-1].split(".")[0]
	
	pattern = {'rnxfile1':f'{rnxFilepath}'}

	outputdir = {'rnxfile1':'GNSSVOD/nc/'}

	keepvars = ['S?','S??']

	gv.preprocess(pattern, interval='1s', keepvars=keepvars, outputdir=outputdir, overwrite=True)

	print("Opening nc dataset")
	ds = xr.open_mfdataset('GNSSVOD/nc/success1.nc',combine='nested',concat_dim='Epoch',join='outer')

	df = ds.to_dataframe().dropna(how='all').sort_index()

	# ALL SATELLITES, ONE SITE\
	print("Subsetting Dataframe")
	station_name = 'rnxfile1'
	subdf = df
	
	# initialize figure with polar axes
	print("Plot setup")
	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))

	# polar plots need a radius and theta direction in radians
	radius = 90-subdf.Elevation
	theta = np.deg2rad(subdf.Azimuth)
		
	# plot each measurement and color by signal to noise ratio
	for j in subdf.columns.tolist():
		if j[0] == 'S':
			hs = ax.scatter(theta,radius,c=subdf[j])
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
	for k in subdf.columns.tolist():
		if k[0] == 'S':
			pc = PatchCollection(ipatches.Patches,array=ipatches[k],edgecolor='face',linewidth=1)
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
