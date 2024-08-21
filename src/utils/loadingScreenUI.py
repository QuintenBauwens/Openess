import tkinter as tk

class LoadScreen():
    def __init__(self, master):
        self.master = master
        self.loadLabel = None
        self.loading_dots = 0
    
    def show_loading(self, message: str):
        """
        Display a loading screen with a message.

        Parameters:
        message (str): The message to display on the loading screen.

        Returns:
        None
        """

        self.message = message
        
        self.loading_frame = tk.Frame(self.master, bg="white")
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.loadLabel = tk.Label(self.master, text=message, bg="white")
        self.loadLabel.pack(expand=True)
        self.loading_effect()
    
    
    def hide_loading(self):
        """
        Hide the loading screen.

        Returns:
        None
        """

        if self.loading_frame:
            self.loading_frame.destroy()
            self.loading_frame = None
        if self.loadLabel:
            self.loadLabel.destroy()
            self.loadLabel = None

    def loading_effect(self):
        """
        Display a loading screen with a message for a specified duration.

        Parameters:
        message (str): The message to display on the loading screen.
        duration (int): The duration to display the loading screen.

        Returns:
        None
        """

        if self.loadLabel is not None:
            self.loading_dots = (self.loading_dots + 1) % 4
            dots = "." * self.loading_dots
            self.loadLabel.config(text=f'{self.message}{dots}')
            self.master.update_idletasks()
            self.master.after(500, self.loading_effect)
        else:
            pass