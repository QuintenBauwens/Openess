import inspect
import core
import utils
from utils.loadingScreenUI import LoadScreen
from utils.loggerConfig import get_logger
from utils.statusCircleUI import StatusCircle
import utils.statusCircleUI

logger = get_logger(__name__)


class Project():
    def __init__(self, master, content_frame, myproject, myinterface):
        self.master = master
        self.content_frame = content_frame
        self.myproject = myproject
        self.myinterface = myinterface
        logger.debug(f"Initializing loading screen for the '{__name__.split('.')[-1]}' instance")
        self.loading_screen = LoadScreen(self.master, self.content_frame)
        self.module_map = {}
        self.status_icon = None
        logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

    
    def set_statusIcon(self, header_frame):
        logger.debug(f"Creating the global status icon in the '{__name__.split('.')[-1]}' instance")
        try:
            self.status_icon = StatusCircle(header_frame)
            return self.status_icon
        except Exception as e:
            logger.error(f"Error trying to create the global status icon: {str(e)}", exc_info=True)


    def set_module_map(self, module_map: dict):
        if self.myproject is None:
            return
        
        self.module_map = module_map
        logger.debug(f"Initializing a total of '{len(self.module_map)}' core-modules in Project: {list(self.module_map.keys())}")
        self.init_classes()


    def init_classes(self):
        for file, module in self.module_map.items():
            try:
                module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x))
                for class_name, class_obj in module_classes:
                    if class_name.lower() != module.__name__.split('.')[-1]:
                        continue

                    logger.debug(f"Initializing class: '{class_name}', with object: '{class_obj}'")
                    instance = class_obj(self)
                    setattr(self, class_name.lower(), instance)
            except Exception as e:
                raise Exception(str(e))
        # has to be done after all classes are initialized to avoid missing attributes in Project
        self.init_class_function('get_core_classes')
        self.init_class_function('get_core_functions')
        logger.debug(f"Initialized a total of '{len(self.module_map)}' classes in '{__name__.split('.')[-1]}' instance")


    def init_class_function(self, function_name):
        message = 'objects' if function_name == 'get_core_classes' else 'functions of objects'
        for file, module in self.module_map.items():
            try:
                module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x))
                for class_name, class_obj in module_classes:
                    if class_name.lower() != module.__name__.split('.')[-1]:
                        continue

                    logger.debug(f"Granting the '{class_name}' object access to other {message} it needs within the '{__name__.split('.')[-1]}' instance")
                    instance = getattr(self, class_name.lower())
                    if hasattr(instance, function_name):
                        instance.__getattribute__(function_name)()
            except Exception as e:
                raise Exception(str(e))


    def update_project(self, myproject, myinterface):
        self.myproject = myproject
        self.myinterface = myinterface