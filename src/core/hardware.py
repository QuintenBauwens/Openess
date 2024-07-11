"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import clr
# add the reference to the Siemens.Engineering.dll
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll") 
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf


class Hardware:
	"""
	Represents the logic behind hardware components in a project.
	
	Attributes:
		myproject (Project): The project containing the hardware.
		myinterface (Interface): The interface of the hardware.
	"""

	def __init__(self, myproject, myinterface):
		self.myproject = myproject
		self.myinterface = myinterface


	def give_items(self, device, Items=[]):
		"""
		Recursively retrieves all the items from a device and its sub-devices.

		Args:
			device (Device): The device to retrieve items from.
			Items (list, optional): The list to store the retrieved items. Defaults to an empty list.

		Returns:
			list: The list of retrieved items.
		"""

		for item in device.DeviceItems:
			Items.append(item)
			Items = self.give_items(item, Items)
		return Items


	def get_devices(self, group, Items=[]):
		"""
		Retrieves all the devices from a group and its sub-groups.

		Args:
			group (Group): The group to retrieve devices from.
			Items (list, optional): The list to store the retrieved devices. Defaults to an empty list.

		Returns:
			list: The list of retrieved devices.
		"""

		for device in group.Devices:
			Items = self.give_items(device, Items)
		return Items


	def get_interface_devices(self, projectItems, Items=None):
		"""
		Retrieves all the devices with an interface service.

		Args:
			projectItems (list): The list of project items.
			Items (list, optional): The list to store the retrieved devices. Defaults to None.

		Returns:
			list: The list of retrieved devices with an interface service.
		"""

		if Items is None:
			Items = []
		for deviceitem in projectItems:
			network_service = tia.IEngineeringServiceProvider(deviceitem).GetService[hwf.NetworkInterface]()
			if isinstance(network_service, hwf.NetworkInterface):
				Items.append(deviceitem)
		return Items


	def get_plc_devices(self, Items=None):
		"""
		Retrieves all the devices with a PLC service.

		Args:
			Items (list, optional): The list to store the retrieved devices. Defaults to None.

		Returns:
			list: The list of retrieved devices with a PLC service.
		"""

		projectItems = self.GetAllItems()
		if Items is None:
			Items = []
		for deviceitem in projectItems:
			if str(deviceitem.Classification) == 'CPU':
				Items.append(deviceitem)
		return Items


	def get_groups(self, group_composition, Items=[]):
		"""
		Retrieves all the groups and devices from a group composition.

		Args:
			group_composition (list): The list of group compositions.
			Items (list, optional): The list to store the retrieved groups and devices. Defaults to an empty list.

		Returns:
			list: The list of retrieved groups and devices.
		"""

		for group in group_composition:
			Items = self.get_devices(group, Items)
			Items = self.get_groups(group.Groups, Items)
		return Items


	def GetAllItems(self):
		"""
		Retrieves a list of all the device items such as PLCs, interfaces, ports, etc. Does not include the stations.

		Returns:
			list: The list of all device items.
		"""

		Items = []
		Items.extend(self.get_devices(self.myproject))
		Items.extend(self.get_devices(self.myproject.UngroupedDevicesGroup))
		Items.extend(self.get_groups(self.myproject.DeviceGroups))

		# Removes all the duplicates
		Items = list(set(Items))

		return Items