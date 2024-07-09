"""
Description: 

Author: Quinten Bauwens
Last updated: 08/07/2024
"""

import tkinter as tk
from  tkinter import ttk, scrolledtext, messagebox
from src.utils.tabUI import Tab
from src.utils.tooltipUI import RadioSelectDialog
from ...core.file import File

class TabSummary(Tab):
    '''class to create the menu sub-items for the file head-item in the main menu'''

    def __init__(self, master, main_class_instance, project=None, interface=None):
        super().__init__("Summary", master, main_class_instance, project, interface) #mainclass is instance of FileUI

    def create_tab_content(self):
        self.tab_content = self.main_class_instance.create_summary_tab()



class FileUI:
    def __init__(self, master, myproject, myinterface, status_icon=None):
        self.master = master
        self.project = myproject
        self.interface = myinterface
        self.myproject = myproject
        self.myinterface = myinterface
        self.status_icon = status_icon
        self.frame = None # Frame for the file UI set in the mainApp

        self.output_summary = None
        self.tab_summary = None

        self.initialize_file()

    def initialize_file(self):
        if self.myproject is None or self.myinterface is None:
            self.file = None
            return
        
        try:
            self.file = File(self.myproject, self.myinterface)
        except Exception as e:
            self.file = None
            message = f'Failed to initialize file object: {str(e)}'
            messagebox.showerror("ERROR", message)
            self.status_icon.change_icon_status("#FF0000", message)

    def create_summary_tab(self):
        if self.frame is None:
            self.frame = ttk.Frame(self.master)

        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.output_summary = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, width=100, height=10)
        self.output_summary.pack(padx=10, pady=10)

        self.btn_get_summary = ttk.Button(self.frame, text="Get summary", command=self.show_summary)
        self.btn_get_summary.pack(pady=5)

        return self.frame

    def show_summary(self):
        if self.file is None:
            content = "Please open a project to view the summary."
            self.status_icon.change_icon_status("#FFFF00", content)
        else:
            try:
                content = self.file.file_summary()
                self.status_icon.change_icon_status("#39FF14", "Summary retrieved successfully")
            except Exception as e:
                content = f"An error occurred: {str(e)}"
                self.status_icon.change_icon_status("#FF0000", content)
        self.output_summary.delete(1.0, tk.END)
        self.output_summary.insert(tk.END, content)

    def update_project(self, myproject, myinterface):
        if self.myproject != myproject or self.myinterface != myinterface:
            self.myproject = myproject
            self.myinterface = myinterface
            self.initialize_file()
            self.status_icon.change_icon_status("#39FF14", f'Updated project and interface to {myproject} and {myinterface}')