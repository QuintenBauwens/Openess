"""
Library module for the core package.
created by: Quinten Bauwens
created on: 01/08/2024
"""

import pandas as pd
import traceback
import datetime
import Siemens.Engineering as tia # Copy the Siemens.Engineering.dll to the folder of the script (current working dir.)!!

from core.software import Software 
from utils.logger_config import get_logger

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
		used_lib_blocks_info (dict): Dictionary containing used library blocks information.
		project_blocks_df (object): The project blocks dataframe.
	"""

	def __init__(self, project, plc_list=None):
		logger.debug(f"Initializing {__name__.split('.')[-1]} instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		self.plc_list = plc_list

		self.library_types = None
		self.library_content = None
		self.library_df = None
		self.library_info = None
		self.instance_count = {}

		self.used_lib_blocks_df = None
		self.used_lib_blocks_info = None

		self.project_blocks_df = None
		self.types_blocks_df = None
		self.project_types_df = None

		self.folder_path = False
		self.include_safety_blocks = True
		self.include_system_types = True

		self.settings = {
			'folder_path': False,
			'safety_blocks': True,
			'system_types': True
		}

		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully with settings: {self.settings}")
	

	def get_core_classes(self):
		self.software = self.project.software

	def get_core_functions(self):
		self.software_container = self.software.get_software_container()

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


	def get_library_types(self, group, types=None):
		if types is None:
			types = []
		
		types.extend([type for type in group.Types])

		for subfolder in group.Folders:
			self.get_library_types(subfolder, types)

		return types


	def get_library_content(self, reload: bool=False):
		logger.debug('Retrieving library data, reload: {reload}')

		if self.library_content is not None and not reload:
			logger.debug('Library dataframe retrieved earlier, returning cached content...')
			return self.library_content
		
		libraryType_folder = self.myproject.ProjectLibrary.TypeFolder
		project_name = self.myproject.Name
		library_content = pd.DataFrame()
		
		try:
			self.library_types = self.get_library_types(libraryType_folder)

			logger.debug(f'Found {len(self.library_types)} library types')

			if self.library_types is None:
				raise ValueError('No library types found')

			for type in self.library_types:
				folder = type.Parent.GetAttribute('Name')
				type_comment = ''.join(s.Text for s in type.Comment.Items)
				type_name = type.Name

				logger.debug(
							f"Found {len(type.Versions)} versions of type {type_name}\n"
							f'Making dataframe entry for each version with the following settings: {self.get_settings()}'
							)
				for version in type.Versions:
					instance_count = 0
					version_comment = ''.join(s.Text for s in version.Comment.Items)
					for plc in self.plc_list:
						instance_count += version.FindInstances(self.software_container[plc.Name]).Count
					# convert date in every df to datetime object for later comparison in validate_used_blocks
					date = version.ModifiedDate
					version_modifiedDate = datetime.datetime(date.Year, date.Month, date.Day, date.Hour, date.Minute, date.Second).strftime('%d-%m-%Y %H:%M:%S')
					version_author = version.Author
					version_xDependents = version.Dependents.Count
					library_state = version.State

					df_update = pd.DataFrame({
						'Project':[project_name],
						'Folder':[folder],
						'Name':[type_name],
						'Version':[version.VersionNumber],
						'ModifiedDate':[version_modifiedDate],
						'Author':[version_author],
						'LibraryState':[library_state],
						'Dependents':[version_xDependents],
						'instanceCount':[instance_count],
						'TypeComment':[type_comment],
						'VersionComment':[version_comment],
						'ReferenceObject':[version]
						})
					
					library_content = pd.concat([library_content, df_update], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to make library blocks dataframe: {str(e)}')
		
		self.library_content = library_content
		logger.debug(f'Returning library dataframe: {type(self.library_content)}, total entries: {len(self.library_content)} and columns: {self.library_content.columns}')
		return self.library_content


	def get_project_types_df(self, group, reload: bool=False):
		"""
		Retrieves the project types dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			object: The project types dataframe.
		"""
		logger.debug('Retrieving project blocks and types data, reload: {reload}')

		if self.project_types_df is not None and not reload:
			logger.debug('Project types and blocks dataframe retrieved earlier, returning cached content...')
			return self.project_types_df

		project_types_df = pd.DataFrame()

		try:
			project_types = self.software.get_software_types(group, include_system_types=self.include_system_types)
			logger.debug(
						f'Found a total of {len(project_types)} types in {group.Name} and its subgroups, system types included: {self.include_system_types}\n'
						f'Making dataframe entry for each type with the following settings: {self.get_settings()}'
						)
			project_name = self.myproject.Name

			for type in project_types:
				date = type.ModifiedDate
				type_modifiedDate = datetime.datetime(date.Year, date.Month, date.Day, date.Hour, date.Minute, date.Second).strftime('%d-%m-%Y %H:%M:%S')
				plc_name = self.plc_name
				folder = type.Parent.GetAttribute('Name')
				type_name = type.Name
				struc = struc = type.ToString().split('.')[-1]
				isConsistent = type.IsConsistent

				try:
					type_number = type.GetAttribute('Number')
				except:
					type_number = None
					logger.debug(f'No type_number found for type {type_name} under {folder}')
				
				df_update = pd.DataFrame({
						'Project':[project_name], 
						'PLC':[plc_name], 
						'Folder':[folder],
						'Name':[type_name], 
						'Type':[struc], 
						'Number':[type_number],
						'IsConsistent':[isConsistent],
						'ModifiedDate':[type_modifiedDate],
						'ReferenceObject':[type]
						})
				
				if self.folder_path:
					reversed_structure = self.get_map_structure(type)
					df_update['Path'] = '/'.join(reversed(reversed_structure))
				
				project_types_df = pd.concat([project_types_df, df_update], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to make project types dataframe: {str(e)}')
		
		self.project_types_df = project_types_df
		logger.debug(f'Returning project types dataframe: {type(self.project_types_df)}, total entries: {len(self.project_types_df)} and columns: {self.project_types_df.columns}')
		return self.project_types_df


	def get_project_blocks_df(self, group, reload=False):
		"""
		Retrieves the project blocks dataframe.

		Args:
			group (object): The group object.
			folder_path (bool, optional): Whether to include the folder path. Defaults to False.

		Returns:
			tuple: Tuple containing the project blocks dataframe and instance DB.
		"""

		logger.debug(f'Retrieving project blocks data, reload: {reload}')

		if self.project_blocks_df is not None and not reload:
			logger.debug('Project blocks dataframe retrieved earlier, returning cached content...')
			return self.project_blocks_df
		
		project_blocks_df = pd.DataFrame()

		try:
			project_blocks = self.software.get_software_blocks(group, include_group=False, include_safety_blocks=self.include_safety_blocks)
			logger.debug(
						f'Found a total of {len(project_blocks)} types in {group.Name} and its subgroups, safety blocks included: {self.include_system_types}\n'
						f'Making dataframe entry for each type with the following settings: {self.get_settings()}'
						)
			accepted_types = ['OB', 'FC', 'FB', 'GlobalDB', 'InstanceDB']
			project_name = self.myproject.Name
			
			for block in project_blocks:
				blockType = block.GetType().Name
				
				if blockType not in accepted_types:
					logger.debug(f'Blocktype {blockType} of block {block.Name} not recognised, continuing...')
					continue

				blockNumber = block.Number
				isConsistent = block.IsConsistent
				date = block.ModifiedDate
				block_modifiedDate = datetime.datetime(date.Year, date.Month, date.Day, date.Hour, date.Minute, date.Second).strftime('%d-%m-%Y %H:%M:%S')
				folder = block.Parent.GetAttribute('Name')
				plc_name = self.plc_name

				try:
					instanceOfNumber = block.GetAttribute('InstanceOfNumber')
				except:
					instanceOfNumber = 'NaN'
					logger.debug(f'No instanceOfNumber found for block {block.Name} under {folder}')
				
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
				
				if self.folder_path:
					reversed_structure = self.get_map_structure(block)
					df_update['Path'] = '/'.join(reversed(reversed_structure))
				
				project_blocks_df = pd.concat([project_blocks_df, df_update], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to retrieve project blocks dataframe: {str(e)}')
		
		self.project_blocks_df = project_blocks_df
		logger.debug(f'Returning project blocks dataframe: {type(self.project_blocks_df)}, total entries: {len(self.project_blocks_df)} and columns: {self.project_blocks_df.columns}')
		return self.project_blocks_df
	

	def get_types_blocks_df(self, reload=False):
		logger.debug(f'Retrieving project types and blocks data for each plc in {self.plc_list}, reload: {reload}')
		types_blocks_df = pd.DataFrame()

		try:
			for plc in self.plc_list:
				logger.debug(f"Handling plc: {plc.Name}")
				self.plc_name = plc.Name
				software_container = self.software_container[plc.Name]
				location_projectBlocks = software_container.BlockGroup
				location_datatypes = software_container.TypeGroup
				
				project_blocks_df = self.get_project_blocks_df(location_projectBlocks, reload)
				project_types_df = self.get_project_types_df(location_datatypes, reload)

				types_blocks_df = pd.concat([types_blocks_df, project_blocks_df, project_types_df], ignore_index=True)
		except Exception as e:
			raise Exception(f'Failed to retrieve types blocks dataframe: {str(e)}')
		
		self.types_blocks_df = types_blocks_df
		logger.debug(f'Returning types blocks dataframe: {type(self.types_blocks_df)}, total entries: {len(self.types_blocks_df)} and columns: {self.types_blocks_df.columns}')
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

		logger.debug('Checking used blocks data and validating against library blocks, reload: {reload}')

		if self.used_lib_blocks_df is not None and not reload:
			logger.debug('Blocks have been validated earlier, returning cached content...')
			return self.used_lib_blocks_df, self.used_lib_blocks_info
		
		data_collection = []
		used_lib_blocks_info = {}
		used_lib_blocks_df = None
			
		try:
			project_blocks_df = self.get_types_blocks_df(reload)
			library_content_df = self.get_library_content(reload)
			library_service = tia.Library.Types.LibraryTypeInstanceInfo

			logger.debug(f'Validating {len(project_blocks_df)} project blocks against {len(library_content_df)} library blocks, and making dataframe entry for each block')
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
						message = f'Corresponding programblock {block_instanceOfName} that {block_name} is instanceOf not found in project blocks'
						row_block_data['warning'] = message
						data_collection.append(row_block_data)
						logger.warning(message) 
						continue
					
					block_object = search_instance['ReferenceObject'].values[0]
					block_modifiedDate = search_instance['ModifiedDate'].values[0]
					logger.debug(f'Found instanceOf block {block_instanceOfName} for {block_name} in project blocks')
				else:
					block_object = row['ReferenceObject']
					block_modifiedDate = row['ModifiedDate']

				try:
					connect_to_library = block_object.GetService[library_service]()
					connection = True if isinstance(connect_to_library, library_service) else False
				except Exception as e:
					connection = False
					logger.debug(f'Cannot connect to library with block {block_name} - unofficial programblock')
				
				if connection:
					library_type_name = connect_to_library.LibraryTypeVersion.TypeObject.Name
					library_type_version = connect_to_library.LibraryTypeVersion.VersionNumber
					library_conformanceStatus = block_object.GetAttribute('LibraryConformanceStatus')

					row_block_data['ConnectedToLibrary'] = connection

					library_search_filter = (
						(library_content_df['Name'] == library_type_name) & 
						(library_content_df['Version'] == library_type_version)
					)

					library_search_type = library_content_df.loc[library_search_filter]
					library_modifiedDate = library_search_type['ModifiedDate'].values[0]

					if library_search_type.empty:
						row_block_data['warning'] = f'Library block {library_type_name} with version {library_type_version} not found in library content dataframe'
						data_collection.append(row_block_data)
						logger.debug(f'Block {block_name} is connected to library block {library_type_name} with version {library_type_version} but not found in library content dataframe')
						continue					

					row_block_data['NameInLibrary'] = library_type_name
					row_block_data['VersionInLibrary'] = library_type_version
					row_block_data['ModifiedDateInLibrary'] = library_search_type['ModifiedDate'].values[0]
					row_block_data['LibraryState'] = library_search_type['LibraryState'].values[0]
					row_block_data['LibraryConformanceStatus'] = library_conformanceStatus

					if block_modifiedDate != library_modifiedDate:
						message = f'Block outdated {block_modifiedDate}, library block {library_type_name} with version {library_type_version} has been updated on {library_search_type["ModifiedDate"].values[0]}'
						row_block_data['ConnectedToLibrary'] = 'Outdated'
						row_block_data['warning'] = message
						logger.warning(message)
				else:
					row_block_data['ConnectedToLibrary'] = connection
				data_collection.append(row_block_data)

			used_lib_blocks_df = pd.DataFrame(data_collection)
			used_lib_blocks_df = used_lib_blocks_df.drop('ReferenceObject', axis=1)
			used_lib_blocks_df.fillna('NaN', inplace=True)
			logger.debug(f'Adding NaN to empty values and removing ReferenceObject column because no later use in dataframe: {used_lib_blocks_df.columns}')

			columns = list(used_lib_blocks_df.columns)
			logger.debug(f'Reordering columns: {columns}')
			if 'Path' in columns:
				columns.append(columns.pop(columns.index('Path')))
			used_lib_blocks_df = used_lib_blocks_df[columns]
			logger.debug(f'Reordered columns: {used_lib_blocks_df.columns}')

			used_lib_blocks_info['total'] = len(used_lib_blocks_df)
			used_lib_blocks_info['connected'] = used_lib_blocks_df['ConnectedToLibrary'].astype(bool).sum()
			used_lib_blocks_info['disconnected'] = used_lib_blocks_info['total'] - used_lib_blocks_info['connected']
			used_lib_blocks_info['instanceDB'] = used_lib_blocks_df['Type'].value_counts().get('InstanceDB', 0)
		except Exception as e:
			raise Exception(f'Failed to validate used blocks: {str(e)}\n{traceback.format_exc()}')

		self.used_lib_blocks_df = used_lib_blocks_df
		self.used_lib_blocks_info = used_lib_blocks_info
		logger.debug(f'Returning used library blocks dataframe: {type(self.used_lib_blocks_df)}, total entries: {len(self.used_lib_blocks_df)} and columns: {self.used_lib_blocks_df.columns}')
		return self.used_lib_blocks_df, self.used_lib_blocks_info


	def set_libraryType_folder(self, libraryType_folder):
		"""
		Sets the software library groups.

		Args:
			software_library_groups (list): List of software library groups.
		"""
		self.libraryType_folder = libraryType_folder


	def get_libraryType_folder(self):
		"""
		Gets the software library groups.

		Returns:
			list: List of software library groups.
		"""
		return self.libraryType_folder
	

	def set_settings(self, settings):
		"""
		Sets the settings.

		Args:
			settings (dict): Dictionary containing the settings.
		"""
		logger.debug(f'Changing settings {self.settings} to {settings}')
		self.folder_path = settings.get('folder_path', self.folder_path)
		self.include_safety_blocks = settings.get('safety_blocks', self.include_safety_blocks)
		self.include_system_types = settings.get('system_types', self.include_system_types)

		self.settings = {
			'folder_path': self.folder_path,
			'safety_blocks': self.include_safety_blocks,
			'system_types': self.include_system_types
		}

	
	def get_settings(self):		
		"""
		Returns a string representation of the settings.

		Returns:
			str: A string representation of the settings.
		"""
		return str(self.settings)
