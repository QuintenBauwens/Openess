from utils.logger_config import get_logger

from core.file import File
from core.hardware import Hardware
from core.library import Library
from core.nodes import Nodes
from core.software import Software

logger = get_logger(__name__)

class InvalidClassNameError(Exception):
    def __init__(self, class_name):
        self.class_name = class_name
        self.message = f"Invalid class name '{class_name}'. Please provide a valid class name or add the class to the list of available classes."
        super().__init__(self.message)

class Project():
    def __init__(self, myproject, myinterface):
        logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance for shared resources")
        self.myproject = myproject
        self.myinterface = myinterface
        self.class_map = {
            'File': File,
            'Hardware': Hardware,
            'Library': Library,
            'Nodes': Nodes,
            'Software': Software
            }
        logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")
    
    def init_class(self, class_name):
        _class_ = self.class_map.get(class_name)

        if _class_:
            instance = _class_(self)
            setattr(self, class_name.lower(), instance)
        else:
            raise InvalidClassNameError(class_name)