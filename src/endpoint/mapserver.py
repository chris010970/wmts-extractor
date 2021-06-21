import os
import pycurl
import certifi
import xmltodict
import tempfile
import pandas as pd
import geopandas as gpd

from datetime import datetime
from endpoint.base import Endpoint
from shapely.geometry import Polygon

class Mapserver ( Endpoint ):

    def __init__( self, config, args ):

        """
        constructor
        """

        # initialise base object
        super().__init__( config, args )
        self._prefix = 'tile/1.0.0/World_Imagery/default'

        return


    def getInventory( self, aoi ):

        """
        get catalog entries collocated with area of interest
        """

        # create and append feature record
        records = []
        records.append ( {  'platform' : 'misc',
                            'product' : 'default',
                            'acq_datetime' : pd.NaT,
                            'cloud_cover' : 0.0,
                            'geometry' : aoi } )

        return  gpd.GeoDataFrame( records, crs='EPSG:4326' )
        
        

    def getUri( self, record ):

        """
        get template uri for inventory record
        """

        # generate template uri including record feature id
        return  "{root}/{prefix}/{tilematrixset}/{{z}}/{{y}}/{{x}}.jpeg".format (   root=self._config.uri,
                                                                                    prefix=self._prefix,
                                                                                    tilematrixset=self._config.tilematrixset  )


    def getPathname( self, record, aoi ):

        """
        get pathname 
        """
    
        # construct pathname
        filename = '{name}_{zoom}_{distance}.TIF'.format (  name=aoi.name, 
                                                            zoom=self._args.zoom, 
                                                            distance=aoi.distance )

        return os.path.join( aoi.name, filename )
