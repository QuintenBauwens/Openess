import tkinter as tk
from utils.appSettings import appSettings
from utils.loggerConfig import get_logger
from utils.loggerConfig import update_logger_config
from gui.main import mainApp

logger = get_logger(__name__)

def main(root):
	try:
		settings = appSettings(root)
		update_logger_config(settings.get('logger', {}))
		logger.info(f"Lanching application with settings: {settings}")
	except Exception as e:
		logger.warning("Launching application has been aborted due to an error: ", e, exc_info=True)
	return settings

if __name__ == "__main__":
	root = tk.Tk()
	root.withdraw()
	screen_width = root.winfo_screenwidth()  # get the width of the screen

	settings = main(root)
	gui = mainApp(root, settings)
	# gui = mainApp(root)

	# root.geometry(f'-{screen_width}+100')  # position root on the second screen.
	root.deiconify()
	root.mainloop()

	# C:\Temp\P712713A01\P712713A01.ap15_1
	
