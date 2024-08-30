import tkinter as tk
from tkinter import simpledialog
from tkinter import ttk
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

class DialogTemplate(simpledialog.Dialog):
	def __init__(self, parent, dialogName, title, options=None, label_name="", window_info=None):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance, popup-name: '{dialogName}', title: '{title}' with options: {options}")
		self.dialogName = dialogName
		self.options = options
		self.label_name = label_name
		self.window_info = window_info
		self.selectionInput = None
		self.entryInput = None
		parent.iconbitmap("resources\\img\\tia.ico")
		super().__init__(parent, title)
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' succesfully")

	def body(self, master):
		pass

	def apply(self):
		if self.selectionInput and self.entryInput:
			logger.debug(f"Selected options after closing popup '{self.dialogName}': {self.selectionInput} and entry input: '{self.entryInput}'")
		elif self.selectionInput:
			logger.debug(f"Selected options after closing popup '{self.dialogName}': {self.selectionInput}")
		elif self.entryInput:
			logger.debug(f"Entry input after closing popup '{self.dialogName}': {self.entryInput}")

	def get_selectionInput(self):
		logger.debug(f"Returning selected options: {self.selectionInput}")
		return self.selectionInput

	def get_entryInput(self):
		logger.debug(f"Returning entry input: {self.entryInput}")
		return self.entryInput

# {setting-title :  [("setting-name", "setting-description", "default-value", [(optionName, ui-element1, value1), (labelname, ui-element2, value2)])]}
# "Select Mode": ("mode", "Mode 1", "Choose the mode of operation", [("Mode 1", "Radiobutton", "Mode 1"), ("Mode 2", "Radiobutton", "Mode 2")]),
class AppSettingsDialog(tk.Toplevel):
	def __init__(self, parent, title, options={}, window_info=None):
		super().__init__(parent)
		self.settings_config = options
		self.settings_values = {}
		self.window_info = window_info
		self.title(title)
		self.body(self)

	def body(self, master):
		if self.window_info is not None:
			self.label_info = tk.Label(master, text=self.window_info)
			self.label_info.pack(anchor=tk.W)
		
		sections = len(self.settings_config.keys())

		for row_section, (title, settings) in enumerate(self.settings_config.items()):
			section = ttk.LabelFrame(master, text=title)
			section.grid(row=row_section, column=0, padx=10, pady=5, sticky="w")
			section.columnconfigure(0, weight=1)
			for row, (setting, desc, options) in enumerate(settings):
				setting_description = tk.Label(section, text=desc)
				setting_description.grid(row=row*2, column=0, columnspan=len(options), padx=10, pady=5, sticky="w")

				if title not in self.settings_values.keys():
					self.settings_values[title] = {}
				if setting not in self.settings_values[title].keys():
					self.settings_values[title][setting] = []

				frame = tk.Frame(section)
				frame.grid(row=row*2+1, column=0, columnspan=len(options), padx=10, pady=5, sticky="w")

				# group the setting-options together, so only one can be selected, and set the default value
				if options and options[0][1].lower() == "radiobutton":
					var = tk.StringVar(value=next((opt for opt, _, default in options if default), None))
					
				for col, (option, element, default_value) in enumerate(options):
					if element.lower() == "checkbox":
						var = tk.BooleanVar(value=default_value)
						checkbox = tk.Checkbutton(frame, text=option, variable=var)
						checkbox.grid(row=row, column=col, padx=15, pady=5, sticky="w")
						self.settings_values[title][setting].append((option, default_value, var, "checkbox"))
					elif element.lower() == "radiobutton":
						radiobutton = tk.Radiobutton(frame, text=option, variable=var, value=option)
						radiobutton.grid(row=row, column=col, padx=15, pady=5, sticky="w")
						if col == 0:  # only append once for all radiobuttons
							self.settings_values[title][setting].append((option, default_value, var, "radiobutton"))
					elif element.lower() == "entry":
						var = tk.StringVar(value=default_value)
						entry_label = tk.Label(frame, text=option)
						entry_label.grid(row=row, column=col, padx=15, pady=5, sticky="w")
						entry = tk.Entry(frame, textvariable=var)
						entry.grid(row=row, column=col, padx=15, pady=5, sticky="w")
						self.settings_values[title][setting].append((option, default_value, var, "entry"))
			
		save_button = tk.Button(master, text="Apply", command=self.apply)
		save_button.grid(row=sections+1, column=0, padx=10, pady=5, sticky="e")
		master.columnconfigure(0, weight=1)
		return master

	def apply(self):
		settings_values = {}

		for titel, settings in self.settings_values.items():
			if titel not in settings_values:
				settings_values[titel] = {}

			for setting, var_list in settings.items():
				settings_values[titel][setting] = []
				for option, default_value, value, widget_type in var_list:
					if widget_type == "checkbox":
						if value.get() != default_value:
							settings_values[titel][setting].append(option)
					elif widget_type == "radiobutton":
						option = value.get()
						if option != default_value:
							settings_values[titel][setting].append(option)
						break
					elif widget_type == "entry":
						settings_values[titel][setting].append(value.get())
		self.settings_values = settings_values
		self.destroy()

	def get_settings_values(self):
		return self.settings_values


class ExportDataDialog(DialogTemplate):
	def __init__(self, parent, title, options=None, label_name="", window_info=None):
		super().__init__(parent, __name__, title, options, label_name, window_info)


	def body(self, master):
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
		self.selectionInput = self.var.get()
		self.entryInput = self.entry.get()
		super().apply()


class LibrarySettingsDialog(DialogTemplate):
	def __init__(self, master, title, options=None, default_values=None, label_name="", window_info=None):
		self.default_values = default_values if default_values is not None else [False] * len(options)
		super().__init__(master, __name__, title, options, label_name, window_info)

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
		self.selectionInput = {option: var.get() for option, var in zip(self.options, self.var)}
		super().apply()
