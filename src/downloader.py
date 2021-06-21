import os
import glob
from osgeo import gdal
from scraper import TileScraper
from tiler import MercatorTiler, SlippyTiler

class Downloader:

    def __init__( self, config ):

        """
        constructor
        """

        # copy config
        self._config = config
        self._credentials = config.credentials if 'credentials' in config else None

        # copy optional arguments    
        self._options = self._config.get( 'options' )
        self._threads = self._config.get( 'threads', 1 )

        # create flavour of tiler object
        if self._config.get( 'type' ) == 'slippy':
            self._tiler = SlippyTiler()
        else:
            self._tiler = MercatorTiler()

        return


    def getTileMinMax ( self, bbox, zoom ):

        """
        return coordinates of top left and bottom right tiles for aoi
        """

        # get tile x, y coordinates of bbox
        x1, y1 = self._tiler.LatLonToTile( bbox[ 1 ], bbox[ 0 ], zoom )
        x2, y2 = self._tiler.LatLonToTile( bbox[ 3 ], bbox[ 2 ], zoom )

        return x1, y1, x2, y2


    def process ( self, uri, aoi, args, out_pathname ):

        """
        download tiles aligned with aoi and assimilate into single georeferenced image
        """

        # create output folder if required
        out_path = os.path.dirname( out_pathname )
        if not os.path.exists( out_path ):
            os.makedirs( out_path )

        # create config dict
        config = {  'tiler' : self._tiler, 
                    'options' : self._options, 
                    'credentials' : self._credentials, 
                    'geometry' : None if aoi.type is 'Point' else aoi.geometry  } # geometry assumed rectangualar if original point-based

        # get tile x, y limits of bbox
        x1, y1, x2, y2 = self.getTileMinMax( aoi.geometry.bounds, args.zoom )

        # get tasklist for threads
        threads = []
        tasklist = self.getTaskList( uri, (x1,y1,x2,y2), args.zoom, out_path )
        
        for idx, tasks in enumerate( tasklist ):

            # create derived tilescraper object 
            obj = TileScraper( idx, tasks, config )
            obj.start()
            threads.append( obj )

        # pause main thread until all child threads complete
        for obj in threads:
            obj.join()

        # generate list of newly downloaded tiles
        tiles = []
        for thread in threads:
            tiles.extend ( thread._tiles )

        # merge tiles into single image
        gdal.Warp( out_pathname, tiles, options=gdal.WarpOptions( gdal.ParseCommandLine( args.options ) ) )

        # remove tile files
        files = glob.glob( os.path.join( out_path, 'tile*' ) )
        for f in files:
            os.remove( f )

        # remove path if empty 
        files = glob.glob( os.path.join( out_path, '*' ) )
        if len( files ) == 0:
            os.rmdir( out_path )

        return


    def getTaskList( self, uri, bbox, zoom, out_path ):

        """
        get tile image from https url
        """

        # initialise list of tasklists
        tasklist = [ [] for t in range( self._threads ) ]
        x1, y1, x2, y2 = bbox

        # loop through tile coordinates
        index = 0
        for y in range( min( y1, y2 ), max( y1, y2 ) + 1 ):
            for x in range( x1, x2 + 1 ):

                # construct url
                values = { 'x' : x, 'y' : y, 'z' : zoom, 'format' : self._config.format }
                _uri = uri.format( **values ) 

                # download tile to pathname
                pathname = os.path.join( out_path, 'tile_{}_{}_{}.{}'.format( zoom, x, y, self._config.format ) ) 

                # append job to list
                tasklist[ index ].append( { 'xyz' : ( x, y, zoom ), 'uri' : _uri, 'pathname' : pathname } )
                index += 1
                
                # reset thread / taskset index
                if index == self._threads:
                    index = 0

        return tasklist
