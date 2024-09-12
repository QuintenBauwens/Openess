"""
Description: 
base class for the tabs in the main.py file to dynamically import the tabs from the apps folder
the menu head-item is created by
it contains the execute method that is called when the tab is selected in the main menu

Author: Quinten Bauwens
Last updated: 08/07/2024
"""

import threading
from utils.loadingScreenUI import LoadScreen
from utils.loggerConfig import get_logger

logger = get_logger(__name__)

# TODO : DOCSTRING
class Tab:
	def __init__(self, name, project, main_class_instance):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance, name: '{name}'")
		self.name = name
		self.master = project.master
		self.content_frame = project.content_frame
		self.main_class_instance = main_class_instance
		self.project = project
		self.myproject = project.myproject
		self.myinterface = project.myinterface
		self.loading_screen = project.loading_screen
		self.status_icon = project.status_icon
		self.tab_content = None
		self.thread = None
		self.force_stop = False
		logger.debug(f"Initialized '{name}' successfully")


	def execute(self, myproject, myinterface):
		logger.debug(f"Executing Tab '{self.name}'")
		self.myproject = myproject
		self.myinterface = myinterface
		if self.name != "connections":
			self._start_thread()
		else:
			self.create_tab_content()
		logger.debug(f"Tab '{self.name}' executed")


	def _start_thread(self):
		'''
		method to create a thread for the tab content
		'''
		logger.thread(f"Starting thread for Tab '{self.name}'...")
		if self.thread and self.thread.is_alive():
			logger.thread(f"Thread for Tab '{self.name}' is already running", exc_info=True)
			return
		
		try:
			if self.myproject is not None:
				self.loading_screen.show_loading(f"Loading '{self.name}' tab, please wait")
			self.thread = threading.Thread(target=self.create_tab_content, daemon=True)
			self.thread.start()
			logger.thread("Checking thread status...")
			self.master.after(100, self._check_thread)
		except Exception as e:
			message = f"Error with starting the thread for Tab '{self.name}'"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def _check_thread(self):
		logger.thread(f"Thread of '{self.name}' is alive, checking status...")
		if self.thread and self.thread.is_alive():
			self.content_frame.after(100, self._check_thread)
		else:
			self.on_thread_finished()


	def on_thread_finished(self):
		message = f"Thread of '{self.name}' finished, displaying content..."
		logger.thread(message)
		try:
			if self.tab_content or self.force_stop:
				self.tab_content.pack(fill="both", expand=True)
				self.loading_screen.hide_loading()
		except Exception as e:
			message = f"Error with finishing the thread for Tab '{self.name}'"
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')


	def create_tab_content(self):
		try:
			self.tab_content = self.main_class_instance.create_tab(self)
		except Exception as e:
			message = f"Error with creating tab content for {self.name}"
			self.loading_screen.hide_loading()
			logger.critical(message, exc_info=True)
			self.status_icon.change_icon_status("#FF0000", f'{message} {str(e)}')