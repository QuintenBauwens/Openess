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

from ..core import DemoLogic as logic
from ..utils import InitTia as Init
from ..utils import base_tab


class mainApp:
	'''the main class object for visualizing the main window of the app'''

	def __init__(self, master):
		print("Initializing mainApp")  # type: debug

		self.master = master
		master.title("TIA openess demo")
		master.geometry("1000x500")
		master.iconbitmap("resources\\img\\tia.ico")

		# make a permanent frame for the project section (header)
		self.permanent_frame = ttk.Frame(master)
		self.permanent_frame.pack(side="top", fill="x")

		# insert the elements in the permanent frame
		self.create_project_section()

		# make frame for the tab content
		self.tab_content_frame = ttk.Frame(master)
		self.tab_content_frame.pack(side="bottom", expand=True, fill="both")
		self.menubar = tk.Menu(master)
		self.import_apps()
		master.config(menu=self.menubar)


	def create_project_section(self):
		'''create the project section of the main window'''

		ttk.Label(self.permanent_frame, text="Project Path:").grid(row=0, column=0, padx=5, pady=5)
		self.project_path_entry = ttk.Entry(self.permanent_frame, width=40)
		self.project_path_entry.grid(row=0, column=1, padx=5, pady=5)

		ttk.Button(self.permanent_frame, text="Open Project", command=self.open_project).grid(row=0, column=2, padx=5, pady=5)
		ttk.Button(self.permanent_frame, text="Close Project", command=self.close_project).grid(row=0, column=3, padx=5, pady=5)

		self.action_label = ttk.Label(self.permanent_frame, text="")
		self.action_label.grid(row=1, column=2, columnspan=4, padx=5, pady=5)


	def import_apps(self):
		'''
		import all the apps within the apps folder
		each app is a module that could contain classes that are subclasses of base_tab.Tab,
		if this is the case, a menu head-item is created for the module, and for each subclass of base_tab.Tab,
		a menu sub-item is created that executes the execute method of the class when clicked.

		this is done dynamically, so that new tabs can be added by simply adding a new module in the apps folder.
		'''

		print("Starting import_apps method") # type: debug

		apps = []
		directory = os.listdir('src\\gui\\apps')
		directory_exceptions = ['__pycache__', '__init__.py', 'main.py']

		print(f"Contents of 'apps' directory: {directory}") # type: debug

		for file in directory:
			if file.endswith('.py') and file not in directory_exceptions:
				module_name = file.split('.')[0]

				print(f"Processing file: {file}") # type: debug

				try:
					# import the modules dynamically
					module = importlib.import_module(f"src.gui.apps.{module_name}")

					# get all classes that are subclasses of base_tab.Tab
					module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x) and issubclass(x, base_tab.Tab) and x != base_tab.Tab)
					
					if not module_classes:
						print(f"No tab classes found in {module_name}") # type: debug
						continue
					
					apps.append(module_name)

					# create a menu head-item for each module
					file_menu = tk.Menu(self.menubar, tearoff=0)
					self.menubar.add_cascade(label=module_name, menu=file_menu)
					
					# creating a menu sub-item for each subclass of base_tab.Tab, and linking it to the execute method
					for class_name, class_obj in module_classes:
						print(f"Processing class: {class_name}") # type: debug

						# create an instance of the class Tab
						tab_instance = class_obj()
						file_menu.add_command(
							label=tab_instance.name, 
							command=lambda tab=tab_instance: self.switch_tab(tab)
						)
				
				except Exception as e:
					print(f"Warning: Error processing {module_name} module. {e}")
			
		if apps:
			messagebox.showinfo("Imported", f'Tabs imported successfully: {", ".join(apps)}') # type: debug
		else:
			messagebox.showwarning("Warning", "No tabs were imported.")


	def switch_tab(self, tab):
		'''
		switch the tab content to the selected tab content frame by
		removing all widgets from the previous tab content frame and executing the new tab
		'''
		# remove all widgets of the tab content frame from the previous tab
		for widget in self.tab_content_frame.winfo_children():
			widget.destroy()

		# execute the new tab
		tab.execute(self.tab_content_frame)


	def stop_siemens_processes(self):
		'''
		force stop all Siemens processes running on the machine
		NEEDS TO BE UPDATED! This is a temporary solution
		'''
		command = 'Get-Process | Where-Object {$_.ProcessName -like "Siemens*"} | Stop-Process -Force'
		try:
			subprocess.run(["powershell", "-Command", command], check=True)
			self.update_action_label("Siemens processes stopped successfully.")
		except subprocess.CalledProcessError as e:
			self.update_action_label(f"An error occurred while stopping Siemens processes: {e}")


	def open_project(self):
		'''open the project and initialize the Hardware and Nodes classes'''

		try:
			self.update_action_label("Project is opening, please wait...")
			project_path = self.project_path_entry.get()
			self.myproject, self.myinterface = Init.open_project(False, project_path)
			self.hardware = logic.Hardware(self.myproject, self.myinterface) # Initialize the Hardware class
			self.nodes = logic.Nodes(self.myproject, self.myinterface) # Initialize the Nodes class
			self.projectItems = self.hardware.GetAllItems(self.myproject) # Get all items in the project
			self.update_action_label("Project opened successfully!")
		except Exception as e:
			self.update_action_label(f"Error: project could not be opened. {e}")


	def close_project(self):
		'''close the project and reset the Hardware and Nodes classes'''

		try:
			if self.myproject and self.myinterface:
				Init.close_project(self.myproject, self.myinterface)
				self.myproject, self.myinterface = None, None
				self.update_action_label("Project closed successfully!")
			else:
				response = messagebox.askyesno("Force closing project", "Would you like to force close any project opened in a previous session?")
				if response:
					self.stop_siemens_processes()
				else:
					self.update_action_label("Operation cancelled by user.")
		except Exception as e:
				self.update_action_label("Error: project could not be closed. No project is opened.")


	def update_action_label(self, text):
		'''update the action label with the given text'''

		self.action_label.config(text=text)
		self.master.update_idletasks()


	