import ctypes
import os
import tkinter as tk

from utils.statusCircleUI import StatusCircle
from tkinter import ttk, scrolledtext
from gui.main import mainApp
from utils.dialogsUI import AppSettingsDialog
from utils.loggerConfig import FILE_NAME, LOG_LEVEL

main_settings = {}
STYLES = {
	"Light": {
		"TButton": {"background": "#f5f5f5", "foreground": "black"},
		"TFrame": {"background": "#f5f5f5"},
		"TLabel": {"background": "#f5f5f5", "foreground": "black"},
		"TLabelframe": {"background": "#f5f5f5"},
		"TLabelframe.Label": {"background": "#f5f5f5", "foreground": "black"},
		"ScrolledText": {"bg": "#f5f5f5", "fg": "black", "insertbackground": "black"},
		"Text": {"background": "#f5f5f5", "foreground": "black", "insertbackground": "black"},
		".": {"background": "#f5f5f5", "foreground": "black"}
	},
	"Dark": {
		"TButton": {"background": "black", "foreground": "black"},
		"TFrame": {"background": "black"},
		"TLabel": {"background": "black", "foreground": "white"},
		"TLabelframe": {"background": "black"},
		"TLabelframe.Label": {"background": "black", "foreground": "white"},
		"ScrolledText": {"bg": "black", "fg": "white", "insertbackground": "white"},
		"Text": {"background": "black", "foreground": "white", "insertbackground": "white"},
		".": {"background": "black", "foreground": "white"}
	}
}

def exlude_modules():
	current_dir = os.path.dirname(__file__)
	parent_dir = os.path.dirname(current_dir)
	apps_dir = os.path.join(parent_dir, 'gui', 'apps')
	files = [file for file in os.listdir(apps_dir) if file.endswith('.py') and not file.startswith('__')]

	modules = [(f"{file.split('.')[0]}", "Checkbox", False) for file in files]
	main_settings["modules"] = [("exclude_modules", "Select modules to be excluded from import", modules)]
	
def logger_settings():
	log_levels = ["(lowest) THREAD", "DEBUG", "INFO", "WARNING", "ERROR", "(highest) CRITICAL"]
	level_desc = "Set the log-level of the logger, when selected the levels above will be included."
	log_level_options = [(level, "Radiobutton", (True if level == LOG_LEVEL else False)) for level in log_levels]
	main_settings["logger"] = [
		("logger_level", level_desc, log_level_options),
		("logger_file", "Set the name of the log-file", [("log name", "Entry", FILE_NAME)])
	]
	
def style_settings():
	mode_desc = "Select the UI-presentation mode, lightmode is default."
	mode_options = [(mode, "Radiobutton", (True if mode == "Light" else False)) for mode in STYLES.keys()]
	main_settings["styles"] = [
		("adaption", mode_desc, mode_options)
	]

def apply_settings(root, settings):
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
			StatusCircle.BG_COLOR = "black" if style_name == "Dark" else "#f5f5f5"

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
				style.configure(f'{w.winfo_class()}.TWidget', **styles.get(".", {}))
			elif isinstance(w, tk.Widget):
				w.configure(**styles.get(".", {}))
		
		configure_widget(widget)
		for child in widget.winfo_children():
			configure_widget(child)
			apply_styles(child, style_name, False)

	apply_styles(root, mode)


def appSettings(root):
	exlude_modules()
	logger_settings()
	style_settings()
	
	dialog = AppSettingsDialog(root, "MainApp settings", main_settings)
	root.wait_window(dialog)

	settings = dialog.get_settings_values()
	apply_settings(root, settings)
	return settings