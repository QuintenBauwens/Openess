"""
Description: 
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

from utils.loggerConfig import get_logger
__package__ = "utils"
import clr

logger = get_logger(__name__)

def open_project(interface=False, project_path=None):
    """
    Opens a TIA project using the Openness library.
    Args:
        interface (bool, optional): Specifies whether to open the TIA project with a user interface. Defaults to False.
        project_path (str, optional): The path to the TIA project file. Defaults to None.
    Returns:
        tuple: A tuple containing the opened TIA project and the TIA portal instance.
    Raises:
        None
    Example:
        myproject, mytia = open_project(interface=True, project_path="C:/path/to/project.tia")
    """
    # Refference to the Openness library
    if interface:
        logger.debug(f"Opening TIA project with interface: '{project_path}'")
    else:
        logger.debug(f"Opening TIA project without interface: '{project_path}'")
    
    dll_path = "C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll"
    clr.AddReference(dll_path)

    listPathItems = dll_path.split("\\")[:-3]
    listPathItems.append('Bin\\PublicAPI\\Siemens.Engineering.Contract.dll')
    dll_path2 = "\\".join(listPathItems)

    clr.AddReference(dll_path2)

    import Siemens.Engineering as tia 

    # Starting tia with User Interface (handy for development) or not
    if interface:
        mytia = tia.TiaPortal(tia.TiaPortalMode.WithUserInterface)
    else:
        mytia = tia.TiaPortal(tia.TiaPortalMode.WithoutUserInterface)

    from System.IO import FileInfo
    # Opening a TIA Project
    fileInfo = FileInfo(project_path) # path to project
    myproject = mytia.Projects.Open(fileInfo)

    logger.debug(f"Opened TIA project succesfully: '{project_path}'")
    return myproject, mytia

def close_project(myproject, mytia):
    """
    Closes the TIA project and disposes the TIA instance.

    Args:
        myproject: The TIA project to be closed.
        mytia: The TIA instance to be disposed.

    Returns:
        None

    Raises:
        None
    """
    logger.debug(f"Closed TIA project successfully")
    logger.debug(f"Closing TIA project: '{myproject.Name}'")
    myproject.Close()
    mytia.Dispose()
    logger.debug(f"Closed TIA project succesfully")
    