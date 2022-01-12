import os
import time
import random
import requests
import shutil

from tiler import SlippyTiler
from threading import Thread

from osgeo import gdal
from shapely import geometry
from shapely.ops import transform

import pyproj

class TileScraper( Thread ):

    def __init__( self, idx, tasks, config, verbose=False ):

        """
        constructor
        """

        # init base
        Thread.__init__(self)

        # copy arguments    
        self._idx = idx
        self._tasks = tasks

        self._tiler = config[ 'tiler' ]
        self._options = config[ 'options' ]
        self._credentials = config[ 'credentials' ]        
        self._verbose = verbose

        # config geometry
        self._geometry = None 
        if 'geometry' in config:
            
            self._geometry = config[ 'geometry' ]

            # reproject aoi from geographic to mercator
            project = pyproj.Transformer.from_proj(
                            pyproj.Proj(init='epsg:4326'),
                            pyproj.Proj(init='epsg:3857'))

            self._geometry = transform(project.transform, self._geometry ) 

        self._tiles = []
        return


    def run( self ):

        """
        constructor
        """

        # for each task
        for task in self._tasks:

            # get bounds
            s,w,n,e = self._tiler.TileBounds( *( task[ 'xyz' ] ) )
            intersects = True

            # compute intersection between tile aoi and geometry
            if self._geometry is not None:
                bbox = geometry.Polygon( [  [ w, n ], 
                                            [ e, n ], 
                                            [ e, s ],
                                            [ w, s ],
                                            [ w, n ] ] )

                intersects = bbox.intersects( self._geometry )

            # if intersection exists
            if intersects:

                # download tile
                self.getTile( task[ 'uri' ], task[ 'pathname'] )
                if os.path.exists ( task[ 'pathname' ] ):

                    # open newly created tile with gdal
                    ds = gdal.Open( task[ 'pathname'] )
                    if ds is not None:

                        # setup geotiff translation options
                        options = '-of GTiff -co compress=lzw '                    
                        options += '-a_srs "{}" -a_ullr {} {} {} {} '.format ( self._tiler._proj, w, n, e, s )
                        
                        if self._options is not None:
                            options += self._options

                        try:

                            # translate png / jpg into geotiff
                            pathname = os.path.splitext( task[ 'pathname'] )[ 0 ] + '.tif'
                            ds = gdal.Translate( pathname, ds, options=options )
                            ds = None

                            # record pathname of newly created image
                            self._tiles.append( pathname )

                        except Exception as e:

                            # translation error
                            print ( 'Translation Exception: {}'.format( str( e ) ) )

        return


    def getTile( self, uri, pathname ):

        """
        get tile image from https url
        """

        # already exists on file system 
        if not os.path.exists ( pathname ):

            # retry counters
            tries = 1; max_tries = 3
            while tries <= max_tries:

                try:

                    # writeback if enabled
                    if self._verbose:
                        print ( '{}: {} -> {}'. format( self._idx, uri, pathname ) )

                    # optionally create auth tuple
                    auth=None
                    if self._credentials is not None:
                        auth = (self._credentials[ 'username'], self._credentials[ 'password' ])

                    # use requests to get tile image
                    with requests.get( uri, auth=auth, stream=True) as r:
                        with open( pathname, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)

                    break

                except Exception as e:

                    # increment retry counter - wait for random interval
                    print ( 'Download Exception {}: {} -> {}'.format( str( e ), uri, pathname ) )
                    tries += 1
                    time.sleep ( random.randrange( 5 ) )

            # delete file if download failed 
            if tries > max_tries:
                os.remove( pathname )

        return 
