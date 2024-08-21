import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pandastable import Table, TableModel
from utils.tableDesignUI import DesignTable
from utils.loadingScreenUI import LoadScreen
import pandas as pd

from utils.tabUI import Tab

from core.hardware import Hardware
from core.library import Library
from utils.dialogsUI import CheckboxDialog

class TabConnection(Tab):
	def __init__(self, master, main_class_instance, menubar, project=None, interface=None):
		super().__init__("content", master, main_class_instance, menubar, project, interface)
	
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
			self.loading_screen = LoadScreen(self.master)
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

			# for tab_name, tab_instance in self.tabs.items():
			# 	self.show_content(tab_instance)

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

		self.btn_table_settings = ttk.Button(self.section1, text="Settings", command=lambda: self.tab_settings_window(tab), state=tk.NORMAL)
		self.btn_table_settings.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.btn_table_settings2 = ttk.Button(self.section1, text="test", command=lambda: self.get_settings(), state=tk.NORMAL)
		self.btn_table_settings2.grid(row=2, column=0, sticky="nw", padx=10, pady=5)
		
		self.section2 = ttk.Frame(self.frame)
		self.section2.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
		self.section2.columnconfigure(0, weight=1)
		self.section2.rowconfigure(0, weight=1)

		self.output_tab = scrolledtext.ScrolledText(self.section2, wrap=tk.WORD)
		self.output_tab.grid(row=0, padx=5, pady=5, sticky="nsew")

		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)
			self.btn_table_settings.config(state=tk.DISABLED)

		if tab.name == "content" and self.myproject is not None:
			self.create_content_tab(tab)
		elif tab.name == "validate project blocks" and self.myproject is not None:
			self.create_validate_tab(tab)
		
		if tab.name not in self.tabs.keys():
			self.tabs[tab.name] = tab
		self.show_content(tab)
		return self.frame


	def create_content_tab(self, tab):
		for widget in self.section2.winfo_children():
			widget.destroy()
		
		self.btn_table_settings = ttk.Button(self.section1, text="Settings", command=lambda: self.tab_settings_window(tab), state=tk.NORMAL)
		self.btn_table_settings.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")

	
	def create_validate_tab(self, tab):
		for widget in self.section2.winfo_children():
			widget.destroy()

		self.table_frame = ttk.Frame(self.section2)
		self.table_frame.grid(row=0, column=0, sticky="nsew")


	def show_content(self, tab, reload=False):
		if self.myproject is None:
			self.btn_export_output.config(state=tk.DISABLED)
			content = f'Please open a project to view the content in {tab.name}.'
			self.status_icon.change_icon_status("#FFFF00", content)
		else:
			try:
				self.master.after(100, self.loading_screen.show_loading(f'Retrieving content for {tab.name} tab, please wait...'))
				self.master.update_idletasks()

				if tab.name == "content":
					library_df = self.library.get_library_content(reload=reload)

					if isinstance(library_df, pd.DataFrame):
						self.btn_export_output.config(state=tk.NORMAL)
						self.btn_table_settings.config(state=tk.NORMAL)
						self.set_table_content(tab, library_df)

				elif tab.name == "validate project blocks":
					used_lib_blocks_df, used_lib_blocks_info = self.library.validate_used_blocks(reload=reload)

					if isinstance(used_lib_blocks_df, pd.DataFrame):
						self.btn_export_output.config(state=tk.NORMAL)
						self.btn_table_settings.config(state=tk.NORMAL)
						self.set_table_content(tab, used_lib_blocks_df, used_lib_blocks_info)

				self.status_icon.change_icon_status("#39FF14", f'{tab.name} tab retrieved successfully')
				return
			except Exception as e:
				content = f'Failed to show content in {tab.name}: {str(e)}'
				self.status_icon.change_icon_status("#FF0000", content)
			finally:
				self.master.update_idletasks()
		self.output_tab.delete(1.0, tk.END)
		if not isinstance(content, pd.DataFrame):
			self.output_tab.insert(tk.END, content)
		else:
			self.output_tab.insert(tk.END, content.to_string())


	def set_table_content(self, tab, content, content_info=None):
		try:
			if tab.name == "content":
				self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)

				info = f'Library contains a total of {len(content)} blocks.'
			
			if tab.name == "validate project blocks":
				self.pt = Table(self.table_frame, dataframe=content, showtoolbar=True, showstatusbar=True)
				self.design_table = DesignTable(self.pt, content)
				self.design_table.add_color_conditions(
					[
						('ConnectedToLibrary', True, '#90ee90'),
						('ConnectedToLibrary', 'Outdated', '#FF474C')
					], apply_on='row'
					)
				self.design_table.add_color_condition(('Warning', 'NaN', 'lightred'), apply_on='col')
				self.pt = self.design_table.apply_color_conditions()

				info = f'Found a total of {content_info["total"]} used blocks in the project, of which {content_info["instanceDB"]} are instanceDB:\n\n' \
					f'\tofficial blocks: {content_info["connected"]}\n' \
					f'\tnon-official blocks: {content_info["disconnected"]}\n\n' \
					f'*official blocks are blocks that are connected to the library.'
		except Exception as e:
			content_msg = f'Failed to set table content: {str(e)}'
			self.status_icon.change_icon_status("#FF0000", content_msg)
		finally:
			self.loading_screen.hide_loading()
			self.master.update_idletasks()
		self.pt.grid(row=0, column=0, sticky="nsew")
		self.pt.show()

		self.pt.redraw() # renew the table

		messagebox.showinfo("Library Connection", info)
		return


	def tab_settings_window(self, tab):
		window_info = 'Settings for table view, be aware it can reduce the workload.'
		settings = [key for key in self.library.settings.keys()]
		default_values = [self.library.settings[key] for key in settings]

		try:
			popup = CheckboxDialog(self.master, "Changes table settings", options=settings, default_values=default_values, window_info=window_info)
			selected_settings = popup.get_selection()
			print('selected_settings', selected_settings)
		except Exception as e:
			content = f'Failed to open settings window: {str(e)}'
			self.status_icon.change_icon_status("#FF0000", content)

		if selected_settings:
			self.update_table(tab, selected_settings)


	def update_table(self, tab, settings):
		print('updating table...')
		# TODO: doesnt work yet loadscreen
		self.loading_screen.show_loading(f'Updating table, please wait...')
		self.master.update_idletasks()
		try:
			self.library.set_settings(settings)
			if tab.name == "content":
				content_df, content_info = self.library.get_library_content(reload=True)
				
			elif tab.name == "validate project blocks":
				content_df, content_info = self.library.validate_used_blocks(reload=True)
			
			if isinstance(content_df, pd.DataFrame):
					self.pt.clearTable()
					self.pt.updateModel(TableModel(content_df))
					if tab.name == "validate project blocks": 
						self.pt = self.design_table.redesign_table(self.pt)
					self.status_icon.change_icon_status("#39FF14", f'Content table updated successfully')
					
					info = f'Checked the connection between the library and a total of {content_info["total"]} library blocks.\n\n' \
								f'Connected blocks: {content_info["connected"]}\n' \
								f'Disconnected blocks: {content_info["disconnected"]}'
						
					messagebox.showinfo("Library Connection", info)
		except Exception as e:
			content = f'Failed to update library connection: {str(e)}'
			self.status_icon.change_icon_status("#FF0000", content)
		finally:
			self.loading_screen.hide_loading()
			self.master.update_idletasks()


	def get_settings(self):
		print('getting settings...')
		print(self.library.get_settings())