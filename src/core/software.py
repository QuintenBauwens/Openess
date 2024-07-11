"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import clr
# add the reference to the Siemens.Engineering.dll
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll") 
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf
from .hardware import Hardware

class Software:
    """
    Represents the extraction of software components in the system/plc by useing the PLC-software container.

    Args:
        myproject (str): The project associated with the software.
        myinterface (str): The interface used by the software.

    Attributes:
        myproject (str): The project associated with the software.
        myinterface (str): The interface used by the software.
        hardware (Hardware): The hardware component associated with the software.

    Methods:
        get_software_container: Retrieves the software container of the first PLC device.
        get_software_blocks: Retrieves all the blocks in a given group recursively.
    """

    def __init__(self, myproject, myinterface) -> None:
        self.myproject = myproject
        self.myinterface = myinterface
        self.hardware = Hardware(self.myproject, self.myinterface)


    def get_software_container(self):
        """
        Retrieves the software container of the first PLC device.

        Returns:
            SoftwareContainer: The software container of the first PLC device.
        """

        PLC_List = self.hardware.get_plc_devices()
        software_container = PLC_List[0].GetService[hwf.SoftwareContainer]() # Get the plc software of the first plc in the list
        return software_container.Software # Get the software of the plc out of the software container


    def get_software_blocks(self, group, blocks={}):
        """
        Retrieves all the blocks in a given group recursively.

        Args:
            group: The group to retrieve the blocks from.
            blocks (dict): A dictionary to store the blocks. (default: {})

        Returns:
            dict: A dictionary containing the blocks in the group.
        """

        if blocks is None:
            blocks = {}
        if group not in blocks: # Instance group is in more than one group, so we need to check if the group is already in the dictionary
            blocks[group] = []
            blocks[group].extend([block for block in group.Blocks])
            for sub_group in group.Groups:
                self.get_software_blocks(sub_group, blocks)
        return blocks