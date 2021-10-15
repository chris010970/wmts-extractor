import os
import requests

class WfsCatalog():

    def __init__( self, config ):
    
        """
        constructor
        """

        # copy args
        self._credentials = config.credentials if 'credentials' in config else None
        return


    def downloadFeatures( self, uri, out_pathname ):

        """
        download feature info xml file
        """

        # create output path
        if not os.path.exists( os.path.dirname ( out_pathname ) ):
            os.makedirs( os.path.dirname ( out_pathname ) )

        # optionally create auth tuple
        auth = None
        if self._credentials is not None:
            auth = ( self._credentials.username, self._credentials.password )

        # request catalog file from server
        with requests.get(uri, auth=auth, stream=True) as r:
            with open(out_pathname, 'w') as f:
                f.write(r.text)

        return

    def getItem( self, root, field ):

        """              
        get node value from xml schema
        """

        item = None

        # return first item in list else none
        items = self.findItems( root, field )
        if len( items ) > 0:
            item = items[ 0 ]

        return item


    def findItems( self, node, field ):

        """              
        recursively extract key values from dictionary
        """

        # for all key value pairs
        values = []
        for key, value in node.items():

            # record value of key match
            if key == field:
                values.append( value )

            # recursive call on nested dict
            elif isinstance( value, dict ):
                results = self.findItems( value, field )
                for result in results:
                    values.append( result )

            # loop through contents in array
            elif isinstance( value, list ):
                for item in value:

                    # recursive call on nested dict
                    if isinstance( item, dict ):
                        results = self.findItems( item, field )
                        for result in results:
                            values.append( result )

        return values        
