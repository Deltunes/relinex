"""
preprocess reads files and returns analysis-ready DataSet

gather_stations merges observations from sites according to specified pairing rules over the desired time intervals
"""
# ===========================================================
# ========================= imports =========================
import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import tempfile
import fnmatch
from pathlib import Path
from typing import Union, Literal, Any
from gnssvod.io.io import Observation
from gnssvod.io.readFile import read_obsFile
from gnssvod.io.exporters import export_as_nc
from gnssvod.position.interpolation import sp3_interp_fast
from gnssvod.funcs.constants import _system_name

# CHANGED CODE HERE
from azim_elev_helper import azim_elev_fromFile

#-------------------------------------------------------------------------
#----------------- FILE SELECTION AND BATCH PROCESSING -------------------
#-------------------------------------------------------------------------
def preprocess(filepattern: dict,
               orbit: bool = True,
               interval: Union[str,pd.Timedelta,None] = None,
               keepvars: Union[list,None] = None,
               outputdir: Union[dict, None] = None,
               overwrite: bool = False,
               encoding: Union[None, Literal['default'], dict] = 'default',
               outputresult: bool = False,
               aux_path: Union[str, None] = None,
               approx_position: list[float] = None) -> dict[Any,list[Observation]]:
    """
    Reads and processes structured lists of RINEX observation files.

    Parameters
    ----------
    filepattern : dict
        Dictionary mapping station names to UNIX-style patterns matching
        RINEX observation files. For example::
        
            filepattern={'station1':'/path/to/files/of/station1/*O'}

    orbit : bool, optional
        If True, downloads orbit solutions and calculates Azimuth and
        Elevation parameters. If False, no additional GNSS parameters are
        calculated.

    interval : str, pandas.Timedelta, or None, optional
        If None, observations are returned at their original sampling rate.
        If a string or pandas.Timedelta is provided, observations are resampled
        (averaged) over that interval.

    keepvars : list of str or None, optional
        List of columns to keep after processing, reducing the size of saved data.
        If None, all columns are kept.

    outputdir : dict or None, optional
        Dictionary mapping station names to folders where preprocessed data
        should be saved. Dictionary keys must match the `filepattern` argument.
        Data are saved as NetCDF files, reusing the original filenames. If None,
        data are not saved.

    overwrite : bool, optional
        If False (default), files that already exist in the output directory are skipped.

    encoding : None, str, or dict, optional
        Controls compression and encoding options when saving NetCDF files.

        - None: no variable encodings applied.
        - "default": applies default encoding to SNR, VOD, Azimuth, and Elevation variables.

          Default encoding is::

              {
                  "dtype": "int16",
                  "scale_factor": 0.1,
                  "zlib": True,
                  "_FillValue": -9999,
              }

        - dict: per-variable encodings that are passed to :meth:`xarray.Dataset.to_netcdf`
          for fine-grained control by the user.

    outputresult : bool, optional
        If True and `outputdir` is None, observation objects are returned as a
        dictionary.

    aux_path : str or None, optional
        Directory for auxiliary orbit and clock files. If None, a temporary
        directory is created and cleaned up after processing.

    approx_position : list of float, optional
        Cartesian coordinates [X, Y, Z] of the antenna. Used if source RINEX
        files lack "APPROX POSITION XYZ" and `orbit` is True.
        To convert geographic coordinates (lat, lon, h) to Cartesian use
        :func:`gnssvod.geodesy.ell2cart`.

    Returns
    -------
    dict or None
        If `outputresult` is True, returns a dictionary with one key per
        station name. Each value is a list of GNSS observation objects read
        from the input RINEX files.

    Examples
    --------
    .. code-block:: python

        filepattern = {
            "station1": "/path/to/files/of/station1/*O",
            "station2": "/path/to/files/of/station2/*O"
        }

        interval = "15s"

        keepvars = ["S1*", "S2*", "Azimuth", "Elevation"]

        outputdir = {
            "station1": "/path/where/to/save/preprocessed/data",
            "station2": "/path/where/to/save/preprocessed/data"
        }

        output = preprocess(
            filepattern=filepattern,
            orbit=True,
            interval=interval,
            keepvars=keepvars,
            outputdir=outputdir
            outputresult=True
        )
    """
    # set up temporary directory if necessary
    if orbit and (aux_path is None):
        tmp_folder = tempfile.TemporaryDirectory()
        aux_path = tmp_folder.name
        print(f"Created a temporary directory at {aux_path}")
    else: 
        tmp_folder = None
    # grab all files matching the patterns
    stations = get_filelist(filepattern)
    
    out = dict()
    for item in stations.items():
        station_name = item[0]
        filenames = item[1]

        # checking which files will be skipped (if necessary)
        if (not overwrite) and (outputdir is not None):
            # gather all files that already exist in the outputdir
            files_to_skip = get_filelist({station_name:f"{outputdir[station_name]}*.nc"})
            files_to_skip = [os.path.basename(x) for x in files_to_skip[station_name]]
        else:
            files_to_skip = []
        
        # for each file
        result = []
        for i,filename in enumerate(filenames):
            # determine the name of the output file that will be saved at the end of the loop
            out_name = os.path.splitext(os.path.basename(filename))[0]+'.nc'
            # if the name of the saved output file is in the files to skip, skip processing
            if out_name in files_to_skip:
                print(f"{out_name} already exists, skipping.. (pass overwrite=True to overwrite)")
                continue # skip remainder of loop and go directly to next filename
            
            # read in the file
            x = read_obsFile(filename)
            print(f"Processing {len(x.observation):n} individual observations")

            # only keep required vars
            if keepvars is not None:
                x.observation = subset_vars(x.observation,keepvars)
                # update the observation_types list
                x.observation_types = x.observation.columns.to_list()

            # resample if required
            if interval is not None:
                x = resample_obs(x,interval)
                
            # calculate Azimuth and Elevation if required
            if orbit:
                # use a prescribed position if one was passed as argument
                if approx_position is not None:
                    x.approx_position = approx_position
                # check that an approximate position exists before proceeding
                if (x.approx_position == [0,0,0]) or (x.approx_position is None):
                    raise ValueError("Missing an approximate antenna position. Provide the argument 'approx_position' to preprocess()")
                print(f"Calculating Azimuth and Elevation")
                # note: orbit cannot be parallelized easily because it 
                # downloads and unzips third-party files in the current directory

                # CHANGED CODE HERE
                if not 'orbit_data' in locals():
                    # if there is no previous orbit data, the orbit data is returned as well
                    x, orbit_data = add_azi_ele(filename, x, station_name, aux_path = aux_path)
                else:
                    # on following iterations the orbit data is tentatively recycled to reduce computational time
                    x, orbit_data = add_azi_ele(filename, x, station_name, orbit_data, aux_path = aux_path)

            # make sure we drop any duplicates
            x.observation=x.observation[~x.observation.index.duplicated(keep='first')]
            
            # store result in memory if required
            if outputresult:
                result.append(x)
                
            # write to file if required
            if outputdir is not None:
                outpath = str(Path(outputdir[station_name],out_name))
                export_as_nc(ds = x.to_xarray(),
                             outpath = outpath,
                             encoding = encoding)
                print(f"Saved {len(x.observation):n} individual observations in {outpath}")

        # store station in memory if required
        if outputresult:
            out[station_name]=result

    # clean up temporary directory if one exists
    if tmp_folder is not None:
        tmp_folder.cleanup()
        print(f"Removed the temporary directory at {aux_path}")

    if outputresult:
        return out
    else:
        return

def subset_vars(df: pd.DataFrame,
                keepvars: list,
                force_epoch_system: bool = True) -> pd.DataFrame:
    """
    Subset an observation DataFrame to keep only selected columns.

    This function filters columns of a pandas DataFrame based on a list
    of variable patterns. Optionally, it ensures that the 'epoch' and
    'SYSTEM' columns are always retained, as they are required for
    computing GNSS-derived quantities such as Azimuth and Elevation.

    Parameters
    ----------
    df : pandas.DataFrame
        Observation DataFrame, typically obtained from
        :attr:`~gnssvod.io.Observation.observation`.

    keepvars : list of str
        List of variable names or patterns to keep. Pattern matching
        uses Unix shell-style wildcards (see :func:`fnmatch.filter`).

    force_epoch_system : bool, optional
        If True (default), always retain the 'epoch' and 'SYSTEM' columns
        in addition to `keepvars`. Set to False to keep only columns
        matching `keepvars`.

    Returns
    -------
    pandas.DataFrame
        Subset of `df` containing only the requested columns. Rows with
        all NaNs in the selected columns are dropped.
    """
    # find all matches for all elements of keepvars
    keepvars = np.concatenate([fnmatch.filter(df.columns.tolist(),x) for x in keepvars])
    # subselect those of the required columns that are present 
    tokeep = np.intersect1d(keepvars,df.columns.tolist())
    # + always keep 'epoch' and 'SYSTEM' as they are required for calculating azimuth and elevation
    if force_epoch_system:
        tokeep = np.unique(np.concatenate((keepvars,['epoch','SYSTEM'])))
    else:
        tokeep = np.unique(keepvars)
    # find columns not to keep
    todrop = np.setdiff1d(df.columns.tolist(),tokeep)
    # drop unneeded columns
    if len(todrop)>0:
        df = df.drop(columns=todrop)
    # drop rows for which all of the required vars are NA
    df = df.dropna(how='all')
    return df

def resample_obs(obs: Observation, interval: str) -> Observation:
    """
    Temporally resample an observation object.

    This function averages the variables in an :class:`~gnssvod.io.Observation`
    over a specified time interval while preserving the multi-index
    (Epoch/SV) structure. The 'epoch' and 'SYSTEM' columns are reconstructed
    after resampling.

    Parameters
    ----------
    obs : Observation
        Observation object to resample. Data are taken from
        :attr:`~gnssvod.io.Observation.observation`.

    interval : str
        Resampling interval as a pandas-compatible frequency string
        (e.g., '15s', '1min').

    Returns
    -------
    Observation
        The input observation object with the resampled
        :attr:`~gnssvod.io.Observation.observation` DataFrame and updated
        :attr:`~gnssvod.io.Observation.interval` (in seconds).
    """
    # list all variables except SYSTEM and epoch as these are handled differently
    subset = np.setdiff1d(obs.observation.columns.to_list(),['epoch','SYSTEM'])
    # resample those variables using temporal averaging
    obs.observation = obs.observation[subset].groupby([pd.Grouper(freq=interval, level='Epoch'),pd.Grouper(level='SV')]).mean()
    # restore SYSTEM and epoch
    obs.observation['epoch'] = obs.observation.index.get_level_values('Epoch')
    obs.observation['SYSTEM'] = _system_name(obs.observation.index.get_level_values("SV"))
    obs.interval = pd.Timedelta(interval).seconds
    return obs

def add_azi_ele(filename: str,
                obs: Observation,
                station_name,
                orbit_data: Union[pd.DataFrame,None] = None,
                aux_path: Union[str,None] = None) -> tuple[Observation,pd.DataFrame]:
    """
    Adds GNSS azimuth and elevation to an Observation object.

    This function computes Azimuth and Elevation for all measurements in the
    provided :class:`Observation` object. If necessary, it will download
    orbit and clock data to the directory specified by ``aux_path``.

    Parameters
    ----------
    obs : Observation
        The GNSS observation object to update.
    
    orbit_data : pandas.DataFrame or None, optional
        Precomputed orbit information. If provided and valid, it will be reused
        to avoid repeated downloads.

    aux_path : str or None, optional
        Directory where auxiliary orbit and clock files will be stored or
        retrieved from. If None, a temporary directory is used.

    Returns
    -------
    tuple
        A tuple containing:

        - Updated :class:`Observation` object with Azimuth and Elevation columns.
        - Orbit data used for the computation (may be newly calculated or reused from a previous call).
    """

    start_time = min(obs.observation.index.get_level_values('Epoch'))
    #print(f"START TIME - {start_time}")
    end_time = max(obs.observation.index.get_level_values('Epoch'))
    #print(f"END TIME - {end_time}")
      
    if orbit_data is None:
        do = True
    elif (orbit_data.start_time<start_time) and (orbit_data.end_time>end_time) and (orbit_data.interval==obs.interval):
        # if the orbit for the day corresponding to the epoch and interval is the same as the one that was passed, just reuse it. This drastically reduces the number of times orbit files have to be read and interpolated.
        do = False
    else:
        do = True

    # CHANGED CODE HERE
    do = False

    if do:
        # read (=usually download) orbit data
        orbit = sp3_interp_fast(start_time, end_time, interval=obs.interval, aux_path=aux_path)
        # prepare an orbit object as well
        orbit_data = orbit
        orbit_data.start_time = orbit.index.get_level_values('Epoch').min()
        orbit_data.end_time = orbit.index.get_level_values('Epoch').max()
        orbit_data.interval = obs.interval
    else:
        orbit = orbit_data
    
    # CHANGED CODE HERE
    # calculate the gnss parameters (including azimuth and elevation)
    #gnssdf = gnssDataframe(obs,orbit,cut_off=-10)
    epochRange = ""
    epochNums = False
    #digits="0123456789"
    print(filename)
    for char in filename:
        if char == ".":
            break
        if epochNums == True:
            epochRange += char
        elif char == "_" and epochNums == False:
            epochNums = True

    print(epochRange)
    azimelevdf = azim_elev_fromFile(epochRange)

    # add the gnss parameters to the observation dataframe
    obs.observation = obs.observation.join(azimelevdf)

    # CHANGED CODE HERE
    #obs.observation = obs.observation.join(gnssdf[['Azimuth','Elevation']])

    # drop variables 'epoch' and 'SYSTEM' as they are not needed anymore by gnssDataframe
    obs.observation = obs.observation.drop(columns=['epoch','SYSTEM'])
    # update the observation_types list
    obs.observation_types = obs.observation.columns.to_list()
    return obs, orbit_data


def get_filelist(filepatterns: dict) -> dict:
    """
    Retrieve lists of files matching UNIX-style patterns for one or more stations.

    Parameters
    ----------
    filepatterns : dict
        Dictionary mapping station names to file search patterns.
        Each pattern should be a valid glob expression (e.g., '\*.O').

    Returns
    -------
    dict
        Dictionary mapping each station name to a list of matching files.
        If no files match a given pattern, an empty list is returned.

    Examples
    --------
    Single station:

    .. code-block:: python

        filepatterns = {
            "station1": "/path/to/files/station1/*.O"
        }
        get_filelist(filepatterns)
        # Output:
        # {
        #     "station1": [
        #         "/path/to/files/station1/obs1.O",
        #         "/path/to/files/station1/obs2.O"
        #     ]
        # }

    Multiple stations:

    .. code-block:: python

        filepatterns = {
            "station1": "/path/to/files/station1/*.O",
            "station2": "/path/to/files/station2/*.O"
        }
        get_filelist(filepatterns)
        # Output:
        # {
        #     "station1": [
        #         "/path/to/files/station1/obs1.O",
        #         "/path/to/files/station1/obs2.O"
        #     ],
        #     "station2": [
        #         "/path/to/files/station2/obs1.O",
        #         "/path/to/files/station2/obs2.O"
        #     ]
        # }
    """
    if not isinstance(filepatterns,dict):
        raise Exception(f"Expected the input of get_filelist to be a dictionary, got a {type(filepatterns)} instead")
    filelists = dict()
    for item in filepatterns.items():
        station_name = item[0]
        search_pattern = item[1]
        flist = glob.glob(search_pattern)
        if len(flist)==0:
            print(f"Could not find any files matching the pattern {search_pattern}")
        filelists[station_name] = flist
    return filelists


#--------------------------------------------------------------------------
#----------------- PAIRING OBSERVATION FILES FROM SITES -------------------
#-------------------------------------------------------------------------- 

def gather_stations(filepattern: dict,
                    pairings: dict,
                    timeintervals: Union[pd.IntervalIndex,None] = None,
                    keepvars: Union[list,None] = None,
                    outputdir: Union[dict, None] = None,
                    encoding: Union[None, Literal['default'], dict] = None,
                    outputresult: bool = False) -> dict[Any,pd.DataFrame]:
    """
    Merge observations from different sites according to specified pairing rules.

    The returned dataframe contains a new index level corresponding to each site,
    with keys given by station names.

    Parameters
    ----------
    filepattern : dict
        Dictionary mapping station names to UNIX-style file patterns used to locate
        preprocessed NetCDF observation files. For example::

            filepattern={'station1':'/path/to/files/of/station1/*.nc','station2':'/path/to/files/of/station2/*.nc'}

    pairings : dict
        Dictionary mapping case names to tuples of station names indicating which
        stations should be gathered together. For example::

            pairings={'case1':('station1','station2')}

        If data is saved, the case name is used as the output filename.

    timeintervals : None or pandas.IntervalIndex, optional
        Time interval(s) over which data are sequentially gathered (see example below).
        Sequential processing avoids loading and pairing too much data at once.
        If ``outputdir`` is not ``None``, the interval frequency also defines how
        data are saved (e.g. daily files).
        If ``None``, all available files are used.

    keepvars : list of str or None, optional
        List of column names to keep after gathering. Helps reduce the size
        of the dataset when saving. If ``None``, no columns are removed.

    outputdir : dict or None, optional
        Dictionary mapping case names to output directories where gathered data
        should be saved. For example::

            outputdir={'case1':'/path/where/to/save/data'}

        Data are saved as NetCDF files. The dictionary must be consistent with the
        ``pairings`` argument.
        If ``None``, data are not saved.

    encoding : None, str, or dict, optional
        Controls compression and encoding options when saving NetCDF files.

        - ``None``: no variable encodings are applied.
        - ``"default"``: applies a default encoding to SNR, Azimuth, and Elevation variables.
          The default encoding is::

              {
                  "dtype": "int16",
                  "scale_factor": 0.1,
                  "zlib": True,
                  "_FillValue": -9999,
              }

        - ``dict``: per-variable encodings passed directly to
          :meth:`xarray.Dataset.to_netcdf`, allowing fine-grained customization.

    outputresult : bool, optional
        If ``True``, observation objects are also returned as a dictionary.

    Returns
    -------
    dict or None
        If ``outputresult`` is ``True``, returns a dictionary with one key per case.
        Each value is a :class:`pandas.DataFrame` containing the paired data.

    Examples
    --------
    .. code-block:: python

        filepattern = {
            "station1": "/path/to/files/of/station1/*.nc",
            "station2": "/path/to/files/of/station2/*.nc",
        }

        pairings = {
            "case1": ("station1", "station2")
        }

        timeintervals = pd.interval_range(
            start=pd.Timestamp("2018-01-01"),
            periods=8,
            freq="D"
        )

        keepvars = ["S1", "S2", "Azimuth", "Elevation"]

        outputdir = {
            "case1": "/path/where/to/save/data"
        }

        result = gather_stations(
            filepattern=filepattern,
            pairings=pairings,
            timeintervals=timeintervals,
            keepvars=keepvars,
            outputdir=outputdir,
            outputresult=True
        )
    """
    # get all files for all stations
    filenames = get_filelist(filepattern)
    print(f'Extracting Epochs from files')
    # extract only Epoch timestamps from all files (should be fast enough)
    epochs = {key:[xr.open_mfdataset(x)['Epoch'].values for x in items] for key,items in filenames.items()}
    # get min and max timestamp for each file (will be used to select which files to read later)
    epochs_min = {key:[np.min(x) for x in items] for key,items in epochs.items()}
    epochs_max = {key:[np.max(x) for x in items] for key,items in epochs.items()}
    
    result=dict()
    for case_name, station_names in pairings.items():
        out = []
        print(f'----- Processing {case_name}')
        if timeintervals is None:
            timeintervals = pd.interval_range(start=epochs_min, end=epochs_max)
        for interval in timeintervals:
            print(f'-- Processing interval {interval}')
            iout = []
            # gather all data required for that interval
            for station_name in station_names:
                # check which files have data that overlaps with the desired time intervals
                isin = [interval.overlaps(pd.Interval(left=pd.Timestamp(tmin),
                    right=pd.Timestamp(tmax))) for tmin,tmax in zip(epochs_min[station_name],epochs_max[station_name])]
                print(f'Found {sum(isin)} file(s) for {station_name}')
                if sum(isin)>0:
                    print(f'Reading')
                    # open those files and convert them to pandas dataframes
                    idata = [xr.open_mfdataset(x).to_dataframe().dropna(how='all') \
                            for x in np.array(filenames[station_name])[isin]]
                    # concatenate
                    idata = pd.concat(idata)
                    # keep only data falling within the interval
                    idata = idata.loc[[x in interval for x in idata.index.get_level_values('Epoch')]]
                    # drop duplicates and sort the dataframes
                    idata = idata[~idata.index.duplicated()].sort_index(level=['Epoch','SV'])
                    # add the station data in the iout list
                    iout.append(idata)
                else:
                    iout.append(pd.DataFrame(index=pd.MultiIndex(levels=[[], []], codes=[[], []], names=['Epoch', 'SV'])))
                    print(f"No data for station {station_name}.")
                    continue

            if not all([x.empty for x in iout]):
                print(f'Concatenating stations')
                iout = pd.concat(iout, keys=station_names, names=['Station'])

                # only keep required vars and drop potential empty rows
                if keepvars is not None:
                    iout = subset_vars(iout,keepvars,force_epoch_system=False)
                    if len(iout)==0:
                        print(f"No observations left after subsetting columns (argument 'keepvars')")
                        continue
                
                # output the data as .nc if required
                if outputdir:
                    ioutputdir = outputdir[case_name]
                    print(f'Saving result in {ioutputdir}')
                    # make destination path
                    ts = f"{interval.left.strftime('%Y%m%d%H%M%S')}_{interval.right.strftime('%Y%m%d%H%M%S')}"
                    filename = f"{case_name}_{ts}.nc"
                    outpath = str(Path(ioutputdir,filename))
                    # sort dimensions
                    ds = iout.to_xarray()
                    ds = ds.sortby(['Epoch','SV','Station'])
                    # write nc file
                    export_as_nc(ds = ds,
                        outpath = outpath,
                        encoding = encoding)
                    print(f"Saved {len(iout)} observations in {filename}")

                # add interval in memory if required
                if outputresult:
                    out.append(iout)
            else:
                print(f"No data at all for that interval, skipping..")

        # store case in memory if required
        if outputresult and len(out)>0:
            result[case_name] = pd.concat(out)

    return result
