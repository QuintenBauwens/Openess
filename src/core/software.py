"""
Author: Quinten Bauwens
Last updated: 05/08/2024
"""

import clr
import System
# add the reference to the Siemens.Engineering.dll
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll") 
import Siemens.Engineering.HW.Features as hwf
import Siemens.Engineering as tia

from utils.logger_config import get_logger

logger = get_logger(__name__)

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

	def __init__(self, project) -> None:
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface

		self.software_container = {}
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

	def get_core_classes(self):
		self.hardware = self.project.hardware

	def get_core_functions(self):
		logger.debug(f"Retrieved {len(self.PLC_list)} PLC devices from the hardware component {self.PLC_list}")


	def get_software_container(self) -> dict:
		"""
		Retrieves the software container of all PLC devices.

		Returns:
			SoftwareContainer: List of the software container of all PLC devices.
		"""
		self.PLC_list = self.hardware.get_plc_devices()
		logger.debug(f"Retrieving software container of all PLC devices: {[plc.Name for plc in self.PLC_list]}")
		for plc in self.PLC_list:
			self.software_container[plc.Name] = tia.IEngineeringServiceProvider(plc).GetService[hwf.SoftwareContainer]().Software
		logger.debug(f"Returning {type(self.software_container)} of software containers of all PLC devices: {len(self.software_container)}")
		return self.software_container


	def get_software_blocks(self, group, blocks=None, include_group=True, include_safety_blocks=False) -> dict | list:
		"""
		Retrieves the software blocks from the given group and its subgroups.
		Parameters:
			group (object): The group/folder object from which to retrieve the software blocks.
			blocks (dict or list, optional): The dictionary or list to store the retrieved blocks. If not provided, a new dictionary will be created if group_included is True, otherwise a new list will be created. Defaults to None.
			group_included (bool, optional): Specifies whether the group itself should be included in the blocks. Defaults to True.
		Returns:
			dict or list: The dictionary or list containing the retrieved software blocks.
		Raises:
			Exception: If there is an error retrieving the software blocks.
		"""
		
		if blocks is None:
			blocks = {} if include_group else [] # create new dict if not provided
		
		if not include_group:
			blocks.extend([block for block in group.Blocks])

			if hasattr(group, 'Groups'):
				for sub_group in group.Groups:
					self.get_software_blocks(sub_group, blocks, include_group)

			if include_safety_blocks:
				self.get_software_blocks(group.SystemBlockGroups[0], blocks, include_group)
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
				if hasattr(group, 'SystemBlockGroups'):
					for sub_group in group.SystemBlockGroups:
						sub_blocks = self.get_software_blocks(sub_group)
						blocks[group].append({sub_group: sub_blocks[sub_group]})
		except Exception as e:
			raise Exception(f'Failed to retrieve software blocks with its group: {str(e)}')
		return blocks


	def get_software_types(self, group, types=None, include_system_types=False) -> list:
		if types is None:
			types = []
		
		types.extend([type for type in group.Types])

		if hasattr(group, 'Groups'):
			for sub_group in group.Groups:
				self.get_software_types(sub_group, types)
		
		if include_system_types:
			self.get_software_types(group.SystemTypeGroups[0], types)
		return types


	def find_block(self, group, block_name, block_number=None) -> object:
		"""
		Retrieves a software block with the given name.

		Parameters:
		- block_name (str): The name of the software block to retrieve.

		Returns:
		- block: The software block with the given name, or None if not found.
		"""

		try:
			search_result = group.Blocks.Find(block_name)

			if search_result is not None:
				if block_number and search_result.Number != block_number:
					logger.debug(f'Block number does not match: {search_result.Number} != {block_number}')
					return None
				return search_result
			
			for subgroup in group.Groups:
				search_result = self.find_block(subgroup, block_name, block_number)
				if search_result is not None:
					return search_result
		except Exception as e:
			raise Exception(f'Failed to retrieve software block: {str(e)}')
		finally:
			if isinstance(group, System.IDisposable):
				group.Dispose()
		logger.debug(f'Returning the found software block-object {type(search_result)}: {search_result.Name}')
		return search_result


	def get_project_tags(self, group=None) -> dict:
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
		logger.debug(f"Returning list {type(Tags)} of all the tags in the project, total of: {len(Tags)} tags")
		return Tags