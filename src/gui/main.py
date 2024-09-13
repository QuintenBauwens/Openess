"""
Description: 
This is the main fundamental file that runs the app.
It imports all modules dynamically as long as they are in the apps folder, and creates a menu for each module.
For each module, it creates a menu head-item with the name of the module, and for each function of a class in the module

conditions for dynamic import:
- the module should be in the apps folder
- the module should not be in the directory_exceptions list
- the module-name should end with *UI.py, if not it takes the whole name as a menu-item
- the module should have a subclass of TabUI.Tab to create a menu sub-item for each subclass of TabUI.Tab
- the module should have a class with the same name as the module to create an instance of the main class of the module

Author: Quinten Bauwens
Last updated: 09/07/2024
ToDo: FEATURE LOG LATER ON, SIEMENS FORCE STOP NEEDS TO BE REPLACED, COMPLETE THE DOCSTRINGS
"""

import importlib
import inspect
import threading
import tkinter as tk
import subprocess
import os
from tkinter import filedialog

from tkinter import BooleanVar, ttk, messagebox
from utils import InitTia as Init
from utils.tabUI import Tab
from utils.loggerConfig import get_logger
from utils.about import About
from core.project import Project
import config

logger = get_logger(__name__)

# TODO : Add logging to the app, docstrings
class mainApp:
	'''the main class object for visualizing the main window of the app'''

	@staticmethod
	def capitalize_first_letter(s):
		if not s:
			return s
		return s[0].upper() + s[1:]

	def __init__(self, master, settings=None):
		logger.info(f"Initializing '{__name__}' instance")
		self.myproject = None
		self.myinterface = None
		self.master = master
		self.app_settings = settings
		self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
		self.base_title = config.APP_NAME
		master.title(self.base_title)
		master.geometry("1000x500")

		# try:
		# 	master.iconbitmap(config.APP_ICON)
		# except tk.TclError:
		# 	logger.warning(f"Failed to set icon: {config.APP_ICON}")

		self.current_tab = None
		self.module_frames = {}
		self.modules = {}
		
		# permanent frame for the project section (header)
		self.header_frame = ttk.Frame(master)
		self.header_frame.pack(side="top", fill="x")

		# frame for the tab content
		self.tab_content_frame = ttk.Frame(master)
		self.tab_content_frame.pack(side="top", expand=True, fill="both")

		# frame for the about section
		self.about_frame = ttk.Frame(self.tab_content_frame)

		# permanent frame for the footer
		
		self.footer_frame = tk.Frame(master, height=1)
		self.footer_frame.pack(side='bottom', fill="x", anchor="s")

		logger.debug(f"Initializing 'Project' instance for shared module resources in later modules/classes")
		self.projectInstance = Project(self.master, self.tab_content_frame, self.myproject, self.myinterface)
		self.loading_screen = self.projectInstance.loading_screen
		self.loading_thread = None

		# insert the elements in the permanent frame
		self.create_project_section()

		self.menubar = tk.Menu(master)

		if settings is not None:
			self.module_exceptions = settings.get("modules", []).get("exclude_modules", [])
			self.module_exceptions.append("project")
		else:
			self.module_exceptions = ["libraryUI", "project"]
		self.import_UI_modules()

		master.config(menu=self.menubar)

		# self.style = self.setup_styles()
		self.home_screen()
		logger.debug(f"Initialized '{__name__}' instance successfully")

	def create_project_section(self):
		'''create the project section of the main window'''

		# sticky to allign the elements of the same column
		# for the labels you want to change the text later on, you need to store them in a variable, and use the grid method on the next line
		logger.debug("Creating master app frame and its UI...")
		self.status_icon = self.projectInstance.set_statusIcon(self.header_frame)
		self.status_icon.change_icon_status("#FFFF00", "no project opened, some features may not be available.")
		self.status_icon.canvas.grid(row=0, column=7, sticky="e", pady=10, padx=10)

		self.current_project_label = ttk.Label(self.header_frame, text="current project :")
		self.current_project_label.grid(row=0, column=0, sticky="w", padx=5)
		self.current_name_label = ttk.Label(self.header_frame, text="no project opened")
		self.current_name_label.grid(row=0, column=1, sticky="w" ,padx=5)
		self.action_label = ttk.Label(self.header_frame, text="", foreground="#FF0000")
		self.action_label.grid(row=0, column=5, sticky="ew", padx=5, pady=(5, 0))

		ttk.Button(self.header_frame, text="open project", command=self._start_thread).grid(row=0, column=2, sticky="w", padx=5, pady=(5, 0))
		ttk.Button(self.header_frame, text="close Project", command=self.close_project).grid(row=1, column=2, sticky="w", padx=5)
		ttk.Button(self.header_frame, text="about", command=self.home_screen).grid(row=1, column=1, sticky="e", padx=5)

		self.checkbox_interface = BooleanVar(value=False)
		ttk.Checkbutton(self.header_frame, text="open with interface", variable=self.checkbox_interface).grid(row=0, column=3, sticky="w", padx=5, pady=(5, 0))

		seperator = ttk.Separator(self.header_frame, orient="horizontal")
		seperator.grid(row=2, column=0, columnspan=11 ,sticky="ew", pady=(10))

		self.about = About(self.master, self.about_frame)
		self.module_frames["about"] = self.about_frame
		self.about.show_footer(self.footer_frame)

		self.header_frame.grid_columnconfigure(4, weight=1) # make the column of the status icon expandable
		self.header_frame.grid_columnconfigure(6, weight=1) # make the column of the action label expandable
		logger.debug("Created master app frame and its UI successfully")

	# TODO: popup if the user wants to run the app with all the features, or select the features he wants to use
	def import_UI_modules(self): 
		'''
		import all the apps within the apps folder
		each app is a module that could contain classes that are subclasses of base_tab.Tab,
		if this is the case, a menu head-item is created for the module, and for each subclass of base_tab.Tab,
		a menu sub-item is created that executes the execute method of the class when clicked.

		this is done dynamically, so that new tabs can be added by simply adding a new module in the apps folder.
		'''
		logger.info("Importing UI modules...")

		# dynamically import all modules in the apps folder
		apps = []
		current_dir = os.path.dirname(__file__)
		apps_dir = os.path.join(current_dir, 'apps')
		modules = [file for file in os.listdir(apps_dir) if file.endswith('.py') and not file.startswith('__')]
		modules = [file.split('.')[0] for file in modules]

		logger.info(f"Excluded modules: {self.module_exceptions}")
		logger.info(f"Contents of 'apps' directory: {modules}, excluded modules: {self.module_exceptions}")
	
		for file in modules:
			if file not in self.module_exceptions:
				logger.debug(f"Processing file: '{file}'")

				# handle UI modules
				module_name = file.split('.')[0] 
				try:
					# import the modules dynamically
					module = importlib.import_module(f"gui.apps.{module_name}")
					# get all classes that are subclasses of base_tab.Tab
					module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x) and issubclass(x, Tab) and x != Tab)
					
					if not module_classes:
						logger.critical(f"No tab classes found in '{module_name}'") 
						continue
					
					apps.append(module_name)

					# create a menu head-item for each module
					# adjust module_name index if the module names in apps folder dont end with UI
					module_menu = tk.Menu(self.menubar, tearoff=0)
					logger.debug(f"Creating menu head-item '{module_name}'")
					self.menubar.add_cascade(label=module_name[:-2], menu=module_menu)
					
					# initializing main class instance of module (class same name as module), storing it in the modules dictionary
					main_class_name = mainApp.capitalize_first_letter(module_name)
					main_class_instance = None

					if hasattr(module, main_class_name):
						main_class = getattr(module, main_class_name)
						logger.debug(f"Module '{module.__name__}' has mainclass '{main_class}'")
						main_class_instance = main_class(self.projectInstance)
						self.modules[module_name] = main_class_instance

					frame = ttk.Frame(self.tab_content_frame)
					self.module_frames[module_name] = frame
					main_class_instance.frame = frame  # assign the frame to the module instance for its content

					# creating a menu sub-item for each subclass of TabUI.Tab, and linking it to the execute method
					# create an instance of every subclass of TabUI.Tab in module_classes
					logger.debug(f"Creating menu sub-items for '{module_name}'")
					for class_name, class_obj in module_classes:
						tab_instance = class_obj(self.projectInstance, main_class_instance)

						module_menu.add_command(
							label=tab_instance.name, 
							command=lambda tab=tab_instance: self.switch_tab(tab)
						)
				except Exception as e:
					message = f"ERROR: Error processing '{module_name}' module."
					self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")
					logger.error(message, exc_info=True)
		if apps:
			message = f"Modules imported successfully: '{', '.join(apps)}'"
			self.status_icon.change_icon_status("#00FF00", message)
			logger.info(message)
		else:
			message = "No tabs were imported. Please make sure that the apps folder contains at least one module with a subclass of TabUI.Tab."
			messagebox.showwarning("WARNING", message)
			logger.warning(message)
			self.status_icon.change_icon_status("#FFFF00", message)

	
	def import_core_modules(self):
		logger.info("Importing core-modules...")
		current_dir = os.path.dirname(__file__)
		parent_dir = os.path.dirname(current_dir)
		core_dir = os.path.join(parent_dir, 'core')
		modules = os.listdir(core_dir)
		logger.debug(f"Contents of 'core' directory: {modules}")
		logger.warning(f"Excluded modules: {self.module_exceptions}")

		try:
			module_map = {
				file_name: importlib.import_module(f"core.{file_name.split('.')[0]}")
				for file_name in modules
				if file_name.endswith('.py') and file_name.split('.')[0] not in self.module_exceptions
			}
			self.projectInstance.set_module_map(module_map)
			logger.info(f"Core-modules imported successfully: {list(module_map.keys())}")
		except Exception as e:
			if isinstance(e, ImportError):
				message = f"ERROR: Failed to import the core-module, check the modules for syntax errors."
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')
			else:
				message = f"ERROR: Failed import/initialize the core-modules:"
				logger.error(message, exc_info=True)
				self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def switch_tab(self, tab):
		'''
		switch the tab content to the selected tab content frame by
		removing all widgets from the previous tab content frame and executing the new tab
		'''
		logger.debug("Switching from tab '%s' to tab '%s'", self.current_tab, tab.name)
		# hide the previous tab content
		for frame_name, frame in self.module_frames.items():
			try:
				if frame.winfo_exists():
					logger.debug(f"Hiding frame '{frame_name}' with children: {frame.winfo_children()}")
					for widget in frame.winfo_children():
						widget.destroy()
					frame.pack_forget()
				else:
					logger.warning(f"Frame '{frame_name}' does not exist.")
			except Exception as e:
				logger.error(f"Error while hiding frame '{frame_name}': {e}", exc_info=True)
		
		# Show the frame for the current module
		module_name = tab.__class__.__module__.split('.')[-1]
		self.current_tab = tab.name
		current_frame = self.module_frames[module_name]
		current_frame.pack(fill='both', expand=True)

		# Execute the new tab
		tab.execute(self.myproject, self.myinterface)
		self.update_frame_title(tab.name)


	def _start_thread(self):
		'''
		method to create a thread for the tab content
		'''
		logger.thread(f"Starting thread for project loading...")
		if self.loading_thread and self.loading_thread.is_alive():
			logger.thread(f"Thread for 'opening project' is already running", exc_info=True)
			return
		
		try:
			self.footer_frame.pack_forget() # hide the description frame
			
			self.loading_screen.show_loading(f"Opening project, please wait")
			self.status_icon.change_icon_status("#00FF00", "Opening project, please wait...")
			self.loading_thread = threading.Thread(target=self.open_project, daemon=True)
			self.loading_thread.start()

			logger.thread("Checking thread status...")
			self.master.after(250, self._check_thread)
		except Exception as e:
			message = f"Error with starting the thread for 'opening the project'"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def _check_thread(self):
		logger.thread("Thread of 'opening project' is alive, checking status...")
		if self.loading_thread and self.loading_thread.is_alive():
			self.master.after(250, self._check_thread)
		else:
			self.on_thread_finished()


	def on_thread_finished(self):
		message = "Thread of 'opening project' finished, returning to description..."
		logger.thread(message)

		self.loading_screen.hide_loading()
		self.footer_frame.pack(expand=True, fill="both") # show the description frame
		self.master.update_idletasks()


	def open_project(self):
		'''open the project and initialize the Hardware and Nodes classes'''

		try:
			logger.info("Opening project, please wait...")
			project_path = str(filedialog.askopenfilename())
			project_path = project_path.replace("/", "\\")

			self.myproject, self.myinterface = Init.open_project(self.checkbox_interface.get(), project_path)
			logger.info(f"Project opened succesfully: '{project_path}'")

			self.loading_screen.set_loading_text("Opened project successfully,\nimporting core modules and updating the UI-modules...")
			self.projectInstance.update_project(self.myproject, self.myinterface)
			self.import_core_modules()
			
			# update the project in all modules, try cath needed for the canvas
			logger.debug(f"Updating 'myproject' to '{self.myproject.Name}' in all modules: {self.modules.keys()}")
			for module_name, module_instance in self.modules.items():
				try:
					if hasattr(module_instance, 'update_project'):
						module_instance.update_project()
					else:
						raise AttributeError(f"Module '{module_name}' does not have an 'update_project' method. Please add the method to the module.")
				except tk.TclError as e:
						message = f"Warning: Updating canvas '{module_name}':"
						self.update_action_label(f"{message} {str(e)}")
						logger.warning(message, exc_info=True)
						self.status_icon.change_icon_status("#FFFF00", f"{message} {str(e)}")
						continue
				except Exception as e:
					message = f"Error: Error occurred while updating '{module_name}':"
					logger.error(message, exc_info=True)
					self.status_icon.change_icon_status("#FFFF00", f"{message} {str(e)}")

			logger.debug(f"All modules updated succesfully: {self.modules.keys()}")
			project_name = project_path.split("\\")[-1]
			self.status_icon.change_icon_status("#00FF00", f"Project '{project_name}' opened successfully")
			self.update_project_label(project_name)
		except Exception as e:
			message = f"ERROR: Project could not be opened."
			messagebox.showerror("ERROR", f"{message} {str(e)}")
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")
			


	def close_project(self):
		'''close the project and reset the Hardware and Nodes classes'''

		try:
			if self.myproject and self.myinterface:
				logger.info("Closing project...")
				Init.close_project(self.myproject, self.myinterface)
				self.myproject, self.myinterface = None, None
				logger.info("Project closed successfully")
				self.update_project_label("No project opened")

				# update the project in all modules, try cath needed for the canvas
				logger.debug(f"Updating parameters 'myproject, myinterface' to '{self.myproject, self.myinterface}' in all modules: {self.modules.keys()}")
				self.projectInstance.update_project(self.myproject, self.myinterface)

				for module_name, module_instance in self.modules.items():
					try:
						# if isinstance(module_instance, NodesUI):
						# 	module_instance.clear_widgets()
						if hasattr(module_instance, 'update_project'):
							module_instance.update_project()
						else:
							main_class = getattr(importlib.import_module(f"src.gui.apps.{module_name}"), module_name.capitalize())
							self.modules[module_name] = main_class(None, None)
					except tk.TclError as e:
						message = f"Warning: Updating canvas '{module_name}':"
						self.update_action_label(f"{message} {str(e)}")
						logger.warning(message, exc_info=True)
						self.status_icon.change_icon_status("#FFFF00", f"{message} {str(e)}")
						continue
					except Exception as e:
						message = f"Error: Error occurred while updating '{module_name}':"
						self.update_action_label(f"{message} {str(e)}")
						logger.error(message, exc_info=True)
						self.status_icon.change_icon_status("#FFFF00", f"{message} {str(e)}")
				logger.debug(f"All modules updated succesfully: {self.modules.keys()}")

				self.status_icon.change_icon_status("#00FF00")
			else:
				response = messagebox.askyesno("Force closing project", "Would you like to force close any project opened in a previous session?")
				if response:
					self.stop_siemens_processes()
				else:
					message = "Operation 'stopping Siemens processes' cancelled by user."
					logger.info(message)
					self.status_icon.change_icon_status("#FFFF00", message)
		except Exception as e:
			message = f"ERROR: Project could not be closed."
			self.update_action_label(f"{message} {str(e)}")
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")


	# TODO : This method needs to be updated 
	def stop_siemens_processes(self): 
		'''
		force stop all Siemens processes running on the machine
		NEEDS TO BE UPDATED! This is a temporary solution
		'''
		logger.info("Stopping Siemens processes")
		command = 'Get-Process | Where-Object {$_.ProcessName -like "Siemens*"} | Stop-Process -Force'
		try:
			subprocess.run(["powershell", "-Command", command], check=True)
			message = "Siemens processes stopped successfully."
			self.update_action_label(message)
			logger.info(message)
			self.status_icon.change_icon_status("#00FF00", message)
		except subprocess.CalledProcessError as e:
			message = f"ERROR: an error occurred while stopping Siemens processes:"
			self.update_action_label(f"{message} {str(e)}")
			logger.error(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f"{message} {str(e)}")


	# close instances that need to be closed before closing the main window, otherwise the program will hang
	def on_closing(self):
		if messagebox.askokcancel("Quit", "Do you want to quit?"):
			try:
				# close the Tkinter window
				self.master.destroy()

				# force exit the program
				logger.info("Application closed by user")
				os._exit(0)
			except Exception as e:
				logger.error("Error occurred while trying to close the application", exc_info=True)
				os._exit(1)


	def update_action_label(self, text):
		'''update the action label with the given text'''

		self.action_label.config(text=text)
		self.master.update_idletasks()


	def update_project_label(self, text):
		'''update the current project name label with the given text'''
		
		self.current_name_label.config(text=text)
		self.master.update_idletasks()


	def update_frame_title(self, screen_name):
		"""Update the frame title with the base title and current screen name."""
		
		self.master.title(f"{self.base_title} - {screen_name}")		


# Stratscreen for the app: 
	def home_screen(self):
		'''show the description of the app in the description frame'''
		if self.current_tab is not None:
			# hide the previous tab content
			for frame_name, frame in self.module_frames.items():
				if frame_name != "about":
					try:
						if frame.winfo_exists():
							logger.debug(f"Hiding frame '{frame_name}' with children: {frame.winfo_children()}")
							for widget in frame.winfo_children():
								widget.destroy()
							frame.pack_forget()
						else:
							logger.warning(f"Frame '{frame_name}' does not exist.")
					except Exception as e:
						logger.error(f"Error while hiding frame '{frame_name}': {e}", exc_info=True)
		logger.info("Showing home screen...")
		self.about.show_about()
		logger.debug(f"Packing about frame at top with children: {self.about.frame.winfo_children()}")
		self.about.frame.pack(side="top", fill="both", expand=True)
		self.update_frame_title("Home")



	# def show_more_info(self):
	# # Create a new window or dialog with additional information
	# 	info_window = tk.Toplevel(self.master)
	# 	info_window.title("Additional Information")
	# 	info_label = ttk.Label(info_window, text="This is additional information about the application.", 
	# 						wraplength=300, style="Custom.TLabel")
	# 	info_label.pack(padx=20, pady=20)

	
	# def link_config(self, text_widget, links_dict):
	# 	'''make the links in the links_text clickable'''

	# 	for link, url in links_dict.items():
	# 		text_widget.insert(tk.END, f'{link}\n')
	# 	text_widget.config(state="disabled")

	# 	for link, url in links_dict.items():
	# 		start = text_widget.search(link, "1.0", tk.END)
	# 		end = f"{start}+{len(link)}c"
	# 		text_widget.tag_add(link, start, end)
	# 		text_widget.tag_config(link, foreground="blue", underline=True)
	# 		text_widget.tag_bind(link, "<Button-1>", lambda e, url=url: self.open_link(url))

	# 		text_widget.tag_bind(link, "<Enter>", self.on_enter)
	# 		text_widget.tag_bind(link, "<Leave>", self.on_leave)

	# def open_link(self, url):
	# 	webbrowser.open_new(url)

	# def on_enter(self, event):
	# 	event.widget.config(cursor="hand2")

	# def on_leave(self, event):
	# 	event.widget.config(cursor="")