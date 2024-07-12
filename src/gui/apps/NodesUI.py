"""

Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import tkinter as tk
from  tkinter import ttk, scrolledtext, messagebox
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

from utils.tabUI import Tab
from utils.tooltipUI import RadioSelectDialog
from core.nodes import Nodes

# all the menu sub-items are defined here
class TabNodes(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, master, main_class_instance, project=None, interface=None):
		super().__init__("node list", master, main_class_instance, project, interface) #mainclass is nodesUI 

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_node_list_tab(self)

class TabFindDevice(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, master, main_class_instance, project=None, interface=None):
		super().__init__("find device", master, main_class_instance, project, interface)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_find_device_tab()

class TabAddressCheck(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, master, main_class_instance, project=None, interface=None):
		super().__init__("address check", master, main_class_instance, project, interface)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_check_address_tab()

class TabDisplayConnections(Tab):
	'''class to create the menu sub-items for the nodes head-item in the main menu'''

	def __init__(self, master, main_class_instance, project=None, interface=None):
		super().__init__("connections", master, main_class_instance, project, interface)

	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_display_connections_tab()


# TODO : can be optimized more, see fileUI.py
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

	def __init__(self, master, myproject, myinterface, status_icon=None):
		"""
		Initializes the NodesUI object.

		Args:
			master (object): The master widget for the UI.
			myproject (object): The project object.
			myinterface (object): The interface object.
			status_icon (object, optional): The status icon object. Defaults to None.
		"""
		self.master = master
		self.myproject = myproject
		self.myinterface = myinterface
		self.status_icon = status_icon
		self.frame = None # Frame for the nodes UI set in the mainApp
		self.canvas = None
		self.figure = None

		self.node = None

		self.output_node_list = None
		self.output_find_device = None
		self.output_check_address = None

		self.btn_get_node_list = None
		self.btn_export_node_list = None
		self.btn_export_graph = None
		self.btn_find_device = None
		self.btn_check_address = None

		self.initialize_node()


	def clear_widgets(self):
		"""Safely destroy widgets and clear references."""

		if self.canvas:
			self.canvas.get_tk_widget().destroy()
			self.canvas = None
		if self.figure:
			plt.close(self.figure)
			self.figure = None
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
			self.node = None
			return
		
		try:
			self.node = Nodes(self.myproject, self.myinterface)

		except Exception as e:
			self.node = None
			message = f"Failed to initialize node object: {str(e)}"
			messagebox.showerror("ERROR", message)
			self.status_icon.change_icon_status("#FF0000", message)


	def update_project(self, myproject, myinterface):
		'''Overwrites the previous project and interface with the new ones and reinitializes the node object.

		Args:
			myproject (type): The new project object.
			myinterface (type): The new interface object.

		Returns:
			None
		'''

		self.clear_widgets()
		self.myproject = myproject
		self.myinterface = myinterface
		self.initialize_node()

		self.create_display_connections_tab()

		self.status_icon.change_icon_status("#39FF14", f"Updated project and interface to {myproject} and {myinterface}")



	def create_node_list_tab(self, tab):
		'''Setup for the node list tab-screen, with a button to get the node list.

		This method creates a tab in the GUI application for displaying the node list. If the tab already exists, it selects the existing tab. Otherwise, it creates a new tab and adds it to the notebook.

		The tab contains a button labeled "Get Node List" which triggers the show_node_list method when clicked. It also includes a scrolled text widget for displaying the output of the node list.

		Returns:
			None
		'''

		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		# Clear existing widgets
		for widget in self.frame.winfo_children():
			widget.destroy()

		self.btn_get_node_list = ttk.Button(self.frame, text="Get Node List", command=self.show_node_list)
		self.btn_export_node_list = ttk.Button(self.frame, text="Export", command=lambda: self.export_content(tab.Name), state=tk.NORMAL)

		self.btn_get_node_list.grid(row=0, column=0, padx=10, pady=10)
		self.btn_export_node_list.grid(row=1, column=1, sticky="nw", padx=10, pady=10)

		if self.myproject is None:
			self.btn_export_node_list.config(state=tk.DISABLED)

		self.output_node_list = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD)
		self.output_node_list.grid(row=1, padx=10, pady=10, sticky="nsew")
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		return self.frame


	def create_find_device_tab(self):
		'''Setup for the find device tab-screen, with entries for the PLC and device name and a button to find the nodes based on the input.

		Returns:
			None
		'''

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

		return self.frame


	def create_check_address_tab(self):
		'''Setup for the check address tab-screen.

		This method creates a tab in the GUI application for checking an IP address. It adds a label, an entry field for the address, a button to check the address, and an output area to display the results.

		If the tab already exists, it will be selected instead of creating a new one.

		Returns:
			None
		'''

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

		return self.frame


	def create_display_connections_tab(self):
		'''Setup for the display connections tab-screen.

		This method creates a tab in the GUI application for displaying the connections between devices. It adds a button to display the connections and an output area to display the results.

		If the tab already exists, it will be selected instead of creating a new one.

		Returns:
			None
		'''

		self.clear_widgets()

		if self.frame is None:
			self.frame = ttk.Frame(self.master)

		self.btn_export_graph = tk.Button(self.frame, text="Export", command=lambda: self.export_content("connections"), state=tk.NORMAL)
		self.btn_export_graph.pack(pady=10)

		self.figure = Figure(dpi=100)
		self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
		self.canvas_widget = self.canvas.get_tk_widget()
		self.canvas_widget.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

		# Only call display_connections if a project is open
		if self.myproject is None and self.myinterface is None:
			self.btn_export_graph.config(state=tk.DISABLED)
			self.display_no_project_message()
		else:
			self.display_connections()
			
		return self.frame


	def show_node_list(self):
		'''Method that is linked to the button in the node list tab.
		
		Retrieves the function output in the nodes logic to get the node list.
		If no project is open, it displays a message indicating that a project needs to be opened.
		If an error occurs during the retrieval of the node list, it displays the error message.
		'''

		if self.node is None:
			content = "Please open a project to view the node list."
			self.status_icon.change_icon_status("#FFFF00", content)
		else:
			try:
				content = self.node.show_node_table()
				self.status_icon.change_icon_status("#39FF14", "Node list retrieved successfully")
				self.output_node_list.insert(tk.END, content.to_string())
			except Exception as e:
				content = f"An error occurred: {str(e)}"
				self.status_icon.change_icon_status("#FF0000", content)
		self.output_node_list.delete(1.0, tk.END)
		if isinstance(content, pd.DataFrame):
			self.output_node_list.insert(tk.END, content.to_string())
		self.output_node_list.insert(tk.END, content)


	def find_nodes(self):
		'''Method that is linked to the button in the find device tab, to retrieve the function output in the nodes logic to find the nodes based on the PLC and device name.

		Returns:
			str: The output of the find_device_nodes function, which contains the nodes found based on the PLC and device name.

		Raises:
			Exception: If an error occurs during the execution of the find_device_nodes function.
		'''

		if self.node is None:
			content = "Please open a project to find nodes."
			self.status_icon.change_icon_status("#FFFF00", content)
		elif self.entry_plc_name.get() or self.entry_device_name.get():
			content = "Please enter both the PLC name and device name."
			self.status_icon.change_icon_status("#FFFF00", content)
		else:
			try:
				plc_name = self.entry_plc_name.get()
				device_name = self.entry_device_name.get()
				content = self.node.find_device_nodes(plc_name.upper(), device_name.upper())
				self.status_icon.change_icon_status("#39FF14", "find_nodes retrieved successfully")
			except Exception as e:
				content = f"An error occurred: {str(e)}"
				self.status_icon.change_icon_status("#FF0000", content)
		self.output_find_device.delete(1.0, tk.END)
		self.output_find_device.insert(tk.END, content)


	def check_address(self):
		'''Method that is linked to the button in the check address tab.
		Retrieves the function output in the nodes logic to check if an address exists in the project.

		Returns:
			str: The result of checking if the address exists in the project.
		'''

		if self.node is None:
			content = "Please open a project to check addresses."
			self.status_icon.change_icon_status("#FFFF00", content)
		elif self.entry_address.get():
			content = "Please enter an address to check."
			self.status_icon.change_icon_status("#FFFF00", content)
		else: 
			try:
				address = self.entry_address.get()
				content = self.node.address_exists(address)
				self.status_icon.change_icon_status("#39FF14", "check_address retrieved successfully")
			except Exception as e:
				content = f"An error occurred: {str(e)}"
				self.status_icon.change_icon_status("#FF0000", content)
		self.output_check_address.delete(1.0, tk.END)
		self.output_check_address.insert(tk.END, content)

	# FIXME : when selecting connections tab before opening/closeing project raises ERROR: Project could not be closed. invalid comman name ".!fram2.!frame.!frame5.!frame.!scrollledtext"
	def display_connections(self):
		'''Method that is linked to the button in the display connections tab.
		Retrieves the function output in the nodes logic to display the connections between devices.

		Returns:
			str: The result of displaying the connections between devices.
		'''

		if self.node is None:
			content = "Please open a project to display connections."
			self.status_icon.change_icon_status("#FFFF00", content)
			self.display_no_project_message(content)
			return
		else:
			try:
				self.figure.clf()
				content, graph, _ = self.node.display_connections(self.figure)
				self.canvas.draw()
				self.status_icon.change_icon_status("#39FF14", "display_connections retrieved successfully")
			except Exception as e:
				content = f"An error occurred: {str(e)}"
				self.status_icon.change_icon_status("#FF0000", content)
				self.display_no_project_message(content)
				print(content)


	def display_no_project_message(self, message="Please open a project to display the connections."):
		"""
		Display a message on the canvas when no project is open.

		Parameters:
		- message (str): The message to be displayed. Defaults to "Please open a project to display the connections."
		"""

		if self.figure:
			self.figure.clear()
			ax = self.figure.add_subplot(111)
			ax.text(0.5, 0.5, message, horizontalalignment='center', verticalalignment='center', fontsize=12)
			ax.axis('off')
			if self.canvas:
				self.canvas.draw()


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

		extensions = ["*.csv", "*.xlsx", "*.json"]

		if self.myproject and self.myinterface:
			if tab_name == "connections":
				extensions.append("*.png")

			dialog = RadioSelectDialog(self.master, "Choose export option", extensions)
			
			try:
				content = self.node.export_data(dialog.filename, dialog.selection, tab_name)
				messagebox.showinfo("Export successful", content)
				self.status_icon.change_icon_status("#39FF14", content)
			except ValueError as e:
				content = f"Export failed: {str(e)}"
				messagebox.showwarning("WARNING", content)
				self.status_icon.change_icon_status("#FF0000", content)
		else:
			self.btn_export_node_list.config(state=tk.DISABLED)
			self.btn_export_graph.config(state=tk.DISABLED)
			content = f"Please open a project to view the {tab_name}."
			self.status_icon.change_icon_status("#FFFF00", content)
			messagebox.showwarning("WARNING", content)

