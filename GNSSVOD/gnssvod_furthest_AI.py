import xarray as xr
import pandas as pd

def load_nc_as_df(ncPath):
	"""
	Open a preprocessed gnssvod netCDF file and return a tidy dataframe with
	Epoch, SV (satellite), Azimuth, Elevation, and SNR columns as plain columns
	(not index levels), sorted by time.
	"""
	ds = xr.open_mfdataset(ncPath, combine='nested', concat_dim='Epoch', join='outer')
	df = ds.to_dataframe().dropna(how='all')

	# Bring index levels (Epoch, SV, etc.) out as columns so merge_asof/groupby are simple
	df = df.reset_index()

	# Compute a single SNR value per observation by averaging all S? / S?? columns present
	Sfreq = [c for c in df.columns if c[0] == 'S' and c not in ('SV',)]
	df['SNR_mean'] = df[Sfreq].mean(axis=1)

	df = df.sort_values('Epoch')
	return df

def find_lowest_elevation_detection(df, receiver_label=""):
	valid = df[(df['Elevation'] >= 0) & (df['Elevation'] <= 90)]
	idx_min = valid['Elevation'].idxmin()
	row = valid.loc[idx_min]

	print(f"{receiver_label}: lowest elevation detected = {row['Elevation']:.2f} deg "
		  f"(SV {row['SV']}, Azimuth {row['Azimuth']:.2f} deg, Epoch {row['Epoch']})")

	return row


def compare_lowest_elevation(df_sdr, df_ublox):
	"""
	Compare the lowest-elevation (furthest) satellite detection between the
	SDR and uBlox receivers.
	"""
	row_sdr = find_lowest_elevation_detection(df_sdr, receiver_label="SDR")
	row_ublox = find_lowest_elevation_detection(df_ublox, receiver_label="uBlox")

	if row_sdr['Elevation'] < row_ublox['Elevation']:
		print(f"\nSDR tracked a lower-elevation (more distant) satellite "
			  f"by {row_ublox['Elevation'] - row_sdr['Elevation']:.2f} degrees")
	elif row_ublox['Elevation'] < row_sdr['Elevation']:
		print(f"\nuBlox tracked a lower-elevation (more distant) satellite "
			  f"by {row_sdr['Elevation'] - row_ublox['Elevation']:.2f} degrees")
	else:
		print("\nBoth receivers tracked the same lowest elevation")

	return row_sdr, row_ublox

sdr_ncPath="GNSSVOD/nc/obs_site53_2026_07_22_14_55_35-2026_07_22_20_25_19.nc"
ublox_ncPath="GNSSVOD/nc/obs_site52_2026_07_22_14_52_18-2026_07_22_20_17_14.nc"

df1 = load_nc_as_df(sdr_ncPath)
df2 = load_nc_as_df(ublox_ncPath)

row1, row2 = compare_lowest_elevation(df1, df2)