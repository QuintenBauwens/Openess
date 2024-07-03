""" 

# module for handling nodes

"""

from  tkinter import ttk, scrolledtext, messagebox, Tk
from apps.base_tab import Tab

class TabNodes(Tab):
    def __init__(self):
        super().__init__("Nodes")
    
    def execute(self):
        print("Executing Nodes tab")

class TabFindDevice(Tab):
    def __init__(self):
        super().__init__("Find")
    
    def execute(self):
        print("Executing Find tab")

class TabAddressCheck(Tab):
    def __init__(self):
        super().__init__("Address check")
    
    def execute(self):
        print("Executing Address check tab")

class NodeScreen:
    '''nodescreen class'''

    def __init__(self, master):
        self.master = master
        master.title("TIA openess demo")
        master.geometry("1000x500")
        master.iconbitmap(".\img\\tia.ico")

        self.myproject = None
        self.myinterface = None
        self.action_label = None
        self.hardware = None
        self.nodes = None
        self.projectItems = None

        self.create_project_section()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")

        self.create_node_list_tab()

        self.create_find_device_tab()
        self.create_check_address_tab()

    def tab_file(self): 
        pass

    
    def create_node_list_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Node List")

        btn = ttk.Button(tab, text="Get Node List", command=self.show_node_list)
        btn.pack(pady=10)

        self.node_list_output = scrolledtext.ScrolledText(tab, wrap=Tk.WORD, width=100, height=20)
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

        self.find_nodes_output = scrolledtext.ScrolledText(tab, wrap=Tk.WORD, width=70, height=10)
        self.find_nodes_output.pack(padx=10, pady=10)

    def create_check_address_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Check Address")

        ttk.Label(tab, text="IP Address:").pack(pady=5)
        self.address_entry = ttk.Entry(tab)
        self.address_entry.pack(pady=5)

        btn = ttk.Button(tab, text="Check Address", command=self.check_address)
        btn.pack(pady=10)

        self.check_address_output = scrolledtext.ScrolledText(tab, wrap=Tk.WORD, width=70, height=10)
        self.check_address_output.pack(padx=10, pady=10)

    def show_node_list(self):
        node_list = self.nodes.show_node_table()
        self.node_list_output.delete(1.0, Tk.END)
        self.node_list_output.insert(Tk.END, node_list)

    def find_nodes(self):
        plc_name = self.plc_name_entry.get()
        device_name = self.device_name_entry.get()
        result = self.nodes.find_device_nodes(plc_name.upper(), device_name.upper())
        self.find_nodes_output.delete(1.0, Tk.END)
        self.find_nodes_output.insert(Tk.END, result)

    def check_address(self):
        address = self.address_entry.get() 
        result = self.nodes.address_exists(address)
        self.check_address_output.delete(1.0, Tk.END)
        self.check_address_output.insert(Tk.END, result)