from utils.tooltipUI import Tooltip
from utils.logger_config import get_logger
import tkinter as tk

logger = get_logger(__name__)

# TODO: optimimalization possible, created statuscircle.error, statuscircle.success, statuscircle.warning instead of change_icon_status
class StatusCircle:
	"""
	A class representing a status circle widget with a tooltip.

	Args:
		master (tkinter.Tk or tkinter.Toplevel): The parent widget.
		status_color (str, optional): The color of the status circle. Defaults to "#FF0000".
		tooltip_text (str, optional): The text to display in the tooltip. Defaults to "Status description".

	Attributes:
		master (tkinter.Tk or tkinter.Toplevel): The parent widget.
		canvas (tkinter.Canvas): The canvas widget to draw the status circle.
		status_color (str): The color of the status circle.
		circle (int): The ID of the oval representing the status circle.
		tooltip_text (str): The text to display in the tooltip.
		tooltip (Tooltip): The tooltip widget associated with the status circle.

	Methods:
		change_icon_status: Changes the color and tooltip text of the status circle.
		on_enter: Event handler for mouse enter event.
		on_leave: Event handler for mouse leave event.
	"""

	def __init__(self, master, status_color="#FF0000", tooltip_text="Status description"):
		logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
		self.master = master
		self.canvas = tk.Canvas(master, width=25, height=25)
		self.status_color = status_color
		self.circle = self.canvas.create_oval(7, 7, 22, 22, fill=self.status_color)
		self.canvas.grid(row=0, column=0, pady=10)  # Adjust row and column as needed
		self.tooltip_text = tooltip_text
		self.tooltip = Tooltip(self.canvas, self.tooltip_text)
		self.canvas.bind("<Enter>", self.on_enter)
		self.canvas.bind("<Leave>", self.on_leave)
		logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")


	def change_icon_status(self, new_color, tooltip_text=None):
		"""
		Changes the color and tooltip text of the status circle.
		Colors used in the status circle are: "#FF0000" (red), "#00FF00" (green), "#FFFF00" (yellow).

		Args:
			new_color (str): The new color of the status circle.
			tooltip_text (str, optional): The new text to display in the tooltip. Defaults to None.
		"""
		# colors = ["#FF0000", "#00FF00", "#FFFF00"]
		logger.debug(f"Changing status circle color to {new_color} and tooltip text to {tooltip_text}")
		self.status_color = new_color
		self.canvas.itemconfig(self.circle, fill=self.status_color)
		self.tooltip.update_tooltip_text(tooltip_text)


	def on_enter(self, event=None):
		"""
		Event handler for mouse enter event.
		Shows the tooltip.
		"""
		self.tooltip.showtip()


	def on_leave(self, event=None):
		"""
		Event handler for mouse leave event.
		Hides the tooltip.
		"""
		self.tooltip.hidetip()