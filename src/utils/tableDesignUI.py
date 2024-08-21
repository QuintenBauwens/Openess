import tkinter as tk
from pandastable import Table, TableModel

class DesignTable():
	def __init__(self, table, df):
		self.pt = table
		self.df = df
		self.conditionSet = []

	def add_color_condition(self, condition: tuple, apply_on: str):
		"""
		Add a color condition to the table.

		Parameters:
		condition (tuple): A tuple containing (column_name, value, color)
							- column_name (str): The name of the column to check.
							- value (str): The value to match in the column.
							- color (str): The color to apply to the row.

		Example:
		add_color_condition(('label', 'medium', 'lightgreen'), apply_on='row')
		"""
		if apply_on not in ['row', 'col']:
			raise ValueError("assign where to apply the color condition: row or col")
		elif len(condition) != 3:
			raise ValueError(f"Condition must be a tuple with three items: (column_name, value, color) {len(condition)}")
		self.conditionSet.append((condition, apply_on))

	def add_color_conditions(self, conditions: list, apply_on: str):
		"""
		Add multiple color conditions to the table.

		Parameters:
		conditions (list): A list of tuples, each containing (column_name, value, color)
							- column_name (str): The name of the column to check.
							- value (str): The value to match in the column.
							- color (str): The color to apply to the row.

		Example:
		add_color_conditions([('label', 'medium', 'lightgreen'), ('status', 'active', 'lightblue')], apply_on='row')
		"""
		for condition in conditions:
			self.add_color_condition(condition, apply_on)

	def apply_color_conditions(self):
		"""
		Apply color conditions to the table based on the given condition set.
		The condition set is a list of tuples, where each tuple contains a condition, the column to apply the condition on,
		the value to compare against, and the color to apply if the condition is met.
		The method iterates through the condition set and applies the color conditions to the table. If the condition is
		specified to be applied on a row, it checks each row in the table and applies the color to the corresponding cells
		that meet the condition. If the condition is specified to be applied on a column, it checks each cell in the
		specified column and applies the color to the corresponding cells that do not meet the condition.
		After applying the color conditions, the method redraws the table and returns the updated table.
		"""

		for (condition, apply_on) in self.conditionSet:
			column, value, color = condition
			if apply_on == 'row':
				for row_idx in range(len(self.df)):
					if self.df.iloc[row_idx][column] == value:
						for col_idx in range(len(self.df.columns)):
							col_name = self.df.columns[col_idx]
							self.pt.setColorByMask(
								col_name, 
								self.pt.model.df.index == row_idx, 
								color
							)
			if apply_on == 'col':
				for col_idx in range(len(self.df.columns)):
					col_name = self.df.columns[col_idx]
					if col_name == column:
						for row_idx in range(len(self.df)):
							if self.df.iloc[row_idx][column] != value:
								self.pt.setColorByMask(
									col_name, 
									self.pt.model.df.index == row_idx, 
									color
								)
		self.pt.redraw()
		return self.pt
	
	def redesign_table(self, table):
		self.pt = table
		self.apply_color_conditions()
		return self.pt