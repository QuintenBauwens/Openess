"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import threading
import tkinter as tk
import pandas as pd
from tkinter import ttk, scrolledtext, messagebox
from pandastable import Table

from utils.tabUI import Tab
from utils.dialogsUI import ExportDataDialog
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class TabSummary(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("summary", project, main_class_instance) #mainclass is instance of FileUI

	def create_tab_content(self):
		super().create_tab_content()

class TabProjectTree(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("project tree", project, main_class_instance) #mainclass is instance of FileUI

	def create_tab_content(self):
		super().create_tab_content()

class TabFindBlock(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("find programblock", project, main_class_instance) #mainclass is instance of FileUI

	def create_tab_content(self):
		super().create_tab_content()

class TabTags(Tab):
	'''class to create the menu sub-items for the file head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("project tags", project, main_class_instance) #mainclass is instance of FileUI

	def create_tab_content(self):
		super().create_tab_content()


# TODO : DOCSTRINGS
class FileUI:
	def __init__(self, project):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.master = project.master
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		self.status_icon = project.status_icon

		self.frame = None # Frame for the file UI set in the mainApp
		self.table_frame = None
		self.tabs = {}

		self.output_tab = None
		self.btn_export_output = None
		self.loading_thread = None
		self.tab_summary = None

		self.initialize_file()
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")


	def initialize_file(self):
		if self.myproject is None or self.myinterface is None:
			return
		
		self.file = self.project.file


	def update_project(self):
		myproject = self.project.myproject
		myinterface = self.project.myinterface
		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface

			self.initialize_file()

			for tab_name, tab_instance in self.tabs.items():
				if myproject is not None:
					self.show_content(tab_instance)
				else:
					self.create_tab(tab_instance)
			
			self.status_icon.change_icon_status("#00FF00", f'Updated project and interface to {myproject} and {myinterface}')


	def create_tab(self, tab):
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")
		
		if self.frame is None:
			self.frame = ttk.Frame(self.master)
		# clear existing widgets
		for widget in self.frame.winfo_children():
			widget.destroy()

		# configure the frame to expand in both directions
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		# section 1 for content 
		self.section1 = ttk.Frame(self.frame)
		self.section1.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
		self.section1.columnconfigure(0, weight=1)
		self.section1.rowconfigure(0, weight=1)

		self.output_tab = scrolledtext.ScrolledText(self.section1, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		# section 2 for general buttons
		self.section2 = ttk.Frame(self.frame)
		self.section2.grid(row=1, column=5, padx=5, pady=5, sticky="nw")

		self.btn_export_output = ttk.Button(self.section2, text="Export", command=lambda: self.export_content(tab), state=tk.NORMAL)
		self.btn_export_output.grid(row=0, column=0, sticky="nw", padx=10, pady=5)
		self.btn_refresh = ttk.Button(self.section2, text="Refresh", command=lambda: self._start_thread(tab, reload=True))
		self.btn_refresh.grid(row=1, column=0, sticky="nw", padx=10, pady=5)
		
		if self.myproject is None:
			self.disable_buttons()

		if tab.name == "find programblock":
			self.created_tab_find_block(tab)
		elif tab.name == "project tags" and self.myproject is not None:
			self.created_tab_tags(tab)

		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab
		
		self.show_content(tab)
		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def created_tab_find_block(self, tab):
		logger.debug(f"Adding unique UI elements to tab '{tab.name}'")
		self.output_tab.config(height=5)
		# section 3 for components specific to the tab
		section3 = ttk.Frame(self.frame)
		section3.grid(row=0, padx=10, pady=10)

		ttk.Label(section3, text="block name").grid(row=0, column=0, pady=5, padx=5)

		self.entry_block_name = ttk.Entry(section3)
		self.entry_block_name.grid(row=0, column=1, pady=5, padx=5)

		self.btn_find_block = ttk.Button(section3, text="Find", command=lambda: self._start_thread(tab))
		self.btn_find_block.grid(row=0, column=2, pady=5, padx=5)

		section3.columnconfigure(1, weight=1)


	def created_tab_tags(self, tab):
		logger.debug(f"Adding unique UI elements to tab '{tab.name}'")

		# clear existing widgets in section1
		for widget in self.section1.winfo_children():
			widget.destroy()

		# configure the grid for section1 to allow the table to expand
		self.table_frame = ttk.Frame(self.section1)
		self.table_frame.grid(row=0, column=0, sticky="nsew")


	def _start_thread(self, tab, reload=False):
		logger.thread(f"Starting thread for '{tab.name}'...")

		if self.loading_thread and self.loading_thread.is_alive():
			logger.thread(f"Thread for '{tab.name}' is already running...")
			return

		try:
			self.tab = tab
			if tab.name == "project tags":
				tab.loading_screen.show_loading(f"Updating table on tab '{tab.name}', please wait", progress=True)
			elif tab.name == "find programblock":
				tab.loading_screen.show_loading(f"Searching for block '{self.entry_block_name.get()}', please wait")
			else:
				tab.loading_screen.show_loading(f"Updating content for tab '{tab.name}', please wait")

			self.loading_thread = threading.Thread(target=self.show_content, args=(tab, reload))
			self.loading_thread.start()

			logger.thread('Checking thread status...')
			self.master.after(100, self._check_thread(tab))
		except Exception as e:
			message = f"Error with starting the thread for '{tab.name}'"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def _check_thread(self, tab):
		logger.thread(f"Thread of '{tab.name}' is alive, checking status...")
		if self.loading_thread and self.loading_thread.is_alive():
			self.master.after(100, lambda: self._check_thread(tab))
		else:
			self.on_thread_finished(tab)


	def on_thread_finished(self, tab):
		try:
			message = f"Thread of '{tab.name}' finished"
			logger.thread(message)
		except Exception as e:
			message = f"Error on thread of {tab.name}:"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		finally:
			self.selected_settings = None
			tab.loading_screen.hide_loading()
			self.master.update_idletasks()


	def show_content(self, tab, reload=False):
		logger.debug(f"Setting content of tab '{tab.name}'...")

		if self.myproject is None:
			self.disable_buttons()
			content = f"Please open a project to view the content in '{tab.name}'."
			logger.warning(content)
			self.status_icon.change_icon_status("#FFFF00", content)
		else:
			try:
				if tab.name == "summary":
					content, _ = self.file.file_summary(reload=reload)
				elif tab.name == "project tree":
					content, _ = self.file.projectTree(reload=reload)
				elif tab.name == "find programblock":
					if self.entry_block_name.get():
						block_name = self.entry_block_name.get()
						content = self.file.find_block_location(block_name, reload=reload)
						if content is not None:
							self.enable_buttons()
						else:
							self.disable_buttons()
							content = f"No block has been found with name '{block_name}'"
					else:
						content = "Please enter a block name to search for."
						logger.warning(content)
						self.status_icon.change_icon_status("#FFFF00", content)
				elif tab.name == "project tags":
					content = self.file.show_tagTables(reload=reload)
					logger.debug(f"Inserting tags into table if there has been a dataframe retrieved: '{isinstance(content, pd.DataFrame)}'")
					if isinstance(content, pd.DataFrame):
						# create the table, allowing it to expand to fill all available space
						self.enable_buttons()
						self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
						self.pt.grid(row=0, column=0, sticky="nsew")
						self.pt.show()
						self.pt.redraw() # redraw the table to ensure the table isnt empty
					else:
						raise Exception(f"Failed to show content in '{tab.name}' due to retrieved content not being a dataframe: '{type(content)}'")
				logger.debug(f"Content '{type(content)}' for tab '{tab.name}' has been set successfully")
				self.status_icon.change_icon_status("#00FF00", f'{tab.name} has been set successfully')
			except Exception as e:
				message = f"Failed to show content in '{tab.name}':"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		if tab.name == "project tags" and self.myproject is not None:
			return
		self.output_tab.delete(1.0, tk.END)
		self.output_tab.insert(tk.END, content)


	def export_content(self, tab):
		'''method that is linked to the button in the node list tab, to export the function output of Nodes logic to a file'''
		logger.debug(f"Exporting content from tab '{tab.name}'...")
		
		extensions = ["*.csv", "*.xlsx", "*.json"]

		if self.myproject is None:
			self.disable_buttons()
			message = f"Please open a project to view the '{tab.name}'."
			messagebox.showwarning("WARNING", message)
			self.status_icon.change_icon_status("#FFFF00", message)
		else:
			if tab.name == "find programblock":
				extensions = ["*.xlm"]
			dialog = ExportDataDialog(self.master, "Choose export option", extensions, label_name="file name")

			try:
				selected_tab = tab.name
				message = self.file.export_data(dialog.entryInput, dialog.selectionInput, selected_tab, self)
				messagebox.showinfo("Export successful", message)
				logger.info(f"Export successful: {message}")
				self.status_icon.change_icon_status("#00FF00", message)
			except Exception as e:
				message = f"Export failed:"
				messagebox.showwarning("WARNING", f'{message} {str(e)}')
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def disable_buttons(self):
		try:
			self.btn_export_output.config(state=tk.DISABLED)
		except Exception as e:
			pass


	def enable_buttons(self):
		try:
			self.btn_export_output.config(state=tk.NORMAL)
			self.btn_refresh.config(state=tk.NORMAL)
			self.btn_find_block.config(state=tk.NORMAL)
		except Exception as e:
			pass