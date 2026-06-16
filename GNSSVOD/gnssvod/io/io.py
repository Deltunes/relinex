"""
Class definitions for I/O opreations
"""
# ===========================================================
# ========================= imports =========================
import xarray as xr

# ======================================================================
class Observation:
    """
    GNSS observation object representing a RINEX (\*.\*o) file.

    This class stores the measurements, metadata, and approximate receiver
    position for a single station and observation file. Objects of this class
    are returned by preprocessing functions (e.g., :func:`gnssvod.preprocess`) 
    and are intended to be used for analysis, subsetting, or conversion to 
    :class:`xarray.Dataset`.

    Attributes
    ----------
    filename : str
        Name of the source RINEX observation file.

    epoch : datetime.datetime
        Timestamp corresponding to the last observation in the file.

    observation : pandas.DataFrame
        DataFrame containing the GNSS measurements. Indexed by
        Epoch and SV (satellite), with columns corresponding to measurement
        types (e.g., S1, S2, Azimuth, Elevation).

    approx_position : list of float
        Approximate receiver position as Cartesian coordinates [X, Y, Z].

    receiver_type : str
        Receiver type from the RINEX metadata, if available.

    antenna_type : str
        Antenna type from the RINEX metadata, if available.

    interval : float
        Measurement interval in seconds.

    receiver_clock : float
        Receiver clock offset, if provided.

    version : str
        RINEX file version.

    observation_types : list of str
        Names of the measurement types present in `observation`.

    Methods
    -------
    to_xarray()
        Converts the observation object into an :class:`xarray.Dataset` with
        preserved metadata (filename, observation types, epoch, approximate
        position). Useful for further analysis or exporting to NetCDF.
    """
    def __init__(self, filename=None, epoch=None, observation=None, approx_position=None,
                 receiver_type=None, antenna_type=None, interval=None,
                 receiver_clock=None, version=None, observation_types=None):
        self.filename          = filename 
        self.epoch             = epoch 
        self.observation       = observation
        self.approx_position   = approx_position
        self.receiver_type     = receiver_type
        self.antenna_type      = antenna_type
        self.interval          = interval
        self.receiver_clock    = receiver_clock
        self.version           = version
        self.observation_types = observation_types

    def to_xarray(self) -> xr.Dataset:
        ds = self.observation.to_xarray()
        ds = ds.assign_attrs({'filename' : self.filename,
                            'observation_types' : self.observation_types,
                            'epoch' : self.epoch.isoformat(),
                            'approx_position' : self.approx_position})
        return ds

class _ObservationTypes:
    def __init__(self, ToB_GPS=None, ToB_GLONASS=None, ToB_GALILEO=None,
                 ToB_COMPASS=None, ToB_QZSS=None, ToB_IRSS=None, ToB_SBAS=None):
        self.GPS     = ToB_GPS
        self.GLONASS = ToB_GLONASS
        self.GALILEO = ToB_GALILEO
        self.COMPASS = ToB_COMPASS
        self.QZSS    = ToB_QZSS
        self.IRSS    = ToB_IRSS
        self.SBAS    = ToB_SBAS
# ======================================================================

# ======================================================================
class Header:
    """
    Header class for RINEX Observation (*.*o) files
    """
    def __init__(self, filename=None, approx_position=None, receiver_type=None, 
                 antenna_type=None, start_date=None, end_date=None,
                 version=None, observation_types=None):
        self.filename          = filename
        self.approx_position   = approx_position
        self.receiver_type     = receiver_type
        self.antenna_type      = antenna_type
        self.start_date        = start_date
        self.end_date          = end_date
        self.version           = version
        self.observation_types = observation_types
# ======================================================================

# ======================================================================
class Navigation:
    """
    Navigation class for RINEX Observation (*.*n/p) files
    """
    def __init__(self, epoch = None, navigation = None, version = None):
        self.epoch           = epoch
        self.navigation      = navigation
        self.version         = version
# ======================================================================

# ======================================================================
class PEphemeris:
    """
    Class definition for SP3 file (Precise Ephemeris)
    """
    def __init__(self, epoch=None, ephemeris=None):
        self.epoch = epoch
        self.ephemeris = ephemeris
