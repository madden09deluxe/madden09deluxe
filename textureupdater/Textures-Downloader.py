import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from threading import Thread
import datetime
import requests
import psutil
from datetime import datetime  # Import the datetime class
import subprocess  # Add this line to import subprocess module

from utils.helpers import load_config_new, save_config_new, ConfigManager
from utils.sync import main_sync
from utils.download_repo import download_repo_main

config_manager = ConfigManager()

# Access co nfiguration variables
debug_mode = config_manager.debug_mode
initial_setup_done = config_manager.initial_setup_done
local_directory = config_manager.local_directory
github_token = config_manager.github_token
last_run_date = config_manager.last_run_date
project_name = config_manager.project_name
owner = config_manager.owner
repo = config_manager.repo
branch_name = config_manager.branch_name
subdirectory = config_manager.subdirectory
slus_folder = config_manager.slus_folder
json_url = config_manager.json_url
# Other variables
github_repo_url = config_manager.github_repo_url
# Initialize user_choice_var as a global variable
user_choice_var = config_manager.user_choice_var

class DebugModeMixin:
    def toggle_debug_mode(self):
        debug_mode = self.debug_mode_var.get()
        save_config_new({'debug_mode': debug_mode})


class OnSaveButtonClickMixin:
    def on_save_button_click(self, config_dict, button, master):
        for variable_name, entry_widget in config_dict.items():
            # Get the value from the Entry widget
            value_to_save = entry_widget.get()

            # Special case for initial_setup_var: Convert to boolean
            if variable_name == "initial_setup_done":
                value_to_save = value_to_save.lower() == "true"

            # Call save_config_new with the value and variable name
            save_config_new({variable_name: value_to_save})

        # Reload the configuration
        config = load_config_new()

        # Destroy the LOCAL DIRECTORY PATH warning/instructions label if exists and local_directory has a value
        if hasattr(self, 'path_to_replacements_label') and self.path_to_replacements_label and config.get("local_directory"):
            self.path_to_replacements_label.destroy()

        # Destroy the GITHUB TOKEN warning/instructions label if exists and github_token has a value
        if hasattr(self, 'github_token_label') and self.github_token_label and config.get("github_token"):
            self.github_token_label.destroy()

        # Update the button text and color
        button.config(text="Saved! (restart app)", fg="green")

        # Schedule the reversion after 5000 milliseconds (5 seconds)
        master.after(5000, lambda: button.config(text="Save Config", fg="black"))





class PostInstallScreen(tk.Frame, DebugModeMixin, OnSaveButtonClickMixin):
    def __init__(self, master, switch_func):
        tk.Frame.__init__(self, master)
        self.config_manager = ConfigManager()

        self.master.title(f"{project_name} Textures Updater")
        self.master.minsize(900, 720)

        # Create a boolean variable to store the checkbox state of debug_mode
        self.debug_mode_var = tk.BooleanVar(value=self.config_manager.debug_mode)

        # Heading
        heading_label = tk.Label(self, text=f"{project_name} Textures Updater", font=('TkDefaultFont', 18, 'bold'))
        heading_label.grid(row=0, column=0, columnspan=3, pady=(10, 10))

        # Configure columns to expand with the window
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # Path to Replacements
        tk.Label(self, text="Path to PCSX2\\textures:", justify="left").grid(row=1, column=0, sticky="e", padx=(20, 0), pady=2)
        local_directory_entry = tk.Entry(self, width=50)
        local_directory_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(10, 20), pady=2, ipady=3)
        local_directory_entry.insert(0, self.config_manager.local_directory)



        # Check if Path to Replacements is provided in the config file
        self.path_to_replacements_label = tk.Label(self, text=f"Enter the full path to your emulator's TEXTURES FOLDER and click Save Config. Find this in PCSX2 > Settings > Graphics > Texture Replacements. Copy that path exactly as-is. Example: C:\\Whatever\\PCSX2\\textures", font=('TkDefaultFont', 12), fg="red", justify="left", wraplength=530)
        if not local_directory:  
            self.path_to_replacements_label.grid(row=2, column=1, columnspan=2, pady=(0, 10), padx=(20, 0), sticky="w")

        # GitHub Token
        tk.Label(self, text="GitHub API Token:", justify="left").grid(row=3, column=0, sticky="e", pady=2)
        github_token_entry = tk.Entry(self, width=30) 
        github_token_entry.grid(row=3, column=1, sticky="w", padx=(10, 20), pady=2, ipady=3)
        github_token_entry.insert(0, github_token)

        # Check if Github Token is provided in the config file
        self.github_token_label = tk.Label(self, text=f"Log in to Github.com and go to Settings > Developer Settings > Personal Access Tokens", font=('TkDefaultFont', 11), fg="red", justify="left", wraplength=250)
        if not github_token: 
            self.github_token_label.grid(row=4, column=1, columnspan=2, pady=(0, 10), padx=(20, 0), sticky="w")
        
        # Last Run Date
        last_run_date_label = tk.Label(self, text="Last Sync Date:", justify="right")
        last_run_date_label.grid(row=5, column=0, sticky="e", pady=2)
        last_run_date_entry = tk.Entry(self, width=30)
        last_run_date_entry.grid(row=5, column=1, sticky="w", padx=(10, 20), pady=2, ipady=3)

        # Check if last_run_date is provided and in the correct format
        if last_run_date:
            try:
                # Check if the value looks like a datetime string and convert it
                last_run_date_entry.insert(0, last_run_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
            except ValueError:
                # Handle the case where the value is not a valid datetime
                default_last_run_date = datetime(2005, 7, 11, 0, 0, 0)
                last_run_date_entry.insert(0, default_last_run_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
                save_config_new({'last_run_date': default_last_run_date.strftime('%Y-%m-%d %H:%M:%S.%f')})
        else:
            # Handle the case where last_run_date is not provided
            default_last_run_date = datetime(2005, 7, 11, 0, 0, 0)
            last_run_date_entry.insert(0, default_last_run_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
            save_config_new({'last_run_date': default_last_run_date.strftime('%Y-%m-%d %H:%M:%S.%f')})
        
        # Create a StringVar for initial_setup_done because it doesn't have an entry field
        initial_setup_var = tk.StringVar(value="False")  # Set the initial value as needed

        # Save Button
        config_dict_main = {
            "local_directory": local_directory_entry,
            "github_token": github_token_entry,
            "last_run_date": last_run_date_entry,
            "initial_setup_done": initial_setup_var,
        }
        save_button_on_main = tk.Button(self, text="Save Configuration", command=lambda: self.on_save_button_click(config_dict_main, save_button_on_main, self), justify="left", width=20, cursor="hand2")
        save_button_on_main.grid(row=3, column=2, rowspan=4, pady=20, padx=(0, 60))

        # Divider
        ttk.Separator(self, orient="horizontal").grid(row=7, column=0, columnspan=3, pady=15, sticky="ew")


        # Choose an Option Section
        tk.Label(self, text="Would you like to only check for files in Github that are new or have changed\nsince your last sync date or would you like to do a full sync of the entire repo?", font=('TkDefaultFont', 13, 'bold')).grid(row=8, column=0, columnspan=3, pady=(5, 5))
       
        # Create a frame for the radio button options
        radio_buttons = tk.Frame(self)
        radio_buttons.grid(row=9, column=0, columnspan=3, pady=(3, 10), padx=(0, 0), sticky="n")  # Adjust the pady values as needed

        # Your radio buttons can be added here. For example:
        self.user_choice_var = tk.IntVar(value=1)  # Set the default value to 1
        tk.Radiobutton(radio_buttons, text="Download New Content (recommended)", variable=self.user_choice_var, value=1).grid(row=0, column=0, sticky="e", padx=(0, 10))
        tk.Radiobutton(radio_buttons, text="Full Sync (slower, but can fix issues)", variable=self.user_choice_var, value=2).grid(row=0, column=1, sticky="w", padx=(50, 0))


        # Create a PanedWindow for resizable terminal window
        terminal_paned = tk.PanedWindow(self, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.SUNKEN)
        terminal_paned.grid(row=11, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Add a Text widget for the terminal with vertical scrollbar
        self.terminal_frame = tk.Frame(self)
        self.terminal_text = tk.Text(self.terminal_frame, height=17, width=120, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = tk.Scrollbar(self.terminal_frame, command=self.terminal_text.yview)
        self.terminal_text.configure(yscrollcommand=scrollbar.set)

        # Pack the widgets
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal_frame.grid(row=11, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
       
        # Insert the warning text
        self.terminal_text.insert(tk.END, "!!! ATTENTION !!! This Run Sync tool is only intented to be used for updates AFTER you have completed the initial installation. If you are attemping to do a first time download/install of the textures pack, click the 'Fresh Install' button at the bottom right of this screen.\n")
        self.terminal_text.yview(tk.END)  # Scroll to the end to make the new text visible



        tk.Label(self, text="PUT ALL OF YOUR CUSTOM TEXTURES AND DLC FILES\nIN '- 1 2 user-customs' OR THEY WILL BE DELETED!", font=('TkDefaultFont', 13, 'bold'), fg="red", justify="left").grid(row=12, column=0, columnspan=2, pady=(0, 0))
        tk.Label(self, text="When using custom files, leave the default textures in place and\ndisable them by prepending the name with a dash (eg. '-file.png').", font=('TkDefaultFont', 12), justify="left").grid(row=13, column=0, columnspan=2,  padx=(20, 0), pady=(0, 5))

        user_choice = "full_scan" if self.user_choice_var.get() == 2 else "only_new_content"
        def main_sync_wrapper(event):
            self.terminal_text.delete(1.0, tk.END)
            thread = Thread(target=main_sync, args=(user_choice, self.terminal_text))
            thread.start()
        


        # Create a Canvas
        self.canvas = tk.Canvas(self, width=150, height=40, highlightthickness=0)
        self.canvas.grid(row=12, column=2, rowspan=2, sticky="w", pady=(0, 0))

        # Create a rounded rectangle on the canvas
        rounding = 10
        self.button_bg = self.create_rounded_rectangle(0, 0, 148, 38, rounding, fill='#cccccc', outline="black")  # Set a different background color
        text_id = self.canvas.create_text(75, 20, text="Run Sync", fill="black", font=('TkDefaultFont', 16, 'bold'))

        # Bind events to the canvas items (rounded rectangle and text)
        self.canvas.tag_bind(self.button_bg, "<Enter>", self.on_enter)
        self.canvas.tag_bind(self.button_bg, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.button_bg, "<Button-1>", main_sync_wrapper)


        self.canvas.tag_bind(text_id, "<Enter>", self.on_enter)
        self.canvas.tag_bind(text_id, "<Leave>", self.on_leave)
        self.canvas.tag_bind(text_id, "<Button-1>", main_sync_wrapper)

        # Set the cursor when hovering
        self.canvas.bind("<Enter>", lambda event: self.canvas.config(cursor="hand2"))
        self.canvas.bind("<Leave>", lambda event: self.canvas.config(cursor=""))




        # Debug mode checkbox
        debug_mode_checkbox = tk.Checkbutton(self,
                    text='Debug Mode',
                    command=self.toggle_debug_mode,
                    variable=self.debug_mode_var,  # Use self.debug_mode_var here
                    onvalue=True,
                    offvalue=False)
        debug_mode_checkbox.grid(row=0, column=0, padx=10, pady=10)

        
        # Divider
        ttk.Separator(self, orient="horizontal").grid(row=18, column=0, columnspan=3, pady=10, sticky="ew") 

        # Debug mode toggle
        debug_mode_checkbox.grid(row=19, column=0, padx=(20, 5), pady=(0, 10), sticky="w")

        # Go to new install screen
        link_label = tk.Label(self, text="Fresh Install →", cursor="hand2", underline=True)
        link_label.grid(row=19, column=2, padx=(5, 20), pady=(0, 10), sticky="e")
        # Bind the label to the function that should be executed on click
        link_label.bind("<Button-1>", lambda event: switch_func())
    
    def on_enter(self, event):
        self.canvas.itemconfig(self.button_bg, fill='lightblue')

    def on_leave(self, event):
        self.canvas.itemconfig(self.button_bg, fill='#cccccc')  # Set it back to the default color

    def create_rounded_rectangle(self, x1, y1, x2, y2, rounding, **kwargs):
        return self.canvas.create_polygon(
            x1, y1 + rounding,
            x1, y1 + rounding,
            x1, y1,
            x1 + rounding, y1,
            x2 - rounding, y1,
            x2, y1,
            x2, y1 + rounding,
            x2, y2 - rounding,
            x2, y2,
            x2 - rounding, y2,
            x1 + rounding, y2,
            x1, y2,
            x1, y2 - rounding,
            x1, y1 + rounding,
            smooth=True,
            **kwargs
        )
      
    def run_main(self, event):
        user_choice = "full_scan" if self.user_choice_var.get() == 2 else "only_new_content"
        run_subprocess('utils/main.py', user_choice, self.terminal_text, self.master)

    def run_deep_scan(self):
        user_choice = "full_scan" if self.user_choice_var.get() == 2 else "only_new_content"
        run_subprocess('utils/fullscan.py', user_choice, self.terminal_text, self.master)  # Pass terminal_text parameter for deep scan

    def on_save_button_click(self, config_dict, button, master):
        # Call the mixin's on_save_button_click method
        super().on_save_button_click(config_dict, button, master)
        config_manager = ConfigManager()
        # Access configuration variables
        debug_mode = config_manager.debug_mode
        initial_setup_done = config_manager.initial_setup_done
        local_directory = config_manager.local_directory
        github_token = config_manager.github_token
        last_run_date = config_manager.last_run_date
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.insert(tk.END, "\n\nVariables updated. RESTART THE APP TO APPLY.\n\n")
        self.terminal_text.yview(tk.END) 
        self.terminal_text.see(tk.END)




class InstallerScreen(tk.Frame, DebugModeMixin, OnSaveButtonClickMixin):
    def __init__(self, master, switch_func):
        tk.Frame.__init__(self, master)
        self.config_manager = ConfigManager()

        self.master.title(f"{project_name} Textures Installer")
        self.master.minsize(900, 800)

        # Create a boolean variable to store the checkbox state of debug_mode
        self.debug_mode_var = tk.BooleanVar(value=self.config_manager.debug_mode)

        def open_hyperlink(event):
            import webbrowser
            webbrowser.open(release_url)

        def get_free_disk_space(directory="/"):
            try:
                disk_info = psutil.disk_usage(directory)
                free_space_gb = disk_info.free / (1024 ** 3)  # Convert bytes to gigabytes
                return free_space_gb
            except PermissionError:
                # Handle permission error gracefully
                print(f"Permission error: Unable to access disk space information for {directory}")
                return None

        def run_installer():
            user_choice = "whatever"
            run_subprocess('utils/download_repo.py', user_choice, self.terminal_text, self.master)  

              
        # Configure columns to expand with the window
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)



        # Create a PanedWindow for resizable terminal window
        terminal_paned = tk.PanedWindow(self, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.SUNKEN)
        terminal_paned.grid(row=8, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Add a Text widget for the terminal with vertical scrollbar
        self.terminal_frame = tk.Frame(self)
        self.terminal_text = tk.Text(self.terminal_frame, height=13, width=120, wrap=tk.WORD, padx=10, pady=10)
        scrollbar = tk.Scrollbar(self.terminal_frame, command=self.terminal_text.yview)
        self.terminal_text.configure(yscrollcommand=scrollbar.set)

        # Pack the widgets
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal_frame.grid(row=8, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Adjust the column weight for the terminal_frame
        self.terminal_frame.columnconfigure(0, weight=1)

        
        try:
            # Fetch the JSON data from the URL
            json_url = self.config_manager.json_url
            response = requests.get(json_url)
            response.raise_for_status()

            # Parse the JSON data
            json_data = response.json()

            # About this release
            version = json_data.get("version")
            release_date = json_data.get("release_date")
            release_url = json_data.get("release_url")
            total_size_gb = json_data.get("total_size")
            largest_size_gb = json_data.get("temp_size")
            

            self.terminal_text.insert(tk.END, f"Internet connection test passed. Remote JSON data retrieved. Ready to proceed.")
            # self.terminal_text.insert(tk.END, json_data)
            self.terminal_text.see(tk.END)  # Scroll to the end
            self.terminal_text.update()
        
        except Exception as e:
            # print(f"Error fetching JSON data: {str(e)}")
            self.terminal_text.insert(tk.END, f"Error fetching remote JSON data (debug info: {str(e)})")
            self.terminal_text.see(tk.END)  # Scroll to the end
            self.terminal_text.update()

        # Heading
        heading_label = tk.Label(self, text="First Time Setup – Textures Installation", font=('TkDefaultFont', 18, 'bold'), justify="center")
        heading_label.grid(row=0, column=0, columnspan=3, pady=(10,0))
        # Subheading
        subheading_label = tk.Label(self, text=f"{project_name} Version {version} • {release_date}", font=('TkDefaultFont', 12))
        subheading_label.grid(row=1, column=0, columnspan=3, pady=(0,5))

        # Create a hyperlink label
        hyperlink_label = ttk.Label(self, text="View Release Notes and Instructions", font=('TkDefaultFont', 11), cursor="hand2")
        hyperlink_label.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        # Bind the label to the callback function
        hyperlink_label.bind("<Button-1>", open_hyperlink)

        # Body copy
        description_text = "This utility will download all of the required textures packs and extract them in the proper order into your emulator's textures folder. This is a very large download and requires multiple GBs of free disk space  (see below for details). Don't proceed unless you have the necessary space and the time to leave this window open to complete the downloads. Depending on your internet speed, this could take up to a few hours." 
        description = tk.Label(self, text=description_text, justify=tk.LEFT, wraplength=750)
        description.grid(row=3, column=0, columnspan=3, pady=(0,10))

        # Path to Replacements
        local_directory_entry_first_label = tk.Label(self, text="Enter the full path to your emulator's TEXTURES FOLDER, click Save Config, and restart this app.", font=('TkDefaultFont', 13, 'bold'), justify="center").grid(row=4, column=0, columnspan=3, sticky="n", padx=(0, 0))
        local_directory_entry_first_label2 = tk.Label(self, text="Find this in PCSX2 > Settings > Graphics > Texture Replacements.", font=('TkDefaultFont', 13), justify="center").grid(row=5, column=0, columnspan=3, sticky="n", padx=(0, 0))
        local_directory_entry_first_label3 = tk.Label(self, text=r"Copy that path exactly as-is. Example: C:\Whatever\PCSX2\textures", font=('TkDefaultFont', 13), justify="center").grid(row=6, column=0, columnspan=3, sticky="n", padx=(0, 0))
        

        # Create a frame for input and button
        input_frame = tk.Frame(self)
        input_frame.grid(row=7, columnspan=3, column=0, pady=(3, 10), padx=(0, 0), sticky="nsew")  # Adjust the pady values as needed

        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(2, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)

        # Local Directory / Path to Textures
        local_directory_entry_first_label4 = tk.Label(input_frame, text="Full Path to Textures Folder:", font=('TkDefaultFont', 13, 'bold'), justify="left").grid(row=0, column=0, columnspan=1, sticky="w", padx=(20, 0), pady=3)
        local_directory_entry_first = tk.Entry(input_frame, width=50, justify="left")
        local_directory_entry_first.grid(row=0, column=1, columnspan=3, sticky="nsew", padx=(5, 0), ipady=3)
        local_directory_entry_first.insert(0, local_directory)
        
        # Check if Path to Textures is provided in the config file
        self.path_to_replacements_label = tk.Label(input_frame, text=f"Enter the full path to TEXTURES FOLDER. Example: C:\\Whatever\\PCSX2\\textures", font=('TkDefaultFont', 12), fg="red", justify="left", wraplength=450)
        if not local_directory:  
            self.path_to_replacements_label.grid(row=1, column=1, columnspan=2, pady=(0, 10), padx=(5, 0), sticky="w")

        # Github Token
        github_token_entry_label = tk.Label(input_frame, text="Github Personal Access Token:", font=('TkDefaultFont', 13, 'bold'), justify="left").grid(row=2, column=0, columnspan=1, sticky="w", padx=(20, 0), pady=3)
        github_token_entry = tk.Entry(input_frame, width=50, justify="left")
        github_token_entry.grid(row=2, column=1, columnspan=3, sticky="nsew", padx=(5, 0), ipady=3)
        github_token_entry.insert(0, github_token)

        # Check if Github Token is provided in the config file
        self.github_token_label = tk.Label(input_frame, text=f"An API token is required. Log in (or create a free account) to Github.com and go to (profile pic at top right) > Settings > Developer Settings > Personal Access Tokens.", font=('TkDefaultFont', 11), fg="red", justify="left", wraplength=450)
        if not github_token: 
            self.github_token_label.grid(row=3, column=1, columnspan=2, pady=(0, 10), padx=(5, 0), sticky="w")
        
        # Create a StringVar for initial_setup_done because it doesn't have an entry field
        initial_setup_var = tk.StringVar(value="False")  # Set the initial value as needed

        # Save Button Next to Input Field
        # config_dict = {"local_directory": local_directory_entry_first, "github_token": github_token_entry, "initial_setup_done": initial_setup_var}
        config_dict = {"local_directory": local_directory_entry_first, "github_token": github_token_entry}
        save_button_next_to_input = tk.Button(input_frame, text="Save Config", command=lambda: self.on_save_button_click(config_dict, save_button_next_to_input, self), justify="left", width=12, cursor="hand2")
        save_button_next_to_input.grid(row=0, column=4, rowspan=4,pady=(0, 3), padx=(5, 25), sticky="w")


        # Create a frame for the buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=9, columnspan=3, column=0, pady=(0, 10))  # Adjust the pady values as needed

        try:
            # Function to get the color based on free disk space
            def get_text_color():
                free_space = get_free_disk_space()
                if free_space is not None:
                    return "green" if free_space > total_size_gb else "red"
                return "black"  # Default color

            # Display the "Requires <total_dl_size> GB free disk space" message
            if get_free_disk_space() is not None:
                requirement_label = tk.Label(button_frame, text=f"Requires {total_size_gb:.2f} GB free disk space (including {largest_size_gb:.2f} GB of temporary space)\nYou have {get_free_disk_space():.2f} GB free.")
            else:
                requirement_label = tk.Label(button_frame, text=f"Requires {total_size_gb:.2f} GB free disk space (including {largest_size_gb:.2f} GB of temporary space).")

            # Get the text color based on free disk space
            text_color = get_text_color()


            # Apply the text color to the label
            requirement_label.grid(row=0, column=0)
            requirement_label.config(fg=text_color)

            def download_repo_main_wrapper():
                self.terminal_text.delete(1.0, tk.END)
                thread = Thread(target=download_repo_main, args=(json_url, local_directory, slus_folder, self.terminal_text))
                thread.start()
            
            bold_font = ('TkDefaultFont', 15, 'bold')  # Adjust the font details as needed
            download_button = tk.Button(
                button_frame,
                text="Begin Installation",
                command=download_repo_main_wrapper,
                cursor="hand2",
                width=20, 
                height=2,
                font=bold_font
            )
            download_button.grid(row=1, column=0)
            
            # Display a message and disable the button based on the text_color
            if text_color == "red":
                message = "Not enough free disk space to proceed."
                if debug_mode == False:
                    download_button.config(state=tk.DISABLED)
            elif text_color == "green":
                message = "You have enough disk space. Do you have the time to let this run?"
                download_button.config(state=tk.NORMAL)  # Ensure the button is enabled
            else:
                message = "Error determining free disk space."

            # Display the message below the button
            message_label = tk.Label(button_frame, text=message)
            message_label.grid(row=2, column=0, pady=(5, 20))


            # Divider
            ttk.Separator(self, orient="horizontal").grid(row=10, column=0, columnspan=3, pady=15, sticky="ew") 



            # Debug mode checkbox
            debug_mode_checkbox = tk.Checkbutton(self,
                        text='Debug Mode',
                        command=self.toggle_debug_mode,
                        variable=self.debug_mode_var,
                        onvalue=True,
                        offvalue=False)

            debug_mode_checkbox.grid(row=11, column=0, padx=(20, 5), pady=(5, 20), sticky="w")


            
            # Go to post-install updtaer screen
            link_label = tk.Label(self, text="Post-Install Updater →", cursor="hand2", underline=True)
            link_label.grid(row=11, column=2, padx=(5, 20), pady=(5, 20), sticky="e")
            # Bind the label to the function that should be executed on click
            link_label.bind("<Button-1>", lambda event: switch_func())

            

        except Exception as e:
            # print(f"Error fetching JSON data: {str(e)}")
            self.terminal_text.insert(tk.END, f"Error (debug info: {str(e)})")
            self.terminal_text.see(tk.END)  # Scroll to the end
            self.terminal_text.update()



        # Your widgets for screen 2
        # tk.Button(self, text="Switch to Post-Install Updater", command=switch_func).grid(row=1, column=0)

    def on_save_button_click(self, config_dict, button, master):
        # Call the mixin's on_save_button_click method
        super().on_save_button_click(config_dict, button, master)
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.insert(tk.END, "\n\nVariables updated. RESTART THE APP TO APPLY.\n\n")
        self.terminal_text.yview(tk.END) 
        self.terminal_text.see(tk.END)
  




class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # Initialize current_frame attribute
        self.current_frame = None

        # Use the existing boolean variable initial_setup_done
        if not initial_setup_done:
            # Initial setup not done, load InstallerScreen
            self.switch_frame(InstallerScreen)
        else:
            # Initial setup done, load PostInstallScreen
            self.switch_frame(PostInstallScreen)

    def switch_frame(self, frame_class):
        new_frame = frame_class(self, lambda: self.switch_frame(PostInstallScreen if frame_class == InstallerScreen else InstallerScreen))

        if self.current_frame:
            self.current_frame.grid_forget()

        self.current_frame = new_frame
        self.current_frame.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()