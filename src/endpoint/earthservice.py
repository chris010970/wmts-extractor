import os
import pandas as pd
import geopandas as gpd

from endpoint.base import Endpoint

class Earthservice ( Endpoint ):

    def __init__( self, config, args ):

        """
        constructor
        """

        # initialise base object
        super().__init__( config, args )
        self._prefix = 'tmsaccess/tms/1.0.0'

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

        return  gpd.GeoDataFrame( records, crs='EPSG:3857' )
        
        
    def getUri( self, _ ):

        """
        get template uri for inventory record
        """

        # generate template uri including record feature id
        return  "{root}/{prefix}/{layer}/{tilematrixset}/{{z}}/{{x}}/{{y}}.png?connectId={id}".format ( root=self._config.uri,
                                                                                                prefix=self._prefix,
                                                                                                layer=self._config.layer,
                                                                                                tilematrixset=self._config.tilematrixset,
                                                                                                id=self._config.id  )

    def getPathname( self, aoi, _ ):

        """
        get pathname 
        """
    
        # construct pathname
        filename = '{name}_{zoom}_{distance}.TIF'.format (  name=aoi.name, 
                                                            zoom=self._args.zoom, 
                                                            distance=aoi.distance )

        return os.path.join( aoi.name, filename )
