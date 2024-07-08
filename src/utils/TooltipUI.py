"""
Description: 
# 

Author: Quinten Bauwens
Last updated:
"""

import tkinter as tk
from tkinter import ttk

class Tooltip:
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
        self.text = new_text

        if not self.text:
            self.hidetip()

        if self.tipwindow:
            for widget in self.tipwindow.winfo_children():
                widget.configure(text=new_text)

class StatusCircle:
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

    def change_status_color(self, new_color, tooltip_text=None):
        self.status_color = new_color
        self.canvas.itemconfig(self.circle, fill=self.status_color)
        self.tooltip.update_tooltip_text(tooltip_text)

    def on_enter(self, event=None):
        self.tooltip.showtip()

    def on_leave(self, event=None):
        self.tooltip.hidetip()
