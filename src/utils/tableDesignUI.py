import operator
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

comparison_operators = {
	'equal': operator.eq,
	'not_equal': operator.ne,
	'less': operator.lt,
	'greater': operator.gt,
	'less_equal': operator.le,
	'greater_equal': operator.ge,
	'version_higher': operator.gt,
	'version_lower': operator.lt,
	'version_equal': operator.eq,
	'version_not_equal': operator.ne
}

def compare_versions(version1: str, version2: str, operator: operator = operator.eq) -> bool:
	"""
	Function created to extract the version numbers from the version strings and compare them.
	The function splits the version strings by '.' and converts the resulting list of strings to a list of integers.
	Then, it compares the given version number in the condition of DesignTable with the selected operater against the version numbers in the table.
	Finally, it returns the result of the comparison, default return is 'True' if the condition is met.

	Parameters:
	version1 (str): The first version string stand for the version number in the table.
	version2 (str): The second version string stands for the static version number in the condition.
	operator (operator): The comparison operator to use. Default is 'eq' (equal).
	"""
	if version1 == 'NaN':
		return False
	v1 = (int, version1.replace('.', ''))
	v2 = (int, version2.replace('.', ''))  # Treat the given version as a single integer in a list

	# Compare element by element
	for a, b in zip(v1, v2):
		if a != b:
			return operator(a, b)
	return operator(len(v1), len(v2))


class DesignTable():
	"""
	Represents a table design with color conditions.

	Attributes:
		pt (object): The table object.
		df (object): The dataframe object.
		conditionSet (list): A list of color conditions.

	Methods:
		add_color_condition(condition: tuple, apply_on: str):
			Adds a color condition to the table.
		add_color_conditions(conditions: list, apply_on: str):
			Adds multiple color conditions to the table.
		apply_color_conditions():
			Applies color conditions to the table based on the given condition set.
		redesign_table(table):
			Redesigns the table with a new table object.
	"""

	def __init__(self, table, df):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance for table: {table} and dataframe: {len(df)}")
		self.pt = table
		self.df = df
		self.conditionSet = []
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")


	def add_color_condition(self, condition: tuple, apply_on: str):
		"""
		Add a color condition to the table.

		Parameters:
		condition (tuple): A tuple containing (column_name, comparison_operator, value, color)
							- column_name (str): The name of the column to check.
							- comparison_operator (str): The comparison operator to use.
							- value (str): The value to match in the column.
							- color (str): The color to apply to the row.

		Example:
		add_color_condition(('label', 'medium', 'lightgreen'), apply_on='row')
		"""
		logger.debug(f"Adding color condition: {condition} for table '{self.pt}'")

		if apply_on not in ['row', 'col']:
			raise ValueError("assign where to apply the color condition: row or col")
		elif len(condition) != 4:
			raise ValueError(f"Condition must be a tuple with three items: (column_name, compatison_operator, value, color) '{len(condition)}'")
		
		self.conditionSet.append((condition, apply_on))
		logger.debug(f"Added color condition: {condition} to the table '{self.pt}'")


	def add_color_conditions(self, conditions: list, apply_on: str):
		"""
		Add multiple color conditions to the table.

		Parameters:
		conditions (list): A list of tuples, each containing (column_name, comparison_operator, value, color)
							- column_name (str): The name of the column to check.
							- comparison_operator (str): The comparison operator to use.
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
		logger.debug(f"Applying color conditions {self.conditionSet} to the table '{self.pt}'")
		try:
			for (condition, apply_on) in self.conditionSet:
				column, comparison_operator, value, color = condition
				comp_func = comparison_operators.get(comparison_operator)
				if not comp_func:
					raise ValueError(f"Invalid comparison operator: {comparison_operator}")

				if apply_on == 'row':
					for row_idx in range(len(self.df)):
						if comparison_operator.startswith('version'): 
							condition_met = compare_versions(str(self.df.iloc[row_idx][column]), value, comp_func)
						else:
							condition_met = comp_func(self.df.iloc[row_idx][column], value)

						if condition_met:
							for col_idx in range(len(self.df.columns)):
								col_name = self.df.columns[col_idx]
								self.pt.setColorByMask(
									col_name, 
									self.pt.model.df.index == row_idx, 
									color
								)
				if apply_on == 'col':
					for col_idx in range(len(self.df.columns)):
						if comparison_operator.startswith('version'): 
							condition_met = compare_versions(self.df.iloc[row_idx][column], value)
						else:
							condition_met = comp_func(self.df.iloc[row_idx][column], value)

						if condition_met:
							col_name = self.df.columns[col_idx]
							if col_name == column:
								for row_idx in range(len(self.df)):
									if not comp_func(self.df.iloc[row_idx][column], value):
										self.pt.setColorByMask(
											col_name, 
											self.pt.model.df.index == row_idx, 
											color
										)
				logger.debug(f"Applied color condition: {condition} to the table '{self.pt}'")
		except Exception:
			logger.error(f"Error while applying color conditions to the table '{self.pt}'", exc_info=True)
		self.pt.show()
		self.pt.redraw()
		return self.pt


	def get_legenda(self):
		"""
		Returns the legend of the color conditions.
		The legend is a list of tuples, where each tuple contains the label of the condition and the color to apply.
		"""
		logger.debug(f"Getting legend of color conditions for table '{self.pt}'")
		legenda = []
		for (condition, apply_on) in self.conditionSet:
			column, comparison_operator, value, color = condition
			legenda.append((f"values in the column '{column}' that meet the condition '{comparison_operator} {value}'", color))
		logger.debug(f"Got legend of color conditions for table '{self.pt}'")
		return legenda


	def redesign_table(self, table, df):
		logger.info(f"Redesigning table '{self.pt}' with new table '{table}'")
		self.pt = table
		self.df = df
		self.apply_color_conditions()
		logger.info(f"Redesigned table '{self.pt}' successfully")
		return self.pt