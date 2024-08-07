"""
Description: 
base class for the tabs in the main.py file to dynamically import the tabs from the apps folder
the menu head-item is created by
it contains the execute method that is called when the tab is selected in the main menu

Author: Quinten Bauwens
Last updated: 08/07/2024
"""

from tkinter import ttk

# TODO : DOCSTRING
class Tab:
	def __init__(self, name, master, main_class_instance, menubar, project=None, interface=None):
		self.name = name
		self.master = master
		self.main_class_instance = main_class_instance
		self.myproject = project
		self.myinterface = interface
		self.content_frame = None
		self.tab_content = None
		self.menubar = menubar
		
		self.create_tab_content()


	def execute(self, project, interface):
		'''
		method to execute the tab content when the tab is selected in the main menu
		if the content already exists, it will be shown, otherwise it will be created
		
		'''
		self.project = project
		self.interface = interface
		if self.content_frame is None:
			self.create_tab_content()
		if self.content_frame:
			self.content_frame.pack(fill="both", expand=True)
	
	def create_tab_content(self):
		pass
		# if self.content_frame is None:
		# 	self.content_frame = ttk.Frame(self.master)
		# if self.tab_content is None:
		# 	self.tab_content = self.main_class_instance.create_tab_content()
		# 	if self.tab_content:
		# 		self.tab_content.pack(in_=self.content_frame, fill="both", expand=True)