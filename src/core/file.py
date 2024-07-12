"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import os
import clr
import pandas as pd
import datetime

clr.AddReference("C:\\Program Files\\Siemens\\Automation\\Portal V15_1\\PublicAPI\\V15.1\\Siemens.Engineering.dll")
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


	def find_block_group(self, block_name):
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
					return f'the location of {block_name} in tia-project "{self.myproject.Name}" : {group.Parent.Parent.GetAttribute("Name")}\\{group.Parent.GetAttribute("Name")}\\{group.Name}\\{block_name}'
		
		return f'{block_name} has not been found'


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


	def export_data(self, filename, extension, tab):
		"""
		Exports certain data in retrieved in this module.

		Returns:
			None
		"""

		extension = extension[1:]
		cwd = os.getcwd() + f'\\docs\\TIA demo exports\\{self.myproject.Name}'
		directory = os.makedirs(cwd + f"\\{tab}", exist_ok=True)
		timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
		
		if not filename:
			filename = timestamp
		
		if tab == "summary":
			_, content = self.file_summary()
			df = pd.DataFrame(content['HistoryEntries'])
		elif tab == "project tree":
			_, content = self.projectTree()
			df = pd.DataFrame(content)

		export_path = os.path.join(cwd, tab, filename + extension)
		if extension == ".csv":
			df.to_csv(export_path, index=False)
		elif extension == ".xlsx":
			df.to_excel(export_path, index=False)
		elif extension == ".json":
			df.to_json(export_path, orient='records')
		else:
			raise ValueError("Extension not supported. Please use .csv, .xlsx or .json")
		
		return f"{tab} exported to {export_path}"
