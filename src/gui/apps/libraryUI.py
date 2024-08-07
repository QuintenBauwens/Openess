import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pandastable import Table, TableModel
import pandas as pd

from utils.tabUI import Tab

from core.hardware import Hardware
from core.library import Library
from utils.tooltipUI import UserInputDialog

class TabConnection(Tab):
	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("status", master, main_class_instance, menubar, project, interface)
	
	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)

class TabValidate(Tab):
	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("validate project blocks", master, main_class_instance, menubar, project, interface)
	
	def create_tab_content(self):
		self.tab_content = self.main_class_instance.create_tab(self)


class LibraryUI:
	def __init__(self, master, myproject, myinterface, status_icon=None):
		self.master = master
		self.myproject = myproject
		self.myinterface = myinterface
		self.status_icon = status_icon

		self.frame = None
		self.table_frame = None
		self.tabs = {}
		self.output_tab = None

		self.initialize_library()


	def initialize_library(self):
		if self.myproject is None or self.myproject is None:
			self.library = None
			self.hardware = None
			self.plc_list = None
			return
		try:
			self.hardware = Hardware(self.myproject, self.myinterface)
			self.plc_list = self.hardware.get_plc_devices()
			self.library = Library(self.myproject, self.myinterface, self.plc_list)
		except Exception as e:
			self.library = None
			message = f'Failed to initialize library object: {str(e)}'
			messagebox.showerror("ERROR", message)
			self.status_icon.change_icon_status("#FF0000", message)


	def update_project(self, myproject, myinterface):
		if self.myproject != myproject or self.myinterface != myinterface:
			self.myproject = myproject
			self.myinterface = myinterface

			self.initialize_library()

			for tab_name, tab_instance in self.tabs.items():
				self.show_content(tab_instance)

			self.status_icon.change_icon_status("#39FF14", f'Updated project and interface to {myproject} and {myinterface}')


	def create_tab(self, tab):
		if self.frame is None:
			self.frame = ttk.Frame(self.master)
		
		for widget in self.frame.winfo_children():
			widget.destroy()
		
		self.frame.grid_columnconfigure(0, weight=1)
		self.frame.grid_rowconfigure(1, weight=1)

		# split the frame in sections, one for general items
		self.section1 = ttk.Frame(self.frame)
		self.section1.grid(row=1, column=5, padx=5, pady=5, sticky="nw")

		self.btn_export_output = ttk.Button(self.section1, text="Export", command=lambda: self.export_content(tab), state=tk.NORMAL)
		self.btn_export_output.grid(row=0, column=0, sticky="nw", padx=10, pady=5)
		
		self.section2 = ttk.Frame(self.frame)
		self.section2.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
		self.section2.columnconfigure(0, weight=1)
		self.section2.rowconfigure(0, weight=1)

		self.output_tab = scrolledtext.ScrolledText(self.section2, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)

		if tab.name == "status" and self.myproject is not None:
			self.create_status_tab(tab)
		elif tab.name == "validate project blocks" and self.myproject is not None:
			self.create_validate_tab(tab)
		
		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab
		self.show_content(tab)
		return self.frame


	def create_status_tab(self, tab):
		for widget in self.section2.winfo_children():
			widget.destroy()
		
		self.btn_change_lib_groups = ttk.Button(self.section1, text="Change Library Folder", command=lambda: self.change_library_groups(), state=tk.NORMAL)
		self.btn_change_lib_groups.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")

	
	def create_validate_tab(self, tab):
		for widget in self.section2.winfo_children():
			widget.destroy()

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")


	def show_content(self, tab):
		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)
			content = f'Please open a project to view the content in {tab.name}.'
			self.status_icon.change_icon_status("#FFFF00", content)
		else:
			try:
				if tab.name == "status":
					library_df, library_info = self.library.check_library_connection()

					if isinstance(library_df, pd.DataFrame):
						self.btn_export_output.config(state=tk.NORMAL)
						self.pt = Table(self.table_frame, dataframe=library_df, showtoolbar=True, showstatusbar=True)
						self.pt.grid(row=0, column=0, sticky="nsew")
						self.pt.show()

					info = f'Checked the connection between the library and a total of {library_info["total"]} library blocks.\n\n' \
							f'\tconnected blocks: {library_info["connected"]}\n' \
							f'\tdisconnected blocks: {library_info["disconnected"]}'
					
					messagebox.showinfo("Library Connection", info)
					return
				#TODO: PATH
				elif tab.name == "validate project blocks":
					used_lib_blocks_df, used_lib_blocks_info = self.library.validate_used_blocks()

					if isinstance(used_lib_blocks_df, pd.DataFrame):
						self.btn_export_output.config(state=tk.NORMAL)
						self.pt = Table(self.table_frame, dataframe=used_lib_blocks_df, showtoolbar=True, showstatusbar=True)
						self.pt.grid(row=0, column=0, sticky="nsew")
						self.pt.show()

					info = f'Found {used_lib_blocks_info["total"]} used project blocks of which are:\n\n' \
							f'\tofficial blocks: {used_lib_blocks_info["connected"]}\n' \
							f'\tnon-official blocks: {used_lib_blocks_info["disconnected"]}\n\n' \
							f'*official blocks are blocks that are connected to the library.'
					
					messagebox.showinfo("Library Connection", info)
					return
				self.status_icon.change_icon_status("#39FF14", f'{tab.name} tab retrieved successfully')
			except Exception as e:
				content = f'Failed to show content in {tab.name}: {str(e)}'
				self.status_icon.change_icon_status("#FF0000", content)
				
		self.output_tab.delete(1.0, tk.END)
		if not isinstance(content, pd.DataFrame):
			self.output_tab.insert(tk.END, content)
		else:
			self.output_tab.insert(tk.END, content.to_string())


	def change_library_groups(self):
		window_info = f'Enter the library group-names where the library blocks are located if they are different from the default groups: ["_GlobalLib", "_LocalLibGB", "_LocalLibVCG"].\n\n' \
						'Example: _GlobalLib - "add group", _LocalLibGB - "add group"'
		
		self.master.withdraw()
		try:
			popup = GroupInputDialog(self.master, "Change Library Groups", 
										components={
											'button': ['add group'],
											'label': ['enter group-name:', ''],
											'entry': ['input group']}, 
										popup_info=window_info
									)
			self.groups = popup.apply()
		except Exception as e:
			content = str(e)
			self.status_icon.change_icon_status("#FF0000", content)
		
		self.master.deiconify()
		if self.groups:
				self.update_library_df(self.groups)


	def update_library_df(self, groups):
		try:
			Library_df, library_info = self.library.check_library_connection(groups, reload=True)
			if isinstance(Library_df, pd.DataFrame):
				self.pt.clearTable()
				self.pt.updateModel(TableModel(Library_df))
				self.status_icon.change_icon_status("#39FF14", f'Library connection updated successfully')
				
				info = f'Checked the connection between the library and a total of {library_info["total"]} library blocks.\n\n' \
							f'Connected blocks: {library_info["connected"]}\n' \
							f'Disconnected blocks: {library_info["disconnected"]}'
					
				messagebox.showinfo("Library Connection", info)
		except Exception as e:
			content = f'Failed to update library connection: {str(e)}'
			self.status_icon.change_icon_status("#FF0000", content)


class GroupInputDialog(UserInputDialog):
	def __init__(self, master, title, components, popup_info=None):
		self.label_group_key = components.get('label', [None])[0]
		self.label_warning_key = components.get('label', [None])[1]
		self.entry_key = components.get('entry', [None])[0]
		self.button_key =components.get('button', [None])[0]
		self.groups = []
		super().__init__(master=master, title=title, popup_info=popup_info, components=components)

	def body(self, master):
		result = super().body(master)

		self.label_group = self.labels[self.label_group_key]
		self.label_warning = self.labels[self.label_warning_key]
		self.entry_group = self.entries[self.entry_key]
		self.button_add_group = self.buttons[self.button_key]
		
		if self.label_group_key is not None:
			self.label_group.grid(row=0, column=0, padx=5, pady=5)
		if self.label_warning_key is not None:
			self.label_warning.grid(row=1, column=1,padx=5, pady=5, sticky="w")
		if self.entry_key is not None:
			self.entry_group.grid(row=0, column=1, padx=5, pady=5)
		if self.button_key is not None:
			self.button_add_group.config(command=self.add_group)
			self.button_add_group.grid(row=0, column=2, padx=5, pady=5)
	
		self.initial_label_text = self.label_group.cget("text")
		return result

	def add_group(self):
		group = self.entry_group.get()
		
		if group not in self.groups:
			self.groups.append(group)
			self.label_group.config(text=f'{self.initial_label_text} {self.groups}')
			self.entry_group.delete(0, tk.END)
		else:
			self.label_warning.config(text="group already added", fg="red", font=("Arial", 8, "bold"))

	def apply(self): # called when the user clicks the "OK" button
		return self.groups
	

