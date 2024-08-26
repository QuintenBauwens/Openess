import time
import tkinter as tk
import threading

from utils.logger_config import get_logger

logger = get_logger(__name__)

class LoadScreen():
    def __init__(self, master, content_frame=None):
        logger.debug(f"Initializing '{__name__.split('.')[-1]}' instance")
        self.master = master
        self.content_frame = content_frame
        self.loadLabel = None
        self.loading_frame = None
        self.loading_dots = 0
        logger.debug(f"Initialized '{__name__.split('.')[-1]}' instance successfully")
    
    def show_loading(self, text: str):
        """
        Displays a loading screen with the given message for a specified delay.
        Parameters:
            message (str): The message to be displayed on the loading screen.
        """
        logger.debug(f"Showing loading screen with message '{text}'")

        self.text = text

        self.loading_frame = tk.Frame(self.content_frame, bg="white")
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.loadLabel = tk.Label(self.content_frame, text=self.text, bg="white",font=("tkDefaultFont", 14))
        self.loadLabel.place(relx=0.5, rely=0.5, anchor="center")

        logger.debug("Loading screen displayed, starting loading effect")
        threading.Thread(target=self.loading_effect, daemon=True).start()

    
    def set_loading_text(self, text: str):
        logger.debug(f"Setting loading text from {self.text} to '{text}'")
        self.loadLabel.config(text=text)


    def hide_loading(self):
        """
        Hide the loading screen.

        Returns:
        None
        """
        logger.debug("Hiding loading screen")

        if self.loading_frame is None:
            return
        if self.loading_frame:
            self.loading_frame.destroy()
            self.loading_frame = None
        if self.loadLabel:
            self.loadLabel.destroy()
            self.loadLabel = None

        logger.debug("Loading screen hidden, updating master frame...")
        self.master.update_idletasks()

    def loading_effect(self):
        """
        Display a loading screen with a message for a specified duration.

        Parameters:
        message (str): The message to display on the loading screen.
        duration (int): The duration to display the loading screen.

        Returns:
        None
        """

        while self.loading_frame:
            current_text = self.loadLabel.cget("text")
            if current_text.endswith("..."):
                current_text = current_text[:-3]
            else:
                current_text = current_text + "."
            self.loadLabel.config(text=current_text)
            time.sleep(0.5)