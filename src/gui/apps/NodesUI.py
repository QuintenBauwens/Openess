"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import tempfile
import webview
import tkinter as tk
import os

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
		self.tab_content = self.main_class_instance.create_tab(self)

class TabFindDevice(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("find device", project, main_class_instance)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabAddressCheck(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("address check", project, main_class_instance)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabDisplayConnections(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("connections", project, main_class_instance)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)


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
				self.show_content(tab_instance)
			
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

		self.btn_refresh = ttk.Button(self.section2, text="Refresh", command=lambda: self.show_content(tab, reload=True))
		self.btn_refresh.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.output_tab = scrolledtext.ScrolledText(self.section1, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		if self.myproject is None:
			self.disable_buttons()

		if tab.name == "node list":
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
		self.output_tab = scrolledtext.ScrolledText(self.section1, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

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
					content = self.node.show_node_table(reload=reload)
				elif tab.name == "find device":
					if self.entry_plc_name.get() and self.entry_device_name.get():
						plc_name = self.entry_plc_name.get()
						device_name = self.entry_device_name.get()
						content = self.node.find_device_nodes(plc_name.upper(), device_name.upper(), reload=reload)
					else:
						content = "Please enter both the PLC name and device name."
				elif tab.name == "address check":
					if self.entry_address.get():
						address = self.entry_address.get()
						content = self.node.address_exists(address, reload=reload)
					else:
						content = "Please enter an address to check."
				elif tab.name == "connections":
					self.display_connections_rendered(reload=reload)
					return

				logger.debug(f"Content for tab '{tab.name}' has been set successfully")
				self.status_icon.change_icon_status("#00FF00", f"{tab.name} has been set successfully")
			except Exception as e:
				message = f"Failed to show content in '{tab.name}':"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")
				content = str(e)

		if hasattr(self, 'output_tab') and self.output_tab:
			self.output_tab.delete(1.0, tk.END)
			self.output_tab.insert(tk.END, content)

	def display_connections_rendered(self, reload=False):
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
			logger.debug("Webview window already open")
			self.webview_window.show()
			return

		self.webview_frame = ttk.Frame(self.frame)
		self.webview_frame.pack(fill=tk.BOTH, expand=True)

		self.info_label = ttk.Label(self.webview_frame, text='Close the graph window to return to the main window.')
		self.info_label.pack(pady=10, padx=10, anchor=tk.N)

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
		if self.webview_window is None and self.temp_path:
			self.webview_window = webview.create_window("Connections Graph", self.temp_path, width=800, height=600)
			webview.start()

	def on_closing(self):
		if self.webview_window:
			self.webview_window.destroy()
		if self.temp_path:
			try:
				os.remove(self.temp_path)
			except Exception:
				message = f"Closed the webview windows successfully but failed to remove the temporary file at: {self.temp_path}"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status(message)
		logger.debug("Closed the webview window and cleaned up the temporary file successfully")
		self.master.deiconify()

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
			
			try:
				message = self.node.export_data(dialog.entryInput, dialog.selection, tab_name)
				messagebox.showinfo(f"Export successful: {message}")
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
			self.btn_get_node_list.config(state=tk.DISABLED)
			self.btn_export_node_list.config(state=tk.DISABLED)
			self.btn_find_device.config(state=tk.DISABLED)
			self.btn_check_address.config(state=tk.DISABLED)
		except Exception as e:
			pass


	def enable_buttons(self):
		'''Method to enable the buttons in the UI.'''
		try:
			self.btn_get_node_list.config(state=tk.NORMAL)
			self.btn_export_node_list.config(state=tk.NORMAL)
			self.btn_find_device.config(state=tk.NORMAL)
			self.btn_check_address.config(state=tk.NORMAL)
		except Exception as e:
			pass