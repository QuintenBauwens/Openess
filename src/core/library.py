"""
Library module for the core package.
created by: Quinten Bauwens
created on: 01/08/2024
"""

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

		self.lib_blocks = None
		self.library_df = None
		self.library_info = None

		self.used_lib_blocks_df = None
		self.used_lib_blocks_info = None

		self.project_blocks_df = None


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
					blocks_list = self.software.get_software_blocks(group, group_included=False)
					lib_blocks[plc][group] = blocks_list
		except Exception as e:
			raise Exception(f'Failed to retrieve library blocks: {str(e)}')
		
		self.lib_blocks = lib_blocks
		return self.lib_blocks


	def check_library_connection(self, software_library_groups=['_GlobalLib', '_LocalLibGB', '_LocalLibVCG'], reload=False):
		"""
		Checks the library connection.

		Returns:
			tuple: Tuple containing the library dataframe and library information.
		"""

		print('Checking library connection...')

		if self.library_df is not None and not reload:
			return self.library_df, self.library_info
		
		try:
			lib_blocks = self.get_library_blocks(software_library_groups, reload)
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
					blockType = block.GetType().Name
					blockNumber = block.Number
					folder = block.Parent.GetAttribute("Name")
					block_modifiedDate = block.ModifiedDate
					isConsistent = block.IsConsistent
					libraryConformanceStatus = block.GetAttribute('LibraryConformanceStatus')

					status = isinstance(instanceInfo, service) # true if connected to library, False if not

					update_library_df = pd.DataFrame({
						'Project':[project_name], 
						'ModifiedDate':[block_modifiedDate], 
						'PLC':[plc_name], 
						'LibraryFolder':[library_group_name], 
						'Folder':[folder], 
						'Name':[block.Name], 
						'Type':[blockType], 
						'Number':[blockNumber], 
						'ConnectedToLibrary':[status],
						'isConsistent':[isConsistent],
						'Version':[instanceInfo.LibraryTypeVersion.VersionNumber if status else 'NaN'],
						'LibraryState':[instanceInfo.LibraryTypeVersion.State if status else 'NaN'],
						'LibraryConformanceStatus':[libraryConformanceStatus]
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


	def get_project_blocks_df(self, group, folder_path=False, reload=False):
		"""
		Retrieves the project blocks dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the project blocks dataframe and instance DB.
		"""

		# if self.project_blocks_df is not None and not reload:
		# 	return self.project_blocks_df, self.instance_db
		
		print('retrieving project_blocks_df...')
		project_blocks = self.software.get_software_blocks(group, group_included=False)
		print('in group:', group.Name, 'found', len(project_blocks), 'blocks')
		exepted_types = ['OB', 'FC', 'FB', 'GlobalDB', 'InstanceDB']
		project_name = self.myproject.Name

		df = pd.DataFrame()
		instance_db = []
		aantal_doorlopen_plc = 0
		aantal_doorlopen_block = 0
		
		for plc in self.plc_list:
			aantal_doorlopen_plc += 1
			for block in project_blocks:
				aantal_doorlopen_block += 1
				blockType = block.GetType().Name
				blockNumber = block.Number
				folder = block.Parent.GetAttribute('Name')
				plc_name = plc.Name
				
				if blockType in exepted_types:
					if blockType == 'InstanceDB':
						instance_db.append(block)
						instanceOf = block.InstanceOfName
					else: 
						instanceOf = 'NaN'

					df_update = pd.DataFrame({
							'Project':[project_name], 
							'ModifiedDate':[block.ModifiedDate], 
							'PLC':[plc_name], 
							'Folder':[folder],
							'Name':[block.Name], 
							'Type':[blockType], 
							'Number':[blockNumber],
							'InstanceOf':[instanceOf]
							})
				else:
					raise ValueError('Blocktype not recognised')
				
				if folder_path:
					reversed_structure = self.get_map_structure(block)
					structure = reversed(reversed_structure)
					path = '/'.join(folder for folder in structure)
					df_update['Path'] = path
				
				project_blocks_df = pd.concat([df, df_update], ignore_index=True)
		
		print('aantal doorlopen plc:', aantal_doorlopen_plc)
		print('aantal doorlopen block:', aantal_doorlopen_block)
		self.project_blocks_df = project_blocks_df
		self.instance_db = instance_db
		return self.project_blocks_df, self.instance_db

	# TODO: also show non-instanceDB blocks in df - add if type InstanceDB to filter + instanceOfNumber for non lib blocks?
	def validate_used_blocks(self, folder_path=False, reload=False):
		"""
		Retrieves the used library blocks dataframe.

		Args:
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the used library blocks dataframe and used library blocks information.
		"""

		# if self.used_lib_blocks_df is not None and not reload:
		# 	return self.used_lib_blocks_df, self.used_lib_blocks_info
		
		print('Validating used blocks...')
		plc_list = self.plc_list
		myproject = self.myproject

		for plc in plc_list:
			software_container = self.software_container[plc.Name]
			
			location_projectBlocks = software_container.BlockGroup
			location_safetyBlocks = software_container.BlockGroup.SystemBlockGroups[0]
			print('getting project df and safety df...')
			project_blocks_df, instanceDB_object = self.get_project_blocks_df(location_projectBlocks)
			safety_blocks_df, safety_instanceDB_object = self.get_project_blocks_df(location_safetyBlocks)
			print('returned project df and safety df...')
			print('project blocks df = ', project_blocks_df)
			print('safety blocks df = ', safety_blocks_df)
			combined_df = pd.concat([project_blocks_df, safety_blocks_df], ignore_index=True)
			combined = instanceDB_object + safety_instanceDB_object 
			print('combined = ', len(combined))

			instanceDB_data = []
			used_lib_blocks_info = {}

			# if self.library_df is None:
			# 	print('self.library_df is None')
			# 	self.library_df, self.library_info = self.check_library_connection()
			
			# print('self.library_df is not None')
			# connected_lib_group_blocks_df = self.library_df
			
			connected_lib_group_blocks_df, _ = self.check_library_connection()
			print('connected_lib_group_blocks_df = ', connected_lib_group_blocks_df)
			print('retrieved connected_lib_group_blocks_df...')

			print(f'Number of blocks in combined: {len(combined)}')
			loop_combined_aantal = 0
			for i, block in enumerate(combined):
				loop_combined_aantal += 1
				block_name = block.Name
				isConsistent = block.IsConsistent
				try:
					instanceOfNumber = block.GetAttribute('InstanceOfNumber')
					instanceOfName = block.GetAttribute('InstanceOfName')
				except:
					pass

				search_filter_library = (connected_lib_group_blocks_df['Name'] == instanceOfName) & (connected_lib_group_blocks_df['Number'] == instanceOfNumber)
				search_filter_project = (combined_df['Name'] == block_name) & (combined_df['Type'] == 'InstanceDB')

				project_block_data = combined_df.loc[search_filter_project].copy()

				# add columns to project_block_data
				if not connected_lib_group_blocks_df.loc[search_filter_library].empty: 
					project_block_data['InstanceOfNumber'] = instanceOfNumber
					project_block_data['ConnectedToLibrary'] = connected_lib_group_blocks_df.loc[search_filter_library, 'ConnectedToLibrary'].values[0]
					project_block_data['NameInLibrary'] = connected_lib_group_blocks_df.loc[search_filter_library, 'Name'].values[0]
					project_block_data['Version'] = connected_lib_group_blocks_df.loc[search_filter_library, 'Version'].values[0]
					project_block_data['isConsistent'] = isConsistent
					project_block_data['LibraryState'] = connected_lib_group_blocks_df.loc[search_filter_library, 'LibraryState'].values[0]
				
				if folder_path:
					reversed_structure = self.get_map_structure(block)
					structure = reversed(reversed_structure)
					path = '/'.join(folder for folder in structure)
					project_block_data['Path'] = path
				
				instanceDB_data.append(project_block_data)

				if i % 100 == 0:
					print(f'Processed {i} blocks, instanceDB_data length: {len(instanceDB_data)}')
			
		print('Total number of blocks processed:', len(instanceDB_data))

		used_lib_blocks_df = pd.DataFrame(instanceDB_data)
		print(f'Rows in used_lib_blocks_df: {len(used_lib_blocks_df)}')
		unconnected_blocks = used_lib_blocks_df.loc[used_lib_blocks_df['ConnectedToLibrary'] == False].shape[0]
		connected_blocks = used_lib_blocks_df.loc[used_lib_blocks_df['ConnectedToLibrary'] == True].shape[0]

		used_lib_blocks_info['total'] = unconnected_blocks + connected_blocks
		used_lib_blocks_info['disconnected'] = unconnected_blocks
		used_lib_blocks_info['connected'] = connected_blocks

		print('aantal doorlopen combined:', loop_combined_aantal)
		self.used_lib_blocks_df = used_lib_blocks_df
		self.used_lib_blocks_info = used_lib_blocks_info

		return self.used_lib_blocks_df, self.used_lib_blocks_info