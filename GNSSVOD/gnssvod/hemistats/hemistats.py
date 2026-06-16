"""
Tools for building and working with equi-angular hemispheric grids.

The main entry point is :func:`hemibuild`, which constructs a hemispheric
grid and returns a :class:`Hemi` object containing grid geometry and
helper methods for mapping GNSS observations onto the grid.
"""
# ===========================================================
# ========================= imports =========================
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
# ===========================================================
"""
Class definition for hemispheric polar grid object
"""
# ======================================================================
class Hemi:
    """
    Hemispheric polar grid object.

    This class stores the geometry of an equi-angular hemispheric grid and
    provides utilities to work with hemispheric binning of GNSS observations
    (e.g., assigning measurements to grid cells or generating plotting patches).

    Objects of this class are typically created using :func:`hemibuild`.

    Attributes
    ----------
    angular_resolution : float
        Angular diameter of the zenith cell (degrees).

    ncells : int
        Total number of grid cells.

    grid : pandas.DataFrame
        DataFrame describing grid cell geometry. Contain the columns:

        - ``azi`` : cell center azimuth (degrees)
        - ``ele`` : cell center elevation (degrees)
        - ``azimin`` / ``azimax`` : azimuthal cell edges (degrees)
        - ``elemin`` / ``elemax`` : elevation cell edges (degrees)

    coords : pandas.DataFrame
        Subset of ``grid`` containing cell center coordinates
        (columns ``azi`` and ``ele``).

    elelims : numpy.ndarray
        Elevation band limits.

    azilims : list of numpy.ndarray
        Azimuthal bin edges for each elevation band.

    CellIDs : list of numpy.ndarray
        Cell IDs per elevation band.

    Examples
    --------
    .. code-block:: python

        # Build a hemispheric grid
        hemi = hemibuild(angular_resolution=10)

        # Access the patches for plotting
        patches = hemi.patches()

        # Assign grid cell IDs to observation dataframe
        df_with_cells = hemi.add_CellID(df_obs, aziname='Azimuth', elename='Elevation')
    """
    def __init__(self,angular_resolution,grid,elelims,azilims,CellIDs):
        self.angular_resolution = angular_resolution
        self.ncells = len(grid)
        self.grid = grid
        self.coords = self.grid.loc[:,['azi','ele']]
        self.elelims = elelims
        self.azilims = azilims
        self.CellIDs = CellIDs

    def patches(self):
        """
        Generate matplotlib patches for hemispheric grid cells.

        Creates rectangular patches in polar projection space that can be
        used to visualize the hemispheric grid.

        Returns
        -------
        pandas.Series
            Series of :class:`matplotlib.patches.Rectangle` objects indexed
            by ``CellID``.

        Notes
        -----
        Elevation is transformed to polar coordinates using:

        ``r = 90° - elevation``

        This representation is suitable for hemispheric sky plots.
        """
        def plotpatch(dfrow):
            azimin = np.deg2rad(dfrow.azimin)
            elemax = 90-dfrow.elemax
            azimax = np.deg2rad(dfrow.azimax)
            elemin = 90-dfrow.elemin
            return(Rectangle([azimin,elemax],azimax-azimin,elemin-elemax,fill=True))
        patches = self.grid.apply(plotpatch,axis=1)
        return(patches.rename('Patches'))
    
    def add_CellID(self,
                  df: pd.DataFrame,
                  aziname: str='Azimuth',
                  elename: str='Elevation',
                  idname: str='CellID',
                  drop: bool=True):
        """
        Assign hemispheric grid cell IDs to observations.

        Maps each observation to the corresponding hemispheric grid cell
        based on its azimuth and elevation coordinates.

        Parameters
        ----------
        df : pandas.DataFrame
            Input dataframe containing azimuth and elevation observations.

        aziname : str, optional
            Name of the azimuth column in ``df`` (degrees).
            Default is ``'Azimuth'``.

        elename : str, optional
            Name of the elevation column in ``df`` (degrees).
            Default is ``'Elevation'``.

        idname : str, optional
            Name of the output column containing assigned CellIDs.
            Default is ``'CellID'``.

        drop : bool, optional
            Controls handling of observations that cannot be assigned
            to a grid cell:

            - ``True`` (default): rows without CellID are dropped.
            - ``False``: rows are preserved and assigned ``NaN``.

        Returns
        -------
        pandas.DataFrame
            DataFrame with an added ``CellID`` column.

            - If ``drop=True`` → only rows with valid CellIDs.
            - If ``drop=False`` → all rows retained.

        Notes
        -----
        - Azimuth values are normalized to the range [0°, 360°].
        - Observations with missing azimuth or elevation are ignored.
        - Elevation binning is performed first, followed by azimuthal binning
          within each elevation band.
        """
        # check that columns specified by aziname and elename exist in df
        if not aziname in df:
            raise ValueError(f"No column '{aziname}' in the dataframe, indicate which column should be used with azi='ColumnName'")
        if not elename in df:
            raise ValueError(f"No column '{elename}' in the dataframe, indicate which column should be used with ele='ColumnName'")

        # extract a subset of the df which we can manipulate 
        idf = df.loc[:, (aziname, elename)].copy()
        # remove all data missing azi or ele
        idf = idf[~idf.isnull().any(axis=1)]
        # use modulo to ensure all azimuths are [0-360] (not i.e. -10 or 370)
        idf[aziname] = np.mod(idf[aziname]+360*10,360)
        # first cut the data by elevation band
        idf['eleind'] = pd.cut(idf[elename],
                              bins = np.concatenate((np.flip(self.elelims),[90])),
                              labels = np.flip(list(range(len(self.elelims)))))
        
        # define a function that retrieves indices for each elevation band, cutting with azimuthal edges specific to the given band
        def azicut(idf):
            # if elevation band contains no obs, just return empty result
            if len(idf)==0:
                idf[idname] = pd.Series(dtype=int)
                return(idf[idname])
            # find out which band we are in
            iele = idf['eleind'].iloc[0]
            # retrieve the corresponding azimuthal edges
            iazilims = self.azilims[iele]
            # cut data with azimuthal edges to retrieve azimuthal index
            idf['aziind'] = pd.cut(idf[aziname], 
                                  bins = np.concatenate((iazilims,[360])),
                                  labels = False,
                                  right = False)
            # return the corresponding CellID values
            idf[idname] = self.CellIDs[iele][idf['aziind'].values]
            return(idf[idname])

        # apply the azicut function to each elevation band
        idf=idf.groupby('eleind',group_keys=False, observed=False)[['eleind',aziname]].apply(azicut) # groupby will drop rows with eleind=NaN
        if idname in df:
            df = df.drop(columns=idname)
        # if drop is True, we are returning the input df with only rows that have a CellID
        
        if drop:
            return(df.join(idf,how='inner'))
        # if drop is False, we are returning the entire input df, including NaN CellIDs
        else:
            return(df.join(idf,how='left'))
        
    
    # plot(), plot empty grid, or if passing dataframe + ID name + var name, make a join and plot the data

#-------------------------------------------------------------------------
#----------------- building hemispheric grids and meshes -------------------
#-------------------------------------------------------------------------
def hemibuild(angular_resolution,cutoff=0):
    """
    Build an equi-angular hemispheric grid.

    Constructs a hemispheric partition where grid cells have approximately
    equal angular area. The grid is organized into concentric elevation
    rings, each subdivided azimuthally.

    The function returns a :class:`~Hemi` object containing grid geometry
    and helper utilities.

    Parameters
    ----------
    angular_resolution : float
        Angular diameter (degrees) of the zenith cell. This defines the
        target angular size of all grid cells and controls overall grid
        density.

    cutoff : float, optional
        Minimum elevation angle (degrees) included in the grid.

        - ``0`` (default) builds a full hemisphere down to the horizon.
        - Higher values exclude low-elevation cells.

    Returns
    -------
    :class:`~Hemi`
        Hemispheric grid object containing:

        - Cell center coordinates
        - Cell edge geometry
        - Elevation and azimuth bin definitions
        - Cell ID mappings
        - Helper methods (:meth:`~Hemi.patches`, :meth:`~Hemi.add_CellID`)

    Examples
    --------
    .. code-block:: python

        # Build a hemispheric grid
        hemi = hemibuild(angular_resolution=10)

        # Access the patches for plotting
        patches = hemi.patches()

        # Assign grid cell IDs to observation dataframe
        df_with_cells = hemi.add_CellID(df_obs, aziname='Azimuth', elename='Elevation')

    References
    ----------
    Beckers, B., & Beckers, P. (2012).
    *A general rule for disk and hemisphere partition into equal-area cells*.
    Computational Geometry, 45(7), 275–283.
    """
    # calculate number of rings
    ringlims = np.arange(angular_resolution/2,90-cutoff,angular_resolution)
    # calculate area of a cell
    cell_area = 2*np.pi*(1-np.cos(np.deg2rad(angular_resolution/2)))

    # instantiate empty lists
    cells = []
    elelims = []
    azilims = []
    CellIDs = []
    # add first zenith cell as df
    cells.append(pd.DataFrame(data={'azi':[0],
                                    'ele':[90],
                                    'azimin':[0],
                                    'azimax':[360],
                                    'elemin':[90-angular_resolution/2],
                                    'elemax':[90]}))
    elelims.append(90-angular_resolution/2)
    azilims.append(np.array([0]))
    CellIDs.append(np.array([0]))
    nextCellID = 1
    
    # add cells, ring by ring
    for iring, outer_radius in enumerate(ringlims[1:]):
        inner_radius = ringlims[iring]
        # calculate area of ring
        ring_area = 2*np.pi*(1-np.cos(np.deg2rad(outer_radius)))-2*np.pi*(1-np.cos(np.deg2rad(inner_radius)))
        # evenly split ring according to requested cell area
        numcells = round(ring_area/cell_area)
        # span of a single cell
        azispan = 360/numcells
        # generate CellIDs
        CellID = list(range(nextCellID,nextCellID+numcells))
        # also prepare the starting CellID for the next iteration
        nextCellID = CellID[-1]+1
        # add all cells into a list of dataframes
        azimin = np.linspace(0,360.0-azispan,numcells)
        cells.append(pd.DataFrame(data={'azi':np.linspace(azispan/2,360-azispan/2,numcells),
                                    'ele':np.full(numcells,90-(inner_radius+angular_resolution/2)),
                                    'azimin':azimin,
                                    'azimax':np.concatenate((azimin[1:],[360.0])),
                                    'elemin':np.full(numcells,90-outer_radius),
                                    'elemax':np.full(numcells,90-inner_radius)}))
        elelims.append(90-outer_radius)
        azilims.append(np.array(azimin))
        CellIDs.append(np.array(CellID))
    # concatenate all cells from all rings
    cells = pd.concat(cells).reset_index(drop=True).rename_axis('CellID')
    
    # instantiate Hemi object
    return Hemi(angular_resolution,cells,np.array(elelims),azilims,CellIDs)