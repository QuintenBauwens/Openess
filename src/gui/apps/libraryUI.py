import threading
import tkinter as tk
import pandas as pd

from tkinter import ttk, scrolledtext, messagebox
from pandastable import Table, TableModel

from utils.tabUI import Tab
from utils.tableDesignUI import DesignTable
from utils.loadingScreenUI import LoadScreen
from utils.dialogsUI import LibrarySettingsDialog
from utils.logger_config import get_logger
from core.hardware import Hardware
from core.library import Library

logger = get_logger(__name__)

class TabConnection(Tab):
	def __init__(self, master, content_frame, main_class_instance, menubar, project=None, interface=None):
		super().__init__("content", master, content_frame, main_class_instance, menubar, project, interface)
	
	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabValidate(Tab):
	def __init__(self, master, content_frame, main_class_instance, menubar, project=None, interface=None):
		super().__init__("validate project blocks", master, content_frame, main_class_instance, menubar, project, interface)
	
	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)


class LibraryUI:
	def __init__(self, master, myproject, myinterface, status_icon=None):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.master = master
		self.myproject = myproject
		self.myinterface = myinterface
		self.status_icon = status_icon

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
			self.library = None
			self.hardware = None
			self.plc_list = None
			return
		try:
			self.hardware = Hardware(self.myproject, self.myinterface)
			self.plc_list = self.hardware.get_plc_devices()
			self.library = Library(self.myproject, self.myinterface, self.plc_list)
		except Exception as e:
			self.library = None
			message = f'Failed to initialize library object:'
			messagebox.showerror("ERROR", f'{message} {str(e)}')
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def update_project(self, myproject, myinterface):
		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface

			self.initialize_library()
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

		self.btn_table_settings = ttk.Button(self.section1, text="Settings", command=lambda: self._settings_window(tab), state=tk.NORMAL)
		self.btn_table_settings.grid(row=1, column=0, sticky="nw", padx=10, pady=5)
		
		self.section2 = ttk.Frame(self.frame)
		self.section2.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
		self.section2.columnconfigure(0, weight=1)
		self.section2.rowconfigure(0, weight=1)

		self.output_tab = scrolledtext.ScrolledText(self.section2, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)
			self.btn_table_settings.config(state=tk.DISABLED)

		if tab.name == "content" and self.myproject is not None:
			self.create_content_tab(tab)
		elif tab.name == "validate project blocks" and self.myproject is not None:
			self.create_validate_tab(tab)
		
		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab
		
		self._load_content(tab)
		self._set_content(tab)
		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def create_content_tab(self, tab):
		logger.debug(f"Adding unique UI elements to tab '{tab.name}'")

		for widget in self.section2.winfo_children():
			widget.destroy()
		
		self.btn_table_settings = ttk.Button(self.section1, text="Settings", command=lambda: self._settings_window(tab), state=tk.NORMAL)
		self.btn_table_settings.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")

	
	def create_validate_tab(self, tab):
		logger.debug(f"Adding unique UI elements to tab '{tab.name}'")

		for widget in self.section2.winfo_children():
			widget.destroy()

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")


	def _load_content(self, tab, reload=False):
		try:
			if self.myproject is None:
				return
			
			if self.selected_settings is not None:
				logger.debug(f"Changing the current table settings of tab '{tab.name}': {self.library.get_settings()} to {self.selected_settings}")
				self.library.set_settings(self.selected_settings)

			logger.debug(f"Retrieving data for tab '{tab.name}' with its table settings: {self.library.get_settings()}, reload: {reload}")
			if tab.name == "content":
				self.library_df = self.library.get_library_content(reload=reload)
			elif tab.name == "validate project blocks":
				self.used_lib_blocks_df, self.used_lib_blocks_info = self.library.validate_used_blocks(reload=reload)
		except Exception as e:
			self.message_error = str(e)
			logger.error('Error loading data:', exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'Failed to load data for tab {tab.name}: {self.message_error}')
		logger.info(f"Data for menu-tab '{tab.name}' retrieved successfully")


	def _set_content(self, tab):
		logger.debug(f"Setting data of tab '{tab.name}'")

		if self.selected_settings is not None:
			logger.info(f"Applying new settings to table of menu-tab '{tab.name}', please wait...")
			if tab.name == "content":
				self._update_table(tab, (self.library_df, None))
			if tab.name == "validate project blocks":
				self._update_table(tab, (self.used_lib_blocks_df, self.used_lib_blocks_info))
			self.selected_settings = None
		else:
			self._show_content(tab)
		self.master.update_idletasks()


	def _show_content(self, tab):
		logger.info(f"Inserting data in table on tab '{tab.name}'")
		
		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)
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
						self.btn_export_output.config(state=tk.NORMAL)
						self.btn_table_settings.config(state=tk.NORMAL)
						self.set_table(tab, self.library_df)

				elif tab.name == "validate project blocks":
					if isinstance(self.used_lib_blocks_df, pd.DataFrame):
						self.btn_export_output.config(state=tk.NORMAL)
						self.btn_table_settings.config(state=tk.NORMAL)
						self.set_table(tab, self.used_lib_blocks_df, self.used_lib_blocks_info)

				message = f"Data has been inserted in the table succesfully on tab '{tab.name}' "
				self.status_icon.change_icon_status("#00FF00", message)
				logger.info(message)
			except Exception as e:
				message = f"Failed to instert data in the table on tab '{tab.name}':"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def set_table(self, tab, content, content_info=None):
		logger.debug(f"Setting table data on tab '{tab.name}'")
		
		try:
			if tab.name == "content":
				self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
				info = f'Library contains a total of {len(content)} blocks.'
			
			if tab.name == "validate project blocks":
				self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
				self.design_table = DesignTable(self.pt, content)
				self.design_table.add_color_conditions(
					[
						('ConnectedToLibrary', True, '#90ee90'),
						('ConnectedToLibrary', 'Outdated', '#FF474C')
					], apply_on='row'
					)
				self.design_table.add_color_condition(('Warning', 'NaN', 'lightred'), apply_on='col')
				self.pt = self.design_table.apply_color_conditions()

				info = f'Found a total of {content_info["total"]} used blocks in the project, of which {content_info["instanceDB"]} are instanceDB:\n\n' \
					f'\tofficial blocks: {content_info["connected"]}\n' \
					f'\tnon-official blocks: {content_info["disconnected"]}\n\n' \
					f'*official blocks are blocks that are connected to the library.'
		except Exception as e:
			message = f'Failed to set table with the data:'
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')

		self.pt.grid(row=0, column=0, sticky="nsew")
		self.pt.show()
		self.pt.redraw() # renew the table

		messagebox.showinfo("Library Connection", info)
		logger.debug(f"Table data on tab '{tab.name}' has been set successfully: {info}")
		return


	def _update_table(self, tab, content: tuple):
		logger.debug(f"Updating table on tab '{tab.name}', with settings {self.selected_settings}")

		content_df, content_info = content
		try:
			if isinstance(content_df, pd.DataFrame):
				self.pt.clearTable()
				self.pt.updateModel(TableModel(content_df))

				if tab.name == "content":
					self.pt = self.design_table.redesign_table(self.pt)
					info = f'Library contains a total of {len(content)} blocks.'

				elif tab.name == "validate project blocks": 
					self.pt = self.design_table.redesign_table(self.pt)
					info = f'Checked the connection between the library and a total of {content_info["total"]} library blocks.\n\n' \
							f'Connected blocks: {content_info["connected"]}\n' \
							f'Disconnected blocks: {content_info["disconnected"]}'
				
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
		logger.debug(f"Succesfully applied new settings {self.selected_settings} to table on tab {tab.name}")
		logger.info(f"Table of menu-tab '{tab.name}' updated successfully")


	def _settings_window(self, tab):
		logger.debug(f"Opening settings window for table on tab '{tab.name}' to let the user change the table settings")
		window_info = 'Settings for table view, be aware it can reduce the workload.'
		settings = [key for key in self.library.settings.keys()]
		default_values = [self.library.settings[key] for key in settings]

		try:
			popup = LibrarySettingsDialog(self.master, "Changes table settings", options=settings, default_values=default_values, window_info=window_info)
			self.selected_settings = popup.get_selection()
		except Exception as e:
			message = f'Failed to process settings window:'
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')

		if self.selected_settings:
			logger.debug(f"Settings retrieved successfully after closing settings window: {self.selected_settings}")
			reload = True if self.selected_settings != default_values else False
			self._start_settings_thread(tab, reload=reload)


	def _start_settings_thread(self, tab, reload):
		logger.debug('Starting settings thread...')

		if self.loading_thread and self.loading_thread.is_alive():
			logger.debug('Settings thread is already running...')
			return

		try:
			self.tab = tab
			self.loading_screen = LoadScreen(self.master, self.frame)
			self.loading_screen.show_loading(f"Applying table settings, please wait")

			self.loading_thread = threading.Thread(target=self._load_content, args=(tab, reload))
			self.loading_thread.start()

			logger.debug('Checking status of the settings thread...')
			self.master.after(100, self._check_settings_thread)
		except Exception as e:
			message = f'Something went wrong while starting the settings thread:'
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def _check_settings_thread(self):
		logger.debug("Thread is alive, checking status...")
		if self.loading_thread and self.loading_thread.is_alive():
			self.master.after(100, self._check_settings_thread)
		else:
			self.on_settings_thread_finished()


	def on_settings_thread_finished(self):
		try:
			logger.debug('Settings thread finished, applying new settings...')
			self._set_content(self.tab)
		except Exception as e:
			message = f'Error on settings thread finished:'
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		finally:
			self.loading_screen.hide_loading()
			self.master.update_idletasks()