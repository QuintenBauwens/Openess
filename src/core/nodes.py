"""
Author: Quinten Bauwens
Last updated: 09/07/2024
ToDo: NEED TO GET UPDATED, GET NODES OUT OF THE SUBNET SECTION 
"""

from collections import OrderedDict as od
import os
import re
import pandas as pd
import datetime
import networkx as nx
import plotly.graph_objects as go

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

#TODO : verdergaan, labels worden nog niet weergegeven
	def display_connections(self, figure):
		"""
		Display the connections between network interfaces in a graph.

		This method creates a graph using the NetworkX library and displays the connections between network interfaces
		as edges in the graph. The nodes in the graph represent the stations to which the network interfaces belong.

		Parameters:
			figure (matplotlib.figure.Figure): The figure object to display the graph.

		Returns:
			tuple: A tuple containing the following elements:
				- str: A message indicating the result of the operation.
				- matplotlib.figure.Figure: The updated figure object with the graph.
				- networkx.Graph: The graph object representing the connections between network interfaces.
		"""

		G = nx.Graph()  # initialize the graph
		items = self.hardware.GetAllItems()

		for deviceitem in items:  # for all items and device items in project
			network_service = tia.IEngineeringServiceProvider(deviceitem).GetService[hwf.NetworkInterface]()  # get the interface service
			if type(network_service) == hwf.NetworkInterface:  # check whether the service exists

				for source_port in network_service.Ports:  # get the ports from the interface
					if source_port.ConnectedPorts.Count != 0:  # check whether the port is connected
						source_node = str(deviceitem.Parent.GetAttribute('Name'))  # Name of the station of the interface to use as node in the graph

						target_port = source_port.ConnectedPorts[0]
						target_node = target_port.Interface.GetAttribute('Name') # Get the name of the station of the connected interface

						try:
							cable_length = target_port.GetAttribute('CableLength') # get the cable length of the connection
							if cable_length:
								cable_length = str(cable_length)
							else:
								extract_lenght_digits = re.findall(r'\d+', cable_length)
								cable_length = int(extract_lenght_digits[0]) if extract_lenght_digits else 50	
						except:
							cable_length = None
						
						G.add_edge(source_node, target_node, length=cable_length)  # add the connection to the graph
		
		# Create an interactive Plotly figure
		pos = nx.spring_layout(G, seed=42)
		edge_x = []
		edge_y = []
		for edge in G.edges():
			x0, y0 = pos[edge[0]]
			x1, y1 = pos[edge[1]]
			edge_x.extend([x0, x1, None])
			edge_y.extend([y0, y1, None])

		edge_trace = go.Scatter(
			x=edge_x, y=edge_y,
			line=dict(width=0.5, color='#888'),
			hoverinfo='none',
			mode='lines')

		node_x = []
		node_y = []
		for node in G.nodes():
			x, y = pos[node]
			node_x.append(x)
			node_y.append(y)

		node_trace = go.Scatter(
			x=node_x, y=node_y,
			mode='markers',
			hoverinfo='text',
			marker=dict(
				showscale=True,
				colorscale='YlGnBu',
				size=10,
				colorbar=dict(
					thickness=15,
					title='Node Connections',
					xanchor='left',
					titleside='right'
				)
			)
		)

		# Add node text and color
		node_adjacencies = []
		node_text = []
		for node, adjacencies in G.adjacency():
			node_adjacencies.append(len(adjacencies))
			node_text.append(f'Device: {node}<br># of connections: {len(adjacencies)}')

		node_trace.marker.color = node_adjacencies
		node_trace.text = node_text

		# Add edge text
		edge_text = []
		for edge in G.edges(data=True):
			source, target, data = edge
			length = data.get('length', 'N/A')
			edge_text.append(f'Connection: {source} - {target}<br>Cable Length: {length}')

		edge_trace.text = edge_text
		edge_trace.hoverinfo = 'text'

		# Create the figure
		fig = go.Figure(data=[edge_trace, node_trace],
						layout=go.Layout(
							title='Network Connections',
							titlefont_size=16,
							showlegend=False,
							hovermode='closest',
							margin=dict(b=20,l=5,r=5,t=40),
							annotations=[ dict(
								text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
								showarrow=False,
								xref="paper", yref="paper",
								x=0.005, y=-0.002 ) ],
							xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
							yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
						)

		return 'Connections displayed in the interactive graph.', fig, G

		# try:
			

		# 	self.figure = figure
		# 	ax = figure.add_subplot(111)  # create an axis for the figure
		# 	pos = nx.spring_layout(G, seed=42)  # positions for all nodes, gives every time the same layout
		# 	nx.draw(G, pos, ax=ax, with_labels=True, node_color='gold', edge_color='slategray')  # draw the graph in the figure
		# 	nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

		# 	return f'Connections displayed in the graph.', figure, G
		# except Exception as e:
		# 	return f'An error occurred trying to display connections graph: {str(e)}', figure, G


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
						return f"Address \'{address}\' is already in use by {node_name} in device \'{device_name}\' in plc \'{plc_name}\'"
					
		return f"Address \'{address}\' is not in use"


	def export_data(self, filename, extension, tab):
		"""
		Exports data from certain functions.

		Returns:
			None
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
			_, graph, G = self.display_connections(self.figure)

			if graph:  
				graph.set_size_inches(18, 12)  
			
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
			graph.savefig(export_path)
		elif df is None or graph is None:
			raise ValueError("No data to export")
		else:
			raise ValueError("Extension not supported. Please use .csv, .xlsx or .json")
		
		return f"{tab} exported to {export_path}"

