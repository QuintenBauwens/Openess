"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import clr
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf
import os
import re
import random as rd
import pandas as pd
import datetime
import networkx as nx
import plotly.graph_objs as go

from matplotlib import pyplot as plt
from collections import OrderedDict as od

from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class Nodes:
	"""
	A class representing a collection of nodes in a project.

	Attributes:
		myproject (str): The name of the project.
		myinterface (str): The name of the interface.
		hardware (Hardware): An instance of the Hardware class.
		projectItems (list): A list of project items.
		nodeList (dict): A dictionary containing all the nodes in the project.
		items (dict): A dictionary containing additional items.

	Methods:
		__init__(self, myproject, myinterface): Initializes a Nodes object.
		getNodeList(self, items={}): Returns a dictionary with all the nodes in the project.
		show_node_table(self, items={}): Returns a table with all the nodes for visualization in a GUI application.
		export_node_list(self, filename, extension): Exports the node list to a file.
		find_device_nodes(self, plcName, deviceName): Returns the nodes of a device.
		address_exists(self, address): Checks if an address is already in use.
		graph_data(self): Display the connections between network interfaces in a graph.
		getDeviceType(self, device_name): Returns the device type based on the device name.
		display_graph_interactive(self): Displays the graph in an interactive plotly figure with device type-based coloring and improved labels.
	"""

	def __init__(self, project):
		"""
		Initializes a Nodes object.

		Args:
			myproject (str): The name of the project.
			myinterface (str): The name of the interface.
		"""
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface

		self.nodeList = None
		self.items = {}
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

	def get_core_classes(self):
		self.hardware = self.project.hardware

	def get_core_functions(self):
		logger.debug(f"Accessing 'GetAllItems' from the hardware object '{self.project.hardware}'...")
		self.projectItems = self.hardware.GetAllItems()

	# TODO: NEEDS TO BE UPDATED (INCORRECT) : get the nodes from subnet section directly instead of looping through all devices
	def getNodeList(self, items={}, reload=False):
		"""
		Returns a dictionary with all the nodes in the project.

		Args:
			items (dict, optional): Additional items to include in the dictionary. Defaults to an empty dictionary.

		Returns:
			dict: A dictionary containing all the nodes in the project.
		"""
		if self.nodeList and not reload:
			logger.debug(f"Returning cached node list: {type(self.nodeList)}, total entries: '{len(self.nodeList)}'...")
			return self.nodeList

		PLC_List = self.hardware.get_plc_devices(reload=reload)
		interface_devices = self.hardware.get_interface_devices(self.projectItems, reload=reload)
		logger.debug(
			f"Gathering nodes from PLC's {[item.Name for item in PLC_List]} and making dict: "
			f"amount of interface devices: '{len(interface_devices)}, '"
			f"reload: '{reload}'"
		)

		for plc in PLC_List:
			this_plc_name = plc.Name
			items[this_plc_name] = od()

			# Initialize an empty "Network" key to ensure it's the first key
			items[this_plc_name]["Network"] = {}
			items[this_plc_name]["devices"] = []

			this_plc_dict = items[this_plc_name]
			devices_list = this_plc_dict["devices"]

			for device in interface_devices:
				network_service = tia.IEngineeringServiceProvider(device).GetService[hwf.NetworkInterface]()

				if not isinstance(network_service, hwf.NetworkInterface): # skip the device if it does not have a network interface
					logger.debug(f"Device '{device.Name}' does not have a network interface")
					continue
						
				this_device_name = device.Name
				this_device_list = []

				if (device.Name == "PROFINET"):
					this_plc_subnet = network_service.Nodes[0].GetAttribute("SubnetMask")
					this_plc_gateway = network_service.Nodes[0].GetAttribute("RouterAddress")

					items[this_plc_name]["Network"] = { # update the network key with values
						"subnetmask" : this_plc_subnet,
						"gateway" : this_plc_gateway
						}

				this_nodes_dict = {}
				
				for index in range(network_service.Nodes.Count):
					this_node_name = network_service.Nodes[index].GetAttribute("Name")
					this_node_address = network_service.Nodes[index].GetAttribute("Address")

					# add node to the dictionary
					this_nodes_dict[this_node_name] = this_node_address
				
				# bundle all the nodes in the corresponding device
				this_device_list.append({"nodes" : this_nodes_dict})	
				devices_list.append({this_device_name : this_device_list})
		self.nodeList = items
		logger.debug(
			f"Returning nodelist {type(self.nodeList)} : "
			f"total nodes: '{len(self.nodeList.items())}'"
		)
		return items


	def getNodeTable(self, items={}, reload=False):
		"""
		Returns a table with all the nodes for visualization in a GUI application.

		Args:
			items (dict, optional): Additional items to include in the table. Defaults to an empty dictionary.

		Returns:
			pandas.DataFrame: A table with all the nodes in the project.
		"""
		if hasattr(self, 'nodesTable') and not reload:
			logger.debug(f"Returning cached nodes table: {type(self.nodesTable)}, total entries: '{len(self.nodesTable)}'...")
			return self.nodesTable
		
		nodesTable = pd.DataFrame()
		self.nodeList = self.getNodeList(items, reload=reload)
		logger.debug(
			f"Creating dataframe for nodes: "
			f"total entries: '{len(self.nodeList)}' "
			f"reload: '{reload}'"
		)

		for plc_name, plc_info in self.nodeList.items():
			for device in plc_info['devices']:
				for device_name, device_info in device.items():
					node_names = [node for node in device_info[0]['nodes'].keys()]

					# make a DataFrame for the device and concatenate it to the network_segment
					device_df = pd.DataFrame({
						'plc_name': [plc_name],  
						'subnetmask': [plc_info['Network']['subnetmask']],
						'gateway': [plc_info['Network']['gateway']],
						'device_name': [device_name],
						'node_names': node_names,
						'node_addresses': [device_info[0]['nodes'][node] for node in node_names]
						}, index=[0])
					
					# Concatenate all network_segments to nodesTable
					nodesTable = pd.concat([nodesTable, device_df], ignore_index=True)
		self.nodesTable = nodesTable
		logger.debug(f"Returning nodesTable as {type(nodesTable)}")
		return nodesTable


	#TODO : add more data to the nodes (isProfinet, isProfibus, redundancyRole etc..)
	def graph_data(self, reload=False):
		"""
		Generates a graph representation of the network connections between devices.

		Returns:
			nx.Graph: The generated graph object representing the network connections.
		"""
		if hasattr(self, "G") and not reload:
			logger.debug(f"Returning cached graph data: {type(self.G)}, with '{len(self.G.nodes)}' nodes and '{len(self.G.edges)}' edges...")
			return self.G

		G = nx.Graph()  # initialize the graph
		items = self.hardware.GetAllItems(reload=reload)
		logger.debug(
			f"Mapping network connections of '{len(items)}' hardware devices in the project to a graph: "
			f"reload: '{reload}'"
		)

		for deviceitem in items:  # for all items and device items in project
			network_service = tia.IEngineeringServiceProvider(deviceitem).GetService[hwf.NetworkInterface]()  # get the interface service
			logger.debug(f"'{deviceitem.Name}' has network interface: '{isinstance(network_service, hwf.NetworkInterface)}'")

			if isinstance(network_service, hwf.NetworkInterface):  # check whether the service exists
				for source_port in network_service.Ports:  # get the ports from the interface
					if source_port.ConnectedPorts.Count != 0:  # check whether the port is connected
						source_node = deviceitem.Parent.Parent.GetAttribute('Name')  # Name of the station of the interface to use as node in the graph
						target_port = source_port.ConnectedPorts[0]
						target_node = target_port.Interface.GetAttribute('Name') # Get the name of the station of the connected interface

						# get device type
						source_device_type = source_port.Interface.Parent.Parent.Parent.GetAttribute('TypeIdentifier')
						target_container = target_port.Interface.Parent.GetAttribute('Container')
						target_device_type = target_container.Parent.GetAttribute('TypeIdentifier')

						G.add_node(source_node, deviceType=source_device_type)
						G.add_node(target_node, deviceType=target_device_type)

						# get the cable length of the connection
						try:
							cable_length = target_port.GetAttribute('CableLength') 
							if cable_length:
								cable_length = str(cable_length)
								extract_lenght_digits = re.findall(r'\d+', cable_length)
								cable_length = int(extract_lenght_digits[0]) if extract_lenght_digits else 50    
						except: 
							cable_length = 'N/A'
							logger.debug(f"Could not retrieve cable length for connection between '{source_node}' and '{target_node}'")

						# convert the cable length back to string and add "m" for meters
						cable_length = str(cable_length) + "m" if cable_length != 'N/A' else cable_length
						G.add_edge(source_node, target_node, length=cable_length)  # add the connection to the graph
						logger.debug(f"Added connection between '{source_node}' and '{target_node}' with a cable length of '{cable_length}'")
		logger.debug(f"Returning graph data {type(G)}: "
			f"total nodes: '{len(G.nodes)}', "
			f"total edges: '{len(G.edges)}'"
		)
		self.G = G
		return G

	# FIXME: scalance and module needs to be fixed they both get called JW sometimes
	def getDeviceType(self, attribute):
		"""
		Returns the device type and color based on the given device name.

		Parameters:
		- attribute (str): The attribute of the device.

		Returns:
		- device_type (str): The type of the device.
		- color (str): The color associated with the device type.
		"""

		types = [
			('PLC', ['S71500'], 'red'),
			('module', ['ET200SP', 'ET200ECO'], 'blue'), # give higher priority than drive, module type can contain SIEMENS and ET200SP
			('scalance', ['SCALANCE'], 'green'),
			('drive', ['SIEMENS', 'DFS', 'SEW'], 'yellow'),
			('PNcoupler', ['PNPNCOUPLER'], 'orange'),
			('other', [''], 'gray')
		]

		for deviceType, identifiers, color in types:
			if any(identifier in attribute.upper() for identifier in identifiers):
				return deviceType, color
		return 'other', 'gray'


	def display_graph_interactive(self, reload=False):
			"""
			Displays the graph in an interactive plotly figure with device type-based coloring and improved labels.

			Returns:
				A tuple containing:
				- A string indicating the result of the operation.
				- The plotly figure object or None if an error occurred.
				- The graph object or None if an error occurred.
			"""
			if hasattr(self, "interactive_graph") and not reload:
				logger.debug(f"Returning cached interactive graph: {type(self.interactive_graph)}...")
				return self.interactive_graph, self.G

			logger.debug(
				f"Creating an interactive graph with device type-based coloring and improved labels: "
				f"reload: '{reload}'"
			)

			G = self.graph_data(reload=reload)
			pos = nx.spring_layout(G, iterations=50, seed=42)
			
			# Generate edge traces
			edge_traces = []
			for edge in G.edges():
				x0, y0 = pos[edge[0]]
				x1, y1 = pos[edge[1]]
				# midpoint
				x_mid, y_mid = (x0 + x1) / 2, (y0 + y1) / 2
				# draw the connection
				edge_trace = go.Scatter(
					x=[x0, x1, None], y=[y0, y1, None],
					line=dict(width=0.5, color='#888'),
					hoverinfo='none',
					mode='lines',
					showlegend=False
					)
				edge_traces.append(edge_trace)
		
				# place marker in the middle of the connection for hover information
				hover_trace = go.Scatter(
					x=[x_mid], y=[y_mid],
					text=f"Source: {edge[0]}<br>Target: {edge[1]}<br>Length: {G.edges[edge].get('length', 'N/A')}",
					mode='markers',
					hoverinfo='text',
					marker=dict(size=1, color='rgba(0,0,0,0)'),  # Make the marker invisible
					showlegend=False
				)
				edge_traces.append(hover_trace)

			# Generate node traces
			node_traces = {}
			for node, attrs in G.nodes(data=True):
				device_type, color = self.getDeviceType(attrs.get('deviceType', ''))
				if device_type not in node_traces:
					node_traces[device_type] = {
						'x': [], 'y': [], 'text': [], 'hovertext': [], 'color': color
					}

				x, y = pos[node]
				node_traces[device_type]['x'].append(x)
				node_traces[device_type]['y'].append(y)
				short_name = node[:10] + '...' if len(node) > 10 else node
				node_traces[device_type]['text'].append(short_name)
				node_traces[device_type]['hovertext'].append(
					f"Name: {node}<br>Device Type: {attrs.get('deviceType', 'N/A')}<br>")
					
			# Combine edge and node traces
			traces = edge_traces
			for device_type, trace_data in node_traces.items():
				trace = go.Scatter(
					x=trace_data['x'], 
					y=trace_data['y'],
					mode='markers+text',
					hoverinfo='text',
					text=trace_data['text'],
					textposition="top center",
					hovertext=trace_data['hovertext'],
					marker=dict(
						color=trace_data['color'],
						size=10,
						line_width=2
					),
					name=device_type,
					showlegend=True
				)
				traces.append(trace)

			# Configure layout
			layout = go.Layout(
				title='Network graph',
				titlefont_size=16,
				showlegend=True,
				hovermode='closest',
				margin=dict(b=20,l=5,r=5,t=40),
				xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
				yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
				legend=dict(
					x=1.05,
					y=0.5,
					traceorder="normal",
					font=dict(family="sans-serif", size=12, color="black"),
					bgcolor="LightSteelBlue",
					bordercolor="Black",
					borderwidth=2
				)
			)
			# Create plotly figure
			fig = go.Figure(data=traces, layout=layout)
			self.interactive_graph = fig
			self.G = G
			return fig, G


	def display_graph_rendered(self, reload=False):
		"""
		Display the rendered graph with nodes colored based on their zones.

		Returns:
			tuple: A tuple containing the following elements:
				- str: A message indicating that the connections are displayed in the rendered graph.
				- matplotlib.figure.Figure: The rendered graph figure.
				- networkx.Graph: The graph object used for rendering.
		"""
		
		if hasattr(self, "rendered_graph") and not reload:
			logger.debug(f"Returning cached rendered graph: {type(self.rendered_graph)}...")
			return self.rendered_graph, self.G
		
		colors = ['gold', 'lightblue', 'lightcoral', 'lightgreen', 'mediumblue', 'orange', 'pink', 'saddlebrown', 'skyblue', 'turquoise', 'violet']
		# define the search pattern for the device name
		regex = r'(?P<location>\d{6})'
		G = self.graph_data(reload=reload)

		logger.debug(
			f"Creating a rendered graph with the mapped network connections: " 
			f"total nodes: '{len(G)}', " 
			f"reload: '{reload}'"
		)
		logger.debug(
			f"Assigning colors to zones based on the regex pattern '{regex}': "
			f"colors: {colors}"
		)

		fig, ax = plt.subplots(figsize=(18, 12))
		pos = nx.spring_layout(G, seed=42)

		# map each zone to a unique color
		zone_colors = {}
		default_color = 'gray'

		for node in G.nodes():
			match = re.match(regex, node)
			if not match:
				logger.debug(f"Node '{node}' does not match the regex pattern '{regex}'")
				continue
			
			location = match.group('location')
			if location not in zone_colors:
				color = rd.choice(colors)
				logger.debug(f"Zone not yet in {zone_colors}, assigning color '{color}' to zone '{location}'")
				while color in zone_colors.values():
					logger.debug(f"Color '{color}' already assigned to zone '{next((key for key, value in zone_colors.items() if value == color))}', generating new color")
					color = rd.choice(colors)
				zone_colors[location] = color
				logger.debug(f"Assigned color {color} to zone '{location}' and added to the zones: {zone_colors}")
		
		# assign the color to each node based on their zone
		color = [zone_colors.get(re.match(regex, node).group('location') if re.match(regex, node) else None, default_color) for node in G.nodes()]
		logger.debug(f"Drawing nodes...")
		nx.draw_networkx_nodes(G, pos, ax=ax, node_size=100, node_color=color)
		nx.draw_networkx_edges(G, pos, ax=ax, width=1, edge_color='gray', alpha=0.5)

		# show the node names on the graph without the location part
		node_labels = {node: re.sub(regex, '', node) if re.match(regex, node) else node for node in G.nodes() }
		logger.debug(f"Drawing node labels...")
		nx.draw_networkx_labels(G, pos, ax=ax, labels=node_labels, font_size=8, font_family='sans-serif')

		logger.debug(f"Retrieving edge labels and drawing them...")
		edge_labels = nx.get_edge_attributes(G, 'length')
		nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

		# reverse the dictionary to get the color as key and the zone as value
		logger.debug(f"Creating legend...")
		legend_labels = {color: zone for zone, color in zone_colors.items()}  
		plt.legend([plt.Line2D([0], [0], marker='o', color='w', label=k, 
			markerfacecolor=v, markersize=10) for v, k in legend_labels.items()], legend_labels.values(), title='zones', title_fontsize='large', fontsize='medium', loc='upper right')
		logger.debug(f"Returning graph {type(fig)} and G object {type(G)}")

		self.rendered_graph = fig
		self.G = G
		return fig, G


	def find_device_nodes(self, plcName, deviceName, reload=False):
		"""
		Returns the nodes of a device.

		Args:
			plcName (str): The name of the PLC.
			deviceName (str): The name of the device.

		Returns:
			str: A message indicating the success of the search and the nodes found.
		"""
		
		items = self.getNodeList(reload=reload)
		plc_list = self.hardware.get_plc_devices(reload=reload)

		if plcName not in [plc.Name for plc in plc_list]:
			logger.warning(f"PLC '{plcName}' not found in the project")
			return f"PLC '{plcName}' not found in the project"

		logger.debug(
			f"Searching under plc '{plcName}' for device '{deviceName}' in a total of '{len(items.values())}' project items, "
			f"reload: '{reload}'"
		)

		search_result = f"Device '{deviceName}' not found in plc '{plcName}'"
		device_df = pd.DataFrame()

		try:
			plc_i_need = items[plcName]
			device_list = plc_i_need['devices']
			device_i_search = None

			for device_dict in device_list:
				if deviceName in device_dict.keys():
					device_i_search = device_dict[deviceName][0]['nodes']
					search_result = f"Device '{deviceName}' in plc '{plcName}' has been found with the following nodes:\n"
					for node_name, node_address in device_i_search.items():
						df_update = pd.DataFrame([{
							'plc_name': plcName,
							'device_name': deviceName,
							'node_name': node_name,
							'node_address': node_address
							}])
						device_df = pd.concat([device_df, df_update], ignore_index=True)
						search_result += f"\tNode '{node_name}' with address '{node_address}'\n"	

			logger.debug(f"Returning search result {type(search_result)}, {search_result} of the node search")
			self.device_df = device_df
			return device_df, search_result
		except Exception as e:
			raise Exception(f"An error occurred while searching for the device nodes: {str(e)}")


	def address_exists(self, address, reload=False):
		"""
		Checks if an address is already in use.

		Args:
			address (str): The address to check.

		Returns:
			str: A message indicating whether the address is in use or not.
		"""

		items = self.getNodeList(reload=reload)
		logger.debug(
			f"Checking in nodelist that contains '{len(items)}' items if address '{address}' is already in use, "
			f"reload: '{reload}'")
		
		search_result = f"Address '{address}' is not in use"
		address_df = pd.DataFrame()

		for plc_name, plc_info in items.items(): # key-value pair in plc dictionary, returns list
			for device in plc_info['devices']: # device is dictionary, plc_info['devices'] is list
				for device_name, device_info in device.items():
					nodes = device_info[0]['nodes']  # gives the dictionary with the nodes key
					if address in nodes.values():  # checking if a value of a node is equal to the input address
						df_update = pd.DataFrame([{
							'plc_name': plc_name,
							'device_name': device_name,
							'node_name': [name for name, ip in nodes.items() if ip == address],
							'node_address': [add for add in nodes.values()]
							}])
						address_df = pd.concat([address_df, df_update], ignore_index=True)
						node_name = [name for name, ip in nodes.items() if ip == address]  # Vind de node_name
						search_result = f"Address '{address}' is already in use by '{device_name}' on port '{node_name}' connected to plc '{plc_name}'"
		
		logger.debug(f"Returning search result {type(search_result)} of the address search")
		return address_df, search_result


	def export_data(self, filename, extension, tab, nodesUI):
			"""
			Exports data from certain functions.

			Args:
				filename (str): The name of the exported file. If not provided, a timestamp will be used as the filename.
				extension (str): The file extension of the exported file. Supported extensions are .csv, .xlsx, .json, and .png.
				tab (str): The tab or category of data to export. Supported tabs are "node list" and "connections".

			Returns:
				str: A message indicating the success of the export operation.

			Raises:
				ValueError: If there is no data to export or if the provided extension is not supported.
			"""
			logger.debug(f"Exporting '{tab}' to '{extension}' format")
			extension = extension[1:]
			cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}\\{__name__.split(".")[-1]}'
			directory = os.makedirs(cwd + f"\\{tab}", exist_ok=True) 
			timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
			
			if not filename:
				logger.debug(f"Filename not provided, using timestamp as filename: '{timestamp}'")
				filename = timestamp
			
			if tab == "node list":
				df = self.getNodeTable()
			elif tab == "connections":
				G = self.graph_data()
				
				nodes_list = list(G.nodes(data=True))
				nodes_df = pd.DataFrame(nodes_list, columns=['Node', 'Attributes'])

				edges_list = list(G.edges(data=True))
				edges_df = pd.DataFrame(edges_list, columns=['Source', 'Target', 'Attributes'])

				df = pd.concat([nodes_df.assign(Type='Node'), edges_df.assign(Type='Edge')], ignore_index=True)
			elif tab == "find device":
				plc_name = nodesUI.entry_plc_name.get()
				device_name = nodesUI.entry_device_name.get()
				df, _ = self.find_device_nodes(plc_name, device_name)
			elif tab == "address exists":
				address = nodesUI.entry_address.get()
				logger.critical(f"Address: {address}")
				df, _ = self.address_exists(address)

			export_path = os.path.join(cwd, tab, filename + extension)
			if extension == ".csv":
				df.to_csv(export_path, index=False)
			elif extension == ".xlsx":
				df.to_excel(export_path, index=False)
			elif extension == ".json":
				df.to_json(export_path, orient='records')
			elif extension == ".png":
				graph, _ = self.display_graph_rendered()
				
				if graph:  
					graph.set_size_inches(18, 12)  
				graph.savefig(export_path)
			elif df is None or graph is None:
				raise ValueError("No data to export")
			else:
				raise ValueError("Extension not supported. Please use .csv, .xlsx or .json")
			logger.debug(f"'{tab}' exported to '{export_path}'")
			return f"'{tab}' exported to '{export_path}'"

