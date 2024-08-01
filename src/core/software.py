"""
Author: Quinten Bauwens
Last updated: 09/07/2024
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

	def get_software_blocks(self, group, blocks={}):
		"""
		Retrieves all the blocks in a given group recursively.

		Args:
			group: The group to retrieve the blocks from.
			blocks (dict): A dictionary to store the blocks. (default: {})

		Returns:
			dict: A dictionary containing the blocks in the group.
		"""

		if blocks is None:
			blocks = {}
		if group not in blocks:
			blocks[group] = []
			blocks[group].extend([block for block in group.Blocks])
			for sub_group in group.Groups:
				self.get_software_blocks(sub_group, blocks)
		return blocks

	def get_block(self, group, block_name):
		"""
		Retrieves a software block with the given name.

		Parameters:
		- block_name (str): The name of the software block to retrieve.

		Returns:
		- block: The software block with the given name, or None if not found.
		"""

		blocks = self.get_software_blocks(group)
		for blockgroup in blocks:
			for block in blocks[blockgroup]:
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