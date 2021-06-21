import os
import time
import random
import pycurl
import certifi

from tiler import SlippyTiler
from threading import Thread

from osgeo import gdal
from shapely import geometry


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

        # geometry
        self._geometry = config[ 'geometry' ] if 'geometry' in config else None
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

                    # setup curl object - include ssl certificates
                    curl = pycurl.Curl()
                    curl.setopt(pycurl.CAINFO, certifi.where())
                    curl.setopt(pycurl.URL, uri )

                    # config authentication
                    if self._credentials is not None:
                        curl.setopt( pycurl.USERPWD, "{}:{}".format( self._credentials[ 'username'], self._credentials[ 'password' ] ) )

                    # writeback if enabled
                    if self._verbose:
                        print ( '{}: {} -> {}'. format( self._idx, uri, pathname ) )

                    # write binary data to file
                    fp = open( pathname, "wb" )
                    curl.setopt(pycurl.WRITEDATA, fp)
                    curl.perform()

                    # close object and file
                    curl.close()
                    fp.close()

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
