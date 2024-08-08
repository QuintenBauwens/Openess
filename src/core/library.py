"""
Library module for the core package.
created by: Quinten Bauwens
created on: 01/08/2024
"""

import numpy as np
import pandas as pd
import Siemens.Engineering as tia # Copy the Siemens.Engineering.dll to the folder of the script (current working dir.)!!

from core.software import Software 


# TODO: DOCSTRINGS & documentation & Export data
class Library:
	"""
	Represents a library in the project.

	Args:
		myproject (object): The project object.
		myinterface (object): The interface object.
		plc_list (list): List of PLC objects.

	Attributes:
		myproject (object): The project object.
		myinterface (object): The interface object.
		plc_list (list): List of PLC objects.
		software (object): The software object.
		software_container (object): The software container object.
		lib_blocks (dict): Dictionary containing library blocks.
		library_df (object): The library dataframe.
		library_info (dict): Dictionary containing library information.
		used_lib_blocks_df (object): The used library blocks dataframe.
		used_lib_blocks_info (dict): Dictionary containing used library blocks information.
		project_blocks_df (object): The project blocks dataframe.
	"""

	def __init__(self, myproject, myinterface, plc_list=None):
		self.myproject = myproject
		self.myinterface = myinterface
		self.plc_list = plc_list
		
		self.software = Software(self.myproject, self.myinterface)
		self.software_container = self.software.get_software_container()

		self.software_library_groups = ['_GlobalLib', '_LocalLibGB', '_LocalLibVCG']
		self.lib_blocks = None
		self.library_df = None
		self.library_info = None

		self.used_lib_blocks_df = None
		self.used_lib_blocks_info = None

		self.project_blocks_df = None
		self.types_blocks_df = None
		self.project_types_df = None

		
	def get_map_structure(self, item, group_path=None):
		"""
		Recursively maps the structure of the item.

		Args:
			item (object): The item to map the structure of.
			groups (list, optional): List of groups. Defaults to None.

		Returns:
			list: List of groups representing the structure.
		"""

		if group_path is None:
			group_path = []

		try:
			folder = item.Parent.GetAttribute('Name')
			item = item.Parent
			if folder is not None and folder not in group_path:
				group_path.append(folder)
				self.get_map_structure(item, group_path)
		except:
			pass
		return group_path


	def get_library_blocks(self, software_library_groups, reload=False):
		"""
		Retrieves the library blocks.

		Args:
			software_library_groups (list, optional): List of software library groups. Defaults to ['_GlobalLib', '_LocalLibGB', '_LocalLibVCG'].

		Returns:
			dict: Dictionary containing library blocks.
		"""

		print('Retrieving library blocks...')

		if self.lib_blocks is not None and not reload:
			return self.lib_blocks
		
		lib_blocks = {}
		try:
			for plc in self.plc_list:
				lib_blocks[plc] = {}
				software_container = self.software_container[plc.Name]

				block_groups = [group for group in software_container.BlockGroup.Groups if group.Name in software_library_groups]

				if not block_groups:
					raise ValueError('no library blocks found in given software library groups')

				for group in block_groups:
					blocks_list = self.software.get_software_blocks(group, include_group=False)
					lib_blocks[plc][group] = blocks_list
		except Exception as e:
			raise Exception(f'Failed to retrieve library blocks: {str(e)}')
		
		self.lib_blocks = lib_blocks
		return self.lib_blocks


	def check_library_connection(self, reload=False):
		"""
		Checks the library connection.

		Returns:
			tuple: Tuple containing the library dataframe and library information.
		"""

		print('Checking library connection...')

		if self.library_df is not None and not reload:
			return self.library_df, self.library_info
		
		try:
			software_library_groups = self.get_software_library_groups()
			lib_blocks = self.get_library_blocks(software_library_groups, reload=reload)
			print(f'Library blocks retrieved...')
		except Exception as e:
			raise Exception(str(e))
			
		
		project_name = self.myproject.Name
		library_df = pd.DataFrame()
		library_info = {}

		for plc in lib_blocks.keys():
			plc_name = plc.Name

			for software_library_group in lib_blocks[plc]:
				library_group_name = software_library_group.Name
				group_blocks_list = lib_blocks[plc][software_library_group]
				
				for block in group_blocks_list:
					service = tia.Library.Types.LibraryTypeInstanceInfo
					instanceInfo = block.GetService[service]()
					
					block_modifiedDate = block.ModifiedDate
					folder_name = block.Parent.GetAttribute("Name")
					block_name = block.Name
					block_type = block.GetType().Name
					block_number = block.Number
					status = isinstance(instanceInfo, service) # true if connected to library, False if not
					isConsistent = block.IsConsistent

					update_library_df = pd.DataFrame({
						'Project':[project_name], 
						'ModifiedDate':[block_modifiedDate], 
						'PLC':[plc_name], 
						'LibraryFolder':[library_group_name], 
						'Folder':[folder_name], 
						'Name':[block_name], 
						'Type':[block_type], 
						'Number':[block_number], 
						'ConnectedToLibrary':[status],
						'isConsistent':[isConsistent],
						'Version':[instanceInfo.LibraryTypeVersion.VersionNumber if status else 'NaN'],
						'LibraryState':[instanceInfo.LibraryTypeVersion.State if status else 'NaN'],
						'LibraryConformanceStatus':[block.GetAttribute('LibraryConformanceStatus')]
						})
					
					library_df = pd.concat([library_df, update_library_df], ignore_index=True)

			if lib_blocks:
				unconnected_blocks = library_df.loc[library_df['ConnectedToLibrary'] == False].shape[0]
				connected_blocks = library_df.loc[library_df['ConnectedToLibrary'] == True].shape[0]

				library_info['total'] = unconnected_blocks + connected_blocks
				library_info['disconnected'] = unconnected_blocks
				library_info['connected'] = connected_blocks

		self.library_df = library_df
		self.library_info = library_info
		return self.library_df, self.library_info


	def get_project_types_df(self, group, folder_path=False, reload=False, include_system_types=False):
		"""
		Retrieves the project types dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			object: The project types dataframe.
		"""

		if self.project_types_df is not None and not reload:
			return self.project_types_df

		project_types = self.software.get_software_types(group, include_system_types=include_system_types)
		project_name = self.myproject.Name
		project_types_df = pd.DataFrame()
		
		for type in project_types:
			date = type.ModifiedDate
			plc_name = self.plc_name
			folder = type.Parent.GetAttribute('Name')
			type_name = type.Name
			struc = struc = type.ToString().split('.')[-1]
			isConsistent = type.IsConsistent

			try:
				type_number = type.GetAttribute('Number')
			except:
				type_number = None
			
			df_update = pd.DataFrame({
					'Project':[project_name], 
					'ModifiedDate':[date], 
					'PLC':[plc_name], 
					'Folder':[folder],
					'Name':[type_name], 
					'Type':[struc], 
					'Number':[type_number],
					'IsConsistent':[isConsistent]
					})
			
			if folder_path:
				reversed_structure = self.get_map_structure(type)
				structure = reversed(reversed_structure)
				path = '/'.join(folder for folder in structure)
				df_update['Path'] = path
			
			project_types_df = pd.concat([project_types_df, df_update], ignore_index=True)
		
		self.project_types_df = project_types_df
		return self.project_types_df


	def get_project_blocks_df(self, group, folder_path=False, reload=False, include_safety_blocks=False):
		"""
		Retrieves the project blocks dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the project blocks dataframe and instance DB.
		"""

		print('retrieving project_blocks_df...')

		if self.project_blocks_df is not None and not reload:
			return self.project_blocks_df
		
		project_blocks = self.software.get_software_blocks(group, include_group=False, include_safety_blocks=include_safety_blocks)
		print('in group:', group.Name, 'found', len(project_blocks), 'blocks')
		accepted_types = ['OB', 'FC', 'FB', 'GlobalDB', 'InstanceDB']
		project_name = self.myproject.Name

		project_blocks_df = pd.DataFrame()
		
		for block in project_blocks:
			blockType = block.GetType().Name
			blockNumber = block.Number
			isConsistent = block.IsConsistent
			folder = block.Parent.GetAttribute('Name')
			plc_name = self.plc_name

			try:
				instanceOfNumber = block.GetAttribute('InstanceOfNumber')
			except:
				instanceOfNumber = 'NaN'
			
			if blockType in accepted_types:
				df_update = pd.DataFrame({
						'Project':[project_name], 
						'ModifiedDate':[block.ModifiedDate], 
						'PLC':[plc_name], 
						'Folder':[folder],
						'Name':[block.Name], 
						'Type':[blockType], 
						'Number':[blockNumber],
						'InstanceOfName':[getattr(block, 'InstanceOfName', 'NaN')], # if block has no instanceOfName, return 'NaN'
						'InstanceOfNumber':[instanceOfNumber],
						'IsConsistent':[isConsistent]
						})
			else:
				raise ValueError('Blocktype not recognised')
			
			if folder_path:
				reversed_structure = self.get_map_structure(block)
				structure = reversed(reversed_structure)
				path = '/'.join(folder for folder in structure)
				df_update['Path'] = path
			
			project_blocks_df = pd.concat([project_blocks_df, df_update], ignore_index=True)
		
		self.project_blocks_df = project_blocks_df
		print("project_blocks_df retrieved...")
		return self.project_blocks_df
	

	def get_types_blocks_df(self, folder_path=False, reload=False):

		print('getting project df and types df...')

		types_blocks_df = pd.DataFrame()

		for plc in self.plc_list:
			self.plc_name = plc.Name
			software_container = self.software_container[plc.Name]
			location_projectBlocks = software_container.BlockGroup
			location_datatypes = software_container.TypeGroup
			
			project_blocks_df = self.get_project_blocks_df(location_projectBlocks, folder_path, reload, include_safety_blocks=True)
			print('project blocks df = ', len(project_blocks_df))
			project_types_df = self.get_project_types_df(location_datatypes, folder_path, reload, include_system_types=True)
			print('types df = ', len(project_types_df))

			types_blocks_df = pd.concat([types_blocks_df, project_blocks_df, project_types_df], ignore_index=True)
		
		self.types_blocks_df = types_blocks_df
		return self.types_blocks_df
	

	# TODO: add path as option setting
	def validate_used_blocks(self, folder_path=False, reload=False):
		"""
		Retrieves the used library blocks dataframe and checks wich instanceDB blocks are official instances of library blocks.

		Args:
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the used library blocks dataframe and used library blocks information.
		"""

		if self.used_lib_blocks_df is not None and not reload:
			return self.used_lib_blocks_df, self.used_lib_blocks_info
		
		print('Validating used blocks...')

		project_blocks_df = self.get_types_blocks_df(folder_path, reload)
		library_df, _ = self.check_library_connection(reload=reload)

		print(len(project_blocks_df), 'blocks in project')
		print(len(library_df), 'blocks in library')

		block_data_collection = []
		used_lib_blocks_info = {}

		try:
			for i, row in project_blocks_df.iterrows():
				block_name = row['Name']

				row_filter_blocks = (project_blocks_df['Name'] == block_name)
				row_block_data = project_blocks_df.loc[row_filter_blocks].copy()
				
				instanceOfNumber = row['InstanceOfNumber']
				instanceOfName = row['InstanceOfName']

				row_filter_library = (library_df['Name'] == instanceOfName) & (library_df['Number'] == instanceOfNumber)
				row_filter_result = library_df.loc[row_filter_library].empty

				# row_filter_result == False if block is connected to library/ is official
				row_block_data['ConnectedToLibrary'] = library_df.loc[row_filter_library, 'ConnectedToLibrary'].values[0] if not row_filter_result else False
				row_block_data['NameInLibrary'] = library_df.loc[row_filter_library, 'Name'].values[0] if not row_filter_result else 'NaN'
				row_block_data['Version'] = library_df.loc[row_filter_library, 'Version'].values[0] if not row_filter_result else 'NaN'
				row_block_data['LibraryState'] = library_df.loc[row_filter_library, 'LibraryState'].values[0] if not row_filter_result else 'NaN'

				# move folder path again to the last column of the dataframe
				if folder_path:
					folderPath_column = row_block_data.pop('Path')
					row_block_data['Path'] = folderPath_column

				block_data_collection.append(row_block_data)

				if i % 100 == 0:
					print(f'Processed {i} blocks, block_data_collection length: {len(block_data_collection)}')

			used_lib_blocks_df = pd.concat(block_data_collection, ignore_index=True)
			used_lib_blocks_df.fillna('NaN', inplace=True)
		
			disconnected_blocks = used_lib_blocks_df.loc[(used_lib_blocks_df['ConnectedToLibrary'] == False) & (used_lib_blocks_df['Type'] == 'InstanceDB')].shape[0]
			connected_blocks = used_lib_blocks_df.loc[used_lib_blocks_df['ConnectedToLibrary'] == True].shape[0]

			used_lib_blocks_info['total'] = len(project_blocks_df)
			used_lib_blocks_info['instanceDB'] = disconnected_blocks + connected_blocks
			used_lib_blocks_info['disconnected'] = disconnected_blocks
			used_lib_blocks_info['connected'] = connected_blocks

			self.used_lib_blocks_df = used_lib_blocks_df
			self.used_lib_blocks_info = used_lib_blocks_info
			return self.used_lib_blocks_df, self.used_lib_blocks_info
		except Exception as e:
			print(f'an error occured: {str(e)}')
			return None, None
	

	def set_software_library_groups(self, software_library_groups):
		"""
		Sets the software library groups.

		Args:
			software_library_groups (list): List of software library groups.
		"""

		self.software_library_groups = software_library_groups

	
	def get_software_library_groups(self):
		"""
		Gets the software library groups.

		Returns:
			list: List of software library groups.
		"""

		return self.software_library_groups