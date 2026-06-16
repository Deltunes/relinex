"""
calc_vod calculates VOD according to specified pairing rules
"""
# ===========================================================
# ========================= imports =========================
import numpy as np
import pandas as pd
import xarray as xr
from gnssvod.io.preprocessing import get_filelist
#-----------------------------------------------------
#----------------- CALCULATING VOD -------------------
#-----------------------------------------------------

def calc_vod(filepattern: str,
             pairings: dict[str, tuple[str, str]],
             bands: dict[str, list[str]]) -> dict[str, pd.DataFrame]:
    """
    Calculate Vegetation Optical Depth (VOD) from processed GNSS observations.

    This function combines multiple NetCDF files containing
    paired GNSS receiver observations (typically generated with
    :func:`gnssvod.gather_stations`) and computes VOD for user-defined
    frequency bands.

    Each band corresponds to a list of observation types (e.g., 'S1', 'S1X', 'S1C')
    across satellites. The function merges all available signals in the band
    to produce a single VOD estimate per band, increasing coverage.

    Parameters
    ----------
    filepattern : str
        UNIX-style pattern to locate preprocessed NetCDF files for a case.
        Example: '/path/to/files/of/case1/\*.nc'

    pairings : dict
        Dictionary mapping case names to tuples of station names, indicating
        the reference station and the ground station, respectively.
        Example: {'Laeg1': ('Laeg2_Twr', 'Laeg1_Grnd')}

    bands : dict
        Dictionary mapping VOD band names to lists of observation types
        to merge. For instance, {'VOD_L1': ['S1', 'S1X', 'S1C']}.

        The function combines all matched observation
        types across satellites.

    Returns
    -------
    dict
        Dictionary mapping case names to :class:`pandas.DataFrame` objects.
        Each DataFrame contains the original measurements along with additional
        columns for each VOD band.

    Example
    -------
    .. code-block:: python

        files = "/path/to/gathered/data/*.nc"

        pairings = {
            "case1": ("Ref1", "Grnd1"),
            "case2": ("Ref1", "Grnd2"),
        }

        bands = {
            "VOD_L1": ["S1", "S1X"],
            "VOD_L2": ["S2", "S2X"],
        }

        vod_results = calc_vod(files, pairings, bands)
    """
    files = get_filelist({'':filepattern})
    # read in all data
    data = [xr.open_mfdataset(x).to_dataframe().dropna(how='all') for x in files['']]
    # concatenate
    data = pd.concat(data)
    # Check that all stations in pairings exist in the loaded data
    all_stations = set(data.index.get_level_values('Station'))
    for case_name, (ref_station, grnd_station) in pairings.items():
        missing = [s for s in (ref_station, grnd_station) if s not in all_stations]
        if missing:
            raise ValueError(
                f"Missing station(s) {missing} in loaded data for case '{case_name}'. "
                f"Available stations: {sorted(all_stations)}"
            )
    # calculate VOD based on pairings
    out = dict()
    for icase in pairings.items():
        iref = data.xs(icase[1][0],level='Station')
        igrn = data.xs(icase[1][1],level='Station')
        idat = iref.merge(igrn,on=['Epoch','SV'],suffixes=['_ref','_grn'])
        for ivod in bands.items():
            ivars = np.intersect1d(data.columns.to_list(),ivod[1])
            for ivar in ivars:
                irefname = f"{ivar}_ref"
                igrnname = f"{ivar}_grn"
                ielename = f"Elevation_grn"
                idat[ivar] = -np.log(np.power(10,(idat[igrnname]-idat[irefname])/10)) \
                            *np.cos(np.deg2rad(90-idat[ielename]))
            
            idat[ivod[0]] = np.nan
            for ivar in ivars:
                idat[ivod[0]] = idat[ivod[0]].fillna(idat[ivar])

        idat = idat[list(bands.keys())+['Azimuth_ref','Elevation_ref']].rename(columns={'Azimuth_ref':'Azimuth','Elevation_ref':'Elevation'})
        # store result in dictionary
        out[icase[0]]=idat
    return out
