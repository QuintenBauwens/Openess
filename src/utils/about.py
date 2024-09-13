
import tkinter as tk
from tkinter import ttk
from utils.loggerConfig import get_logger
import webbrowser
import config

logger = get_logger(__name__)


class About():
	def __init__(self, master, frame):
		self.master = master
		self.frame = frame
		self.app_info = config.APP_INFO
		self.name = config.APP_NAME
		self.repo = config.APP_REPO
		self.author = config.APP_AUTHOR
		self.copyright = config.APP_COPYRIGHT

		self.links = config.APP_AUTHOR_LINKS
		self.description = config.APP_DESCRIPTION


	def show_about(self, previous_frame=None):
		'''show the description of the app in the description frame'''
		logger.info("Showing the about frame")
		max_width = 325
		self.frame.columnconfigure(0, weight=0)
		self.frame.columnconfigure(1, weight=1)
		self.frame.rowconfigure(0, weight=1)
		self.frame.rowconfigure(1, weight=0)
		self.frame.rowconfigure(2, weight=0)
		self.frame.rowconfigure(3, weight=0)
		self.frame.rowconfigure(4, weight=0)
		self.frame.rowconfigure(5, weight=1)

		app_info = ttk.LabelFrame(self.frame, text="App information", width=max_width, name="app_info")
		app_info.grid(row=0, column=0, sticky="nw", padx=(5,2), pady=(5,2))
		app_info_label = ttk.Label(app_info, wraplength=max_width, justify="left")
		app_info_label.pack(anchor="nw", padx=5, pady=2)
		for key, value in self.app_info.items():
			app_info_label.config(text=f"{app_info_label['text']}{key} : ")
			if not isinstance(value, list):
				value = [value]
			for value in value:
				app_info_label.config(text=f"{app_info_label['text']} \n\t{value}\n")

		section_author = ttk.LabelFrame(self.frame, text="Author information", width=max_width, name="section_author") # style in appSettings
		section_author.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=(5,2), pady=(5,2))
		author_info_label = ttk.Label(section_author, wraplength=max_width, justify="left")
		author_info_label.pack(anchor="nw", padx=5, pady=2)
		for key, value in self.author.items():
			author_info_label.config(text=f"{author_info_label['text']}{key} : ")
			if not isinstance(value, list):
				value = [value]
			for value in value:
				author_info_label.config(text=f"{author_info_label['text']} \n\t{value}\n")

		logger.debug(f"Author information: {author_info_label['text']}")
		section_links = ttk.LabelFrame(self.frame, text="Links", name="section_links")
		section_links.grid(row=4, column=0, sticky="w", padx=(5,2), pady=(5,2))
		links_text = tk.Text(section_links, wrap="word", height=4, width=(int(max_width/10)), bg='#f5f5f5', relief="sunken", font=("Helvetica", 10))
		links_text.pack(anchor="sw", padx=5, pady=2)
		self.link_config(links_text, self.links)
		
		logger.debug(f"Links: {links_text.get('1.0', tk.END)}")
		section_app = ttk.LabelFrame(self.frame, text="Description", name="section_app")
		section_app.grid(row=0, column=1, sticky="nw", columnspan=2, rowspan=4, padx=(5,2), pady=(5,2))
		app_description = ttk.Label(section_app, text=self.description, wraplength=700, justify="left")
		app_description.pack(anchor="nw", padx=5, pady=2, fill="both", expand=True)

		# Add a custom separator
		separator = ttk.Separator(self.frame, orient="horizontal")
		separator.grid(row=4, column=1, columnspan=2, sticky="ew", padx=(5,2), pady=(10,10))

		# Add a custom button
		custom_button = ttk.Button(self.frame, text="More Info", command=self.show_more_info)
		custom_button.grid(row=4, column=1, sticky="s", padx=(5,2), pady=(5,2))
		# TODO: to be implemented
		custom_button.config(state=tk.DISABLED)
		logger.debug(f"App information: {app_description['text']}")


	def show_more_info(self):
	# Create a new window or dialog with additional information
		info_window = tk.Toplevel(self.frame)
		info_window.title("Additional Information")
		info_label = ttk.Label(info_window, text="This is additional information about the application.", 
							wraplength=300, style="Custom.TLabel")
		info_label.pack(padx=20, pady=20)

	def show_footer(self, frame):
		"""Create a footer with copyright information."""

		copyright_label = tk.Label(frame, text=self.copyright, fg="grey", font=("Helvetica", 6))
		copyright_label.pack(side="bottom", expand=True, fill="x", anchor="s")
	
	def link_config(self, text_widget, links_dict):
		'''make the links in the links_text clickable'''

		for link, url in links_dict.items():
			text_widget.insert(tk.END, f'{link}\n')
		text_widget.config(state="disabled")

		for link, url in links_dict.items():
			start = text_widget.search(link, "1.0", tk.END)
			end = f"{start}+{len(link)}c"
			text_widget.tag_add(link, start, end)
			text_widget.tag_config(link, foreground="blue", underline=True)
			text_widget.tag_bind(link, "<Button-1>", lambda e, url=url: self.open_link(url))

			text_widget.tag_bind(link, "<Enter>", self.on_enter)
			text_widget.tag_bind(link, "<Leave>", self.on_leave)

	def open_link(self, url):
		webbrowser.open_new(url)

	def on_enter(self, event):
		event.widget.config(cursor="hand2")

	def on_leave(self, event):
		event.widget.config(cursor="")