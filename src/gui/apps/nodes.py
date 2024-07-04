"""
Description: 
# class to handle the nodes within the TIA-portal project
# it contains the functionality to get the node list, find nodes based on PLC and device name and check if an address exists
# it also contains the menu sub-items for the nodes head-item in the main menu

Author: Quinten Bauwens
Last updated: 
"""

import tkinter as tk
from  tkinter import ttk, scrolledtext
from src.utils.base_tab import Tab

# all the menu sub-items are defined here
class TabNodes(Tab):
    '''class to create the menu sub-items for the nodes head-item in the main menu'''
    def __init__(self):
        super().__init__("Node List")
        self.nodeScreen = None

    def create_tab_content(self):
        self.nodeScreen = NodeScreen(self.content_frame)
        self.nodeScreen.create_node_list_tab()

class TabFindDevice(Tab):
    '''class to create the menu sub-items for the nodes head-item in the main menu'''
    def __init__(self):
        super().__init__("Find")
        self.nodeScreen = None

    def create_tab_content(self):
        self.nodeScreen = NodeScreen(self.content_frame)
        self.nodeScreen.create_find_device_tab()

class TabAddressCheck(Tab):
    '''class to create the menu sub-items for the nodes head-item in the main menu'''
    def __init__(self):
        super().__init__("Address check")
        self.nodeScreen = None

    def create_tab_content(self):
        self.nodeScreen = NodeScreen(self.content_frame)
        self.nodeScreen.create_check_address_tab()


# logic behind the content of the menu sub-items
class NodeScreen:
    '''nodescreen class to create the content of its subtabs defined above and its functionality'''

    def __init__(self, master):
        self.master = master
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")
        self.tabs = {}
        
        self.myproject = None
        self.myinterface = None
        self.action_label = None
        self.hardware = None
        self.nodes = None
        self.projectItems = None


    def create_node_list_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Node List")

        btn = ttk.Button(tab, text="Get Node List", command=self.show_node_list)
        btn.pack(pady=10)

        self.node_list_output = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=100, height=20)
        self.node_list_output.pack(padx=10, pady=10)


    def create_find_device_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Find Device Nodes")

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


    def create_check_address_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Check Address")

        ttk.Label(tab, text="IP Address:").pack(pady=5)
        self.address_entry = ttk.Entry(tab)
        self.address_entry.pack(pady=5)

        btn = ttk.Button(tab, text="Check Address", command=self.check_address)
        btn.pack(pady=10)

        self.check_address_output = scrolledtext.ScrolledText(tab, wrap=tk.WORD, width=70, height=10)
        self.check_address_output.pack(padx=10, pady=10)


    def show_node_list(self):
        node_list = self.nodes.show_node_table()
        self.node_list_output.delete(1.0, tk.END)
        self.node_list_output.insert(tk.END, node_list)


    def find_nodes(self):
        plc_name = self.plc_name_entry.get()
        device_name = self.device_name_entry.get()
        result = self.nodes.find_device_nodes(plc_name.upper(), device_name.upper())
        self.find_nodes_output.delete(1.0, tk.END)
        self.find_nodes_output.insert(tk.END, result)


    def check_address(self):
        address = self.address_entry.get() 
        result = self.nodes.address_exists(address)
        self.check_address_output.delete(1.0, tk.END)
        self.check_address_output.insert(tk.END, result)