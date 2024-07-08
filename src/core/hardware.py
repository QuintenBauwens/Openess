"""
Description: 
# this class contains the logic to extract all the hardware from the TIA-portal project

Author: Quinten Bauwens
Last updated: 
"""

import clr
# add the reference to the Siemens.Engineering.dll
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll") 
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf


class Hardware:
	def __init__(self, myproject, myinterface):
		self.myproject = myproject
		self.myinterface = myinterface

		self.projectItems = self.GetAllItems(myproject)
		self.interfaceDevices = self.get_interface_devices(self.projectItems)
		self.plcDevices = self.get_plc_devices(self.projectItems)

	# Get all the hardware 
	def give_items(self, device, Items=[]):
		for item in device.DeviceItems:
			Items.append(item)
			Items = self.give_items(item, Items)
		return Items
	

	def get_devices(self, group, Items=[]):
		'''Returns all the devices of a group.'''

		for device in group.Devices:
			Items = self.give_items(device, Items)
		return Items
	

	def get_interface_devices(self, projectItems, Items=None):
		'''Returns all the devices with an interface-service.'''

		if Items is None:
			Items = []
		for deviceitem in projectItems:  # for all the devices and deviceItems in the project
			network_service = tia.IEngineeringServiceProvider(deviceitem).GetService[hwf.NetworkInterface]()  # get the interface service
			if isinstance(network_service, hwf.NetworkInterface):  # check whether the service does exist
				Items.append(deviceitem)
		return Items
	

	def get_plc_devices(self, projectItems, Items=None):
		'''Returns all the devices with a plc-service.'''
		
		if Items is None:
				Items = []
		for deviceitem in projectItems:  # for all the devices and deviceItems in the project
				if str(deviceitem.Classification) == 'CPU':  # filter out the plc devices
						Items.append(deviceitem)
		return Items
	
		
	def get_groups(self, group_composition, Items=[]):
		'''Returns all the groups and devices of a group-composition'''

		for group in group_composition:
			Items = self.get_devices(group, Items)
			Items = self.get_groups(group.Groups, Items)
		return Items
	

	def GetAllItems(self, myproject):
		'''Returns a list of all the DeviceItems such as plc's, interfaces, ports, ... Does not include the stations. '''

		Items = []
		Items.extend(self.get_devices(myproject))
		Items.extend(self.get_devices(myproject.UngroupedDevicesGroup))
		Items.extend(self.get_groups(myproject.DeviceGroups))

		# removes all the duplicates
		Items = list(set(Items)) 

		return Items