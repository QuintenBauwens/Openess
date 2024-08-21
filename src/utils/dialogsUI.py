import tkinter as tk
from tkinter import simpledialog

class RadioSelectDialog(simpledialog.Dialog):
	"""
	A dialog window that allows the user to select an option from a list of radio buttons.

	Args:
		parent (tkinter.Tk): The parent window of the dialog.
		title (str): The title of the dialog window.
		options (list): A list of options to be displayed as radio buttons.

	Attributes:
		options (list): A list of options to be displayed as radio buttons.
		selection (str): The selected option.
		filename (str): The filename entered by the user.
	"""


	def __init__(self, parent, title, options=None, label_name="", window_info=None):
		self.options = options
		self.selection = None
		self.label_name = label_name
		self.entryInput = None
		self.window_info = window_info
		parent.iconbitmap("resources\\img\\tia.ico")
		super().__init__(parent, title)


	def body(self, master):
		"""
		Create the body of the dialog window.

		Args:
			master (tkinter.Tk): The master widget.

		Returns:
			tkinter.Tk: The master widget.
		"""
		if self.window_info is not None:
			self.label_info = tk.Label(master, text=self.window_info).pack(anchor=tk.W)

		self.var = tk.StringVar(master)
		self.var.set(self.options[0])  # standard value
		self.label = tk.Label(master, text=self.label_name + ':').pack(anchor=tk.W)
		self.entry = tk.Entry(master, textvariable=self.label_name)
		self.entry.pack(anchor=tk.W)

		for option in self.options:
			tk.Radiobutton(master, text=option, variable=self.var, value=option).pack(anchor=tk.W)
		return master


	def apply(self):
		"""
		Apply the selected option and filename.

		This method is called when the user clicks the "OK" button.

		Returns:
			None
		"""

		self.selection = self.var.get()
		self.entryInput = self.entry.get()


class CheckboxDialog(simpledialog.Dialog):
	def __init__(self, master, title, options=None, default_values=None, label_name="", window_info=None):
		self.options = options
		self.default_values = default_values if default_values is not None else [False] * len(options)
		self.selection = {}
		self.label_name = label_name
		self.window_info = window_info
		master.iconbitmap("resources\\img\\tia.ico")
		super().__init__(master, title)

	def body(self, master):
		if self.window_info is not None:
			self.label_info = tk.Label(master, text=self.window_info).pack(anchor=tk.W)

		self.var = []
		for option, default in zip(self.options, self.default_values):
			var = tk.BooleanVar(value=default)
			self.var.append(var)
			tk.Checkbutton(master, text=option, variable=var).pack(anchor=tk.W)
		return master
	
	def	apply(self):
		self.selection = {option: var.get() for option, var in zip(self.options, self.var)}
	
	def get_selection(self):
		return self.selection


class UserInputDialog(simpledialog.Dialog):
	def __init__(self, master, title, window_info=None, components={'button': [], 'label': [], 'entry': [], 'checkbox': []}):
		self.window_info = window_info
		self.components = components

		self.info_frame = None
		self.components_frame = None

		# components in dict for config possibilities
		self.entries = {}
		self.buttons = {}
		self.labels = {}
		self.checkboxes = {}

		master.iconbitmap("resources\\img\\tia.ico")
		super().__init__(master, title)

	def body(self, master):
		if self.window_info is not None:
			self.info_frame = tk.Frame(master)
			self.info_frame.grid(row=0)
			self.label_info = tk.Label(self.info_frame, text=self.window_info, font=("Arial", 10, "italic")).grid(row=0, column=0)
			self.white_space = tk.Label(self.info_frame, text="").grid(row=1, column=0, columnspan=2, pady=10)
		
		self.components_frame = tk.Frame(master)
		self.components_frame.grid(row=2)

		if 'button' in self.components.keys():
			for button_name in self.components['button']:
				button = tk.Button(self.components_frame, text=button_name)
				self.buttons[button_name] = button

		if 'entry' in self.components.keys():
			for entry_name in self.components['entry']:
				entry = tk.Entry(self.components_frame, textvariable=entry_name)
				entry.grid(row=0, column=2)
				self.entries[entry_name] = entry

		if 'label' in self.components.keys():
			for label_name in self.components['label']:
				label = tk.Label(self.components_frame, text=label_name)
				self.labels[label_name] = label

		if 'checkbox' in self.components.keys():
			for checkbox_name in self.components['checkbox']:
				checkbox = tk.Checkbutton(self.components_frame, text=checkbox_name)
				self.checkboxes[checkbox_name] = checkbox
		return master

	def apply(self):
		pass