import pathlib as path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import InitTiaProject as Init
import importlib
import DemoLogic as logic
importlib.reload(logic)
import json
import subprocess

from apps import nodes


nodes.nodeScreen
nodes.devices


class mainApp:
	def stop_siemens_processes(self):
			command = 'Get-Process | Where-Object {$_.ProcessName -like "Siemens*"} | Stop-Process -Force'
			try:
					subprocess.run(["powershell", "-Command", command], check=True)
					self.update_action_label("Siemens processes stopped successfully.")
			except subprocess.CalledProcessError as e:
					self.update_action_label(f"An error occurred while stopping Siemens processes: {e}")

	def update_action_label(self, text):
			self.action_label.config(text=text)
			self.master.update_idletasks()

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





if __name__ == "__main__":
		root = tk.Tk()
		gui = mainApp(root)
		root.mainloop()
		