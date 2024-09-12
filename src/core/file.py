"""
Author: Quinten Bauwens
Last updated: 05/08/2024
"""

import os
import clr
clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
import pandas as pd
import datetime

from utils.loggerConfig import get_logger

logger = get_logger(__name__)

# TODO: DOCSTRINGS & documentation
class File():
	"""
	Represents the project file.

	Args:
		myproject (Project): The project object.
		myinterface (Interface): The interface object.

	Attributes:
		myproject (Project): The project object.
		myinterface (Interface): The interface object.
		software (Software): The software instance.
		software_container (SoftwareContainer): The software container.
	"""

	def __init__(self, project):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface

		self.search_results = {}
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")

	def get_core_classes(self):
		"""
		Returns the project classes.

		Returns:
			list: A list of the project classes.
		"""
		self.software = self.project.software
		self.hardware = self.project.hardware
		self.library = self.project.library
		self.blockdata = self.project.blockdata

	def get_core_functions(self):
		logger.debug(f"Accessing 'get_software_container' from the software object '{self.project.software}'...")
		self.software_container = self.software.get_software_container()


	def file_summary(self, reload=False):
		"""
		Generates a summary of the file.

		Returns:
			str: The file summary.
			list: Extraction of the project information and history entries for future use.
		"""
		if hasattr(self, 'summary_text') and not reload:
			logger.debug(f"Returning cached file summary...")
			return self.summary_text, self.summary_info

		logger.debug(
			f"Retrieving file specifications: "
			f"project: '{self.myproject.Name}', "
			f"reload: '{reload}'"
		)
		project_name = self.myproject.Name
		project_creationTime = self.myproject.CreationTime
		project_lastModifiedDate = self.myproject.LastModified
		project_author = self.myproject.Author
		project_lastModifiedBy = self.myproject.LastModifiedBy
		project_historyEntries = self.myproject.HistoryEntries
		header_dateTime = "DateTime"
		header_event = "Event"

		summary_text = f'Project Information\n' + \
				f'Name:                 {project_name}\n' + \
				f'Creation time:        {project_creationTime}\n' + \
				f'Last Change:          {project_lastModifiedDate}\n' + \
				f'Author:               {project_author}\n' + \
				f'Last modified by:     {project_lastModifiedBy}\n\n' + \
				f'Project history\n' + \
				f'{header_dateTime:<25}{header_event:<30}\n'
		
		for event in project_historyEntries:
			summary_text += f'{event.DateTime.ToString():<25}{event.Text:<30}\n'
		
		project_info = {
			'Name': self.myproject.Name,
			'CreationTime': self.myproject.CreationTime,
			'LastModified': self.myproject.LastModified,
			'Author': self.myproject.Author,
			'LastModifiedBy': self.myproject.LastModifiedBy
			}

		history_entries = [{
			'DateTime': event.DateTime.ToString(),
			'Event': event.Text
		} for event in self.myproject.HistoryEntries]

		summary_info = {'ProjectInfo': project_info, 'HistoryEntries': history_entries}
		self.summary_text, self.summary_info = summary_text, summary_info
		logger.debug(
			f"Returning project information as string {type(summary_text)} and list {type(summary_info)} :"
			f"amount of entries: '{len(history_entries)}'"
		)
		return summary_text, summary_info


	# TODO: add maybe regex condition for block_name input
	def find_block_location(self, block_name, reload=False):
		"""
		Finds the location of a block in the software.
		Args:
			block_name (str): The name of the block to find.
		Returns:
			tuple: A tuple containing a boolean value indicating whether the block was found or not, and a string with the block information if found.
		Raises:
			None
		Example:
			>>> find_block_location("my_block")
			(True, "The block 'my_block' has been found:\nPath: /path/to/block\nType: BlockType\nNumber: 123\nHeaderAuthor: Author\nModifiedDate: 2022-01-01\nProgramming Language: Python")
		"""
		if block_name in self.search_results and not reload:
			logger.debug(f"Returning cached block information of '{block_name}' in search results: '{self.search_results[block_name]}'...")
			return self.search_results[block_name]
		
		logger.debug(
			f"Searching for block '{block_name}' in the project: "
			f"reload: '{reload}'"
		)

		self.PLC_list = self.hardware.get_plc_devices(reload=reload)
		for plc in self.PLC_list:
			blocks_list = self.software.get_software_blocks(self.software_container[plc.Name].BlockGroup, include_group=False, include_safety_blocks=True, reload=reload)

			logger.debug(f"Filtering for block '{block_name}' out of all the blocks in the project: '{len(blocks_list)}' blocks")
			logger.debug(f"Returning block information of '{block_name}' if it has been found")
			for block in blocks_list:
				if str(block.Name.lower()) == block_name.lower():
					reversed_path = self.library.get_map_structure(block)
					path = reversed(reversed_path)
					path = '/'.join(folder for folder in path)
					logger.debug(f'reversed path: {reversed_path}, path: {path}')

					block_type = block.GetType().Name
					block_number = block.Number
					block_author = block.HeaderAuthor
					block_modified = block.ModifiedDate
					block_language = block.ProgrammingLanguage

					result = f'The block \'{block_name}\' has been found:\n' \
							f'Path: {path}\n' \
							f'Type: {block_type}\n' \
							f'Number: {block_number}\n' \
							f'HeaderAuthor: {block_author}\n' \
							f'ModdifiedDate: {block_modified}\n' \
							f'Programming Language: {block_language}\n'
					
					if block_type == 'InstanceDB':
						result += f'InstanceOfName: {block.InstanceOfName}\n' \
								f'InstanceOfNumber: {block.GetAttribute("InstanceOfNumber")}\n' \
								f'IsConsistent: {block.IsConsistent}\n'
					
					self.search_results[block_name] = result
					return result
		return None


	def projectTree(self, reload=False):
		"""
		Generates a project tree representation of the software blocks in the current project.
		Returns:
			text (str): The project tree representation as a string.
			df_data (list): A list of dictionaries containing the name and indentation level of each block.
		"""
		if hasattr(self, 'tree_text') and not reload:
			logger.debug(f"Returning cached project tree representation...")
			return self.tree_text, self.tree_df_data

		blocks = {}
		self.PLC_list = self.hardware.get_plc_devices(reload=reload)
		# returns dict with headgroups as key, and value as list of blocks or a dict with subgroups and blocks
		for plc in self.PLC_list:
			logger.debug(
				f"Extracting project structure of: "
				f"project: '{self.myproject.Name}', "
				f"PLC: '{plc.Name}', "
				f"reload: '{reload}'"
			)
			blocks.update(self.software.get_software_blocks(self.software_container[plc.Name].BlockGroup, include_safety_blocks=True, reload=reload)) 
		
		tree_text = ""
		space = "  " 
		tree_df_data = []

		def process_group(group_items, group_name, indent=1):
			nonlocal tree_text, space
			tree_text += f"{space * indent}{group_name}\n"
			tree_df_data.append({"GroupName": group_name, "GroupLevel": indent})
			for item in group_items:
				if isinstance(item, dict):
					# This is a subgroup
					for sub_group, sub_items in item.items():
						process_group(sub_items, sub_group.Name, indent + 1)
				else:
					# This is a block
					tree_text += f"{space * (indent + 1)}{item.Name}\n"
					tree_df_data.append({"Name": item.Name, "GroupLevel": indent,"Indent": indent + 1})

		for group, items in blocks.items():
			process_group(items, group.Name)

		self.tree_text, self.tree_df_data = tree_text, tree_df_data
		logger.debug(f"Returning project tree representation of the project as a string {type(tree_text)} and as a list {type(tree_df_data)} for export")
		return tree_text, tree_df_data

	
	def show_tagTables(self, reload=False):
		"""
		Retrieves the project tags and creates a DataFrame with the tag tables and tags.

		Returns:
			df (pandas.DataFrame): DataFrame containing the tag tables and tags.
		"""
		if hasattr(self, 'df_tags') and not reload:
			logger.debug(f"Returning cached DataFrame of all '{len(self.df_tags)}' tags in the project...")
			return self.df_tags

		logger.debug(
			f"Retrieving all the tags in the project: "
			f"reload: '{reload}'"			
		)
		
		IO_type_dict = {'I':'Input', 'Q': 'Output', 'M':'Other'}
		tags = self.software.get_project_tags(reload=reload)
		logger.debug(
			f"Inserting the retrieved tags into a dataframe: "
			f"amount of tags: '{len(tags)}'"
		)
		
		df_tags = pd.DataFrame()
		for table in tags.keys():
			logger.debug(f"'{table.Name}' has '{len(tags[table])}' tags")
			plc_name = table.Parent.Parent.GetAttribute("Name")
			for tag in tags[table]:
				comment = ''.join(s.Text for s in tag.Comment.Items)

				add_data_df = pd.DataFrame({
					'plc' : [plc_name],
					'Table': [table.Name],  
					'Tag': [tag.Name],
					'LogAddr': [tag.LogicalAddress],
					'Address': [float(''.join(s for s in tag.LogicalAddress if s.isdigit()))/10],
					'comment': [comment],
					'DataType': [tag.DataTypeName],
					'IO': [IO_type_dict[tag.LogicalAddress[1]]]
				})
				
				df_tags = pd.concat([df_tags, add_data_df], ignore_index=True)
		self.df_tags = df_tags
		logger.debug(
			f"Returning DataFrame {type(df_tags)} of all the tags in the project: "
			f"amount of data entries: '{len(df_tags)}'"
		)
		return df_tags


	def export_data(self, filename, extension, tab, fileUI):
		"""
		Exports certain data in retrieved in this module.

		Returns:
			None
		"""
		logger.debug(f"Exporting '{tab}' to '{extension}' format")
		extension = extension[1:]
		cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}\\{__name__.split(".")[-1]}'
		# make the whole path if it doesnt exist, or just continue if it does
		if tab != "find programblock":
			directory = os.makedirs(cwd + f"\\{tab}", exist_ok=True)
		timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")

		if not filename:
			logger.debug(f"Filename not provided, using timestamp as filename: '{timestamp}'")
			filename = timestamp

		export_path = os.path.join(cwd, tab, filename + extension)
		
		if tab == "summary":
			_, content = self.file_summary()
			df = pd.DataFrame(content['HistoryEntries'])
		elif tab == "project tree":
			_, df_data = self.projectTree()
			df = pd.DataFrame(df_data)
		elif tab == "project tags":
			df = self.show_tagTables()
		elif tab == "find programblock":
			block_name = fileUI.entry_block_name.get()
			try:
				content = self.blockdata.export_block(block_name)
				return content
			except Exception as e:
				raise ValueError(f"An error occurred exporting '{block_name}': {str(e)}")

		if not tab == "find programblock":
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