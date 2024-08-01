"""
Library module for the core package.
created by: Quinten Bauwens
created on: 01/08/2024
"""

import pandas as pd

class Library:
	def __init__(self, myproject):
		self.myproject = myproject
		self.plc_list = None
	
	
	def map_structure(self, item, groups=None):
		if groups is None:
			groups = []

		try:
			# when the item has no more parent, error will be raised wich will be catched/passed and the function will return the groups
			folder = item.Parent.GetAttribute('Name')
			item = item.Parent
			if folder is not None and folder not in groups:
				groups.append(folder)
				self.map_structure(item, groups)
		except:
			pass
		
		return groups
	
	
	def get_project_blocks_df(self, plc_list, group, folder_path=False):
		blocks = self.get_blocks(group, group_included=False)
		exepted_types = ['OB', 'FC', 'FB', 'GlobalDB', 'InstanceDB']
		project_name = self.myproject.Name

		df = pd.DataFrame()
		instance_db = []
		
		for plc in plc_list:
			for block in blocks:
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
					structure = self.map_structure(block)
					reversed_structure = reversed(structure)
					path = '/'.join(folder for folder in reversed_structure)
					df_update['Path'] = path
				
				self.project_blocks_df = pd.concat([df, df_update], ignore_index=True)
				self.instance_db = instance_db
		return self.project_blocks_df, self.instance_db