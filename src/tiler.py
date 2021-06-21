import math

class MercatorTiler(object):

    """
    TMS Global Mercator Profile
    ---------------------------

    Functions necessary for generation of tiles in Spherical Mercator projection,
    EPSG:900913 (EPSG:gOOglE, Google Maps Global Mercator), EPSG:3785, OSGEO:41001.

    Such tiles are compatible with Google Maps, Microsoft Virtual Earth, Yahoo Maps,
    UK Ordnance Survey OpenSpace API, ...
    and you can overlay them on top of base maps of those web mapping applications.
    
    Pixel and tile coordinates are in TMS notation (origin [0,0] in bottom-left).

    What coordinate conversions do we need for TMS Global Mercator tiles::

         LatLon      <->       Meters      <->     Pixels    <->       Tile     

     WGS84 coordinates   Spherical Mercator  Pixels in pyramid  Tiles in pyramid
         lat/lon            XY in metres     XY pixels Z zoom      XYZ from TMS 
        EPSG:4326           EPSG:900913                                         
         .----.              ---------               --                TMS      
        /      \     <->     |       |     <->     /----/    <->      Google    
        \      /             |       |           /--------/          QuadTree   
         -----               ---------         /------------/                   
       KML, public         WebMapService         Web Clients      TileMapService

    What is the coordinate extent of Earth in EPSG:900913?

      [-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244]
      Constant 20037508.342789244 comes from the circumference of the Earth in meters,
      which is 40 thousand kilometers, the coordinate origin is in the middle of extent.
      In fact you can calculate the constant as: 2 * math.pi * 6378137 / 2.0
      $ echo 180 85 | gdaltransform -s_srs EPSG:4326 -t_srs EPSG:900913
      Polar areas with abs(latitude) bigger then 85.05112878 are clipped off.

    What are zoom level constants (pixels/meter) for pyramid with EPSG:900913?

      whole region is on top of pyramid (zoom=0) covered by 256x256 pixels tile,
      every lower zoom level resolution is always divided by two
      initialResolution = 20037508.342789244 * 2 / 256 = 156543.03392804062

    What is the difference between TMS and Google Maps/QuadTree tile name convention?

      The tile raster itself is the same (equal extent, projection, pixel size),
      there is just different identification of the same raster tile.
      Tiles in TMS are counted from [0,0] in the bottom-left corner, id is XYZ.
      Google placed the origin [0,0] to the top-left corner, reference is XYZ.
      Microsoft is referencing tiles by a QuadTree name, defined on the website:
      http://msdn2.microsoft.com/en-us/library/bb259689.aspx

    The lat/lon coordinates are using WGS84 datum, yeh?

      Yes, all lat/lon we are mentioning should use WGS84 Geodetic Datum.
      Well, the web clients like Google Maps are projecting those coordinates by
      Spherical Mercator, so in fact lat/lon coordinates on sphere are treated as if
      the were on the WGS84 ellipsoid.
     
      From MSDN documentation:
      To simplify the calculations, we use the spherical form of projection, not
      the ellipsoidal form. Since the projection is used only for map display,
      and not for displaying numeric coordinates, we don't need the extra precision
      of an ellipsoidal projection. The spherical projection causes approximately
      0.33 percent scale distortion in the Y direction, which is not visually noticable.

    How do I create a raster in EPSG:900913 and convert coordinates with PROJ.4?

      You can use standard GIS tools like gdalwarp, cs2cs or gdaltransform.
      All of the tools supports -t_srs 'epsg:900913'.

      For other GIS programs check the exact definition of the projection:
      More info at http://spatialreference.org/ref/user/google-projection/
      The same projection is degined as EPSG:3785. WKT definition is in the official
      EPSG database.

      Proj4 Text:
        +proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0
        +k=1.0 +units=m +nadgrids=@null +no_defs

      Human readable WKT format of EPGS:900913:
         PROJCS["Google Maps Global Mercator",
             GEOGCS["WGS 84",
                 DATUM["WGS_1984",
                     SPHEROID["WGS 84",6378137,298.2572235630016,
                         AUTHORITY["EPSG","7030"]],
                     AUTHORITY["EPSG","6326"]],
                 PRIMEM["Greenwich",0],
                 UNIT["degree",0.0174532925199433],
                 AUTHORITY["EPSG","4326"]],
             PROJECTION["Mercator_1SP"],
             PARAMETER["central_meridian",0],
             PARAMETER["scale_factor",1],
             PARAMETER["false_easting",0],
             PARAMETER["false_northing",0],
             UNIT["metre",1,
                 AUTHORITY["EPSG","9001"]]]
    """

    def __init__(self, tileSize=256):
        "Initialize the TMS Global Mercator pyramid"
        self._tileSize = tileSize
        self._initialResolution = 2 * math.pi * 6378137 / self._tileSize
        # 156543.03392804062 for tileSize 256 pixels
        self._originShift = 2 * math.pi * 6378137 / 2.0
        # 20037508.342789244

        self._proj = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs'
        return

    def LatLonToMeters(self, lat, lon ):
        "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

        mx = lon * self._originShift / 180.0
        my = math.log( math.tan((90 + lat) * math.pi / 360.0 )) / (math.pi / 180.0)

        my = my * self._originShift / 180.0
        return mx, my

    def MetersToLatLon(self, mx, my ):
        "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"

        lon = (mx / self._originShift) * 180.0
        lat = (my / self._originShift) * 180.0

        lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
        return lat, lon

    def PixelsToMeters(self, px, py, zoom):
        "Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

        res = self.Resolution( zoom )
        mx = px * res - self._originShift
        my = py * res - self._originShift
        return mx, my
        
    def MetersToPixels(self, mx, my, zoom):
        "Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"
                
        res = self.Resolution( zoom )
        px = (mx + self._originShift) / res
        py = (my + self._originShift) / res
        return px, py
    
    def PixelsToTile(self, px, py):
        "Returns a tile covering region in given pixel coordinates"

        tx = int( math.ceil( px / float(self._tileSize) ) - 1 )
        ty = int( math.ceil( py / float(self._tileSize) ) - 1 )
        return tx, ty

    def PixelsToRaster(self, px, py, zoom):
        "Move the origin of pixel coordinates to top-left corner"
        
        mapSize = self._tileSize << zoom
        return px, mapSize - py
        
    def MetersToTile(self, mx, my, zoom):
        "Returns tile for given mercator coordinates"
        
        px, py = self.MetersToPixels( mx, my, zoom)
        return self.PixelsToTile( px, py)

    def TileBounds(self, tx, ty, zoom):
        "Returns bounds of the given tile in EPSG:900913 coordinates"
        
        minx, miny = self.PixelsToMeters( tx*self._tileSize, ty*self._tileSize, zoom )
        maxx, maxy = self.PixelsToMeters( (tx+1)*self._tileSize, (ty+1)*self._tileSize, zoom )
        return ( miny, minx, maxy, maxx )

    def TileLatLonBounds(self, tx, ty, zoom ):
        "Returns bounds of the given tile in latutude/longitude using WGS84 datum"

        bounds = self.TileBounds( tx, ty, zoom)
        minLat, minLon = self.MetersToLatLon(bounds[0], bounds[1])
        maxLat, maxLon = self.MetersToLatLon(bounds[2], bounds[3])
         
        return ( minLat, minLon, maxLat, maxLon )
        
    def Resolution(self, zoom ):
        "Resolution (meters/pixel) for given zoom level (measured at Equator)"
        
        # return (2 * math.pi * 6378137) / (self.tileSize * 2**zoom)
        return self._initialResolution / (2**zoom)
        
    def ZoomForPixelSize(self, pixelSize ):
        "Maximal scaledown zoom of the pyramid closest to the pixelSize."
        
        for i in range(30):
            if pixelSize > self.Resolution(i):
                return i-1 if i!=0 else 0 # We don't want to scale up

    def GoogleTile(self, tx, ty, zoom):
        "Converts TMS tile coordinates to Google Tile coordinates"
        
        # coordinate origin is moved from bottom-left to top-left corner of the extent
        return tx, (2**zoom - 1) - ty

    def QuadTree(self, tx, ty, zoom ):
        "Converts TMS tile coordinates to Microsoft QuadTree"
        
        quadKey = ""
        ty = (2**zoom - 1) - ty
        for i in range(zoom, 0, -1):
            digit = 0
            mask = 1 << (i-1)
            if (tx & mask) != 0:
                digit += 1
            if (ty & mask) != 0:
                digit += 2
            quadKey += str(digit)
            
        return quadKey

    def LatLonToTile( self, lat, lon, z ):
        "Converts latlon to mercator tile coordinates"

        mx, my = self.LatLonToMeters( lat, lon )
        return self.MetersToTile( mx, my, z ) 
        
#-------------------------------------------------------
# Translates between lat/long and the slippy-map tile
# numbering scheme
# 
# http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames
# 
# Written by Oliver White, 2007
# This file is public-domain
#-------------------------------------------------------
class SlippyTiler:

    def __init__( self, tileSize=256 ):
        self._tileSize=tileSize
        self._proj='+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'
        return

    def numTiles( self, z ):
        return( math.pow(2,z) )

    def sec( self, x ):
        return( 1.0 / math.cos(x) )

    def LatLonToRelativeXY( self, lat, lon ):
        x = ( lon + 180.0 ) / 360.0
        y = (1.0 - math.log(math.tan(math.radians(lat)) + self.sec(math.radians(lat))) / math.pi) / 2.0
        return(x,y)

    def LatLonToXY( self, lat, lon, z ):
        n = self.numTiles(z)
        x,y = self.LatLonToRelativeXY(lat,lon)
        return(n*x, n*y)
    
    def LatLonToTile( self, lat, lon, z):
        x,y = self.LatLonToXY(lat,lon,z)
        return(int(x),int(y))

    def XYToLatLon( self, x, y, z ):
        n = self.numTiles(z)
        relY = y / n
        lat =  self.MercatorToLat(math.pi * (1 - 2 * relY))
        lon = -180.0 + 360.0 * x / n
        return(lat,lon)
    
    def LatBounds(self, y, z ):
        n = self.numTiles(z)
        unit = 1 / n
        relY1 = y * unit
        relY2 = relY1 + unit
        lat1 = self.MercatorToLat(math.pi * (1 - 2 * relY1))
        lat2 = self.MercatorToLat(math.pi * (1 - 2 * relY2))
        return( lat1, lat2 )

    def LonBounds( self, x, z ):
        n = self.numTiles(z)
        unit = 360 / n
        lon1 = -180 + x * unit
        lon2 = lon1 + unit
        return(lon1,lon2)
    
    def TileBounds( self, x, y, z ):
        lat1,lat2 = self.LatBounds(y,z)
        lon1,lon2 = self.LonBounds(x,z)
        return( (lat2, lon1, lat1, lon2) ) # S,W,N,E

    def MercatorToLat(self, mercatorY):
        return(math.degrees(math.atan(math.sinh(mercatorY))))


if __name__ == "__main__":
    obj = SlippyTiler()
    for z in range(0,22):
        #x,y = obj.LatLonToTile(51.50610, -0.119888, z)
        x,y = obj.LatLonToTile( 15.5527, 48.5164, z)
        x,y = obj.LatLonToTile( 12.75108333, 44.89085, z )

        x,y = obj.LatLonToTile( 12.749273988762466, 44.88900829538637, z )
        x,y = obj.LatLonToTile( 12.76757362, 44.8908577, z )

        s,w,n,e = obj.TileBounds(x,y,z)
        print ( "%d: %d,%d --> %1.3f :: %1.3f, %1.3f :: %1.3f" % (z,x,y,s,n,w,e) )

