"""
Description: 
# class to handle the nodes within the TIA-portal project
# it contains the functionality to get the node list, find nodes based on PLC and device name and check if an address exists
# it also contains the menu sub-items for the nodes head-item in the main menu

Author: Quinten Bauwens
Last updated: 
"""

import tkinter as tk
from  tkinter import ttk, scrolledtext, messagebox
from src.utils.TabUI import Tab
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

    def __init__(self, master, myproject, myinterface):
        self.master = master
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")
        
        self.myproject = myproject
        self.myinterface = myinterface
        self.node = None

        self.node_list_output = None
        self.find_device_output = None
        self.check_address_output = None

        self.node_list_tab = None
        self.find_device_tab = None
        self.check_address_tab = None


        self.initialize_node()
    
    def update_project(self, myproject, myinterface):
        if self.myproject != myproject or self.myinterface != myinterface:
            self.myproject = myproject
            self.myinterface = myinterface
            self.initialize_node()
            self.cached_node_list = None  # Clear cache when project changes

    def initialize_node(self):
        # Initialize the node object for start screen
        if self.myproject is None or self.myinterface is None:
            self.node = None
            return
        
        try:
            self.node = Nodes(self.myproject, self.myinterface)
        except Exception as e:
            messagebox.showerror("ERROR", f"Failed to initialize Nodes: {str(e)}")
            self.node = None


    def create_node_list_tab(self):
        if not self.node_list_tab is None:
            self.notebook.select(self.node_list_tab)
            return

        tab = ttk.Frame(self.master)
        self.notebook.add(tab, text="Node List")
        self.node_list_tab = tab

        btn = ttk.Button(tab, text="Get Node List", command=self.show_node_list)
        btn.pack(pady=10)

        self.node_list_output = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=100, height=20)
        self.node_list_output.pack(padx=10, pady=10)

        self.notebook.select(self.node_list_tab)


    def create_find_device_tab(self):
        if not self.find_device_tab is None:
            self.notebook.select(self.find_device_tab)
            return 
        
        tab = ttk.Frame(self.master)
        self.notebook.add(tab, text="Find Device Nodes")
        self.find_device_tab = tab

        ttk.Label(tab, text="PLC Name:").pack(pady=5)
        self.plc_name_entry = ttk.Entry(tab)
        self.plc_name_entry.pack(pady=5)
        
        ttk.Label(tab, text="Device Name:").pack(pady=5)
        self.device_name_entry = ttk.Entry(tab)
        self.device_name_entry.pack(pady=5)

        btn = ttk.Button(tab, text="Find Nodes", command=self.find_nodes)
        btn.pack(pady=10)

        self.find_nodes_output = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=70, height=10)
        self.find_nodes_output.pack(padx=10, pady=10)

        self.notebook.select(self.find_device_tab)


    def create_check_address_tab(self):
        if not self.check_address_tab is None:
            self.notebook.select(self.check_address_tab)
            return
        
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Check Address")
        self.check_address_tab = tab

        ttk.Label(tab, text="IP Address:").pack(pady=5)
        self.address_entry = ttk.Entry(tab)
        self.address_entry.pack(pady=5)

        btn = ttk.Button(tab, text="Check Address", command=self.check_address)
        btn.pack(pady=10)

        self.check_address_output = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=70, height=10)
        self.check_address_output.pack(padx=10, pady=10)

        self.notebook.select(self.check_address_tab)


    def show_node_list(self):
        if self.node_list_output is None:
            messagebox.showerror("ERROR", "Node list output not initialized")
            return

        self.node_list_output.delete(1.0, tk.END)
        if self.node is None:
            content = "Please open a project to view the node list."
        else:
            try:
                content = self.node.show_node_table()
            except Exception as e:
                content = f"An error occurred: {str(e)}"

        self.node_list_output.insert(tk.END, content)
    

    def find_nodes(self):
        if self.node is None:
            content = "please open a project to find nodes."
        else:
            try:
                plc_name = self.plc_name_entry.get()
                device_name = self.device_name_entry.get()
                content = self.node.find_device_nodes(plc_name.upper(), device_name.upper())
            except Exception as e:
                content = f"an error occurred: {str(e)}"
        
        self.find_nodes_output.insert(tk.END, content)


    def check_address(self):
        if self.node is None:
            self.initialize_node()

        if self.node is None:
            self.check_address_output.delete(1.0, tk.END)
            self.check_address_output.insert(tk.END, "please open a project to check addresses.")
        else:
            address = self.address_entry.get() 
            try:
                result = self.node.address_exists(address)
                self.check_address_output.delete(1.0, tk.END)
                self.check_address_output.insert(tk.END, result)
            except Exception as e:
                self.check_address_output.delete(1.0, tk.END)
                self.check_address_output.insert(tk.END, f"an error occurred: {str(e)}")

    