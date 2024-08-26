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
from utils.logger_config import get_logger

logger = get_logger(__name__)

# all the menu sub-items are defined here
class TabNodes(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("node list", project, main_class_instance) #mainclass is nodesUI 

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_node_list_tab(self)

class TabFindDevice(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("find device", project, main_class_instance)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_find_device_tab(self)

class TabAddressCheck(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("address check", project, main_class_instance)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_check_address_tab(self)

class TabDisplayConnections(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, project, main_class_instance):
		super().__init__("connections", project, main_class_instance)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_display_connections_tab(self)


# TODO : tab creating has to be optimezed, refer to fileUI.py/libraryUI.py
class NodesUI:
	"""
	The NodesUI class represents the user interface for managing nodes in a project.

	Attributes:
		master (object): The master widget for the UI.
		myproject (object): The project object.
		myinterface (object): The interface object.
		status_icon (object): The status icon object.
		frame (object): The frame for the nodes UI set in the mainApp.
		node (object): The node object.
		output_node_list (object): The output area for displaying the node list.
		output_find_device (object): The output area for displaying the find device results.
		output_check_address (object): The output area for displaying the check address results.
		btn_get_node_list (object): The button for getting the node list.
		btn_export_node_list (object): The button for exporting the node list.
		btn_find_device (object): The button for finding devices.
		btn_check_address (object): The button for checking addresses.
		entry_plc_name (object): The entry field for the PLC name.
		entry_device_name (object): The entry field for the device name.
		entry_address (object): The entry field for the IP address.

	Methods:
		__init__(master, myproject, myinterface, status_icon=None):
			Initializes the NodesUI object.
		update_project(myproject, myinterface):
			Overwrites the previous project and interface with the new ones and reinitializes the node object.
		initialize_node():
			Initializes the node object even if the project or interface is None.
		create_node_list_tab():
			Sets up the node list tab-screen.
		create_find_device_tab():
			Sets up the find device tab-screen.
		create_check_address_tab():
			Sets up the check address tab-screen.
		show_node_list():
			Retrieves the function output in the nodes logic to get the node list.
		export_node_list():
			Exports the function output of Nodes logic to a file.
		find_nodes():
			Retrieves the function output in the nodes logic to find the nodes based on the PLC and device name.
		check_address():
			Retrieves the function output in the nodes logic to check if an address exists in the project.
	"""

	def __init__(self, project):
		"""
		Initializes the NodesUI object.

		Args:
			master (object): The master widget for the UI.
			myproject (object): The project object.
			myinterface (object): The interface object.
			status_icon (object, optional): The status icon object. Defaults to None.
		"""

		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.master = project.master
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		self.status_icon = project.status_icon

		self.frame = None # frame for the nodesUI, is being set in the mainApp
		self.canvas = None
		self.node = None
		self.webview_window = None
		self.temp_path = None

		self.output_node_list = None
		self.output_find_device = None
		self.output_check_address = None

		self.btn_get_node_list = None
		self.btn_export_node_list = None
		self.btn_export_graph = None
		self.btn_find_device = None
		self.btn_check_address = None

		self.initialize_node()
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")


	def clear_widgets(self):
		"""Safely destroy widgets and clear references."""

		logger.debug("Clearing widgets in NodesUI frame from previous project")

		if self.canvas:
			self.canvas.get_tk_widget().destroy()
			self.canvas = None
		if self.frame:
			for widget in self.frame.winfo_children():
				widget.destroy()


	def initialize_node(self):
		'''Initialize the node object even if the project or interface is None, 
		so the screens with limited features can be opened without a project.

		Args:
			None

		Returns:
			None

		Raises:
			None
		'''

		if self.myproject is None or self.myinterface is None:
			return
		
		self.node = self.project.nodes


	def update_project(self):
		'''Overwrites the previous project and interface with the new ones and reinitializes the node object.

		Args:
			myproject (type): The new project object.
			myinterface (type): The new interface object.

		Returns:
			None
		'''

		myproject = self.project.myproject
		myinterface = self.project.myinterface

		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface
			
			self.clear_widgets()
			self.initialize_node()
			self.create_display_connections_tab()

			self.status_icon.change_icon_status("#00FF00", f"Updated project and interface to {myproject} and {myinterface}")


	def create_node_list_tab(self, tab):
		'''Setup for the node list tab-screen, with a button to get the node list.

		This method creates a tab in the GUI application for displaying the node list. If the tab already exists, it selects the existing tab. Otherwise, it creates a new tab and adds it to the notebook.

		The tab contains a button labeled "Get Node List" which triggers the show_node_list method when clicked. It also includes a scrolled text widget for displaying the output of the node list.

		Returns:
			None
		'''
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")

		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		for widget in self.frame.winfo_children():
			widget.destroy()

		self.btn_get_node_list = ttk.Button(self.frame, text="Get Node List", command=self.show_node_list)
		self.btn_export_node_list = ttk.Button(self.frame, text="Export", command=lambda: self.export_content(tab.name), state=tk.NORMAL)

		self.btn_get_node_list.grid(row=0, column=0, padx=10, pady=10)
		self.btn_export_node_list.grid(row=1, column=1, sticky="nw", padx=10, pady=10)

		if self.myproject is None:
			self.btn_export_node_list.config(state=tk.DISABLED)

		self.output_node_list = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD)
		self.output_node_list.grid(row=1, padx=10, pady=10, sticky="nsew")
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def create_find_device_tab(self, tab):
		'''Setup for the find device tab-screen, with entries for the PLC and device name and a button to find the nodes based on the input.

		Returns:
			None
		'''
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")

		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		# Clear existing widgets
		for widget in self.frame.winfo_children():
			widget.destroy()

		ttk.Label(self.frame, text="PLC Name:").pack(pady=5)
		self.entry_plc_name = ttk.Entry(self.frame)
		self.entry_plc_name.pack(pady=5)
		
		ttk.Label(self.frame, text="Device Name:").pack(pady=5)
		self.entry_device_name = ttk.Entry(self.frame)
		self.entry_device_name.pack(pady=5)

		self.btn_find_device = ttk.Button(self.frame, text="Find Device", command=self.find_nodes)
		self.btn_find_device.pack(pady=10)

		self.output_find_device = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, width=70, height=10)
		self.output_find_device.pack(padx=10, pady=10)

		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def create_check_address_tab(self, tab):
		'''Setup for the check address tab-screen.

		This method creates a tab in the GUI application for checking an IP address. It adds a label, an entry field for the address, a button to check the address, and an output area to display the results.

		If the tab already exists, it will be selected instead of creating a new one.

		Returns:
			None
		'''
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")

		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		# Clear existing widgets
		for widget in self.frame.winfo_children():
			widget.destroy()

		ttk.Label(self.frame, text="IP Address:").pack(pady=5)
		self.entry_address = ttk.Entry(self.frame)
		self.entry_address.pack(pady=5)

		self.btn_check_address = ttk.Button(self.frame, text="Check Address", command=self.check_address)
		self.btn_check_address.pack(pady=10)

		self.output_check_address = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, width=70, height=10)
		self.output_check_address.pack(padx=10, pady=10)

		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def create_display_connections_tab(self, tab):
		'''Setup for the display connections tab-screen.

		This method creates a tab in the GUI application for displaying the connections between devices. It adds a button to display the connections and an output area to display the results.

		If the tab already exists, it will be selected instead of creating a new one.

		Returns:
			None
		'''
		logger.info(f"Retrieving menu-tab '{tab.name}' and its content...")
	
		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		for widget in self.frame.winfo_children():
			widget.destroy()
		
		self.button_frame = ttk.Frame(self.frame)
		self.button_frame.pack(side=tk.TOP, pady=10, padx=10)

		self.btn_display_connections = ttk.Button(self.button_frame, text="Open interactive graph", command=self.display_connections_interactive)
		self.btn_display_connections.pack(side=tk.LEFT, padx=5)

		self.btn_export_graph = ttk.Button(self.button_frame, text="Export", command=lambda: self.export_content("connections"), state=tk.NORMAL)
		self.btn_export_graph.pack(side=tk.LEFT, padx=5)

		# Create a frame to hold the matplotlib graph
		self.graph_frame = ttk.Frame(self.frame)
		self.graph_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

		# Only call display_connections if a project is open
		if self.myproject is None and self.myinterface is None:
			self.btn_display_connections.config(state=tk.DISABLED)
			self.btn_export_graph.config(state=tk.DISABLED)
			self.display_no_project_message()
		else:
			self.display_connections_rendered()
		
		logger.info(f"Menu-tab '{tab.name}' loaded successfully")
		return self.frame


	def show_node_list(self):
		'''Method that is linked to the button in the node list tab.
		
		Retrieves the function output in the nodes logic to get the node list.
		If no project is open, it displays a message indicating that a project needs to be opened.
		If an error occurs during the retrieval of the node list, it displays the error message.
		'''
		logger.info("Retrieving node list...")

		if self.node is None:
			message = "Please open a project to view the node list."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
		else:
			try:
				content = self.node.show_node_table()
				logger.info("Node list retrieved successfully")
				self.status_icon.change_icon_status("#00FF00", "Node list retrieved successfully")
			except Exception as e:
				message = f"Error occurred while trying to retrieve node list:"
				logger.error(message)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		self.output_node_list.delete(1.0, tk.END)
		self.output_node_list.insert(tk.END, content)


	def find_nodes(self):
		'''Method that is linked to the button in the find device tab, to retrieve the function output in the nodes logic to find the nodes based on the PLC and device name.

		Returns:
			str: The output of the find_device_nodes function, which contains the nodes found based on the PLC and device name.

		Raises:
			Exception: If an error occurs during the execution of the find_device_nodes function.
		'''
		logger.info("Searching project for node...")

		if self.node is None:
			message = "Please open a project to find nodes."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
		elif not self.entry_plc_name.get() or not self.entry_device_name.get():
			message = "Please enter both the PLC name and device name."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
		else:
			try:
				plc_name = self.entry_plc_name.get()
				device_name = self.entry_device_name.get()
				logger.debug(f"Searching project for node {self.entry_device_name.get()} in plc {self.entry_plc_name.get()}...")
				content = self.node.find_device_nodes(plc_name.upper(), device_name.upper())
				logger.info("Retrieved search result successfully")
				self.status_icon.change_icon_status("#00FF00", "find_nodes retrieved successfully")
			except Exception as e:
				message = f"Error occurred trying to retrieve search result:"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		self.output_find_device.delete(1.0, tk.END)
		self.output_find_device.insert(tk.END, content)


	def check_address(self):
		'''Method that is linked to the button in the check address tab.
		Retrieves the function output in the nodes logic to check if an address exists in the project.

		Returns:
			str: The result of checking if the address exists in the project.
		'''
		logger.info("Searching project for node-address...")

		if self.node is None:
			message = "Please open a project to check addresses."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
		elif not self.entry_address.get():
			message = "Please enter an address to check."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
		else: 
			try:
				address = self.entry_address.get()
				content = self.node.address_exists(address)
				logger.info("Retrieved search result successfully")
				self.status_icon.change_icon_status("#00FF00", "Retrieved search result successfully")
			except Exception as e:
				message = f"Error occurred while trying retrieve search result:"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
		self.output_check_address.delete(1.0, tk.END)
		self.output_check_address.insert(tk.END, content)


	def display_connections_rendered(self):
		"""
		Display the rendered connections graph on the GUI canvas.

		If no project is open, a message will be displayed indicating that a project needs to be opened.
		If an error occurs during the rendering process, an error message will be displayed.

		Returns:
			None
		"""
		logger.info("Displaying the static connections graph...")

		if self.node is None:
			message = "Please open a project to display connections."
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)
			self.display_no_project_message(message)
			return
		try:
			fig, G = self.node.display_graph_rendered()

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


	def display_connections_interactive(self):
		"""
		Displays the connections interactively.

		If the webview window is already open, it will be shown.
		Otherwise, a new webview window will be created and displayed.

		Returns:
			None
		"""
		logger.info("Displaying the interactive connections graph...")

		if self.webview_window is not None:
			logger.debug("Webview window already open")
			self.webview_window.show()
			return

		self.webview_frame = ttk.Frame(self.frame)
		self.webview_frame.pack(fill=tk.BOTH, expand=True)

		self.info_label = ttk.Label(self.webview_frame, text=f'Close the graph window to return to the main window.')
		self.info_label.pack(pady=10, padx=10, anchor=tk.N)
		
		try:
			fig, G = self.node.display_graph_interactive()
			# save the figure to a temporary HTML file
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
			"""
			Create a webview window to display the connections graph.

			This method creates a webview window using the `webview.create_window` function
			and displays the connections graph using the specified `temp_path` file.
			The window is set to a width of 800 pixels and a height of 600 pixels.
			The `webview.start` function is called to start the webview event loop.

			Note: The `temp_path` attribute must be set before calling this method.

			"""
			logger.debug("Starting webview window for interactive connections graph...")

			self.master.withdraw()
			if self.webview_window is None and self.temp_path:
				self.webview_window = webview.create_window("Connections Graph", self.temp_path, width=800, height=600)
				webview.start()


	def on_closing(self):
		"""
		Callback method called when the window is being closed.
		It closes the webview window if it exists and cleans up any temporary files.
		"""
		
		# close the webview window if it exists
		if self.webview_window:
			self.webview_window.destroy()
		# clean up temporary file
		if self.temp_path:
			try:
				os.remove(self.temp_path)
			except Exception:
				message = f"Closed the webview windows succesfully but failed to remove the temporary file at: {self.temp_path}"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status(message)
		logger.debug("Closed the webview window and cleaned up the temporary file successfully")
		self.master.deiconify()


	def display_no_project_message(self, message="Please open a project to display the connections graph."):
		"""Method to display a message when no project is open."""

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
			self.btn_export_node_list.config(state=tk.DISABLED)
			self.btn_export_graph.config(state=tk.DISABLED)
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