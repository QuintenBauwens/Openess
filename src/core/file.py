"""
Author: Quinten Bauwens
Last updated: 8/07/2024
"""

from collections import OrderedDict as od
import os
import pandas as pd

import clr
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf
from .hardware import Hardware

class File:
    def __init__(self, myproject, myinterface):
        self.myproject = myproject
        self.myinterface = myinterface

    def file_summary(self):
        self.name = self.myproject.Name
        self.creation_time = self.myproject.CreationTime
        self.last_modified = self.myproject.LastModified
        self.author = self.myproject.Author
        self.last_modified_by = self.myproject.LastModifiedBy
        self.history_entries = self.myproject.HistoryEntries

        text = f'Project Information\n' + \
                f'Name: \t\t\t {self.name}\n' + \
                f'Creation time:\t\t {self.creation_time}\n' + \
                f'Last Change:\t\t {self.last_modified}\n' + \
                f'Author:\t\t\t {self.author}\n' + \
                f'Last modified by:\t {self.last_modified_by}\n\n' + \
                f'Project History\n' + \
                f'DateTime\t\t Event\t\t\n'
        
        text += f'Project history\n'

        for event in self.history_entries:
            text += f'\t{event.DateTime}\t{event.Text}\n'

        return text

