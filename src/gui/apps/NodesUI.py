"""
Description: 
# class to handle the nodes within the TIA-portal project
# it contains the functionality to get the node list, find nodes based on PLC and device name and check if an address exists
# it also contains the menu sub-items for the nodes head-item in the main menu

Author: Quinten Bauwens
Last updated: 08/07/2024
"""

import tkinter as tk
from  tkinter import ttk, scrolledtext, messagebox
from src.utils.tabUI import Tab
from src.utils.tooltipUI import RadioSelectDialog
from ...core.nodes import Nodes

# all the menu sub-items are defined here
class TabNodes(Tab):
    '''class to create the menu sub-items for the nodes head-item in the main menu'''

    def __init__(self, master, main_class_instance, project=None, interface=None):
        super().__init__("Node List", master, main_class_instance, project, interface) #mainclass is nodesUI

    def create_tab_content(self):
        self.masterTitle = self.master.title(f'{self.masterTitle} - {self.name}')
        self.tab_content = self.main_class_instance.create_node_list_tab()

class TabFindDevice(Tab):
    '''class to create the menu sub-items for the nodes head-item in the main menu'''

    def __init__(self, master, main_class_instance, project=None, interface=None):
        super().__init__("Find device", master, main_class_instance, project, interface)

    def create_tab_content(self):
        self.masterTitle = self.master.title(f'{self.masterTitle} - {self.name}')
        self.tab_content = self.main_class_instance.create_find_device_tab()

class TabAddressCheck(Tab):
    '''class to create the menu sub-items for the nodes head-item in the main menu'''

    def __init__(self, master, main_class_instance, project=None, interface=None):
        super().__init__("Address check", master, main_class_instance, project, interface)

    def create_tab_content(self):
        self.masterTitle = self.master.title(f'{self.masterTitle} - {self.name}')
        self.tab_content = self.main_class_instance.create_check_address_tab()


# logic behind the content of the menu sub-items
class NodesUI:
    '''nodescreen class to create the content of its subtabs defined above and its functionality'''

    def __init__(self, master, myproject, myinterface, status_icon=None):
        self.master = master
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")
        
        self.myproject = myproject
        self.myinterface = myinterface
        self.status_icon = status_icon
        self.node = None

        self.output_node_list = None
        self.output_find_device = None
        self.output_check_address = None

        self.tab_node_list = None
        self.tab_find_device = None
        self.tab_check_address = None

        self.btn_export_node_list = None

        self.initialize_node()


    def update_project(self, myproject, myinterface):
        '''Overwrites the previous project and interface with the new ones and reinitializes the node object.

        Args:
            myproject (type): The new project object.
            myinterface (type): The new interface object.

        Returns:
            None
        '''

        if self.myproject != myproject or self.myinterface != myinterface:
            self.myproject = myproject
            self.myinterface = myinterface
            self.initialize_node()

            if not self.tab_node_list is None:
                if self.myproject is None:
                    self.btn_export_node_list.config(state=tk.DISABLED)
                else:
                    self.btn_export_node_list.config(state=tk.NORMAL)

            self.status_icon.change_icon_status("#39FF14", f'updated project and interface to {myproject} and {myinterface}')


    def initialize_node(self):
        '''Initialize the node object even if the project or interface is None, 
        so the screens with limited features can be opened without a project.

        Args:
            None

        Returns:
            None

        Raises:
            None
        '''

        if self.myproject is None or self.myinterface is None:
            self.node = None
            return
        
        try:
            self.node = Nodes(self.myproject, self.myinterface)

        except Exception as e:
            self.node = None
            message = f'failed to initialize node object: {str(e)}'
            messagebox.showerror("ERROR", message)
            self.status_icon.change_icon_status("#FF0000", message)


    def create_node_list_tab(self):
        '''Setup for the node list tab-screen, with a button to get the node list.

        This method creates a tab in the GUI application for displaying the node list. If the tab already exists, it selects the existing tab. Otherwise, it creates a new tab and adds it to the notebook.

        The tab contains a button labeled "Get Node List" which triggers the show_node_list method when clicked. It also includes a scrolled text widget for displaying the output of the node list.

        Returns:
            None
        '''
        if not self.tab_node_list is None:
            if not self.myproject is None:
                self.btn_export_node_list.config(state=tk.NORMAL)

            self.notebook.select(self.tab_node_list)
            return

        tab = ttk.Frame(self.master)
        self.notebook.add(tab, text="Node List")
        self.tab_node_list = tab

        self.btn_get_node_list = ttk.Button(tab, text="Get Node List", command=self.show_node_list)
        self.btn_export_node_list = ttk.Button(tab, text="Export", command=self.export_node_list, state=tk.NORMAL)

        self.btn_get_node_list.grid(row=0, column=0, padx=10, pady=10)
        self.btn_export_node_list.grid(row=0, column=1, padx=10, pady=10)

        if self.myproject is None:
            self.btn_export_node_list.config(state=tk.DISABLED)

        # Center the button frame in the tab frame
        tab.grid_columnconfigure(0, weight=1)
        self.btn_get_node_list.grid_columnconfigure(0, weight=1)  # This ensures the buttons stay in the middle
        self.btn_export_node_list.grid_columnconfigure(2, weight=1)  # Add an extra column on the right for equal weighting

        self.output_node_list = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=100, height=20)
        self.output_node_list.grid(row=1, padx=10, pady=10, sticky="ew")
        tab.grid_columnconfigure(0, weight=1)

        self.notebook.select(self.tab_node_list)


    def create_find_device_tab(self):
        '''Setup for the find device tab-screen, with entries for the PLC and device name and a button to find the nodes based on the input.

        Returns:
            None
        '''

        if not self.tab_find_device is None:
            self.notebook.select(self.tab_find_device)
            return 
        
        tab = ttk.Frame(self.master)
        self.notebook.add(tab, text="Find Device Nodes")
        self.tab_find_device = tab

        ttk.Label(tab, text="PLC Name:").pack(pady=5)
        self.entry_plc_name = ttk.Entry(tab)
        self.entry_plc_name.pack(pady=5)
        
        ttk.Label(tab, text="Device Name:").pack(pady=5)
        self.entry_device_name = ttk.Entry(tab)
        self.entry_device_name.pack(pady=5)

        self.btn_find_device = ttk.Button(tab, text="Find Device", command=self.find_nodes)
        self.btn_find_device.pack(pady=10)

        self.output_find_device = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=70, height=10)
        self.output_find_device.pack(padx=10, pady=10)

        self.notebook.select(self.tab_find_device)


    def create_check_address_tab(self):
        '''Setup for the check address tab-screen.

        This method creates a tab in the GUI application for checking an IP address. It adds a label, an entry field for the address, a button to check the address, and an output area to display the results.

        If the tab already exists, it will be selected instead of creating a new one.

        Returns:
            None
        '''
        if not self.tab_check_address is None:
            self.notebook.select(self.tab_check_address)
            return
        
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Check Address")
        self.tab_check_address = tab

        ttk.Label(tab, text="IP Address:").pack(pady=5)
        self.entry_address = ttk.Entry(tab)
        self.entry_address.pack(pady=5)

        self.btn_check_address = ttk.Button(tab, text="Check Address", command=self.check_address)
        self.btn_check_address.pack(pady=10)

        self.output_check_address = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=70, height=10)
        self.output_check_address.pack(padx=10, pady=10)

        self.notebook.select(self.tab_check_address)


    def show_node_list(self):
        '''Method that is linked to the button in the node list tab.
        
        Retrieves the function output in the nodes logic to get the node list.
        If no project is open, it displays a message indicating that a project needs to be opened.
        If an error occurs during the retrieval of the node list, it displays the error message.
        '''

        if self.node is None:
            content = "Please open a project to view the node list."
            self.status_icon.change_icon_status("#FFFF00", content)
        else:
            try:
                content = self.node.show_node_table()
                self.status_icon.change_icon_status("#39FF14", "Node list retrieved successfully")

            except Exception as e:
                content = f"An error occurred: {str(e)}"
                self.status_icon.change_icon_status("#FF0000", content)
        self.output_node_list.delete(1.0, tk.END)
        self.output_node_list.insert(tk.END, content)
        


    def export_node_list(self):
        '''method that is linked to the button in the node list tab, to export the function output of Nodes logic to a file'''
    
        dialog = RadioSelectDialog(self.master, "Choose export option", ["*.csv", "*.xlsx", "*.json"])

        try:
            content = self.node.export_node_list(dialog.filename, dialog.selection)
            messagebox.showinfo("Export successful", content)
            self.status_icon.change_icon_status("#39FF14", content)

        except ValueError as e:
            message = f"Export failed: {str(e)}"
            messagebox.showwarning("WARNING", message)
            self.status_icon.change_icon_status("#FF0000", message)


    def find_nodes(self):
        '''Method that is linked to the button in the find device tab, to retrieve the function output in the nodes logic to find the nodes based on the PLC and device name.

        Returns:
            str: The output of the find_device_nodes function, which contains the nodes found based on the PLC and device name.

        Raises:
            Exception: If an error occurs during the execution of the find_device_nodes function.
        '''

        if self.node is None:
            content = "Please open a project to find nodes."
            self.status_icon.change_icon_status("#FFFF00", content)
        else:
            try:
                plc_name = self.entry_plc_name.get()
                device_name = self.entry_device_name.get()
                content = self.node.find_device_nodes(plc_name.upper(), device_name.upper())
                self.status_icon.change_icon_status("#39FF14", "find_nodes retrieved successfully")
            except Exception as e:
                content = f"An error occurred: {str(e)}"
                self.status_icon.change_icon_status("#FF0000", content)
        self.output_find_device.delete(1.0, tk.END)
        self.output_find_device.insert(tk.END, content)


    def check_address(self):
        '''Method that is linked to the button in the check address tab.
        Retrieves the function output in the nodes logic to check if an address exists in the project.

        Returns:
            str: The result of checking if the address exists in the project.
        '''

        if self.node is None:
            content = "Please open a project to check addresses."
            self.status_icon.change_icon_status("#FFFF00", content)
        else: 
            try:
                address = self.entry_address.get()
                content = self.node.address_exists(address)
                self.status_icon.change_icon_status("#39FF14", "check_address retrieved successfully")
            except Exception as e:
                content = f"An error occurred: {str(e)}"
                self.status_icon.change_icon_status("#FF0000", content)
        self.output_check_address.delete(1.0, tk.END)
        self.output_check_address.insert(tk.END, content)