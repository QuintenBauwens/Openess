import tkinter as tk
from gui.main import mainApp  # Adjusted import statement

if __name__ == "__main__":
	print("Starting main script") # type: debug

	root = tk.Tk()
	screen_width = root.winfo_screenwidth()  # Get the width of the screen
	gui = mainApp(root)
	root.geometry(f'-{screen_width}+100')  # TODO : Position window on the second screen
	root.mainloop()

	# C:\Temp\P712713A01\P712713A01.ap15_1