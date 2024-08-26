import tkinter as tk
from utils.logger_config import get_logger
from gui.main import mainApp  # Adjusted import statement

logger = get_logger(__name__)

if __name__ == "__main__":
	logger.info("Starting the application")

	root = tk.Tk()
	screen_width = root.winfo_screenwidth()  # Get the width of the scree
	gui = mainApp(root)
	root.geometry(f'-{screen_width}+100')  # TODO : Position window on the second screen
	root.mainloop()


	# C:\Temp\P712713A01\P712713A01.ap15_1
	
