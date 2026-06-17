import gnssvod as gv
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.dates as mdates
import datetime

def readFileDate():
	datetimeFilename = f"RNX_SUCCESS/azielev/azimuth&elevation1.txt"
	datetimeFile = open(datetimeFilename, "r", encoding="utf-8")
	datetimeData = datetimeFile.readline()
	datetimeSplit = datetimeData.split("/")
	fileDatetime = f"{datetimeSplit[1]}-{datetimeSplit[2]}-{datetimeSplit[3]} {datetimeSplit[4]}:{datetimeSplit[5]}:{datetimeSplit[6]}"
	return fileDatetime

def RNXtoIMG(rnxFilename, azimelevFilename):
	pattern = {'rnxfile1':f'{rnxFilename[0]}',
			  'rnxfile2':f'{rnxFilename[1]}'}
	#pattern = {'rnxfile1':f'{rnxFilename}',
	#		  'fodder%':'RNX_SUCCESS/rinex/fodder%.rnx'}

	outputdir = {'rnxfile1':'GNSSVOD/nc/',
				'rnxfile2':'GNSSVOD/nc/'}
	#outputdir = {'rnxfile1':'GNSSVOD/nc/',
	#			'fodder%':'GNSSVOD/nc/'}

	keepvars = ['S?','S??']

	result = gv.preprocess(pattern, interval='1s', keepvars=keepvars, outputdir=outputdir, overwrite=True)

	pattern={'rnxfile1':'GNSSVOD/nc/success1.nc', 
			'rnxfile2':'GNSSVOD/nc/success2.nc'}
	#pattern={'rnxfile1':'GNSSVOD/nc/success1.nc', 
	#		'fodder%':'GNSSVOD/nc/fodder%.nc'}

	# get time range
	startday = pd.to_datetime(readFileDate())
	timeintervals=pd.interval_range(start=startday, periods=2, freq='D', closed='left')

	# define how to make pairs, always give reference station first, matching the dictionary keys of 'pattern'
	pairings={'gnssvod_test':('rnxfile1','rnxfile2')}
	#pairings={'gnssvod_test':('rnxfile1','fodder%')}

	# define where to save output data, matching the dictionary keys in 'pairings'
	outputdir = {'gnssvod_test':'GNSSVOD/nc2/'}

	# define which variables to keep
	keepvars = ['S*','Azimuth','Elevation']

	# run function
	out = gv.gather_stations(pattern,pairings,timeintervals,keepvars=keepvars,outputdir=outputdir)

	print("Opening nc2 dataset")
	ds = xr.open_mfdataset('GNSSVOD/nc2/*.nc',combine='nested',concat_dim='Epoch',join='outer')
	#ds = xr.open_mfdataset('GNSSVOD/nc2/*.nc',combine='nested',concat_dim='Epoch')

	df = ds.to_dataframe().dropna(how='all').reorder_levels(["Station","Epoch","SV"]).sort_index()

	# ALL SATELLITES, ONE SITE\
	print("Subsetting Dataframe")
	station_name = 'rnxfile1'
	subdf = df.xs(station_name,level='Station')
	
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
	plt.savefig("IMAGE_SUCCESS/plot_oneSite.png")

	hemi = gv.hemibuild(4)
	patches = hemi.patches()

	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))
	pc = PatchCollection(patches.values,facecolor='none',linewidth=1)
	ax.add_collection(pc)
	ax.set_rlim([0,90])
	ax.set_theta_zero_location("N")

	newdf = hemi.add_CellID(df)

	hemi_average = newdf.groupby(['CellID','Station']).mean()

	fig, ax = plt.subplots(figsize=(7,7),subplot_kw=dict(projection='polar'))

	# associate the mean values to the patches, join inner will drop patches with no data, making plotting slightly faster
	ipatches = pd.concat([patches,hemi_average.xs(station_name, level='Station')],join='inner',axis=1)

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
	plt.savefig('IMAGE_SUCCESS/plot_oneSite_hemi.png',facecolor='white',transparent=False,bbox_inches='tight')
	plt.close()
