"""
Description: 
# 

Author: Quinten Bauwens
Last updated: 
"""

from collections import OrderedDict as od
import pandas as pd

import clr
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf
from .hardware import Hardware


# NEED TO GET UPDATED, GET NODES OUT OF THE SUBNET SECTION
class Nodes:
	def __init__(self, myproject, myinterface):
		self.myproject = myproject
		self.hardware = Hardware(myproject, myinterface)
		self.projectItems = self.hardware.GetAllItems(myproject)
		self.nodeList = self.getNodeList()
		self.items = {}

	def getNodeList(self, items={}):
		'''returns a dictionary with all the nodes in the project'''

		PLC_List = self.hardware.get_plc_devices(self.projectItems)
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
		'''returns a table with all the nodes for visualization in a GUI application'''
		
		nodesTable = pd.DataFrame()
	
		for plc_name, plc_info in self.nodeList.items():
			
			# Enclose scalar values in lists to ensure they are treated as single-element columns
			network_segment = pd.DataFrame({
				'plc_name': [plc_name],  
				'subnetmask': [plc_info['Network']['subnetmask']],
				'gateway': [plc_info['Network']['gateway']],
				}, index=[0])   
	
			for device in plc_info['devices']:
				for device_name, device_info in device.items():
					node_names = [node for node in device_info[0]['nodes'].keys()]

					# make a DataFrame for the device and concatenate it to the network_segment
					device_df = pd.DataFrame({
						'device_name': [device_name],
						'node_names': node_names,
						'node_addresses': [device_info[0]['nodes'][node] for node in node_names]
						}, index=[0])
			
					network_segment = pd.concat([network_segment, device_df], ignore_index=True)
			
			# Concatenate all network_segments to nodesTable
			nodesTable = pd.concat([nodesTable, network_segment], ignore_index=True)
			nodesTable.fillna('', inplace=True)

		return nodesTable.to_string()

	def find_device_nodes(self, plcName, deviceName):
		'''returns the nodes of a device'''
		
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
		'''checks if an address is already in use'''

		items = self.nodeList

		for plc_name, plc_info in items.items(): # key-value pair in plc dictionary, returns list
			for device in plc_info['devices']: # device is dictionary, plc_info['devices'] is list
				for device_name, device_info in device.items():
					nodes = device_info[0]['nodes']  # gives the dictionary with the nodes key
					if address in nodes.values():  # checking if a value of a node is equal to the input address
						node_name = [name for name, ip in nodes.items() if ip == address]  # Vind de node_name
						return f"Address \'{address}\' is already in use by {node_name} in device \'{device_name}\' in plc \'{plc_name}\'"
					
		return f"Address \'{address}\' is not in use"