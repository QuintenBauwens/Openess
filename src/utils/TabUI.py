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
from utils.logger_config import get_logger

logger = get_logger(__name__)

# TODO : DOCSTRING
class Tab:
	def __init__(self, name, master, content_frame, main_class_instance, menubar, project=None, interface=None):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance, name: '{name}'")
		self.name = name
		self.master = master
		self.content_frame = content_frame
		self.main_class_instance = main_class_instance
		self.myproject = project
		self.myinterface = interface
		self.tab_content = None
		self.menubar = menubar
		self.thread = None
		self.loading_screen = LoadScreen(self.master, self.content_frame)
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance {name} successfully")

	def execute(self, myproject, myinterface):
		logger.debug(f"Executing Tab '{self.name}'")
		self.myproject = myproject
		self.myinterface = myinterface
		self._start_thread()
		logger.debug(f"Tab '{self.name}' executed")
	
	def _start_thread(self):
		'''
		method to create a thread for the tab content
		'''
		logger.debug(f"Starting thread for Tab '{self.name}'...")
		if self.thread and self.thread.is_alive():
			logger.debug(f'Thread for Tab {self.name} is already running', exc_info=True)
			return
		
		try:
			if self.myproject is not None:
				self.loading_screen.show_loading(f"Loading {self.name} tab, please wait")
			self.thread = threading.Thread(target=self.create_tab_content, daemon=True)
			self.thread.start()
			logger.debug("Checking thread status...")
			self.master.after(100, self._check_thread)
		except Exception:
			logger.error(f'Error with starting the thread for Tab {self.name}', exc_info=True)


	def _check_thread(self):
		logger.debug(f"Thread of '{self.name}' is alive, checking status...")
		if self.thread and self.thread.is_alive():
			self.content_frame.after(100, self._check_thread)
		else:
			self.on_thread_finished()


	def on_thread_finished(self):
		logger.debug(f"Thread of '{self.name}' finished")
		try:
			if self.tab_content:
				self.tab_content.pack(fill="both", expand=True)
				self.loading_screen.hide_loading()
		except Exception as e:
			logger.error(f"Error on thread finished for Tab '{self.name}'", exc_info=True)


	def create_tab_content(self):
		pass