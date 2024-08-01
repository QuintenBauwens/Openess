"""
Author: Quinten Bauwens
Last updated: 09/07/2024
ToDo: NEED TO GET UPDATED, GET NODES OUT OF THE SUBNET SECTION 
"""

from collections import OrderedDict as od
import os
import re
import random as rd
from matplotlib import pyplot as plt
import pandas as pd
import datetime
import networkx as nx
import plotly.graph_objs as go

import clr
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf
from core.hardware import Hardware


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

	def __init__(self, myproject, myinterface):
		"""
		Initializes a Nodes object.

		Args:
			myproject (str): The name of the project.
			myinterface (str): The name of the interface.
		"""

		self.myproject = myproject
		self.myinterface = myinterface
		self.hardware = Hardware(self.myproject, self.myinterface)
		self.projectItems = self.hardware.GetAllItems()
		self.nodeList = self.getNodeList()
		self.items = {}


	def getNodeList(self, items={}):
		"""
		Returns a dictionary with all the nodes in the project.

		Args:
			items (dict, optional): Additional items to include in the dictionary. Defaults to an empty dictionary.

		Returns:
			dict: A dictionary containing all the nodes in the project.
		"""
	
		PLC_List = self.hardware.get_plc_devices()
		interface_devices = self.hardware.get_interface_devices(self.projectItems)
	
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
			
		return items


	def show_node_table(self, items={}):
		"""
		Returns a table with all the nodes for visualization in a GUI application.

		Args:
			items (dict, optional): Additional items to include in the table. Defaults to an empty dictionary.

		Returns:
			pandas.DataFrame: A table with all the nodes in the project.
		"""
		
		nodesTable = pd.DataFrame()

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
		return nodesTable


	#TODO : add more data to the nodes (isProfinet, isProfibus, redundancyRole etc..)
	def graph_data(self):
		"""
		Generates a graph representation of the network connections between devices.

		Returns:
			nx.Graph: The generated graph object representing the network connections.
		"""

		G = nx.Graph()  # initialize the graph
		items = self.hardware.GetAllItems()

		for deviceitem in items:  # for all items and device items in project
			network_service = tia.IEngineeringServiceProvider(deviceitem).GetService[hwf.NetworkInterface]()  # get the interface service
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
						# convert the cable length back to string and add "m" for meters
						cable_length = str(cable_length) + "m" if cable_length != 'N/A' else cable_length

						G.add_edge(source_node, target_node, length=cable_length)  # add the connection to the graph
		self.G = G
		return G

	# FIXME: scalance and module needs to be fixed they both get called JW sometimes
	def getDeviceType(self, device_name):
		"""
		Returns the device type and color based on the given device name.

		Parameters:
		- device_name (str): The name of the device.

		Returns:
		- device_type (str): The type of the device.
		- color (str): The color associated with the device type.

		"""

		types = {
			'PLC': {'identifiers': ['JC'], 'color': 'red'},
			'module': {'identifiers': ['JW'], 'color': 'blue'},
			'scalance': {'identifiers': ['JX'], 'color': 'green'},
			'drive': {'identifiers': ['UE'], 'color': 'yellow'}
		}

		for deviceType, identifier in types.items():
			if any(identifier in device_name for identifier in identifier['identifiers']):
				return deviceType, identifier['color']
		return 'other', 'gray'


	# TODO: change legende to device type instead of # of connections
	def display_graph_interactive(self):
			"""
			Displays the graph in an interactive plotly figure with device type-based coloring and improved labels.

			Returns:
				A tuple containing:
				- A string indicating the result of the operation.
				- The plotly figure object or None if an error occurred.
				- The graph object or None if an error occurred.
			"""
			G = self.G
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
				device_type, color = self.getDeviceType(node)
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

			return "Interactive graph created successfully", fig, G


	def display_graph_rendered(self):
		"""
		Display the rendered graph with nodes colored based on their zones.

		Returns:
			tuple: A tuple containing the following elements:
				- str: A message indicating that the connections are displayed in the rendered graph.
				- matplotlib.figure.Figure: The rendered graph figure.
				- networkx.Graph: The graph object used for rendering.
		"""
		
		if not hasattr(self, 'G'):
			self.graph_data()
		
		colors = ['gold', 'lightblue', 'lightcoral', 'lightgreen', 'mediumblue', 'orange', 'pink', 'saddlebrown', 'skyblue', 'turquoise', 'violet']
		# define the search pattern for the device name
		regex = r'(?P<location>\d{6})'
		G = self.G

		fig, ax = plt.subplots(figsize=(18, 12))
		pos = nx.spring_layout(G, seed=42)

		# map each zone to a unique color
		zone_colors = {}
		default_color = 'gray'
		for node in G.nodes():
			match = re.match(regex, node)
			if not match:
				continue
			
			location = match.group('location')
			if location not in zone_colors:
				color = rd.choice(colors)
				while color in zone_colors.values():
					color = rd.choice(colors)
				zone_colors[location] = color
		
		# assign the color to each node based on their zone
		color = [zone_colors.get(re.match(regex, node).group('location') if re.match(regex, node) else None, default_color) for node in G.nodes()]

		nx.draw_networkx_nodes(G, pos, ax=ax, node_size=100, node_color=color)
		nx.draw_networkx_edges(G, pos, ax=ax, width=1, edge_color='gray', alpha=0.5)

		# show the node names on the graph without the location part
		node_labels = {node: re.sub(regex, '', node) if re.match(regex, node) else node for node in G.nodes() }
		nx.draw_networkx_labels(G, pos, ax=ax, labels=node_labels, font_size=8, font_family='sans-serif')

		edge_labels = nx.get_edge_attributes(G, 'length')
		nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

		# reverse the dictionary to get the color as key and the zone as value
		legend_labels = {color: zone for zone, color in zone_colors.items()}  
		plt.legend([plt.Line2D([0], [0], marker='o', color='w', label=k, 
			markerfacecolor=v, markersize=10) for v, k in legend_labels.items()], legend_labels.values(), title='zones', title_fontsize='large', fontsize='medium', loc='upper right')
		
		return 'Connections displayed in the rendered graph.', fig, G


	def find_device_nodes(self, plcName, deviceName):
		"""
		Returns the nodes of a device.

		Args:
			plcName (str): The name of the PLC.
			deviceName (str): The name of the device.

		Returns:
			str: A message indicating the success of the search and the nodes found.
		"""
		
		items = self.nodeList

		try:
			plc_i_need = items[plcName]
			device_list = plc_i_need['devices']
			device_i_search = None

			for device_dict in device_list:
				if deviceName in device_dict.keys():
					device_i_search = device_dict[deviceName][0]['nodes']
					return f"Device \'{deviceName}\' in plc \'{plcName}\' has been found with the following nodes: {device_i_search}"
				
			return f"Device {deviceName} not found in plc {plcName}"
		except KeyError:
			return f"PLC {plcName} not found"


	def address_exists(self, address):
		"""
		Checks if an address is already in use.

		Args:
			address (str): The address to check.

		Returns:
			str: A message indicating whether the address is in use or not.
		"""

		items = self.nodeList

		for plc_name, plc_info in items.items(): # key-value pair in plc dictionary, returns list
			for device in plc_info['devices']: # device is dictionary, plc_info['devices'] is list
				for device_name, device_info in device.items():
					nodes = device_info[0]['nodes']  # gives the dictionary with the nodes key
					if address in nodes.values():  # checking if a value of a node is equal to the input address
						node_name = [name for name, ip in nodes.items() if ip == address]  # Vind de node_name
						return f"Address \'{address}\' is already in use by \'{device_name}\' on port {node_name} connected to plc \'{plc_name}\'"
					
		return f"Address \'{address}\' is not in use"


	def export_data(self, filename, extension, tab):
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
			
			extension = extension[1:]
			cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}'
			directory = os.makedirs(cwd + f"\\{tab}", exist_ok=True) 
			timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
			
			if not filename:
				filename = timestamp
			
			if tab == "node list":
				_, content = self.getNodeList()
				df = content
			elif tab == "connections":
				G = self.graph_data()
				
				nodes_list = list(G.nodes(data=True))
				nodes_df = pd.DataFrame(nodes_list, columns=['Node', 'Attributes'])

				edges_list = list(G.edges(data=True))
				edges_df = pd.DataFrame(edges_list, columns=['Source', 'Target', 'Attributes'])

				df = pd.concat([nodes_df.assign(Type='Node'), edges_df.assign(Type='Edge')], ignore_index=True)

			export_path = os.path.join(cwd, tab, filename + extension)
			if extension == ".csv":
				df.to_csv(export_path, index=False)
			elif extension == ".xlsx":
				df.to_excel(export_path, index=False)
			elif extension == ".json":
				df.to_json(export_path, orient='records')
			elif extension == ".png":
				_, graph, _ = self.display_graph_rendered()
				
				if graph:  
					graph.set_size_inches(18, 12)  
				graph.savefig(export_path)
			elif df is None or graph is None:
				raise ValueError("No data to export")
			else:
				raise ValueError("Extension not supported. Please use .csv, .xlsx or .json")
			
			return f"{tab} exported to {export_path}"

