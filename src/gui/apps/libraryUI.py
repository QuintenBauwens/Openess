import threading
import tkinter as tk
import pandas as pd

from tkinter import ttk, scrolledtext, messagebox
from pandastable import Table, TableModel

from utils.tabUI import Tab
from utils.tableDesignUI import DesignTable
from utils.dialogsUI import ExportDataDialog, LibrarySettingsDialog, InfoDialog
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class TabConnection(Tab):
	def __init__(self, project, main_class_instance):
		super().__init__("content", project, main_class_instance)
	
	def create_tab_content(self):
		super().create_tab_content()

class TabValidate(Tab):
	def __init__(self, project, main_class_instance):
		super().__init__("validate project blocks", project, main_class_instance)
	
	def create_tab_content(self):
		super().create_tab_content()


class LibraryUI:
	def __init__(self, project):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.master = project.master
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		self.status_icon = project.status_icon

		self.frame = None
		self.table_frame = None
		self.tabs = {}
		self.output_tab = None

		self.selected_settings = None
		self.loading_thread = None

		self.initialize_library()
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")


	def initialize_library(self):
		if self.myproject is None or self.myproject is None:
			return
		
		self.hardware = self.project.hardware
		self.plc_list = self.project.hardware.get_plc_devices()
		self.library = self.project.library


	def update_project(self):
		myproject = self.project.myproject
		myinterface = self.project.myinterface

		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface
			self.initialize_library()
			
			for tab_name, tab_instance in self.tabs.items():
				if myproject is not None:
					self.show_content(tab_instance)
				else:
					self.create_tab(tab_instance) # create empty tabs if project closes
			self.status_icon.change_icon_status("#00FF00", f'Updated project and interface to {myproject} and {myinterface}')


	def create_tab(self, tab):
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")

		if self.frame is None:
			self.frame = ttk.Frame(self.master)
		
		for widget in self.frame.winfo_children():
			widget.destroy()
		
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		# split the frame in sections, one for general items
		self.section1 = ttk.Frame(self.frame)
		self.section1.grid(row=1, column=5, padx=5, pady=5, sticky="nw")

		self.btn_export_output = ttk.Button(self.section1, text="Export", command=lambda: self.export_content(tab), state=tk.NORMAL)
		self.btn_export_output.grid(row=0, column=0, sticky="nw", padx=10, pady=5)

		self.btn_info = ttk.Button(self.section1, text="Info", command=lambda: self._show_info(tab), state=tk.NORMAL)
		self.btn_info.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.btn_table_settings = ttk.Button(self.section1, text="Settings", command=lambda: self._settings_window(tab), state=tk.NORMAL)
		self.btn_table_settings.grid(row=2, column=0, sticky="nw", padx=10, pady=5)

		self.btn_refresh = ttk.Button(self.section1, text="Refresh", command=lambda: self._start_thread(tab, reload=True), state=tk.NORMAL)
		self.btn_refresh.grid(row=3, column=0, sticky="nw", padx=10, pady=5)

		self.section2 = ttk.Frame(self.frame)
		self.section2.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
		self.section2.columnconfigure(0, weight=1)
		self.section2.rowconfigure(0, weight=1)

		self.output_tab = scrolledtext.ScrolledText(self.section2, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		if self.myproject is not None:
			self.create_table_tab(tab)
		else:
			self.disable_buttons()
		
		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab
		
		self._load_content(tab)
		self._show_content(tab)
		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def create_table_tab(self, tab):
		logger.debug(f"Adding unique UI elements to tab '{tab.name}'")

		for widget in self.section2.winfo_children():
			widget.destroy()

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")

	
	def _start_thread(self, tab, reload=False):
		logger.thread(f"Starting thread for '{tab.name}'...")

		if self.loading_thread and self.loading_thread.is_alive():
			logger.thread(f"Thread for '{tab.name}' is already running...")
			return

		try:
			self.tab = tab
			tab.loading_screen.show_loading(f"Updating table on tab '{tab.name}', please wait")

			self.loading_thread = threading.Thread(target=self._load_content, args=(tab, reload))
			self.loading_thread.start()

			logger.thread('Checking thread status...')
			self.master.after(100, self._check_thread(tab, reload))
		except Exception as e:
			message = f"Error with starting the thread for '{tab.name}'"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def _check_thread(self, tab, reload):
		logger.thread(f"Thread of '{tab.name}' is alive, checking status...")
		if self.loading_thread and self.loading_thread.is_alive():
			self.master.after(100, lambda: self._check_thread(tab, reload))
		else:
			self.on_thread_finished(tab, reload)


	def on_thread_finished(self, tab, reload=False):
		try:
			message = f"Thread of '{tab.name}' finished"
			logger.thread(message)
			if self.myproject is None:
				return
			if tab.name == "content":
				self._update_table(tab, self.library_df)
			elif tab.name == "validate project blocks":
				self._update_table(tab, self.used_lib_blocks_df)
			
			if reload:
				logger.info(f"Reloaded data for tab '{tab.name}' succesfully")
		except Exception as e:
			message = f"Error on thread of 'settings table' finished:"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		finally:
			self.selected_settings = None
			tab.loading_screen.hide_loading()
			self.master.update_idletasks()


	def _load_content(self, tab, reload=False):
		try:
			if self.myproject is None:
				return
			
			if reload:
				logger.info(f"Reloading data for tab '{tab.name}'...")
			
			if self.selected_settings is not None:
				logger.debug(f"Changing the current table settings of tab '{tab.name}': {self.library.get_settings()} to {self.selected_settings}")
				self.library.set_settings(self.selected_settings)

			logger.debug(f"Retrieving data for tab '{tab.name}' with its table settings: {self.library.get_settings()}, reload: '{reload}'")
			if tab.name == "content":
				self.library_df = self.library.get_library_content(reload=reload)
			elif tab.name == "validate project blocks":
				self.used_lib_blocks_df= self.library.validate_used_blocks(reload=reload)
		except Exception as e:
			self.message_error = str(e)
			logger.error('Error loading data:', exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'Failed to load data for tab {tab.name}: {self.message_error}')
		logger.info(f"Data for menu-tab '{tab.name}' retrieved successfully")


	# def _set_content(self, tab):
	# 	logger.debug(f"Setting data of tab '{tab.name}'")

	# 	if self.selected_settings is not None:
	# 		logger.info(f"Applying new settings to table of menu-tab '{tab.name}', please wait...")
	# 		if tab.name == "content":
	# 			self._update_table(tab, (self.library_df, None))
	# 		if tab.name == "validate project blocks":
	# 			self._update_table(tab, (self.used_lib_blocks_df, self.used_lib_blocks_info))
	# 		self.selected_settings = None
	# 	else:
	# 		self._show_content(tab)
	# 	self.master.update_idletasks()


	def _show_content(self, tab):
		logger.info(f"Retrieving table with data of '{tab.name}'")
		
		if self.myproject is None:
			self.disable_buttons()
			message = f"Please open a project to view the content in '{tab.name}'."
			self.status_icon.change_icon_status("#FFFF00", message)
			logger.warning(message)
			self.output_tab.delete(1.0, tk.END)
			self.output_tab.insert(tk.END, message)
			return
		else:
			try:
				if hasattr(self, 'content_error'):
					raise Exception(self.message_error)

				if tab.name == "content":
					if isinstance(self.library_df, pd.DataFrame):
						self.enable_buttons()
						self.set_table(tab, self.library_df)

				elif tab.name == "validate project blocks":
					if isinstance(self.used_lib_blocks_df, pd.DataFrame):
						self.enable_buttons()
						self.set_table(tab, self.used_lib_blocks_df)

				message = f"Retrieved table on tab '{tab.name}' succesfully"
				self.status_icon.change_icon_status("#00FF00", message)
				logger.info(message)
			except Exception as e:
				message = f"Failed to instert data in the table of tab '{tab.name}':"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def set_table(self, tab, content):
		logger.debug(f"Inserting data in table of tab '{tab.name}'")
		
		try:
			if tab.name == "content":
				self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
				self.design_table1 = DesignTable(self.pt, content)
				# column, condition, value, color
				self.design_table1.add_color_conditions(
					[	
						('LibraryState', 'equal', 'Committed', '#90ee90'),
						('LibraryState', 'equal', 'InWork', '#FFFF00'),
						('Version', 'version_higher', self.library.system_lib_version, '#FF474C') # last to apply so it overwrites the other colors
					], apply_on='row'
					)
				self.pt = self.design_table1.apply_color_conditions()
				info = self.get_dataframe_info(tab)
			
			if tab.name == "validate project blocks":
				self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
				self.design_table2 = DesignTable(self.pt, content)
				self.design_table2.add_color_conditions(
					[
						('ConnectedToLibrary', 'equal', True, '#90ee90'),
						('LibraryState', 'equal', 'InWork', '#FFFF00'),
						('Version', 'version_higher', self.library.system_lib_version, '#FF474C')
					], apply_on='row'
					)
				self.pt = self.design_table2.apply_color_conditions()
				info = self.get_dataframe_info(tab)
		except Exception as e:
			message = f"Failed to insert data in table on '{tab.name}':"
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')

		self.pt.grid(row=0, column=0, sticky="nsew")
		self.pt.show()
		self.pt.redraw() # renew the table

		messagebox.showinfo("Library Connection", info)
		logger.debug(f"Data has been inserted succesfully in table of '{tab.name}': {info}")
		return


	def _update_table(self, tab, df):
		logger.debug(f"Updating table of tab '{tab.name}', with settings {self.selected_settings}")

		try:
			if isinstance(df, pd.DataFrame):
				self.pt.updateModel(TableModel(df))

				self.pt = self.design_table1.redesign_table(self.pt, self.library_df) if tab.name == "content" else (
					self.design_table2.redesign_table(self.pt, self.used_lib_blocks_df)
				)
				info = self.get_dataframe_info(tab)
				
				message = f'Table of tab {tab.name} updated successfully'
				self.status_icon.change_icon_status("#00FF00", message)
				messagebox.showinfo("Library Connection", info)
				logger.info(f"{message}: {info}")

				self.pt.show()
				self.pt.redraw()
		except Exception as e:
			message = f'Failed to update library connection: '
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def _settings_window(self, tab):
		logger.debug(f"Opening settings window to let the user change the table settings")
		window_info = 'Settings for table view, be aware it can reduce the workload.'
		settings = [key for key in self.library.settings.keys()]

		if tab.name == "content":
			settings = [key for key in self.library.settings.keys() if key != 'warning_column']
		default_values = [self.library.settings[key] for key in settings]
		
		try:
			popup = LibrarySettingsDialog(self.master, "Changes table settings", options=settings, default_values=default_values, window_info=window_info)
			self.selected_settings = popup.get_selectionInput()
		except Exception as e:
			message = f'Failed to process settings window:'
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')

		if self.selected_settings:
			logger.debug(f"Settings retrieved successfully after closing settings window: {self.selected_settings}")
			self._start_thread(tab)


	def get_dataframe_info(self, tab):
		if tab.name == "content":
			library_df = self.library_df
			blocks_inWork = library_df['LibraryState'].value_counts().get('InWork', 0)
			blocks_committed = library_df['LibraryState'].value_counts().get('Committed', 0)
			info = (
				f'library contains a total of {len(library_df)} blocks.\n\n'
				f'\tBlocks in work: {blocks_inWork}\n'
				f'\tBlocks committed: {blocks_committed}\n'
			)
		elif tab.name == "validate project blocks":
			used_lib_blocks_df = self.used_lib_blocks_df
			total_blocks = len(used_lib_blocks_df)
			connected_blocks = used_lib_blocks_df['ConnectedToLibrary'].value_counts().get(True, 0)
			outdated_blocks = used_lib_blocks_df['ConnectedToLibrary'].value_counts().get('Outdated', 0)
			disconnected_blocks = used_lib_blocks_df['ConnectedToLibrary'].value_counts().get(False, 0)
			instanceDB = used_lib_blocks_df['Type'].value_counts().get('InstanceDB', 0)

			info = (
				f'Connection between the library and a total of {total_blocks} project blocks.\n\n' 
				f'\tConnected blocks: {connected_blocks}\n'  
				f'\tDisconnected blocks: {disconnected_blocks}\n\n' 
				f'*official blocks are blocks that are connected to the library.'
			)
		return info


	def _show_info(self, tab):
		logger.debug(f"Showing information about the table of tab '{tab.name}'")
		if tab.name == "content":
			info = f"This tab '{tab.name}' shows the content within the library of the project: \n"
		elif tab.name == "validate project blocks":
			info = f"This tab '{tab.name}' shows the connection between the library and the project blocks: \n"

		info += self.get_dataframe_info(tab)
		legenda = self.design_table1.get_legenda() if tab.name == "content" else (
			self.design_table2.get_legenda()
		)
		dialog = InfoDialog(self.master, "Information about the table", legenda, window_info=info)
		logger.info(f"Information about the table of tab '{tab.name}' has been shown successfully")


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
			dialog = ExportDataDialog(self.master, "Choose export option", extensions, label_name="file name")
			extension = dialog.get_selectionInput()
			file_name = dialog.get_entryInput()

			try:
				selected_tab = tab.name
				message = self.library.export_data(file_name, extension, selected_tab, self)
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
			self.btn_table_settings.config(state=tk.DISABLED)
			self.btn_info.config(state=tk.DISABLED)
		except Exception as e:
			pass

	def enable_buttons(self):
		try:
			self.btn_export_output.config(state=tk.NORMAL)
			self.btn_table_settings.config(state=tk.NORMAL)
			self.btn_info.config(state=tk.NORMAL)
			self.btn_refresh.config(state=tk.NORMAL)
		except Exception as e:
			pass