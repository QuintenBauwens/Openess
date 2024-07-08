"""
Author: Quinten Bauwens
Last updated: 08/07/2024
"""

import tkinter as tk
from tkinter import simpledialog


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
        "Display text in tooltip window"
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                    background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                    font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

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
        self.master = master
        self.canvas = tk.Canvas(master, width=25, height=25)
        self.status_color = status_color
        self.circle = self.canvas.create_oval(7, 7, 22, 22, fill=self.status_color)
        self.canvas.grid(row=0, column=0, pady=10)  # Adjust row and column as needed
        self.tooltip_text = tooltip_text
        self.tooltip = Tooltip(self.canvas, self.tooltip_text)
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)

    def change_icon_status(self, new_color, tooltip_text=None):
        """
        Changes the color and tooltip text of the status circle.

        Args:
            new_color (str): The new color of the status circle.
            tooltip_text (str, optional): The new text to display in the tooltip. Defaults to None.
        """
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


class RadioSelectDialog(simpledialog.Dialog):
    """
    A dialog window that allows the user to select an option from a list of radio buttons.

    Args:
        parent (tkinter.Tk): The parent window of the dialog.
        title (str): The title of the dialog window.
        options (list): A list of options to be displayed as radio buttons.

    Attributes:
        options (list): A list of options to be displayed as radio buttons.
        selection (str): The selected option.
        filename (str): The filename entered by the user.
    """

    def __init__(self, parent, title, options):
        self.options = options
        self.selection = None
        self.filename = None
        parent.iconbitmap("resources\\img\\tia.ico")
        super().__init__(parent, title)

    def body(self, master):
        """
        Create the body of the dialog window.

        Args:
            master (tkinter.Tk): The master widget.

        Returns:
            tkinter.Tk: The master widget.
        """
        self.var = tk.StringVar(master)
        self.var.set(self.options[0])  # standard value
        self.label = tk.Label(master, text="filename:").pack(anchor=tk.W)
        self.entry = tk.Entry(master, textvariable=self.filename)
        self.entry.pack(anchor=tk.W)

        for option in self.options:
            tk.Radiobutton(master, text=option, variable=self.var, value=option).pack(anchor=tk.W)
        return master

    def apply(self):
        """
        Apply the selected option and filename.

        This method is called when the user clicks the "OK" button.

        Returns:
            None
        """
        self.selection = self.var.get()
        self.filename = self.entry.get()
