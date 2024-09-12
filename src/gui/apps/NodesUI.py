"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import tempfile
import threading
import pandas
import webview
import tkinter as tk
import os

from pandastable import Table
from tkinter import ttk, scrolledtext, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.tabUI import Tab
from utils.dialogsUI import ExportDataDialog
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class TabNodeList(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("node list", project, main_class_instance)
	
	def create_tab_content(self):
		super().create_tab_content()


class TabFindDevice(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("find device", project, main_class_instance)
	
	def create_tab_content(self):
		super().create_tab_content()

class TabAddressCheck(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("address check", project, main_class_instance)
	
	def create_tab_content(self):
		super().create_tab_content()

class TabDisplayConnections(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("connections", project, main_class_instance)

	def create_tab_content(self):
		super().create_tab_content()


class NodesUI:
	def __init__(self, project):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.master = project.master
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		self.status_icon = project.status_icon

		self.frame = None
		self.canvas = None
		self.node = None
		self.webview_window = None
		self.temp_path = None

		self.output_tab = None
		self.btn_export = None
		self.btn_refresh = None
		self.loading_thread = None
		self.tabs = {}

		self.initialize_node()
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

	def initialize_node(self):
		if self.myproject is None or self.myinterface is None:
			return
		
		self.node = self.project.nodes

	def update_project(self):
		myproject = self.project.myproject
		myinterface = self.project.myinterface
		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface
			
			self.initialize_node()
			
			for tab_name, tab_instance in self.tabs.items():
				if myproject is not None:
					self.show_content(tab_instance)
				else:
					self.create_tab(tab_instance)
			
			self.status_icon.change_icon_status("#00FF00", f"Updated project and interface to {myproject} and {myinterface}")

	def create_tab(self, tab):
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")

		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		for widget in self.frame.winfo_children():
			widget.destroy()

		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		self.section1 = ttk.Frame(self.frame)
		self.section1.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
		self.section1.columnconfigure(0, weight=1)
		self.section1.rowconfigure(0, weight=1)

		self.section2 = ttk.Frame(self.frame)
		self.section2.grid(row=1, column=5, padx=5, pady=5, sticky="nw")

		self.btn_export = ttk.Button(self.section2, text="Export", command=lambda: self.export_content(tab.name), state=tk.NORMAL)
		self.btn_export.grid(row=0, column=0, sticky="nw", padx=10, pady=5)

		# cant make thread for connections since it has to run in the main thread
		self.btn_refresh = ttk.Button(self.section2, text="Refresh", state=tk.NORMAL)
		if tab.name == "connections":
			self.btn_refresh.config(command=lambda: self.show_content(tab, reload=True))
		else:
			self.btn_refresh.config(command=lambda: self._start_thread(tab))
		self.btn_refresh.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.output_tab = scrolledtext.ScrolledText(self.section1, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		if self.myproject is None:
			self.disable_buttons()

		if tab.name == "node list" and self.myproject is not None:
			self.create_node_list_tab(tab)
		elif tab.name == "find device":
			self.create_find_device_tab(tab)
		elif tab.name == "address check":
			self.create_check_address_tab(tab)
		elif tab.name == "connections" and self.myproject is not None:
			self.create_display_connections_tab(tab)

		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab

		self.show_content(tab)
		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame

	def create_node_list_tab(self, tab):
		# clear existing widgets in section1
		for widget in self.section1.winfo_children():
			widget.destroy()
		
		self.nodeList_frame = ttk.Frame(self.section1)
		self.nodeList_frame.grid(row=0, column=0, sticky="nsew")

	def create_find_device_tab(self, tab):
		section3 = ttk.Frame(self.frame)
		section3.grid(row=0, padx=10, pady=10)

		ttk.Label(section3, text="PLC Name:").grid(row=0, column=0, pady=5, padx=5)
		self.entry_plc_name = ttk.Entry(section3)
		self.entry_plc_name.grid(row=0, column=1, pady=5, padx=5)

		ttk.Label(section3, text="Device Name:").grid(row=1, column=0, pady=5, padx=5)
		self.entry_device_name = ttk.Entry(section3)
		self.entry_device_name.grid(row=1, column=1, pady=5, padx=5)

		self.btn_find_device = ttk.Button(section3, text="Find Device", command=lambda: self.show_content(tab))
		self.btn_find_device.grid(row=0, column=2, columnspan=2, pady=5, padx=5)


	def create_check_address_tab(self, tab):
		section3 = ttk.Frame(self.frame)
		section3.grid(row=0, padx=10, pady=10)

		ttk.Label(section3, text="IP Address:").grid(row=0, column=0, pady=5, padx=5)
		self.entry_address = ttk.Entry(section3)
		self.entry_address.grid(row=0, column=1, pady=5, padx=5)

		self.btn_check_address = ttk.Button(section3, text="Check Address", command=lambda: self.show_content(tab))
		self.btn_check_address.grid(row=0, column=2, columnspan=2, pady=5, padx=5)


	def create_display_connections_tab(self, tab):
		# clear existing widgets in section1
		for widget in self.section1.winfo_children():
			widget.destroy()

		self.graph_frame = ttk.Frame(self.section1)
		self.graph_frame.grid(row=0, column=0, sticky="nsew")

		section3 = ttk.Frame(self.frame)
		section3.grid(row=0, padx=10, pady=10)

		self.btn_display_connections = ttk.Button(section3, text="Open interactive graph", command=self.display_connections_interactive)
		self.btn_display_connections.grid(row=0, column=0, sticky="nw", padx=10, pady=5)


	def _start_thread(self, tab, reload=False):
		logger.thread(f"Starting thread for '{tab.name}'...")

		if self.loading_thread and self.loading_thread.is_alive():
			logger.thread(f"Thread for '{tab.name}' is already running...")
			return

		try:
			self.tab = tab
			if tab.name == "find device":
				tab.loading_screen.show_loading(f"Finding device nodes of '{self.entry_device_name.get()}', please wait")
			elif tab.name == "address check":
				tab.loading_screen.show_loading(f"Checking address '{self.entry_address.get()}', please wait")
			else:
				tab.loading_screen.show_loading(f"Updating content on tab '{tab.name}', please wait")

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
				if tab.name == "node list":
					content = self.node.getNodeTable(reload=reload)
					if isinstance(content, pandas.DataFrame):
						nodesTable = Table(self.nodeList_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
						nodesTable.show()
						nodesTable.redraw()
						return
				elif tab.name == "find device":
					if self.entry_plc_name.get() and self.entry_device_name.get():
						plc_name = self.entry_plc_name.get()
						device_name = self.entry_device_name.get()
						df, content = self.node.find_device_nodes(plc_name.upper(), device_name.upper(), reload=reload)
					else:
						content = "Please enter both the PLC name and device name or refresh."
				elif tab.name == "address check":
					if self.entry_address.get():
						address = self.entry_address.get()
						df, content = self.node.address_exists(address, reload=reload)
					else:
						content = "Please enter an address to check or refresh."
				elif tab.name == "connections":
					self.display_connections_rendered(tab, reload=reload)
					return

				logger.debug(f"Content for tab '{tab.name}' has been set successfully")
				self.status_icon.change_icon_status("#00FF00", f"{tab.name} has been set successfully")
			except Exception as e:
				message = f"Failed to show content in '{tab.name}':"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")
				content = str(e)

		if hasattr(self, 'output_tab'):
			self.output_tab.delete(1.0, tk.END)
			self.output_tab.insert(tk.END, content)


	def display_connections_rendered(self, tab, reload=False):
		logger.info("Displaying the static connections graph...")

		if self.node is None:
			message = "Please open a project to display connections."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
			self.display_no_project_message(message)
			return
		try:
			fig, G = self.node.display_graph_rendered(reload=reload)

			if hasattr(self, 'canvas') and self.canvas:
				self.canvas.get_tk_widget().destroy()

			self.canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
			self.canvas.draw()

			self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
			logger.info("Connections graph displayed successfully")
			self.status_icon.change_icon_status("#00FF00", "display_connections retrieved successfully")
		except Exception as e:
			message = f"Error occurred while trying to display connections graph:"
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')

	def display_connections_interactive(self, reload=False):
		logger.info("Displaying the interactive connections graph...")

		if self.webview_window is not None:
			logger.debug("Interactive graph already open")
			self.webview_window.show()
			return

		self.webview_frame = ttk.Frame(self.frame)
		self.webview_frame.grid(row=2, column=0, sticky="nsew")

		try:
			fig, G = self.node.display_graph_interactive(reload=reload)
			with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
				fig.write_html(f, include_plotlyjs='cdn', full_html=True)
				self.temp_path = f.name
				logger.debug(f"Temporary file created under: {self.temp_path}")

			self.master.after(0, self.create_webview)
			logger.info("Interactive connections graph displayed successfully")
			self.status_icon.change_icon_status("#00FF00", "display_connections_interactive retrieved successfully")
		except Exception as e:
			message = f"Error occurred while trying to display interactive connections graph:"
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')

	def create_webview(self):
		logger.debug("Starting webview window for interactive connections graph...")

		self.master.withdraw()
		try:
			if self.webview_window is None and self.temp_path:
				self.webview_window = webview.create_window("Connections Graph", self.temp_path, width=800, height=600)
				webview.start()
		finally:
			self.on_closing()

	def on_closing(self):
		if self.webview_window is not None:
			self.webview_window.destroy()
			self.webview_window = None
		if self.temp_path:
			try:
				os.remove(self.temp_path)
			except Exception:
				message = f"Closed the webview windows successfully but failed to remove the temporary file at: {self.temp_path}"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status(message)
		self.master.deiconify()
		logger.debug("Closed the webview window and cleaned up the temporary file successfully")

	def display_no_project_message(self, message="Please open a project to display the connections graph."):
		for widget in self.graph_frame.winfo_children():
			widget.destroy()
	
		ttk.Label(self.frame, text=message).pack(pady=10, padx=10)
		self.status_icon.change_icon_status("#FFFF00", message)


	# TODO : add more file types
	def export_content(self, tab_name):
		'''Method that is linked to the button in the node list tab, to export the function output of Nodes logic to a file.

		Args:
			tab_name (str): The name of the tab where the export button is clicked.

		Returns:
			None

		Raises:
			ValueError: If the export fails due to an error.
		'''
		logger.debug(f"Exporting content from tab '{tab_name}'...")

		extensions = ["*.csv", "*.xlsx", "*.json"]

		if self.myproject is None:
			self.disable_buttons()
		else:
			if tab_name == "connections":
				extensions.append("*.png")
			dialog = ExportDataDialog(self.master, "Choose export option", extensions, label_name="file name")
			file_name = dialog.get_entryInput()
			extension = dialog.get_selectionInput()
			try:
				message = self.node.export_data(file_name, extension, tab_name, self)
				messagebox.showinfo(f"Export successful", {message})
				logger.info(f"Export successful: {message}")
				self.status_icon.change_icon_status("#00FF00", message)
			except Exception as e:
				message = f"Export failed: "
				messagebox.showwarning("WARNING", f"{message} {str(e)}")
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")


	def disable_buttons(self):
		'''Method to disable the buttons in the UI.'''
		try:
			self.btn_export.config(state=tk.DISABLED)
		except Exception as e:
			pass


	def enable_buttons(self):
		'''Method to enable the buttons in the UI.'''
		try:
			self.btn_export.config(state=tk.NORMAL)
			self.btn_find_device.config(state=tk.NORMAL)
			self.btn_check_address.config(state=tk.NORMAL)
		except Exception as e:
			pass