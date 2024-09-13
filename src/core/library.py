"""
Library module for the core package.
created by: Quinten Bauwens
created on: 01/08/2024
"""

import os
import pandas as pd
import traceback
import datetime
import xmltodict
import pprint
import xml.etree.ElementTree as ET
import Siemens.Engineering as tia # Copy the Siemens.Engineering.dll to the folder of the script (current working dir.)!!

from utils.loggerConfig import get_logger

logger = get_logger(__name__)

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
		project_blocks_df (object): The project blocks dataframe.
	"""

	def __init__(self, project):
		logger.debug(f"Initializing {__name__.split('.')[-1]} instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface

		self.item_group_path = {}

		self.library_types = None
		self.library_df = None
		self.library_df = None
		self.library_info = None
		self.system_lib_version = None

		self.used_lib_blocks_df = None

		self.project_blocks_df = None
		self.types_blocks_df = None
		self.project_types_df = None

		self.df_path = pd.DataFrame(columns=['Name', 'Path'])
		self.df_warning = pd.DataFrame(columns=['Name', 'Warning'])

		self.folder_path = False
		self.include_warning_column = False
		self.include_safety_blocks = True
		self.include_system_types = True

		self.settings = {
			'folder_path': False,
			'warning_column': False,
			'safety_blocks': True,
			'system_types': True
		}

		self.pp = pprint.PrettyPrinter(indent=2)

		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully with settings: {self.settings}")
	

	def get_core_classes(self):
		self.software = self.project.software
		self.hardware = self.project.hardware
		self.blocks = self.project.blockdata
		self.file = self.project.file

	def get_core_functions(self):
		logger.debug(f"Accessing 'get_software_container' from the software object '{self.project.software}'...")
		self.software_container = self.software.get_software_container()
		logger.debug(f"Accessing 'get_plc_devices' from the hardware object '{self.project.hardware}'...")
		self.plc_list = self.hardware.get_plc_devices()
		if hasattr(self.project.blockdata, 'plc_list'):
			logger.debug(f"Accessing 'get_nwk_para' from the blocks object '{self.project.blockdata}'...")
			self.system_lib_version = self.blocks.get_nwk_para('LSystemVarS7-1500', 'LVccLibVersion')

	def get_map_structure(self, item, group_path=None, initial_call=True):
		"""
		Recursively maps the structure of the item.

		Args:
			item (object): The item to map the structure of.
			groups (list, optional): List of groups. Defaults to None.

		Returns:
			list: List of groups representing the structure.
		"""
		if initial_call:
			if item.Name in self.item_group_path.keys(): # HAS TO BE IN initial_call, OTHERWISE IT RETURNS ON SECOND CALL
				logger.debug(f"Item '{item.Name}' already mapped, returning cached content...")
				return self.item_group_path[item.Name]
		
			logger.debug(
				f"Mapping structure of item '{item.Name}': "
				f"object type: '{item.GetType()}'"
			) if initial_call else None

			item_name = item.Name

		if group_path is None:
			group_path = []

		try:
			folder = item.Parent.GetAttribute('Name')
			item = item.Parent
			if folder is not None and folder not in group_path:
				group_path.append(folder)
			self.get_map_structure(item, group_path, initial_call=False)
		except:
			pass
		
		if initial_call:
			self.item_group_path[item_name] = group_path
			logger.debug(
				f"Structure mapped: "
				f"item: {item_name}, "
				f"path: {group_path}"
			)
		return group_path


	def get_library_types(self, group, types=None, reload=False, initial_call=True):
		if self.library_types is not None and not reload:
			logger.debug('Library types retrieved earlier, returning cached content...')
			return self.library_types
		
		logger.debug(
			f"Retrieving library types recursively from group '{group.Parent}': "
			f"object type: '{group.GetType()}', "
			f"reload: '{reload}'"
		) if initial_call else None

		if types is None:
			types = []
		
		types.extend([type for type in group.Types])

		for subfolder in group.Folders:
			self.get_library_types(subfolder, types, reload=reload, initial_call=False)

		if initial_call:
			logger.debug(
				f"Returning library types {type(types)}: "
				f"total types: '{len(types)}', "
				f"object type: '{types[0].GetType()}'"
			)
			self.library_types = types
		return types


	def get_library_content(self, reload: bool=False):
		if self.library_df is not None and not reload:
			logger.debug('Library dataframe retrieved earlier, returning cached content...')
			return self.library_df
		
		logger.debug(
			f"Retrieving library data: "
			f"reload: '{reload}'"
		)

		libraryType_folder = self.myproject.ProjectLibrary.TypeFolder
		project_name = self.myproject.Name
		library_content = pd.DataFrame()
		
		try:
			self.library_types = self.get_library_types(libraryType_folder, reload=reload)
			self.plc_list = self.hardware.get_plc_devices(reload=reload)

			logger.debug(
				f"Making dataframe entry for each library type: "
				f"entry settings: '{self.get_settings()}', "
				f"plc's: {[plc.Name for plc in self.plc_list]}, "
				f"total types: '{len(self.library_types)}' "
				f"object type: '{self.library_types[0].GetType()}'"
			)

			if self.library_types is None:
				raise ValueError('No library types found')

			for library_type in self.library_types:
				folder = library_type.Parent.GetAttribute('Name')
				type_comment = ''.join(s.Text for s in library_type.Comment.Items)
				type_name = library_type.Name
				type_versions = library_type.Versions
				version_count = type_versions.Count
				instance_count = 0

				logger.debug(
					f"entry '{type_name}': "
					f"amount of versions: '{type_versions.Count}', "
					f"object type: '{type_versions.GetType()}'"
				)
				
				for version in type_versions:
					version_comment = ''.join(s.Text for s in version.Comment.Items)
					for plc in self.plc_list:
						instance_count += version.FindInstances(self.software_container[plc.Name]).Count
					# convert date in every df to datetime object for later comparison in validate_used_blocks
					date = version.ModifiedDate
					version_modifiedDate = datetime.datetime(date.Year, date.Month, date.Day, date.Hour, date.Minute, date.Second).strftime('%d-%m-%Y %H:%M:%S')
					version_author = version.Author
					version_xDependents = version.Dependents.Count
					library_state = str(version.State)

					df_update = pd.DataFrame({
						'Project':[project_name],
						'Folder':[folder],
						'Name':[type_name],
						'Version':[version.VersionNumber],
						'ModifiedDate':[version_modifiedDate],
						'Author':[version_author],
						'LibraryState':[library_state],
						'Dependents':[version_xDependents],
						'InstanceCount':[instance_count],
						'VersionCount':[version_count],
						'TypeComment':[type_comment],
						'VersionComment':[version_comment],
						'ReferenceObject':[version]
						})
					reversed_structure = self.get_map_structure(library_type)

					if self.folder_path:
						df_update['Path'] = '/'.join(reversed(reversed_structure))
					library_content = pd.concat([library_content, df_update], ignore_index=True)
					path = '/'.join(reversed(reversed_structure))
					logger.debug(path)
					
					df_update = pd.DataFrame({
						'Name' : [type_name],
						'Path' : [path]
					})

					self.df_path = pd.concat([self.df_path, df_update], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to make library blocks dataframe: {str(e)}')
		
		self.library_df = library_content
		logger.debug(
			f"Returning library dataframe: {type(self.library_df)}, "
			f"total entries: '{len(self.library_df)}', "
			f"columns: {(self.library_df.columns)}"
		)
		return self.library_df


	def get_project_types_df(self, group, plc, reload: bool=False):
		"""
		Retrieves the project types dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			object: The project types dataframe.
		"""
		if self.project_types_df is not None and not reload:
			logger.debug('Project types and blocks dataframe retrieved earlier, returning cached content...')
			return self.project_types_df

		logger.debug(
			f"Retrieving project types data: "
			f"reload: '{reload}'"
		)

		project_types_df = pd.DataFrame()

		try:
			project_types = self.software.get_software_types(group, include_system_types=self.include_system_types, reload=reload)
			project_name = self.myproject.Name

			logger.debug(
				f"Retrieved project types: ",
				f"plc: '{plc.Name}', "
				f"total types: '{len(project_types)}', "
				f"object type: '{project_types[0].GetType()}'"
			)

			for project_type in project_types:
				date = project_type.ModifiedDate
				type_modifiedDate = datetime.datetime(date.Year, date.Month, date.Day, date.Hour, date.Minute, date.Second).strftime('%d-%m-%Y %H:%M:%S')
				plc_name = plc.Name
				folder = project_type.Parent.GetAttribute('Name')
				type_name = project_type.Name
				struc = project_type.ToString().split('.')[-1]
				isConsistent = project_type.IsConsistent

				logger.debug(
					f"entry '{type_name}': "
					f"plc: {plc_name}', "
					f"object type: '{project_type.ToString()}'"
				)

				try:
					type_number = project_type.GetAttribute('Number')
				except:
					type_number = None
					logger.debug(f"No type_number found for type '{type_name}' under '{folder}'")
				
				df_update = pd.DataFrame({
						'Project':[project_name], 
						'PLC':[plc_name], 
						'Folder':[folder],
						'Name':[type_name], 
						'Type':[struc], 
						'Number':[type_number],
						'IsConsistent':[isConsistent],
						'ModifiedDate':[type_modifiedDate],
						'ReferenceObject':[project_type]
						})
				reversed_structure = self.get_map_structure(project_type)

				if self.folder_path:
					df_update['Path'] = '/'.join(reversed(reversed_structure))
				project_types_df = pd.concat([project_types_df, df_update], ignore_index=True)

				df_update = pd.DataFrame({
					'Name' : [type_name],
					'Path' : ['/'.join(reversed(reversed_structure))]
				})
				self.df_path = pd.concat([self.df_path, df_update], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to make project types dataframe: {str(e)}')
		
		self.project_types_df = project_types_df
		logger.debug(
			f"Returning project types dataframe {type(self.project_types_df)}: "
			f"total entries: '{len(self.project_types_df)}', "
			f"columns: {self.project_types_df.columns}"
		)
		return self.project_types_df


	def get_project_blocks_df(self, group, plc, reload=False):
		"""
		Retrieves the project blocks dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the project blocks dataframe and instance DB.
		"""

		if self.project_blocks_df is not None and not reload:
			logger.debug('Project blocks dataframe retrieved earlier, returning cached content...')
			return self.project_blocks_df
		
		logger.debug(
			f"Retrieving project blocks data: "
			f"reload: '{reload}'"
		)

		project_blocks_df = pd.DataFrame()

		try:
			project_blocks = self.software.get_software_blocks(group, include_group=False, include_safety_blocks=self.include_safety_blocks)

			logger.debug(
				f"Retrieved project blocks: ,"
				f"plc: '{plc.Name}', "
				f"total types: '{len(project_blocks)}', "
				f"object type: '{project_blocks[0].GetType()}'"
			)
			accepted_types = ['OB', 'FC', 'FB', 'GlobalDB', 'InstanceDB']
			project_name = self.myproject.Name
			
			for block in project_blocks:
				blockType = block.GetType().Name
				
				if blockType not in accepted_types:
					logger.debug(f"Blocktype '{blockType}' of block '{block.Name}' not recognised, continuing...")
					continue

				blockNumber = block.Number
				isConsistent = block.IsConsistent
				date = block.ModifiedDate
				block_modifiedDate = datetime.datetime(date.Year, date.Month, date.Day, date.Hour, date.Minute, date.Second).strftime('%d-%m-%Y %H:%M:%S')
				folder = block.Parent.GetAttribute('Name')
				plc_name = plc.Name

				logger.debug(
					f"entry '{block.Name}': "
					f"plc: {plc_name}', "
					f"object type: '{blockType}', "
				)

				try:
					instanceOfNumber = block.GetAttribute('InstanceOfNumber')
				except:
					instanceOfNumber = 'NaN'
					logger.debug(f"No instanceOfNumber found for block '{block.Name} - {block.GetType()}' under '{folder}'")
				
				if blockType in accepted_types:
					df_update = pd.DataFrame({
							'Project':[project_name],
							'PLC':[plc_name], 
							'Folder':[folder],
							'Name':[block.Name], 
							'Type':[blockType], 
							'Number':[blockNumber],
							'InstanceOfName':[getattr(block, 'InstanceOfName', 'NaN')], # if block has no instanceOfName, return 'NaN'
							'InstanceOfNumber':[instanceOfNumber],
							'IsConsistent':[isConsistent],
							'ModifiedDate':[block_modifiedDate],
							'ReferenceObject':[block] 
							})
				else:
					raise ValueError('Blocktype not recognised')
				
				reversed_structure = self.get_map_structure(block)

				if self.folder_path:
					df_update['Path'] = '/'.join(reversed(reversed_structure))
				project_blocks_df = pd.concat([project_blocks_df, df_update], ignore_index=True)

				df_update = pd.DataFrame({
					'Name' : [block.Name],
					'Path' : ['/'.join(reversed(reversed_structure))]
				})

				self.df_path = pd.concat([self.df_path, df_update], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to retrieve project blocks dataframe: {str(e)}')
		
		self.project_blocks_df = project_blocks_df
		logger.debug(
			f"Returning project blocks dataframe {type(self.project_blocks_df)}: "
			f"total entries: '{len(self.project_blocks_df)}', "
			f"columns: '{self.project_blocks_df.columns}'"
		)
		return self.project_blocks_df
	

	def get_types_blocks_df(self, reload=False):
		logger.debug(
				f"Making dataframe entry for each project type/block in each plc: "
				f"entry settings: {self.get_settings()}, "
				f"plc's: {[plc.Name for plc in self.plc_list]}, "
				f"reload: '{reload}'"
			)
		types_blocks_df = pd.DataFrame()
		self.plc_list = self.hardware.get_plc_devices(reload=reload)
		try:
			for plc in self.plc_list:
				logger.debug(f"Handling plc: '{plc.Name}'...")
				software_container = self.software_container[plc.Name]
				location_projectBlocks = software_container.BlockGroup
				location_datatypes = software_container.TypeGroup
				
				project_blocks_df = self.get_project_blocks_df(location_projectBlocks, plc, reload)
				project_types_df = self.get_project_types_df(location_datatypes, plc, reload)

				types_blocks_df = pd.concat([types_blocks_df, project_blocks_df, project_types_df], ignore_index=True)
				logger.debug(
					f"'{plc.Name}' type/block entries added to types-blocks dataframe: "
					f"total blocks: '{len(project_blocks_df)}' "
					f"total types: '{len(project_types_df)}'"
					f"total entries: '{len(types_blocks_df)}'"
				)
		except Exception as e:
			raise Exception(f'Failed to retrieve types blocks dataframe: {str(e)}')
		
		self.types_blocks_df = types_blocks_df
		logger.debug(
			f"Returning types-blocks dataframe {type(self.types_blocks_df)}: "
			f"total entries: '{len(self.types_blocks_df)}', "
			f"columns: {self.types_blocks_df.columns}"
		)
		return self.types_blocks_df
	

	# TODO: add path as option setting
	def validate_used_blocks(self, reload: bool=False):
		"""
		Retrieves the used library blocks dataframe and checks wich instanceDB blocks are official instances of library blocks.

		Args:
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the used library blocks dataframe and used library blocks information.
		"""

		if self.used_lib_blocks_df is not None and not reload:
			logger.debug('Blocks have been validated earlier, returning cached content...')
			return self.used_lib_blocks_df
		
		logger.debug(
			f"Checking used blocks data and validating against library blocks: "
			f"reload: '{reload}'"
		)
		
		data_collection = []
		used_lib_blocks_df = None
			
		try:
			project_blocks_df = self.get_types_blocks_df(reload)
			library_content_df = self.get_library_content(reload)
			library_service = tia.Library.Types.LibraryTypeInstanceInfo

			logger.debug(f"Validating '{len(project_blocks_df)}' project blocks against '{len(library_content_df)}' library blocks, and making dataframe entry for each block")
			for i, row in project_blocks_df.iterrows():
				block_type = row['Type']
				block_name = row['Name']
				row_block_data = row.copy()

				if block_type == 'InstanceDB':
					block_instanceOfName = row['InstanceOfName']
					block_instanceOfNumber = row['InstanceOfNumber']

					search_instance_filter = (project_blocks_df['Name'] == block_instanceOfName) & (project_blocks_df['Number'] == block_instanceOfNumber)
					search_instance = project_blocks_df.loc[search_instance_filter]

					if search_instance.empty:
						message = f"Block '{block_name}' wich is instanceOf '{block_instanceOfName}' not found in project blocks"
						row_block_data['ConnectedToLibrary'] = False
						data_collection.append(row_block_data)
						
						df_warning_update = pd.DataFrame({
							'Name' : [block_name],
							'Warning': [message]
						})
						self.df_warning = pd.concat([self.df_warning, df_warning_update], ignore_index=True)
						logger.warning(message) 
						continue
					
					block_object = search_instance['ReferenceObject'].values[0]
					block_modifiedDate = search_instance['ModifiedDate'].values[0]
					logger.debug(f"Found block '{block_name}' wich is instanceOf block '{block_instanceOfName}' in project blocks")
				else:
					block_object = row['ReferenceObject']
					block_modifiedDate = row['ModifiedDate']

				try:
					connect_to_library = block_object.GetService[library_service]()
					connection = True if isinstance(connect_to_library, library_service) else False
				except Exception as e:
					connection = False
					logger.warning(f"Cannot connect to library with block '{block_name}' - unofficial programblock")
				
				if connection:
					library_type_name = connect_to_library.LibraryTypeVersion.TypeObject.Name
					library_type_version = connect_to_library.LibraryTypeVersion.VersionNumber
					library_conformanceStatus = block_object.GetAttribute('LibraryConformanceStatus')

					library_search_filter = (
						(library_content_df['Name'] == library_type_name)
					)
					library_search_filter2 = (
						(library_content_df['Version'] == library_type_version)
					)

					library_search_type1 = library_content_df.loc[library_search_filter]
					library_search_type2 = library_search_type1.loc[library_search_filter2]
					library_search_versions = library_search_type2['Version'].values if not library_search_type2.empty else None

					row_block_data['ConnectedToLibrary'] = connection
					row_block_data['Version'] = library_type_version
					if not library_search_type1.empty or library_search_versions is not None:
						row_block_data['VersionInLibrary'] =  (library_type_version if library_type_version in library_search_versions else library_search_versions[0])
					else:
						version_tuples = library_search_type1['Version'].apply(lambda v: tuple(map(int, v.split('.')))) if not library_search_type1.empty else None
						max_version = max(version_tuples) if version_tuples is not None else None
						row_block_data['VersionInLibrary'] = max_version if max_version is not None else 'NaN'
					row_block_data['NameInLibrary'] = library_type_name

					if library_search_type1.empty:
						message = (
							f"Block '{block_name}' connected to library block '{library_type_name}', "
							f"version: '{library_type_version}' but not found in library content dataframe"
						)
						# warning column stored separately to enable/disable 
						df_warning_update = pd.DataFrame({
							'Name' : [block_name],
							'Warning': [message]
						})
						self.df_warning = pd.concat([self.df_warning, df_warning_update], ignore_index=True)
						logger.warning(message)
						continue
					
					if (library_search_type2.empty):
						object_name = block_name if block_type != 'InstanceDB' else block_instanceOfName
						var_string = f"'{object_name}' has outdated version '{library_type_version}', {block_modifiedDate}" if library_search_type2.empty else f"'{object_name}' outdated '{block_modifiedDate}'"
						message = (f"Block {var_string}: " 
									f"library block '{library_type_name}', "
									f"library version '{library_search_versions}', " 
									f"updated on '{library_search_type2['ModifiedDate'].values[0]}'"
						)
						row_block_data['ConnectedToLibrary'] = 'Outdated'
						row_block_data['ModifiedDateInLibrary'] = library_search_type1['ModifiedDate'].values[0]
						row_block_data['LibraryState'] = library_search_type1['LibraryState'].values[0]
						row_block_data['LibraryConformanceStatus'] = library_conformanceStatus

						# warning column stored separately to enable/disable 
						df_warning_update = pd.DataFrame({
							'Name' : [block_name],
							'Warning': [message]
						})
						self.df_warning = pd.concat([self.df_warning, df_warning_update], ignore_index=True)
						logger.warning(message)
					else:
						row_block_data['ModifiedDateInLibrary'] = library_search_type2['ModifiedDate'].values[0]
						row_block_data['LibraryState'] = library_search_type2['LibraryState'].values[0]
						row_block_data['LibraryConformanceStatus'] = library_conformanceStatus
				else:
					row_block_data['ConnectedToLibrary'] = connection
				data_collection.append(row_block_data)

			used_lib_blocks_df = pd.DataFrame(data_collection)
			logger.debug(f"Adding 'NaN' as empty value, removing ReferenceObject column because no later use in dataframe: {list(used_lib_blocks_df.columns)}")
			used_lib_blocks_df = used_lib_blocks_df.drop('ReferenceObject', axis=1)
			used_lib_blocks_df.fillna('NaN', inplace=True)

			columns = list(used_lib_blocks_df.columns)
			if 'Path' in columns:
				logger.debug(f"Reordering columns: '{columns}'")
				columns.append(columns.pop(columns.index('Path')))
				used_lib_blocks_df = used_lib_blocks_df[columns]
				logger.debug(f"Reordered columns: '{used_lib_blocks_df.columns}'")
		except Exception as e:
			raise Exception(f'Failed to validate used blocks: {str(e)}\n{traceback.format_exc()}')

		self.used_lib_blocks_df = used_lib_blocks_df
		logger.debug(
			f"Returning used library blocks dataframe {type(self.used_lib_blocks_df)}: "
			f"total entries: '{len(self.used_lib_blocks_df)}', "
			f"columns: {self.used_lib_blocks_df.columns}"
		)
		return self.used_lib_blocks_df


	def update_dataframe(self):
		"""
		Updates the library content.

		Returns:
			None
		"""
		def update_path_column(df, add=True):
			if df is not None:
				logger.debug(f"Updating path column in dataframe: {df.columns}")
				self.df_path.drop_duplicates(subset=['Name'], keep='first', inplace=True)
				if add:
					df['Path'] = df['Name'].map(self.df_path.set_index('Name')['Path'])
				else:
					if 'Path' in df.columns:
						df.drop('Path', axis=1, inplace=True)
		
		def update_warning_column(df, add=True):
			if df is not None:
				logger.debug(f"Updating warning column in dataframe: {df.columns}")
				self.df_warning.drop_duplicates(subset=['Name'], keep='first', inplace=True)
				if add:
					df['Warning'] = df['Name'].map(self.df_warning.set_index('Name')['Warning'])
				else:
					if 'Warning' in df.columns:
						df.drop('Warning', axis=1, inplace=True)
		
		dataframes = {
			'library': self.library_df,
			'used_lib_blocks': self.used_lib_blocks_df
		}
		
		for name, df in dataframes.items():
			update_path_column(df, add=self.folder_path)
			if name == 'used_lib_blocks':
				update_warning_column(df, add=self.include_warning_column)

	
	def set_settings(self, settings):
		"""
		Sets the settings.

		Args:
			settings (dict): Dictionary containing the settings.
		"""
		logger.debug(f"Changing settings {self.settings} to {settings}")
		self.folder_path = settings.get('folder_path', self.folder_path)
		self.include_warning_column = settings.get('warning_column', self.include_warning_column)
		self.include_safety_blocks = settings.get('safety_blocks', self.include_safety_blocks)
		self.include_system_types = settings.get('system_types', self.include_system_types)

		self.settings = {
			'folder_path': self.folder_path,
			'warning_column': self.include_warning_column,
			'safety_blocks': self.include_safety_blocks,
			'system_types': self.include_system_types
		}

		self.update_dataframe()

	
	def get_settings(self):		
		"""
		Returns a string representation of the settings.

		Returns:
			str: A string representation of the settings.
		"""
		return str(self.settings)


	def get_dateframe_info(self, df_name):
		"""
		Returns the library information.

		Returns:
			dict: Dictionary containing the library information.
		"""
		if df_name == 'library':
			return self.library_info
		return self.library_inf



	def export_data(self, filename, extension, tab, libraryUI):
		"""
		Exports certain data in retrieved in this module.

		Returns:
			None
		"""
		logger.debug(f"Exporting '{tab}' to '{extension}' format")
		extension = extension[1:]
		cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}\\{__name__.split(".")[-1]}'
		# make the whole path if it doesnt exist, or just continue if it does
		directory = os.makedirs(cwd + f"\\{tab}", exist_ok=True)
		timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")

		if not filename:
			logger.debug(f"Filename not provided, using timestamp as filename: '{timestamp}'")
			filename = timestamp

		export_path = os.path.join(cwd, tab, filename + extension)
		
		if tab == "content":
			df = self.get_library_content()
		elif tab == "validate project blocks":
			df, info = self.validate_used_blocks()

		if extension == ".csv":
			df.to_csv(export_path, index=False)
		elif extension == ".xlsx":
			df.to_excel(export_path, index=False)
		elif extension == ".json":
			df.to_json(export_path, orient='records')
		else:
			raise ValueError("Extension not supported. Please use .csv, .xlsx or .json")
		logger.debug(f"'{tab}' exported to '{export_path}'")
		return f"'{tab}' exported to '{export_path}'"

