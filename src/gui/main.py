"""
Description: 
# This is the main fundamental file that runs the app.
# It imports all modules dynamically as long as they are in the apps folder, and creates a menu for each module.
# For each module, it creates a menu head-item with the name of the module, and for each function of a class in the module
# that starts with 'tab', it creates a menu sub-item under the module head-item.

Author: Quinten Bauwens
Last updated: 
"""

import sys
import importlib
import inspect
import tkinter as tk
from  tkinter import ttk, messagebox
import subprocess
import os

from ..core.hardware import Hardware
from ..core.nodes import Nodes
from ..utils import InitTia as Init
from ..utils import TabUI
from ..utils.TooltipUI import StatusCircle




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
		master.title("TIA openess demo")
		master.geometry("1000x500")
		master.iconbitmap("resources\\img\\tia.ico")

		# permanent frame for the project section (header)
		self.permanent_frame = ttk.Frame(master)
		self.permanent_frame.pack(side="top", fill="x")

		# insert the elements in the permanent frame
		self.create_project_section()

		# frame for the tab content
		self.tab_content_frame = ttk.Frame(master)
		self.tab_content_frame.pack(side="bottom", expand=True, fill="both")
		self.menubar = tk.Menu(master)

		self.modules = {}
		self.import_modules()

		master.config(menu=self.menubar)


	def create_project_section(self):
		'''create the project section of the main window'''

		# sticky to allign the elements of the same column
		# for the labels you want to change the text later on, you need to store them in a variable, and use the grid method on the next line
		self.status_icon = StatusCircle(self.permanent_frame, "#FFA500", "no project opened, some features may not be available.")
		self.status_icon.canvas.grid(row=0, column=10, pady=10, padx=10)

		self.project_path_label = ttk.Label(self.permanent_frame, text="project path:").grid(row=0, column=0, sticky="w" ,padx=5, pady=5)
		self.project_path_entry = ttk.Entry(self.permanent_frame, width=40)
		self.project_path_entry.grid(row=0, column=1, sticky="w" ,padx=5, pady=5)

		ttk.Button(self.permanent_frame, text="open project", command=self.open_project).grid(row=0, column=2, padx=5, pady=5)
		ttk.Button(self.permanent_frame, text="close Project", command=self.close_project).grid(row=0, column=3, padx=5, pady=5)

		self.action_label = ttk.Label(self.permanent_frame, text="")
		self.action_label.grid(row=0, column=4, columnspan=4, padx=5, pady=5)

		self.current_project_label = ttk.Label(self.permanent_frame, text="current project:").grid(row=1, column=0, sticky="w" ,padx=5, pady=5)
		self.current_name_label = ttk.Label(self.permanent_frame, text="no project opened")
		self.current_name_label.grid(row=1, column=1, sticky="w" ,padx=5, pady=5)


	def update_status_icon(self, status_color, tooltip_text):
		'''update the status icon with the given color and tooltip text'''

		if self.status_icon:
			self.status_icon.change_status_color(status_color)
		else:
			self.status_icon = StatusCircle(self.permanent_frame, status_color, tooltip_text)
		


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
		directory = os.listdir('src\\gui\\apps')
		directory_exceptions = ['__pycache__', '__init__.py', 'main.py']

		print(f"contents of 'apps' directory: {directory}") # type: debug

		for file in directory:
			if file.endswith('.py') and file not in directory_exceptions:
				print(f"processing file: {file}") # type: debug
				module_name = file[:-3]

				try:
					# import the modules dynamically
					module = importlib.import_module(f"src.gui.apps.{module_name}")

					# get all classes that are subclasses of base_tab.Tab
					module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x) and issubclass(x, TabUI.Tab) and x != TabUI.Tab)
					
					if not module_classes:
						print(f"no tab classes found in {module_name}") # type: debug
						continue
					
					apps.append(module_name) # type: debug

					# create a menu head-item for each module
					module_menu = tk.Menu(self.menubar, tearoff=0)
					self.menubar.add_cascade(label=module_name, menu=module_menu)
					
					# initializing main class instance of module (class same name as module), storing it in the modules dictionary
					main_class_name = mainApp.capitalize_first_letter(module_name)
					print(f'module {module_name} heeft {main_class_name}')
					main_class_instance = None
					if hasattr(module, main_class_name):
						main_class = getattr(module, main_class_name)
						print(f'module {module} heeft {main_class}') # type: debug
						main_class_instance = main_class(self.master, self.myproject, self.myinterface)
						print(f'module {module} maakt {main_class_instance}') # type: debug
						self.modules[module_name] = main_class_instance

					# creating a menu sub-item for each subclass of TabUI.Tab, and linking it to the execute method
					# create an instance of every subclass of TabUI.Tab in module_classes
					for class_name, class_obj in module_classes:
						print(f"processing class: {class_name}") # type: debug
						tab_instance = class_obj(self.master, main_class_instance, self.myproject, self.myinterface)

						module_menu.add_command(
							label=tab_instance.name, 
							command=lambda tab=tab_instance: self.switch_tab(tab)
						)
				
				except Exception as e:
					print(f"WARNING: error processing {module_name} module. {e}")
			
		if apps:
			messagebox.showinfo("imported", f'Tabs imported successfully: {", ".join(apps)}') # type: debug
		else:
			message = "no tabs were imported. Please make sure that the apps folder contains at least one module with a subclass of TabUI.Tab."
			self.status_icon.change_status_color("#FFFF00", message)
			messagebox.showwarning("WARNING", message)


	def switch_tab(self, tab):
		'''
		switch the tab content to the selected tab content frame by
		removing all widgets from the previous tab content frame and executing the new tab
		'''
		# hide the previous tab content, but dont destroy it
		for widget in self.tab_content_frame.winfo_children():
			widget.pack_forget()

		# execute the new tab
		tab.execute(self.tab_content_frame, self.myproject, self.myinterface)
		
			

	def stop_siemens_processes(self):
		'''
		force stop all Siemens processes running on the machine
		NEEDS TO BE UPDATED! This is a temporary solution
		'''
		command = 'Get-Process | Where-Object {$_.ProcessName -like "Siemens*"} | Stop-Process -Force'
		try:
			subprocess.run(["powershell", "-Command", command], check=True)
			self.update_action_label("siemens processes stopped successfully.")
		except subprocess.CalledProcessError as e:
			self.update_action_label(f"ERROR: An error occurred while stopping Siemens processes: {e}")


	def open_project(self):
		'''open the project and initialize the Hardware and Nodes classes'''

		try:
			self.update_action_label("project is opening, please wait...")
			project_path = self.project_path_entry.get()
			self.myproject, self.myinterface = Init.open_project(False, project_path)
			
			# update the project in all modules
			for module_name, module_instance in self.modules.items():
				if hasattr(module_instance, 'update_project'):
					module_instance.update_project(self.myproject, self.myinterface)
				else:
					# If update_project method doesn't exist, recreate the instance
					main_class = getattr(importlib.import_module(f"src.gui.apps.{module_name}"), module_name.capitalize())
					self.modules[module_name] = main_class(self.myproject, self.myinterface)

			self.update_action_label("project opened successfully!")
			self.project_path_entry.delete(0, tk.END)

			project_name = project_path.split("\\")[-1]

			self.status_icon.change_status_color("#39FF14")
			self.update_name_label(project_name)

		except Exception as e:
			message = f"ERROR: project could not be opened. {e}"

			self.update_action_label("")
			self.status_icon.change_status_color("#FF0000", message)
			messagebox.showerror("ERROR", message)


	def close_project(self):
		'''close the project and reset the Hardware and Nodes classes'''

		try:
			if self.myproject and self.myinterface:
				Init.close_project(self.myproject, self.myinterface)
				self.myproject, self.myinterface = None, None
				self.update_action_label("Project closed successfully!")
				self.update_name_label("no project opened")
			else:
				response = messagebox.askyesno("force closing project", "Would you like to force close any project opened in a previous session?")
				if response:
					self.stop_siemens_processes()
				else:
					self.update_action_label("operation cancelled by user.")
		except Exception as e:
				self.update_action_label("ERROR: project could not be closed. No project is opened.")


	def update_action_label(self, text):
		'''update the action label with the given text'''

		self.action_label.config(text=text)
		self.master.update_idletasks()
	
	def update_name_label(self, text):
		'''update the current project name label with the given text'''

		self.current_name_label.config(text=text)
		self.master.update_idletasks()








	



	