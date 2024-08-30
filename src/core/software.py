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

from utils.loggerConfig import get_logger

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
		self.search_results = {}
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

	def get_core_classes(self):
		self.hardware = self.project.hardware

	def get_core_functions(self):
		logger.debug(f"Accessing 'get_plc_devices' from the hardware object '{self.project.hardware}'...")


	def get_software_container(self, reload=False) -> dict:
		"""
		Retrieves the software container of all PLC devices.

		Returns:
			SoftwareContainer: List of the software container of all PLC devices.
		"""

		if self.software_container and not reload:
			logger.debug(f"Returning the cached dict {type(self.software_container)} of all the software containers in the project: '{len(self.software_container)}'...")
			return self.software_container
		
		logger.debug(
			f"Retrieving the software container of all PLC devices in the project: "
			f"reload: '{reload}'"
		)
		self.PLC_list = self.hardware.get_plc_devices(reload=reload)

		logger.debug(
			f"Retrieving software container of all PLC devices: " 
			f"plc's: {[plc.Name for plc in self.PLC_list]}, "
			f"object type: '{self.PLC_list[0].GetType()}'"
		)
		for plc in self.PLC_list:
			self.software_container[plc.Name] = tia.IEngineeringServiceProvider(plc).GetService[hwf.SoftwareContainer]().Software

		logger.debug(
			f"Returning {type(self.software_container)} of software containers: "
			f"amount of software containers: '{len(self.software_container)}', "
			f"object type: '{next(iter(self.software_container.values())).GetType()}'"
		)
		return self.software_container


	def get_software_blocks(self, group, blocks=None, include_group=True, include_safety_blocks=False, reload=False, initial_call=True) -> dict | list:
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

		if not reload:
			if include_group and hasattr(self, 'software_blocks_dict'):
				logger.debug(f"Returning the cached dict {type(self.software_blocks_dict)} of all the software blocks in the project: '{len(self.software_blocks_dict)}'...")
				return self.software_blocks_dict
			elif not include_group and hasattr(self, 'software_blocks_list'):
				logger.debug(f"Returning the cached list {type(self.software_blocks_list)} of all the software blocks in the project: '{len(self.software_blocks_list)}'...")
				return self.software_blocks_list
		
		logger.debug(
			f"Retrieving all software blocks recursively from the project starting at group '{group.Name}': "
			f"include_group: '{include_group}', " 
			f"include_safety_blocks: '{include_safety_blocks}', " 
			f"reload: '{reload}'"
		) if initial_call else None

		if blocks is None:
			blocks = {} if include_group else [] # create new dict if not provided
		
		if not include_group:
			blocks.extend([block for block in group.Blocks])

			if hasattr(group, 'Groups'):
				for sub_group in group.Groups:
					self.get_software_blocks(sub_group, blocks, include_group, reload=reload, initial_call=False)

			if include_safety_blocks:
				self.get_software_blocks(group.SystemBlockGroups[0], blocks, include_group, reload=reload, initial_call=False)
			
			# when the recursion is done, the function will return to the initial call and return the blocks
			if initial_call:
				logger.debug(
					f"Returning list {type(blocks)} of all the software blocks in the project: "
					f"amount of blocks: '{len(blocks)}', "
					f"object type: '{blocks[0].GetType()}'"
				)
				self.software_blocks_list = blocks
			return blocks

		try:
			if group not in blocks:
				# if group contains blocks -> add them as a list to the dict, else add an empty list
				blocks[group] = ([block for block in group.Blocks] if hasattr(group, 'Blocks') else [])
				# if group contains a subgroup (.Groups) -> add the group as a dict inside the list of blocks, wich then contains the subgroup and its blocks
				if hasattr(group, 'Groups'):
					for sub_group in group.Groups:
						sub_blocks = self.get_software_blocks(sub_group, reload=reload, initial_call=False)
						blocks[group].append({sub_group: sub_blocks[sub_group]})
				if hasattr(group, 'SystemBlockGroups'):
					for sub_group in group.SystemBlockGroups:
						sub_blocks = self.get_software_blocks(sub_group, reload=reload, initial_call=False)
						blocks[group].append({sub_group: sub_blocks[sub_group]})
		except Exception as e:
			raise Exception(f'Failed to retrieve software blocks with its group: {str(e)}')
		
		# when the recursion is done, the function will return to the initial call and return the blocks
		if initial_call:
			logger.debug(
				f"Returning dict {type(blocks)} of all the software blocks in the project: "
				f"amount of blocks: '{len(blocks.values())}', "
				f"object type: '{blocks[0].GetType()}'"
			)
			self.software_blocks_dict = blocks
		return blocks


	def get_software_types(self, group, types=None, include_system_types=False, reload=False, initial_call=True) -> list:
		if hasattr(self, 'software_types') and not reload:
			logger.debug(f"Returning the cached list {type(self.software_types)} of all the software types in the project: '{len(self.software_types)}'...")
			return self.software_types
		
		logger.debug(
			f"Retrieving all software types recursively from the project starting at group: '{group.Name}': " 
			f"systemTypes: '{include_system_types}', "
			f"reload: '{reload}'"
		) if initial_call else None

		if types is None:
			types = []
		
		types.extend([type for type in group.Types])

		if hasattr(group, 'Groups'):
			for sub_group in group.Groups:
				self.get_software_types(sub_group, types, reload=reload, initial_call=False)
		
		if include_system_types:
			self.get_software_types(group.SystemTypeGroups[0], types)
		
		if initial_call:
			logger.debug(
				f"Returning list {type(types)} of all the software types in the project: "
				f"amount of types: '{len(types)}', "
				f"object type: '{types[0].GetType()}'"
			)
			self.software_types = types
		return types

	# TODO: Doesnt include systemBlocks
	def find_block(self, group, block_name, block_number=None, reload=False, initial_call=True) -> object:
		"""
		Retrieves a software block with the given name.

		Parameters:
		- block_name (str): The name of the software block to retrieve.

		Returns:
		- block: The software block with the given name, or None if not found.
		"""
		if block_name in self.search_results and not reload:
			logger.debug(f"Returning the cached software block-object '{self.search_results[block_name].GetType()}': '{block_name}'...")
			return self.search_results[block_name]
		
		logger.debug(
			f"Searching for software block: '{block_name}': "
			f"block_number: '{block_number}', "
			f"reload: '{reload}'"
		) if initial_call else None

		try:
			search_result = group.Blocks.Find(block_name)

			if search_result is not None:
				if block_number and search_result.Number != block_number:
					logger.debug(f"Block number does not match: '{search_result.Number}' != '{block_number}'")
					return None
				self.search_results[block_name] = search_result
				logger.debug(f"Returning the found software block-object '{search_result.GetType()}': '{search_result.Name}'")
				return search_result
			
			for subgroup in group.Groups:
				search_result = self.find_block(subgroup, block_name, block_number, initial_call=False)
				if search_result is not None:
					self.search_results[block_name] = search_result
					logger.debug(f"Returning the found software block-object '{search_result.GetType()}': '{search_result.Name}'")
					return search_result
		except Exception as e:
			raise Exception(f'Failed to retrieve software block: {str(e)}')
		finally:
			if isinstance(group, System.IDisposable):
				group.Dispose()
		return search_result


	def get_project_tags(self, group=None, reload=False, initial_call=True) -> dict:
		"""
		Generates a list of the project tags.

		Args:
			group: The tag table group to retrieve the tags from. Defaults to None.

		Returns:
			dict: A dictionary containing all the project tags. The keys are the table names and the values are sets of tags.
		"""
		if hasattr(self, 'tags') and not reload:
			logger.debug(f"Returning the cached list {type(self.tags)} of all the tags in the project: '{len(self.tags)}'...")
			return self.tags
		
		logger.debug(
			f"Retrieving all tags recursively from the project: "
			f"reload: '{reload}'"
		) if initial_call else None

		tags = {}

		def retrieve_tags_from_table(group):
			for table in group.TagTables:
				if table not in tags:
					tags[table] = set(table.Tags)
				else:
					tags[table].update(table.Tags)
			for sub_group in group.Groups:
				retrieve_tags_from_table(sub_group)
		
		if group is None: 
			# get tags from all groups
			for plc in self.PLC_list:
				group = self.software_container[plc.Name].TagTableGroup
				retrieve_tags_from_table(group)
		else: 
			# get tags from a specific group
			retrieve_tags_from_table(group)
		
		if initial_call:
			self.tags = tags
		logger.debug(
			f"Returning list {type(tags)} of all the tags in the project: "
			f"amount of tag-tables: '{len(tags)}', "
			f"object type tag-table: '{next(iter(tags.keys())).GetType()}', "
			f"object type tags: '{next(iter(tags.items())).GetType()}'"
		)
		return tags