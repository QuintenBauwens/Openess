"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import tkinter as tk
from  tkinter import ttk, scrolledtext, messagebox

import pandas as pd
from utils.tabUI import Tab
from utils.tooltipUI import RadioSelectDialog
from core.file import File

class TabSummary(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("summary", master, main_class_instance, menubar, project, interface) #mainclass is instance of FileUI

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabProjectTree(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("project tree", master, main_class_instance, menubar, project, interface) #mainclass is instance of FileUI

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabFindBlock(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("find programblock", master, main_class_instance, menubar, project, interface) #mainclass is instance of FileUI

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabTags(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("project tags", master, main_class_instance, menubar, project, interface) #mainclass is instance of FileUI

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)


# TODO : DOCSTRINGS
class FileUI:
	def __init__(self, master, myproject, myinterface, status_icon=None):
		self.master = master
		self.project = myproject
		self.interface = myinterface
		self.myproject = myproject
		self.myinterface = myinterface
		self.status_icon = status_icon
		self.frame = None # Frame for the file UI set in the mainApp
		self.tabs = {}

		self.output_tab = None
		self.btn_export_output = None
		self.tab_summary = None

		self.initialize_file()


	def initialize_file(self):
		if self.myproject is None or self.myinterface is None:
			self.file = None
			return
		try:
			self.file = File(self.myproject, self.myinterface)
		except Exception as e:
			self.file = None
			message = f'Failed to initialize file object: {str(e)}'
			messagebox.showerror("ERROR", message)
			self.status_icon.change_icon_status("#FF0000", message)


	def update_project(self, myproject, myinterface):
		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface

			self.initialize_file()

			for tab_name, tab_instance in self.tabs.items():
				self.show_content(tab_instance)
			
			self.status_icon.change_icon_status("#39FF14", f'Updated project and interface to {myproject} and {myinterface}')


	def create_tab(self, tab):
		if self.frame is None:
			self.frame = ttk.Frame(self.master)
		# Clear existing widgets
		for widget in self.frame.winfo_children():
			widget.destroy()

		# Configure the frame to expand in both directions
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		# Section 1 for output_tab (all tabs have this section)
		section1 = ttk.Frame(self.frame)
		section1.grid(row=1, padx=5, pady=5, sticky="nsew")
		section1.columnconfigure(0, weight=1)
		section1.rowconfigure(0, weight=1)

		self.output_tab = scrolledtext.ScrolledText(section1, wrap=tk.WORD)
		self.btn_export_output = ttk.Button(self.frame, text="Export", command=lambda: self.export_content(tab), state=tk.NORMAL)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")
		self.btn_export_output.grid(row=1, column=1, sticky="nw", padx=10, pady=5)
		
		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)

		if tab.name == "find programblock":
			self.created_tab_find_block(tab)

		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab
		self.show_content(tab)
		return self.frame


	def created_tab_find_block(self, tab):
		# Section 2 for components specific to the tab
		section2 = ttk.Frame(self.frame)
		section2.grid(row=0, padx=10, pady=10)

		self.output_tab.config(height=5)
		ttk.Label(section2, text="block name").grid(row=0, column=0, pady=5, padx=5)
		self.entry_block_name = ttk.Entry(section2)
		self.entry_block_name.grid(row=0, column=1, pady=5, padx=5)
		section2.columnconfigure(1, weight=1)

		self.btn_find_block = ttk.Button(section2, text="Find", command=lambda: self.show_content(tab))
		self.btn_find_block.grid(row=0, column=2, pady=5, padx=5)


	def show_content(self, tab):
		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)
			content = f'Please open a project to view the {tab.name}.'
			self.status_icon.change_icon_status("#FFFF00", content)
		else:
			try:
				if tab.name == "summary":
					content, _ = self.file.file_summary()
				elif tab.name == "project tree":
					content, _ = self.file.projectTree()
				elif tab.name == "find programblock":
					if self.entry_block_name.get():
						block_name = self.entry_block_name.get()
						bool, content = self.file.find_block_location(block_name)
						if not bool:
							self.btn_export_output.config(state=tk.DISABLED)
						else:
							self.btn_export_output.config(state=tk.NORMAL)
					else:
						content = "Please enter a block name to search for."
						self.status_icon.change_icon_status("#FFFF00", content)
						self.btn_export_output.config(state=tk.DISABLED)
				elif tab.name == "project tags":
					content = self.file.show_tagTables()
				
				self.status_icon.change_icon_status("#39FF14", f'{tab.name} retrieved successfully')
			except Exception as e:
				content = f"An error occurred: {str(e)}"
				self.status_icon.change_icon_status("#FF0000", content)
		self.output_tab.delete(1.0, tk.END)
		if not isinstance(content, pd.DataFrame):
			self.output_tab.insert(tk.END, content)
		else:
			self.output_tab.insert(tk.END, content.to_string())


	def export_content(self, tab):
		'''method that is linked to the button in the node list tab, to export the function output of Nodes logic to a file'''

		if self.myproject and self.myinterface:
			dialog_options = ["*.csv", "*.xlsx", "*.json"]
			
			if tab.name == "find programblock":
				dialog_options = ["*.xlm"]

			dialog = RadioSelectDialog(self.master, "Choose export option", dialog_options)
			try:
				selected_tab = tab.name
				content = self.file.export_data(dialog.filename, dialog.selection, selected_tab, self)
				messagebox.showinfo("Export successful", content)
				self.status_icon.change_icon_status("#39FF14", content)
			except ValueError as e:
				content = f"Export failed: {str(e)}"
				messagebox.showwarning("WARNING", content)
				self.status_icon.change_icon_status("#FF0000", content)
		else:
			self.btn_export_output.config(state=tk.DISABLED)
			content = f"Please open a project to view the {tab.name}."
			self.status_icon.change_icon_status("#FFFF00", content)
			messagebox.showwarning("WARNING", content)