import ctypes
import os
import tkinter as tk

from utils.statusCircleUI import StatusCircle
from tkinter import ttk, scrolledtext
from utils.dialogsUI import AppSettingsDialog
from utils.loggerConfig import FILE_NAME, LOG_LEVEL

main_settings = {}
STYLES = {
	"Light": {
		"TButton": {"background": "#f0f0f0", "foreground": "black"},
		"TFrame": {"background": "#f0f0f0"},
		"TLabel": {"background": "#f0f0f0", "foreground": "black"},
		"TLabelframe": {"background": "#f0f0f0"},
		"TLabelframe.Label": {"background": "#f0f0f0", "foreground": "black"},
		"App.TLabelframe.Label": {"background": "#f0f0f0", "foreground": "black", "font": ("Helvetica", 10, "bold")},
		"ScrolledText": {"bg": "#f0f0f0", "fg": "black", "insertbackground": "black"},
		"Text": {"background": "#f0f0f0", "foreground": "black", "insertbackground": "black"},
		".": {"background": "#f0f0f0", "foreground": "black"}
	},
	"Dark": {
		"TButton": {"background": "black", "foreground": "black"},
		"TFrame": {"background": "black"},
		"TLabel": {"background": "black", "foreground": "white"},
		"TLabelframe": {"background": "black"},
		"TLabelframe.Label": {"background": "black", "foreground": "white"},
		"App.TLabelframe.Label": {"background": "black", "foreground": "white", "font": ("Helvetica", 10, "bold")},
		"ScrolledText": {"bg": "black", "fg": "white", "insertbackground": "white"},
		"Text": {"background": "black", "foreground": "white", "insertbackground": "white"},
		".": {"background": "black", "foreground": "white"}
	}
}

def exlude_modules():
	"""
	Generates a list of modules to be excluded from import.
	Returns:
		list: A list of tuples containing module names, checkbox labels, and a boolean value indicating if the module should be excluded.
	"""
	current_dir = os.path.dirname(__file__)
	parent_dir = os.path.dirname(current_dir)
	apps_dir = os.path.join(parent_dir, 'gui', 'apps')
	files = [file for file in os.listdir(apps_dir) if file.endswith('.py') and not file.startswith('__')]

	modules = [(f"{file.split('.')[0]}", "Checkbox", False) for file in files]
	main_settings["modules"] = [("exclude_modules", "Select modules to be excluded from import", modules)]
	
def logger_settings():
	"""
	Returns the logger settings for the application.

	Returns:
		dict: A dictionary containing the logger settings.
			The dictionary has the following structure:
			{
				"logger_level": (str, str, bool),
				"logger_file": (str, str, str)
			}
			- "logger_level": A tuple containing the log level options for the logger.
				The tuple has the following structure:
				(level, control_type, is_selected)
				- level (str): The log level option.
				- control_type (str): The type of control used to select the log level option.
				- is_selected (bool): Indicates whether the log level option is selected.
			- "logger_file": A tuple containing the log file settings.
				The tuple has the following structure:
				(label, control_type, default_value)
				- label (str): The label for the log file setting.
				- control_type (str): The type of control used to set the log file name.
				- default_value (str): The default value for the log file name.
	"""
	# code implementation here
	pass
	log_levels = ["(lowest) THREAD", "DEBUG", "INFO", "WARNING", "ERROR", "(highest) CRITICAL"]
	level_desc = "Set the log-level of the logger, when selected the levels above will be included."
	log_level_options = [(level, "Radiobutton", (True if level == LOG_LEVEL else False)) for level in log_levels]
	main_settings["logger"] = [
		("logger_level", level_desc, log_level_options),
		("logger_file", "Set the name of the log-file", [("log name", "Entry", FILE_NAME)])
	]
	
def style_settings():
	"""
	Returns the style settings for the UI-presentation mode.

	Returns:
		dict: A dictionary containing the style settings.
	"""
	mode_desc = "Select the UI-presentation mode, lightmode is default."
	mode_options = [(mode, "Radiobutton", (True if mode == "Light" else False)) for mode in STYLES.keys()]
	main_settings["styles"] = [
		("adaption", mode_desc, mode_options)
	]

def apply_settings(root, settings):
	"""
	Apply the specified settings to the GUI-root widget and its children.
	Args:
		root (tkinter.Tk): The root widget.
		settings (dict): The settings to apply.
	Returns:
		None
	"""
	mode = settings.get('styles', {}).get('adaption', 'Light')[0]
	
	def apply_styles(widget, style_name, initial=True):
		if initial:
			# Set the window bar color to dark mode on Windows
			if mode == "Dark" and os.name == 'nt':
				hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
				ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int(2)))
				ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int(1)))
			elif mode == "Light" and os.name == 'nt':
				hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
				ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int(1)))
				ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(ctypes.c_int(0)), ctypes.sizeof(ctypes.c_int(0)))
			StatusCircle.BG_COLOR = "black" if style_name == "Dark" else "#f0f0f0"

		style = ttk.Style()
		styles = STYLES.get(style_name, STYLES["Light"])
		for widget_type, options in styles.items():
			style.configure(widget_type, **options)
		
		def configure_widget(w):
			if isinstance(w, tk.Text):
				w.configure(**styles.get("Text", {}))
			elif isinstance(w, scrolledtext.ScrolledText):
				w.configure(**styles.get("ScrolledText", {}))
			elif isinstance(w, ttk.Widget):
				if w.winfo_name() == ["section_author", "section_links", "section_app"]:
					style.configure(f'{w.winfo_class()}.App.TLabelframe.Label', **styles.get("App.TLabelframe.Label", {}))
				else:
					style.configure(f'{w.winfo_class()}.TWidget', **styles.get(".", {}))
			elif isinstance(w, tk.Widget):
				w.configure(**styles.get(".", {}))
		
		configure_widget(widget)
		for child in widget.winfo_children():
			configure_widget(child)
			apply_styles(child, style_name, False)

	apply_styles(root, mode)


def appSettings(root):
	"""
	Opens the AppSettingsDialog to allow the user to modify the application settings.
	Parameters:
	- root: The root Tkinter window.
	Returns:
	- settings: A dictionary containing the modified settings values.
	"""
	exlude_modules()
	logger_settings()
	style_settings()
	
	dialog = AppSettingsDialog(root, "MainApp settings", main_settings)
	root.wait_window(dialog)

	settings = dialog.get_settings_values()
	apply_settings(root, settings)
	return settings