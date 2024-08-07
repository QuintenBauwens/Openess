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
from  tkinter import BooleanVar, ttk, messagebox, font as tkfont
import subprocess
import os
import webbrowser

from gui.apps.nodesUI import NodesUI
from utils import InitTia as Init
from utils.tabUI import Tab
from utils.tooltipUI import StatusCircle


# TODO : Add logging to the app, docstrings
class mainApp:
	'''the main class object for visualizing the main window of the app'''

	@staticmethod
	def capitalize_first_letter(s):
		if not s:
			return s
		return s[0].upper() + s[1:]

	def __init__(self, master):
		print("initializing mainApp")  # type: debug
		self.myproject = None
		self.myinterface = None
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
		self.base_title = "TIA openess demo"
		master.title(self.base_title)
		master.geometry("1000x500")
		master.iconbitmap("resources\\img\\tia.ico")
		
		# permanent frame for the project section (header)
		self.permanent_frame = ttk.Frame(master)
		self.permanent_frame.pack(side="top", fill="x")

		self.description_frame = ttk.Frame(master)
		self.description_frame.pack(expand=True, fill="both")

		# insert the elements in the permanent frame
		self.create_project_section()

		# frame for the tab content
		self.tab_content_frame = ttk.Frame(master)
		self.tab_content_frame.pack(side="bottom", expand=True, fill="both")

		self.menubar = tk.Menu(master)

		self.current_tab = None
		self.module_frames = {}
		self.modules = {}
		self.import_modules()

		master.config(menu=self.menubar)

		self.style = self.setup_styles()
		self.show_description()


	def create_project_section(self):
		'''create the project section of the main window'''

		# sticky to allign the elements of the same column
		# for the labels you want to change the text later on, you need to store them in a variable, and use the grid method on the next line
		self.status_icon = StatusCircle(self.permanent_frame, "#FFFF00", "no project opened, some features may not be available.")
		self.status_icon.canvas.grid(row=0, column=7, sticky="e", pady=10, padx=10)

		self.project_path_label = ttk.Label(self.permanent_frame, text="project path:").grid(row=0, column=0, sticky="w" ,padx=5, pady=(5, 0))
		self.project_path_entry = ttk.Entry(self.permanent_frame, width=40)
		self.project_path_entry.grid(row=0, column=1, sticky="w" ,padx=5, pady=(5, 0))

		self.action_label = ttk.Label(self.permanent_frame, text="", foreground="#FF0000")
		self.action_label.grid(row=0, column=5, sticky="ew", padx=5, pady=(5, 0))

		ttk.Button(self.permanent_frame, text="open project", command=self.open_project).grid(row=0, column=2, sticky="w", padx=5, pady=(5, 0))
		self.checkbox_interface = BooleanVar(value=False)
		ttk.Checkbutton(self.permanent_frame, text="open with interface", variable=self.checkbox_interface).grid(row=0, column=3, sticky="w", padx=5, pady=(5, 0))
		
		# row 1
		self.current_project_label = ttk.Label(self.permanent_frame, text="current project:").grid(row=1, column=0, sticky="w", padx=5)
		self.current_name_label = ttk.Label(self.permanent_frame, text="no project opened")
		self.current_name_label.grid(row=1, column=1, sticky="w" ,padx=5)
		ttk.Button(self.permanent_frame, text="close Project", command=self.close_project).grid(row=1, column=2, sticky="w", padx=5)

		seperator = ttk.Separator(self.permanent_frame, orient="horizontal")
		seperator.grid(row=2, column=0, columnspan=11 ,sticky="ew", pady=(10))

		self.permanent_frame.grid_columnconfigure(4, weight=1) # make the column of the status icon expandable
		self.permanent_frame.grid_columnconfigure(6, weight=1) # make the column of the action label expandable

	# TODO: popup if the user wants to run the app with all the features, or select the features he wants to use
	def import_modules(self): 
		'''
		import all the apps within the apps folder
		each app is a module that could contain classes that are subclasses of base_tab.Tab,
		if this is the case, a menu head-item is created for the module, and for each subclass of base_tab.Tab,
		a menu sub-item is created that executes the execute method of the class when clicked.

		this is done dynamically, so that new tabs can be added by simply adding a new module in the apps folder.
		'''
		print("starting import_apps method") # type: debug

		apps = [] # type: debug
		current_dir = os.path.dirname(__file__)
		apps_dir = os.path.join(current_dir, 'apps')
		directory = os.listdir(apps_dir)
		directory_exceptions = ['__pycache__', '__init__.py', 'main.py', 'fileUI.py', 'nodesUI.py']

		print(f"Contents of 'apps' directory: {directory}") # type: debug

		for file in directory:
			if file.endswith('.py') and file not in directory_exceptions:
				print(f"Processing file: {file}") # type: debug
				module_name = file[:-3]

				try:
					# import the modules dynamically
					module = importlib.import_module(f"gui.apps.{module_name}")

					# get all classes that are subclasses of base_tab.Tab
					module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x) and issubclass(x, Tab) and x != Tab)
					
					if not module_classes:
						print(f"No tab classes found in {module_name}") # type: debug
						continue
					
					apps.append(module_name) # type: debug

					# create a menu head-item for each module
					# adjust module_name index if the module names in apps folder dont end with UI
					module_menu = tk.Menu(self.menubar, tearoff=0)
					self.menubar.add_cascade(label=module_name[:-2], menu=module_menu)
					
					# initializing main class instance of module (class same name as module), storing it in the modules dictionary
					main_class_name = mainApp.capitalize_first_letter(module_name)
					print(f'Module {module_name} has {main_class_name}')
					main_class_instance = None
					if hasattr(module, main_class_name):
						main_class = getattr(module, main_class_name)
						print(f'Module {module} has {main_class}') # type: debug
						main_class_instance = main_class(self.master, self.myproject, self.myinterface, self.status_icon)
						print(f'Module {module} makes {main_class_instance}') # type: debug
						self.modules[module_name] = main_class_instance

					frame = ttk.Frame(self.tab_content_frame)
					self.module_frames[module_name] = frame
					main_class_instance.frame = frame  # Assign the frame to the module instance

					# creating a menu sub-item for each subclass of TabUI.Tab, and linking it to the execute method
					# create an instance of every subclass of TabUI.Tab in module_classes
					for class_name, class_obj in module_classes:
						print(f"Processing class: {class_name}") # type: debug
						tab_instance = class_obj(self.master, main_class_instance, self.menubar, self.myproject, self.myinterface)

						module_menu.add_command(
							label=tab_instance.name, 
							command=lambda tab=tab_instance: self.switch_tab(tab)
						)
				
				except Exception as e:
					message = f"ERROR: Error processing {module_name} module. {e}"
					self.status_icon.change_icon_status("#FF0000", message)
					print(message)
			
		if apps:
			self.status_icon.change_icon_status("#39FF14", f'Tabs imported successfully: {", ".join(apps)}')
		else:
			message = "No tabs were imported. Please make sure that the apps folder contains at least one module with a subclass of TabUI.Tab."
			self.status_icon.change_icon_status("#FFFF00", message)
			messagebox.showwarning("WARNING", message)


	def switch_tab(self, tab):
		'''
		switch the tab content to the selected tab content frame by
		removing all widgets from the previous tab content frame and executing the new tab
		'''
		# hide the previous tab content
		for frame in self.module_frames.values():
			for widget in frame.winfo_children():
				widget.destroy()
			frame.pack_forget()

		for frame in self.description_frame.winfo_children():
			frame.destroy()
		self.description_frame.pack_forget()
		
		# Show the frame for the current module
		module_name = tab.__class__.__module__.split('.')[-1]
		self.current_tab = module_name
		current_frame = self.module_frames[module_name]
		current_frame.pack(fill='both', expand=True)

		# Execute the new tab
		tab.execute(self.myproject, self.myinterface)
		self.update_frame_title(tab.name)

		# if isinstance(self.modules[module_name], NodesUI) and tab.name == "connections":
		# 	self.modules[module_name].create_display_connections_tab(tab)


	# TODO : This method needs to be updated 
	def stop_siemens_processes(self): 
		'''
		force stop all Siemens processes running on the machine
		NEEDS TO BE UPDATED! This is a temporary solution
		'''

		command = 'Get-Process | Where-Object {$_.ProcessName -like "Siemens*"} | Stop-Process -Force'
		try:
			subprocess.run(["powershell", "-Command", command], check=True)
			message = "siemens processes stopped successfully."
			self.update_action_label(message)
			self.status_icon.change_icon_status("#39FF14", message)
		except subprocess.CalledProcessError as e:
			message = f"ERROR: an error occurred while stopping Siemens processes: {e}"
			self.update_action_label(message)
			self.status_icon.change_icon_status("#FF0000", message)


	def open_project(self):
		'''open the project and initialize the Hardware and Nodes classes'''

		try:
			importlib.reload(Init)
			self.update_action_label("project is opening, please wait...")
			project_path = self.project_path_entry.get()
			self.myproject, self.myinterface = Init.open_project(self.checkbox_interface.get(), project_path)
			
			# update the project in all modules, try cath needed for the canvas
			for module_name, module_instance in self.modules.items():
				try:
					# if isinstance(module_instance, NodesUI):
					# 	module_instance.clear_widgets()
					if hasattr(module_instance, 'update_project'):
						module_instance.update_project(self.myproject, self.myinterface)
					else:
						# If update_project method doesn't exist, recreate the instance
						main_class = getattr(importlib.import_module(f"src.gui.apps.{module_name}"), module_name.capitalize())
						self.modules[module_name] = main_class(self.myproject, self.myinterface)
				except tk.TclError as e:
						message = f"Warning: Updating canvas {module_name}: {e}"
						self.update_action_label(message)
						self.status_icon.change_icon_status("#FFFF00", message)
						continue
				except Exception as e:
					message = f"Error: Error occurred while updating {module_name}: {e}"
					self.update_action_label(message)
					self.status_icon.change_icon_status("#FFFF00", message)

			self.update_action_label("project opened successfully!")
			self.project_path_entry.delete(0, tk.END)

			project_name = project_path.split("\\")[-1]

			self.status_icon.change_icon_status("#39FF14")
			self.update_name_label(project_name)

		except Exception as e:
			message = f"ERROR: Project could not be opened. {e}"
			self.update_action_label("")
			self.status_icon.change_icon_status("#FF0000", message)
			messagebox.showerror("ERROR", message)


	def close_project(self):
		'''close the project and reset the Hardware and Nodes classes'''

		try:
			if self.myproject and self.myinterface:
				Init.close_project(self.myproject, self.myinterface)
				self.myproject, self.myinterface = None, None
				self.update_name_label("no project opened")

				# update the project in all modules, try cath needed for the canvas
				for module_name, module_instance in self.modules.items():
					try:
						if isinstance(module_instance, NodesUI):
							module_instance.clear_widgets()
						if hasattr(module_instance, 'update_project'):
							module_instance.update_project(None, None)
						else:
							main_class = getattr(importlib.import_module(f"src.gui.apps.{module_name}"), module_name.capitalize())
							self.modules[module_name] = main_class(None, None)
					except tk.TclError as e:
						message = f"Warning: Updating canvas {module_name}: {e}"
						self.update_action_label(message)
						self.status_icon.change_icon_status("#FFFF00", message)
						continue
					except Exception as e:
						message = f"Error: Error occurred while updating {module_name}: {e}"
						self.update_action_label(message)
						self.status_icon.change_icon_status("#FFFF00", message)
				
				# if self.current_tab == 'nodesUI':
				# 	nodes_ui = self.modules['nodesUI']
				# 	if isinstance(nodes_ui, NodesUI):
				# 		nodes_ui.create_display_connections_tab(None)
				
				self.update_action_label("project closed successfully!")
				self.status_icon.change_icon_status("#39FF14")
			else:
				response = messagebox.askyesno("Force closing project", "Would you like to force close any project opened in a previous session?")
				if response:
					self.stop_siemens_processes()
				else:
					self.update_action_label("Operation cancelled by user.")
		except Exception as e:
			message = f"ERROR: Project could not be closed. {e}"
			self.update_action_label(message)
			self.status_icon.change_icon_status("#FF0000", message)


	# close instances that need to be closed before closing the main window, otherwise the program will hang
	def on_closing(self):
		if messagebox.askokcancel("Quit", "Do you want to quit?"):
			# close NodesUI instance
			for module_name, module_instance in self.modules.items():
				if isinstance(module_instance, NodesUI):
					module_instance.on_closing()
			
			# close the Tkinter window
			self.master.destroy()

			# force exit the program
			os._exit(0)


	def update_action_label(self, text):
		'''update the action label with the given text'''

		self.action_label.config(text=text)
		self.master.update_idletasks()


	def update_name_label(self, text):
		'''update the current project name label with the given text'''
		
		self.current_name_label.config(text=text)
		self.master.update_idletasks()


	def update_frame_title(self, screen_name):
		"""Update the frame title with the base title and current screen name."""
		
		self.master.title(f"{self.base_title} - {screen_name}")		

# TODO: seperate into own class + about button on gui
# Stratscreen for the app: 
	def show_description(self):
		'''show the description of the app in the description frame'''

		links = {
			"LinkedIn": "https://www.linkedin.com/in/quinten-bauwens-3766b0225/",
			"Company": "Volvo Cars Gent",
			"Email": ""
		}

		author_info = (
			"Author: Quinten Bauwens\n"
			"Email: quinten.bauwens@icloud.com\n"
			"Company: Volvo Cars Gent\n"
			"Last updated: 09/07/2024\n"
			)
		
		app_info = (
			"Welcome to the TIA openness demo app.\n"
			"This app is designed to demonstrate the use of the TIA openness API to interact with Siemens TIA Portal projects. " 
			"The app is divided into different sections, each section is a tab that provides different functionalities, "
			"thereby all the tabs are being dynamically imported as long as they are located in the apps folder. " 
			"To get started, open a TIA Portal project by clicking the 'open project' button and selecting the project file. " 
			"If you want to open the project with the TIA Portal interface, check the 'open with interface' checkbox before opening the project. " 
			"Once the project is opened, you can navigate between the tabs to explore the different functionalities. "
			"The app provides a variety of features such as viewing and exporting the project nodes, connections, " 
			"and the project tags, and more. Enjoy exploring the app!"
			)
		
		max_width = 275

		self.description_frame.grid_columnconfigure(0, weight=1, minsize=max_width)
		self.description_frame.grid_columnconfigure(1, weight=0)
		self.description_frame.grid_rowconfigure(0, weight=0)
		self.description_frame.grid_rowconfigure(1, weight=1)
		self.description_frame.grid_rowconfigure(2, weight=0)

		section_author = ttk.LabelFrame(self.description_frame, text="Author information", style="Custom.TLabelframe")
		section_author.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(5,2), pady=(5,2))
		author_info_label = ttk.Label(section_author, text=author_info, wraplength=250, justify="left", style="Custom.TLabel")
		author_info_label.pack(anchor="nw", padx=5, pady=2)

		section_links = ttk.LabelFrame(self.description_frame, text="Links", style="Custom.TLabelframe")
		section_links.grid(row=2, column=0, sticky="sew", padx=(5,2), pady=(5,2))
		links_text = tk.Text(section_links, wrap="word", height=4, width=50, bg="#f5f5f5", relief="sunken", font=("Helvetica", 10))
		links_text.pack(anchor="sw", padx=5, pady=2, expand=True, fill="both")
		self.link_config(links_text, links)
		
		section_app = ttk.LabelFrame(self.description_frame, text="App information", style="Custom.TLabelframe")
		section_app.grid(row=0, column=1, sticky="nsew", columnspan=2, padx=(5,2), pady=(5,2))
		app_info_label = ttk.Label(section_app, text=app_info, wraplength=700, justify="left", style="Custom.TLabel")
		app_info_label.pack(anchor="nw", padx=5, pady=2, fill="both", expand=True)

		# Add a custom separator
		separator = ttk.Separator(self.description_frame, orient="horizontal")
		separator.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(5,2), pady=(10,10))

		# Add a custom button
		custom_button = ttk.Button(self.description_frame, text="More Info", command=self.show_more_info)
		custom_button.grid(row=2, column=1, sticky="se", padx=(5,2), pady=(5,2))


	def show_more_info(self):
	# Create a new window or dialog with additional information
		info_window = tk.Toplevel(self.master)
		info_window.title("Additional Information")
		info_label = ttk.Label(info_window, text="This is additional information about the application.", 
							wraplength=300, style="Custom.TLabel")
		info_label.pack(padx=20, pady=20)

	
	def link_config(self, text_widget, links_dict):
		'''make the links in the links_text clickable'''

		for link, url in links_dict.items():
			text_widget.insert(tk.END, f'{link}\n')
		text_widget.config(state="disabled")

		for link, url in links_dict.items():
			start = text_widget.search(link, "1.0", tk.END)
			end = f"{start}+{len(link)}c"
			text_widget.tag_add(link, start, end)
			text_widget.tag_config(link, foreground="blue", underline=True)
			text_widget.tag_bind(link, "<Button-1>", lambda e, url=url: self.open_link(url))

			text_widget.tag_bind(link, "<Enter>", self.on_enter)
			text_widget.tag_bind(link, "<Leave>", self.on_leave)


	def setup_styles(self):
		style = ttk.Style()
    
		# Create a custom font
		custom_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
		
		# Configure styles
		style.configure("Custom.TLabelframe", font=custom_font)
		style.configure("Custom.TLabelframe.Label", font=custom_font)
		style.configure("Custom.TLabel", font=("Helvetica", 11), background="#f0f0f0", padding=(5, 5))

		return style

	def open_link(self, url):
		webbrowser.open_new(url)

	def on_enter(self, event):
		event.widget.config(cursor="hand2")

	def on_leave(self, event):
		event.widget.config(cursor="")