import tkinter as tk
from tkinter import simpledialog
from utils.logger_config import get_logger

logger = get_logger(__name__)

class DialogTemplate(simpledialog.Dialog):
	def __init__(self, parent, dialogName, title, options=None, label_name="", window_info=None):
		logger.debug(f"Initializing {__name__.split('.')[-1]} instance, popup-name: '{dialogName}', title: '{title}' with options: '{options}'")
		self.dialogName = dialogName
		self.options = options
		self.label_name = label_name
		self.window_info = window_info
		self.selectionInput = None
		self.entryInput = None
		parent.iconbitmap("resources\\img\\tia.ico")
		super().__init__(parent, title)
		logger.debug(f"Initialized {__name__.split('.')[-1]} succesfully")

	def body(self, master):
		pass

	def apply(self):
		if self.selectionInput and self.entryInput:
			logger.debug(f"Selected options after closing popup {self.dialogName}: {self.selectionInput} and entry input: {self.entryInput}")
		elif self.selectionInput:
			logger.debug(f"Selected options after closing popup {self.dialogName}: {self.selectionInput}")
		elif self.entryInput:
			logger.debug(f"Entry input after closing popup {self.dialogName}: {self.entryInput}")

	def get_selectionInput(self):
		logger.debug(f"Returning selected options: {self.selectionInput}")
		return self.selectionInput

	def get_entryInput(self):
		logger.debug(f"Returning entry input: {self.entryInput}")
		return self.entryInput


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
		super().__init__(master, __name__, title, options, label_name, window_info)
		self.default_values = default_values if default_values is not None else [False] * len(options)

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
