"""
Author: Quinten Bauwens
Last updated: 05/08/2024
"""

import clr
# add the reference to the Siemens.Engineering.dll
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll") 
import Siemens.Engineering.HW.Features as hwf
import Siemens.Engineering as tia
from core.hardware import Hardware

class Software:
	"""
	Represents the extraction of software components in the system/plc by using the PLC-software container.

	Args:
		myproject (str): The project associated with the software.
		myinterface (str): The interface used by the software.

	Attributes:
		myproject (str): The project associated with the software.
		myinterface (str): The interface used by the software.
		hardware (Hardware): The hardware component associated with the software.

	Methods:
		get_software_container: Retrieves the software container of the first PLC device.
		get_software_blocks: Retrieves all the blocks in a given group recursively.
	"""

	def __init__(self, myproject, myinterface) -> None:
		self.myproject = myproject
		self.myinterface = myinterface
		self.hardware = Hardware(self.myproject, self.myinterface)
		self.software_container = {}
		self.PLC_list = self.hardware.get_plc_devices()

	def get_software_container(self):
		"""
		Retrieves the software container of all PLC devices.

		Returns:
			SoftwareContainer: List of the software container of all PLC devices.
		"""
		
		for plc in self.PLC_list:
			self.software_container[plc.Name] = tia.IEngineeringServiceProvider(plc).GetService[hwf.SoftwareContainer]().Software
		return self.software_container

	def get_software_blocks(self, group, blocks=None, group_included=True):
		"""
		Retrieves the software blocks from the given group and its subgroups.
		Parameters:
			group (object): The group object from which to retrieve the software blocks.
			blocks (dict or list, optional): The dictionary or list to store the retrieved blocks. If not provided, a new dictionary will be created if group_included is True, otherwise a new list will be created. Defaults to None.
			group_included (bool, optional): Specifies whether the group itself should be included in the blocks. Defaults to True.
		Returns:
			dict or list: The dictionary or list containing the retrieved software blocks.
		Raises:
			Exception: If there is an error retrieving the software blocks.
		"""
		
		if blocks is None:
			blocks = {} if group_included else [] # create new dict if not provided
		
		if not group_included:
			blocks.extend([block for block in group.Blocks])
			for sub_group in group.Groups:
				self.get_software_blocks(sub_group, blocks, group_included=False)
			return blocks

		try:
			if group not in blocks:
				# if group contains blocks -> add them as a list to the dict, else add an empty list
				blocks[group] = ([block for block in group.Blocks] if hasattr(group, 'Blocks') else [])
				# if group contains a subgroup (.Groups) -> add the group as a dict inside the list of blocks, wich then contains the subgroup and its blocks
				if hasattr(group, 'Groups'):
					for sub_group in group.Groups:
						sub_blocks = self.get_software_blocks(sub_group)
						blocks[group].append({sub_group: sub_blocks[sub_group]})
		except Exception as e:
			print(f'Failed to retrieve software blocks with its group: {str(e)}')
		return blocks

	def get_block(self, group, block_name):
		"""
		Retrieves a software block with the given name.

		Parameters:
		- block_name (str): The name of the software block to retrieve.

		Returns:
		- block: The software block with the given name, or None if not found.
		"""

		blocks = self.get_software_blocks(group, group_included=False)
		for block in blocks:
			if block.Name.upper() == block_name.upper():
				return block

	def get_project_tags(self, group=None):
		"""
		Generates a list of the project tags.

		Args:
			group: The tag table group to retrieve the tags from. Defaults to None.

		Returns:
			dict: A dictionary containing all the project tags. The keys are the table names and the values are sets of tags.
		"""

		Tags = {}
		if group is None:
			for plc in self.PLC_list:
				group = self.software_container[plc.Name].TagTableGroup
				for table in group.TagTables:
					Tags[table] = set(table.Tags)
				for sub_group in group.Groups:
					sub_group_tags = self.get_project_tags(sub_group)
					for table, tags in sub_group_tags.items():
						if table in Tags:
							Tags[table].update(tags)
						else:
							Tags[table] = tags
		else:
			for table in group.TagTables:
				Tags[table] = set(table.Tags)
			for sub_group in group.Groups:
				sub_group_tags = self.get_project_tags(sub_group)
				for table, tags in sub_group_tags.items():
					if table in Tags:
						Tags[table].update(tags)
					else:
						Tags[table] = tags
		return Tags