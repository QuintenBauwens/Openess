"""
Author: Quinten Bauwens
Last updated: 05/08/2024
"""

import os
import clr
import pandas as pd
import datetime
from System.IO import FileInfo

clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
from core.software import Software
from core.library import Library

# TODO: DOCSTRINGS & documentation
class File:
	"""
	Represents the project file.

	Args:
		myproject (Project): The project object.
		myinterface (Interface): The interface object.

	Attributes:
		myproject (Project): The project object.
		myinterface (Interface): The interface object.
		software_instance (Software): The software instance.
		software_container (SoftwareContainer): The software container.
	"""

	def __init__(self, myproject, myinterface):
		self.myproject = myproject
		self.myinterface = myinterface
		self.software_instance = Software(self.myproject, self.myinterface)
		self.software_container = self.software_instance.get_software_container()


	def file_summary(self):
		"""
		Generates a summary of the file.

		Returns:
			str: The file summary.
			list: Extraction of the project information and history entries for future use.
		"""
		
		project_name = self.myproject.Name
		project_creationTime = self.myproject.CreationTime
		project_lastModifiedDate = self.myproject.LastModified
		project_author = self.myproject.Author
		project_lastModifiedBy = self.myproject.LastModifiedBy
		project_historyEntries = self.myproject.HistoryEntries
		header_dateTime = "DateTime"
		header_event = "Event"

		text = f'Project Information\n' + \
				f'Name:                 {project_name}\n' + \
				f'Creation time:        {project_creationTime}\n' + \
				f'Last Change:          {project_lastModifiedDate}\n' + \
				f'Author:               {project_author}\n' + \
				f'Last modified by:     {project_lastModifiedBy}\n\n' + \
				f'Project history\n' + \
				f'{header_dateTime:<25}{header_event:<30}\n'
		
		for event in project_historyEntries:
			text += f'{event.DateTime.ToString():<25}{event.Text:<30}\n'
		
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

		info = [project_info, history_entries]

		return text, info


	def find_block_location(self, block_name):
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
		
		library_instance = Library(self.myproject, self.myinterface)
		main_plc = self.software_instance.PLC_list[0]
		blocks_list = self.software_instance.get_software_blocks(self.software_container[main_plc.Name].BlockGroup, group_included=False)

		for block in blocks_list:
			if str(block.Name.lower()) == block_name.lower():
				reversed_path = library_instance.get_map_structure(block)
				path = reversed(reversed_path)
				path = '/'.join(folder for folder in path)

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
					
				return True, result
		return False, f'{block_name} has not been found'


	def projectTree(self):
		"""
		Generates a tree-like representation of the project blocks.

		Returns:
			str: The project tree.
		"""

		main_plc = self.software_instance.PLC_list[0]
		# returns dict with headgroups as key, and value as list of blocks or a dict with subgroups and blocks
		blocks = self.software_instance.get_software_blocks(self.software_container[main_plc.Name].BlockGroup) 
		text = ""

		def process_group(group_items, group_name, indent=""):
			nonlocal text
			text += f"{indent}{group_name}\n"
			for item in group_items:
				if isinstance(item, dict):
					# This is a subgroup
					for sub_group, sub_items in item.items():
						process_group(sub_items, sub_group.Name, indent + "    ")
				else:
					# This is a block
					text += f"{indent}    {item.Name}\n"

		for group, items in blocks.items():
			process_group(items, group.Name)
		return text

	
	def show_tagTables(self):
		"""
		Retrieves the project tags and creates a DataFrame with the tag tables and tags.

		Returns:
			df (pandas.DataFrame): DataFrame containing the tag tables and tags.
		"""

		IO_type_dict = {'I':'Input', 'Q': 'Output', 'M':'Other'}
		tags = self.software_instance.get_project_tags()
		df = pd.DataFrame()

		for table in tags.keys():
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
				
				df = pd.concat([df, add_data_df], ignore_index=True)

		return df


	def export_data(self, filename, extension, tab, fileUI):
		"""
		Exports certain data in retrieved in this module.

		Returns:
			None
		"""

		extension = extension[1:]
		cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}'
		# make directory if it does not exist
		directory = os.makedirs(cwd + f"\\{tab}", exist_ok=True)
		timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
				
		if not filename:
			filename = timestamp

		export_path = os.path.join(cwd, tab, filename + extension)
		
		if tab == "summary":
			_, content = self.file_summary()
			df = pd.DataFrame(content['HistoryEntries'])
		elif tab == "project tree":
			_, content = self.projectTree()
			df = pd.DataFrame(content)
		elif tab == "project tags":
			df = self.show_tagTables()
		elif tab == "find programblock":
			block_name = fileUI.entry_block_name.get()
			try:
				content = self.export_block_data(block_name, tab)
				return content
			except Exception as e:
				raise ValueError(f"An error occurred exporting {block_name}: {str(e)}")

		if not tab == "find programblock":
			if extension == ".csv":
				df.to_csv(export_path, index=False)
			elif extension == ".xlsx":
				df.to_excel(export_path, index=False)
			elif extension == ".json":
				df.to_json(export_path, orient='records')
			else:
				raise ValueError("Extension not supported. Please use .csv, .xlsx or .json")
		
		return f"{tab} exported to {export_path}"


	def export_block_data(self, block_name, tab):
		block = self.software_instance.get_block(self.software_container.BlockGroup, block_name)
		block_instance = str(block).split('.')[-1]
		block_number = str(block.Number)

		cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}\\{tab}'
		export_path = os.path.join(cwd, f"{block_instance}{block_number}.xlm")
		

		if block is None:
			raise ValueError(f"{block_name} is not a valid instance of a block")
		try:
			block.Export(FileInfo(export_path), tia.ExportOptions.WithDefaults)
			message = f"{block_name} exported successfully to {export_path}"
		except:
			# trt fixing error by compiling block
			result = block.GetService[tia.Compiler.ICompilable]().Compile()
			message = ""
			for message in (result.Messages):
				message += message.Description

			try:
				block.Export(FileInfo(export_path), tia.ExportOptions.WithDefaults)
			except:
				raise ValueError(f"Error exporting block: {message}")
		return message