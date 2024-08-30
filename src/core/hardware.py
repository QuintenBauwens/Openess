"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import clr
# add the reference to the Siemens.Engineering.dll
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll") 
import Siemens.Engineering as tia
import Siemens.Engineering.HW.Features as hwf

from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class Hardware:
	"""
	Represents the logic behind hardware components in a project.
	
	Attributes:
		myproject (Project): The project containing the hardware.
		myinterface (Interface): The interface of the hardware.
	"""

	def __init__(self, project):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface

		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")


	def give_items(self, device, items=[], initial_call=True):
		"""
		Recursively retrieves all the items from a device and its sub-devices.

		Args:
			device (Device): The device to retrieve items from.
			Items (list, optional): The list to store the retrieved items. Defaults to an empty list.

		Returns:
			list: The list of retrieved items.
		"""
		logger.debug(f"Retrieving all items recursively from the project starting with device: '{device.Name}'") if initial_call else None
		for item in device.DeviceItems:
			items.append(item)
			items = self.give_items(item, items, initial_call=False)
		return items


	def get_devices(self, group, items=[], initial_call=True):
		"""
		Retrieves all the devices from a group and its sub-groups.

		Args:
			group (Group): The group to retrieve devices from.
			Items (list, optional): The list to store the retrieved devices. Defaults to an empty list.

		Returns:
			list: The list of retrieved devices.
		"""
		logger.debug(f"Retrieving all devices recursively from the project starting at group: '{group.Name}'") if initial_call else None

		for device in group.Devices:
			items = self.give_items(device, items, initial_call=False)
		return items
	

	def get_groups(self, group_composition, items=[]):
		"""
		Retrieves all the groups and devices from a group composition.

		Args:
			group_composition (list): The list of group compositions.
			Items (list, optional): The list to store the retrieved groups and devices. Defaults to an empty list.

		Returns:
			list: The list of retrieved groups and devices.
		"""

		logger.debug(f"Retrieving all groups and their devices from group composition")
		for group in group_composition:
			items = self.get_devices(group, items)
			items = self.get_groups(group.Groups, items)
		return items


	def get_interface_devices(self, projectItems, reload=False, items=None):
		"""
		Retrieves all the devices with an interface service.

		Args:
			projectItems (list): The list of project items.
			Items (list, optional): The list to store the retrieved devices. Defaults to None.

		Returns:
			list: The list of retrieved devices with an interface service.
		"""
		if hasattr(self, 'interface_items') and not reload:
			logger.debug(f"Returning cached list {type(self.interface_items)} of all the interface devices in the project: '{len(self.interface_items)}'...")
			return self.interface_items

		logger.debug(
			f"Filtering for interface-devices out of all the '{len(projectItems)}' project items: "
			f"reload: '{reload}'"
		)

		if items is None:
			items = []

		for deviceitem in projectItems:
			network_service = tia.IEngineeringServiceProvider(deviceitem).GetService[hwf.NetworkInterface]()
			if isinstance(network_service, hwf.NetworkInterface):
				items.append(deviceitem)

		self.interface_items = items
		logger.debug(
			f"Returning filtered list {type(items)} of all the interface devices out of the project-items: "
			f"amount of interface devices: '{len(items)}', "
			f"object type:  '{items[0].GetType()}'"
		)
		return items


	def GetAllItems(self, reload=False):
		"""
		Retrieves a list of all the device items such as PLCs, interfaces, ports, etc. Does not include the stations.

		Returns:
			list: The list of all device items.
		"""
		if hasattr(self, 'items') and not reload:
			logger.debug(f"Returning cached list {type(self.items)} of all the items in the project: '{len(self.items)}'...")
			return self.items

		logger.debug(
			f"Retrieving all items from the project: "
			f"reload: '{reload}'"
		)

		items = []
		items.extend(self.get_devices(self.myproject))
		items.extend(self.get_devices(self.myproject.UngroupedDevicesGroup))
		items.extend(self.get_groups(self.myproject.DeviceGroups))

		# Removes all the duplicates
		items = list(set(items))
		self.items = items
		logger.debug(f"Returning combined list {type(items)} of all the items in the project: '{len(items)}'")
		return items


	def get_plc_devices(self, reload=False, items=None):
		"""
		Retrieves all the devices with a PLC service.

		Args:
			Items (list, optional): The list to store the retrieved devices. Defaults to None.

		Returns:
			list: The list of retrieved devices with a PLC service.
		"""
		if hasattr(self, 'plc_items') and not reload:
			logger.debug(f"Returning cached list {type(self.plc_items)} of all the PLC devices in the project: '{len(self.plc_items)}'...")
			return self.plc_items

		projectItems = self.GetAllItems(reload=reload)
		logger.debug(
			f"Filtering for PLC-devices out of all '{len(projectItems)}' the project items: "
			f"reload: '{reload}'"
		)
		if items is None:
			items = []
		for deviceitem in projectItems:
			if str(deviceitem.Classification) == 'CPU':
				items.append(deviceitem)
		
		self.plc_items = items
		logger.debug(
			f"Returning filtered list {type(items)} of all the PLC devices out of the project-items: "
			f"amount of PLC-items: '{len(items)}', "
			f"object type: '{items[0].GetType()}'"
		)
		return items