"""
Author: Quinten Bauwens
Last updated: 09/07/2024
"""

import tkinter as tk

class Tooltip:
	"""
	A class representing a tooltip for a widget.

	Attributes:
		widget: The widget to which the tooltip is attached.
		text: The text to be displayed in the tooltip window.
		tipwindow: The tooltip window.
		id: The ID of the tooltip.
		x: The x-coordinate of the tooltip window.
		y: The y-coordinate of the tooltip window.
	"""

	def __init__(self, widget, text):
		self.widget = widget
		self.text = text
		self.tipwindow = None
		self.id = None
		self.x = self.y = 0


	def showtip(self):
		"""Display text in tooltip window"""
		if self.tipwindow or not self.text:
			return

		self.tipwindow = tw = tk.Toplevel(self.widget)
		tw.wm_overrideredirect(True)
		label = tk.Label(tw, text=self.text, justify=tk.LEFT,
						background="#ffffe0", relief=tk.SOLID, borderwidth=1,
						font=("tahoma", "8", "normal"))
		label.pack(ipadx=1)

		tw.update_idletasks()  # update layout before getting the width
		tip_width = tw.winfo_reqwidth()  # get the width of the tooltip window

		x = self.widget.winfo_rootx() - tip_width
		y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1

		tw.wm_geometry(f"+{x}+{y}")  # position the tooltip window


	def hidetip(self):
		tw = self.tipwindow
		self.tipwindow = None
		if tw:
			tw.destroy()


	def update_tooltip_text(self, new_text):
		"""
		Update the text of the tooltip.

		Args:
			new_text: The new text to be displayed in the tooltip.
		"""

		self.text = new_text

		if not self.text:
			self.hidetip()

		if self.tipwindow:
			for widget in self.tipwindow.winfo_children():
				widget.configure(text=new_text)