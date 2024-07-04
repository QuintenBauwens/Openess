"""
Description: 
# base class for the tabs in the main.py file to dynamically import the tabs from the apps folder
# the menu head-item is created by
# it contains the execute method that is called when the tab is selected in the main menu

Author: Quinten Bauwens
Last updated: 
"""

from  tkinter import ttk

class Tab:
    def __init__(self, name):
        self.name = name
        self.content_frame = None

    def execute(self, content_frame):
        print(f"Executing {self.name} tab")
        self.content_frame = content_frame
        
        # implement the tab content
        self.create_tab_content()

    def create_tab_content(self):
        # this method should be implemented in the subclasses
        raise NotImplementedError("Subclasses must implement create_tab_content method")