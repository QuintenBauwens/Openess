import tkinter as tk
from src.gui.main import mainApp  # Adjusted import statement

if __name__ == "__main__":
	print("Starting main script") # type: debug

	root = tk.Tk()
	gui = mainApp(root)
	root.mainloop()