'''
# This is the main fundamental file that runs the app.
# It imports all modules dynamically as long as they are in the apps folder.
# For each module, it creates a menu head-item with the name of the module, and for each function of a class in the module
# that starts with 'tab', it creates a menu sub-item under the module head-item.
'''

import sys
import importlib
import inspect
import tkinter as tk
from  tkinter import ttk, scrolledtext, messagebox
import subprocess
import InitTiaProject as Init
import os
from apps import base_tab


class mainApp:
	'''the main class object of the app'''

	def __init__(self, master):
		print("Initializing mainApp")
		self.master = master
		master.title("TIA openess demo")
		master.geometry("1000x500")
		master.iconbitmap(".\img\\tia.ico")

		self.menubar = tk.Menu(master)

		self.create_project_section()
		self.import_apps()

		master.config(menu=self.menubar)



	def import_apps(self):
		'''import all the apps within the apps folder'''

		print("Starting import_apps method")

		apps = []
		directory = os.listdir('apps')
		directory_exceptions = ['__pycache__', '__init__.py', 'base_tab.py']

		print(f"Contents of 'apps' directory: {directory}")
	
		for file in directory:
			if file.endswith('.py') and file not in directory_exceptions:
				module_name = file.split('.')[0]

				print(f"Processing file: {file}")

				try:
					# import the modules dynamically
					module = importlib.import_module(f"apps.{module_name}")

					# get all classes that are subclasses of base_tab.Tab
					module_classes = inspect.getmembers(module, lambda x: inspect.isclass(x) and issubclass(x, base_tab.Tab) and x != base_tab.Tab)
					
					if not module_classes:
						print(f"No tab classes found in {module_name}")
						continue
					
					apps.append(module_name)

					# create a menu head-item for each module
					file_menu = tk.Menu(self.menubar, tearoff=0)
					self.menubar.add_cascade(label=module_name, menu=file_menu)
					
					# creating a menu sub-item for each subclass of base_tab.Tab, and linking it to the execute method
					for class_name, class_obj in module_classes:
						print(f"Processing class: {class_name}")

						tab_instance = class_obj()
						file_menu.add_command(label=tab_instance.name, command=tab_instance.execute)
				
				except Exception as e:
					print(f"Warning: Error processing {module_name} module. {e}")
	
		if apps:
			messagebox.showinfo("Imported", f'Tabs imported successfully: {", ".join(apps)}')
		else:
			messagebox.showwarning("Warning", "No tabs were imported.")



	def create_project_section(self):
		frame = ttk.Frame(self.master)
		frame.pack(fill="x", padx=10, pady=10)

		ttk.Label(frame, text="Project Path:").grid(row=0, column=0, padx=5, pady=5)
		self.project_path_entry = ttk.Entry(frame, width=40)
		self.project_path_entry.grid(row=0, column=1, padx=5, pady=5)

		ttk.Button(frame, text="Open Project", command=self.open_project).grid(row=0, column=2, padx=5, pady=5)
		ttk.Button(frame, text="Close Project", command=self.close_project).grid(row=0, column=3, padx=5, pady=5)

		self.action_label = ttk.Label(frame, text="")
		self.action_label.grid(row=1, column=2, columnspan=4, padx=5, pady=5)



	def stop_siemens_processes(self):
		command = 'Get-Process | Where-Object {$_.ProcessName -like "Siemens*"} | Stop-Process -Force'
		try:
			subprocess.run(["powershell", "-Command", command], check=True)
			self.update_action_label("Siemens processes stopped successfully.")
		except subprocess.CalledProcessError as e:
			self.update_action_label(f"An error occurred while stopping Siemens processes: {e}")



	def open_project(self):
		try:
			self.update_action_label("Project is opening, please wait...")
			project_path = self.project_path_entry.get()
			self.myproject, self.myinterface = Init.open_project(False, project_path)
			self.hardware = log.Hardware(self.myproject, self.myinterface) # Initialize the Hardware class
			self.nodes = log.Nodes(self.myproject, self.myinterface) # Initialize the Nodes class
			self.projectItems = self.hardware.GetAllItems(self.myproject) # Get all items in the project
			self.update_action_label("Project opened successfully!")
		except Exception as e:
			self.update_action_label(f"Error: project could not be opened. {e}")



	def close_project(self):
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
		self.action_label.config(text=text)
		self.master.update_idletasks()




if __name__ == "__main__":
	print("Starting main script")
	root = tk.Tk()
	gui = mainApp(root)
	root.mainloop()
	