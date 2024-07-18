"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import os
import clr
import pandas as pd
import datetime
from System.IO import FileInfo

clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
import Siemens.Engineering as tia
from core.software import Software

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
		"""
		
		self.name = self.myproject.Name
		self.creation_time = self.myproject.CreationTime
		self.last_modified = self.myproject.LastModified
		self.author = self.myproject.Author
		self.last_modified_by = self.myproject.LastModifiedBy
		self.history_entries = self.myproject.HistoryEntries
		head_dateTime = "DateTime"
		head_event = "Event"
		text = f'Project Information\n' + \
				f'Name:                 {self.name}\n' + \
				f'Creation time:        {self.creation_time}\n' + \
				f'Last Change:          {self.last_modified}\n' + \
				f'Author:               {self.author}\n' + \
				f'Last modified by:     {self.last_modified_by}\n\n' + \
				f'Project history\n' + \
				f'{head_dateTime:<25}{head_event:<30}\n'
		
		for event in self.history_entries:
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

		return text, {'ProjectInfo': project_info, 'HistoryEntries': history_entries}


	def find_block_location(self, block_name):
		"""
		Finds the block group/location that contains the specified program block.

		Args:
			block_name (str): The name of the block to find.

		Returns:
			str: The location of the block in the TIA.
		"""

		blocks_dict = self.software_instance.get_software_blocks(self.software_container.BlockGroup)

		for group, block_list in blocks_dict.items():
			for block in block_list:
				if str(block.Name.lower()) == block_name.lower():
					return True, f'the location of {block_name} in tia-project "{self.myproject.Name}" : {group.Parent.Parent.GetAttribute("Name")}\\{group.Parent.GetAttribute("Name")}\\{group.Name}\\{block_name}'
		return False, f'{block_name} has not been found'


	def projectTree(self):
		"""
		Generates a tree-like representation of the project blocks.

		Returns:
			str: The project tree.
		"""

		blocks = self.software_instance.get_software_blocks(self.software_container.BlockGroup)
		blocks_list = []
		text = ""

		for group_name, block_name in blocks.items():
			text += f'\n{group_name.Name}\n'
			for block in block_name:
				text += f"\t{block.Name}\n"
				blocks_list.append({"Group Name": group_name.Name, "Block Name": block.Name})
		return text, blocks_list
	

	def get_project_tags(self):
		"""
		Generates a list of the project tags.

		Returns:
			dict: A dictionary containing all the project tags. The keys are the table names and the values are sets of tags.
		"""
		
		group = self.software_container.TagTableGroup
		Tags = {}  
		# all the tagtables directly in the folder
		for table in group.TagTables:  
			Tags[table] = set(table.Tags)
		# get all the tags of the subgroup
		for sub_group in group.Groups: 
			sub_group_tags = self.project_tags(sub_group)  
			
			for table, tags in sub_group_tags.items():
				if table in Tags:
					Tags[table].update(tags)  # Merge tags if table already exists
				else:
					Tags[table] = tags  # Add new table and its tags
		return Tags


	def show_tagTables(self):
		"""
		Retrieves the project tags and creates a DataFrame with the tag tables and tags.

		Returns:
			df (pandas.DataFrame): DataFrame containing the tag tables and tags.
		"""

		tags = self.get_project_tags()
		df = pd.DataFrame(columns=['tag-table', 'tag'])

		for table in tags.keys():
			for tag in tags[table]:
				dff = pd.DataFrame({
					'tag-table': [table.Name],  
					'tag': [tag.Name],
				}, index=[0])
				
				df = pd.concat([df, dff], ignore_index=True)
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