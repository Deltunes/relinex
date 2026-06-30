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

pattern = {'rnxfile1':'RNX_SUCCESS/rinex/success1.rnx',
           'rnxfile2':'RNX_SUCCESS/rinex/success2.rnx'}

outputdir = {'rnxfile1':'RNX_SUCCESS/nc/',
             'rnxfile2':'RNX_SUCCESS/nc/'}

keepvars = ['S?','S??']

result = gv.preprocess(pattern, interval='1s', keepvars=keepvars, outputdir=outputdir, overwrite=True)

pattern={'rnxfile1':'RNX_SUCCESS/nc/success1.nc', 
         'rnxfile2':'RNX_SUCCESS/nc/success2.nc'}

# get time range
startday = pd.to_datetime(readFileDate())
timeintervals=pd.interval_range(start=startday, periods=2, freq='D', closed='left')

# define how to make pairs, always give reference station first, matching the dictionary keys of 'pattern'
pairings={'gnssvod_test':('rnxfile1','rnxfile2')}

# define where to save output data, matching the dictionary keys in 'pairings'
outputdir = {'gnssvod_test':'RNX_SUCCESS/nc2/'}

# define which variables to keep
keepvars = ['S*','Azimuth','Elevation']

# run function
out = gv.gather_stations(pattern,pairings,timeintervals,keepvars=keepvars,outputdir=outputdir)

print("Opening nc2 dataset")
ds = xr.open_mfdataset('RNX_SUCCESS/nc2/*.nc',combine='by_coords')

df = ds.to_dataframe().dropna(how='all').reorder_levels(["Station","Epoch","SV"]).sort_index()

# get all sites as list
print("Subsetting Dataframe")
station_names = df.index.get_level_values('Station').unique()

# ensure we use the same color limits in all plots
clim = [15,47]

# initialize figure with polar axes
fig, ax = plt.subplots(1,len(station_names),figsize=(10,10),subplot_kw=dict(projection='polar'))
for i, iname in enumerate(station_names):
    # subset the dataset
    subdf = df.xs(iname,level='Station')

    # polar plots need a radius and theta direction in radians
    radius = 90-subdf.Elevation
    theta = np.deg2rad(subdf.Azimuth)

    # plot each measurement and color by signal to noise ratio
    for j in subdf.columns.tolist():
        if j[0] == 'S':
            hs = ax[i].scatter(theta,radius,c=subdf[j],s=10)
        
    hs.set_clim(clim)
    ax[i].set_rlim([0,90])
    ax[i].set_theta_zero_location("N")
    ax[i].set_title(iname)

plt.colorbar(hs, ax=ax, location='bottom', shrink=.5, pad=0.05, label='SNR (L1)')
plt.savefig("plot_allSite.png")
