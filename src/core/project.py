import inspect
from utils.loadingScreenUI import LoadScreen
from utils.loggerConfig import get_logger
from utils.statusCircleUI import StatusCircle

logger = get_logger(__name__)


class Project():
    """
    Represents a project in the application. This class is responsible for initializing the core-modules and classes dynamically.
    Args:
        master: The master widget.
        content_frame: The content frame widget.
        myproject: The project object.
        myinterface: The interface object.
    Attributes:
        loading_screen: The loading screen widget.
        module_map: A dictionary mapping module names to module objects.
        status_icon: The global status icon widget.
    Methods:
        set_statusIcon(header_frame): Creates the global status icon in the project instance.
        set_module_map(module_map: dict): Sets the module map for the project.
        init_classes(): Initializes the classes in the project.
        init_class_function(function_name): Initializes a specific class function in the project.
        update_project(myproject, myinterface): Updates the project with new project and interface objects.
    """
    # write documentation here, with also containing the dynamic class creation

    def __init__(self, master, content_frame, myproject, myinterface):
        """
        Initializes a new instance of the Project class.

        Args:
            master: The master widget.
            content_frame: The content frame widget.
            myproject: The project object.
            myinterface: The interface object.
        """
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
        """
        Sets the status icon for the project.

        Parameters:
        - header_frame: The header frame where the status icon will be placed.

        Returns:
        - The created status icon.

        Raises:
        - Exception: If an error occurs while creating the status icon.
        """
        logger.debug(f"Creating the global status icon in the '{__name__.split('.')[-1]}' instance")
        try:
            self.status_icon = StatusCircle(header_frame)
            return self.status_icon
        except Exception as e:
            logger.error(f"Error trying to create the global status icon: {str(e)}", exc_info=True)


    def set_module_map(self, module_map: dict):
        """
        Sets the module map for the project, which maps module names to module objects.
        Parameters:
            module_map (dict): A dictionary containing the module names as keys and the corresponding module objects as values.
        Returns:
            None
        """
        if self.myproject is None:
            return
        
        self.module_map = module_map
        logger.debug(f"Initializing a total of '{len(self.module_map)}' core-modules in Project: {list(self.module_map.keys())}")
        self.init_classes()


    def init_classes(self):
        """
        Initializes the classes that are set with 'set_module_map' in the project dynamically.
        This method iterates over the module map and initializes the classes found in each module.
        It creates an instance of each class and sets it as an attribute of the project instance.
        Raises:
            Exception: If an error occurs during class initialization.
        Returns:
            None
        """
        inits = []
        for file, module in self.module_map.items():
            try:
                module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x))
                for class_name, class_obj in module_classes:
                    if class_name.lower() != module.__name__.split('.')[-1].lower():
                        continue

                    logger.debug(f"Initializing class: '{class_name}', with object: '{class_obj}'")
                    instance = class_obj(self)
                    setattr(self, class_name.lower(), instance)
                    inits.append(class_name)
            except Exception as e:
                raise Exception(str(e))
        # has to be done after all classes are initialized to avoid missing attributes in Project
        self.init_class_function('get_core_classes')
        self.init_class_function('get_core_functions')
        logger.debug(f"Initialized a total of '{len(inits)}' classes in '{__name__.split('.')[-1]}' instance")


    def init_class_function(self, function_name):
        """
        Initializes a class function.
        Args:
            function_name (str): The name of the function.
        Raises:
            Exception: If an error occurs during the initialization.
        """
        message = 'objects' if function_name == 'get_core_classes' else 'functions of objects'
        for file, module in self.module_map.items():
            try:
                module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x))
                for class_name, class_obj in module_classes:
                    if class_name.lower() != module.__name__.split('.')[-1].lower():
                        continue

                    logger.debug(f"Granting the '{class_name}' object access to other {message} it needs within the '{__name__.split('.')[-1]}' instance")
                    instance = getattr(self, class_name.lower(), None)
                    if hasattr(instance, function_name):
                        instance.__getattribute__(function_name)()
            except Exception as e:
                raise Exception(str(e))


    def update_project(self, myproject, myinterface):
        """
        Update the project with the given project and interface.

        Args:
            myproject: The new project to be assigned.
            myinterface: The new interface to be assigned.
        """
        self.myproject = myproject
        self.myinterface = myinterface