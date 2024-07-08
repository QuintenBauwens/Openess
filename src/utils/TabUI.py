"""
Description: 
# base class for the tabs in the main.py file to dynamically import the tabs from the apps folder
# the menu head-item is created by
# it contains the execute method that is called when the tab is selected in the main menu

Author: Quinten Bauwens
Last updated: 
"""

from tkinter import ttk


class Tab:
	def __init__(self, name, master, main_class_instance, project=None, interface=None):
		self.name = name
		self.master = master
		self.main_class_instance = main_class_instance
		self.myproject = project
		self.myinterface = interface

		self.content_frame = None
		self.masterTitle = master.title()

	def execute(self, parent_frame, project, interface):
		'''
		method to execute the tab content when the tab is selected in the main menu
		if the content already exists, it will be shown, otherwise it will be created
		
		'''
		self.content_frame = ttk.Frame(parent_frame)
		self.create_tab_content()
		
		self.content_frame.pack(fill="both", expand=True)
	
	def create_tab_content(self):
		# Implement in subclasses
		pass
	