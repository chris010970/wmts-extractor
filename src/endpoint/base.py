
import abc

class Endpoint:

    def __init__( self, config, args ):
    
        """
        base class constructor
        """

        # copy args
        self._config = config
        self._args = args
        
        return

    @abc.abstractmethod
    def getInventory( self ):
        pass

    @abc.abstractmethod
    def getUri( self, record ):
        pass

    @abc.abstractmethod
    def getPathname( self, aoi, record ):
        pass

    def filterInventory( self, inventory ):
        return inventory
