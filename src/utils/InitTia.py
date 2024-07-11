"""
Description: 
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

__package__ = "src.utils"
import clr
import os

def open_project(interface=False, project_path=None):
    # Refference to the Openness library
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

    return myproject, mytia

def close_project(myproject, mytia):
    myproject.Close()
    mytia.Dispose()
    