import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, simpledialog
from urllib.parse import urlparse
import requests
from pathlib import Path
from tkinter.font import Font
from datetime import datetime
import zipfile
import shutil
import webbrowser
from PIL import Image, ImageTk
import io
import re

class WebFishingModManager:
    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self, config):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
    def __init__(self, root):
        self.root = root
        self.root.title("WebLoader 1.1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configuration file path
        self.config_path = os.path.join(os.getenv('APPDATA'), 'WebLoader', 'config.json')
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Color scheme
        self.bg_color = "#2d2d2d"
        self.card_bg = "#3a3a3a"
        self.text_color = "#ffffff"
        self.accent_color = "#4a8fe7"
        self.secondary_color = "#5e5e5e"
        self.success_color = "#4CAF50"
        self.error_color = "#F44336"
        self.warning_color = "#FFC107"
        
        self.root.configure(bg=self.bg_color)
        
        # Fonts
        self.title_font = Font(family="Segoe UI", size=12, weight="bold")
        self.text_font = Font(family="Segoe UI", size=10)
        self.button_font = Font(family="Segoe UI", size=10, weight="bold")
        self.console_font = Font(family="Consolas", size=9)
        
        # Variables
        self.download_folder = tk.StringVar(value=os.path.join(os.getcwd(), "webfishing_mods"))
        self.mod_urls = []
        self.download_thread = None
        self.is_downloading = False
        self.current_mods = []
        self.current_mod_images = {}
        
        # Configure styles
        self.configure_styles()
        
        # Build UI
        self.create_ui()
        
        # Load config
        self.config = self.load_config()

        # Load initial mod list
        self.refresh_mod_browser()

        # Show welcome popup and GDWeave check if not disabled
        if not self.config.get("suppress_welcome_popup", False):
            self.root.after(300, self.show_welcome_and_gdweave_prompt)

    def show_welcome_and_gdweave_prompt(self):
        """Show a styled welcome popup and ask about GDWeave installation (no 'don't ask again' logic)."""
        # Create a dim overlay
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_rootx()}+{self.root.winfo_rooty()}")
        overlay.attributes("-alpha", 0.5)
        overlay.configure(bg="#000000")
        overlay.lift()
        overlay.transient(self.root)
        overlay.grab_set()

        # Create the styled popup window without window decorations (no white bar)
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)  # Remove window decorations
        popup.configure(bg="#23272e")
        popup.lift(overlay)
        popup.transient(self.root)
        popup.grab_set()
        popup.resizable(False, False)

        # Center the popup
        popup.update_idletasks()
        w, h = 420, 340
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (w // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        # --- Popup Content ---
        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # Add close "X" button in the top right
        def close_popup():
            popup.destroy()
            overlay.destroy()

        close_btn = tk.Button(
            popup,
            text="✕",
            command=close_popup,
            bg="#23272e",
            fg="#888",
            borderwidth=0,
            font=("Segoe UI", 12, "bold"),
            activebackground="#23272e",
            activeforeground="#fff",
            cursor="hand2"
        )
        close_btn.place(x=w-32, y=8, width=24, height=24)

        # Make the X turn red on hover
        def on_enter(event):
            close_btn.config(fg="#ff4444")
        def on_leave(event):
            close_btn.config(fg="#888")
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)

        title = ttk.Label(frame, text="Welcome to WebLoader 1.1.0", font=self.title_font, foreground=self.accent_color, background="#23272e")
        title.pack(pady=(0, 10))

        flavor = (
            "The all-in-one mod manager for WebFishing.\n"
            "Browse, install, and manage your mods with ease.\n\n"
            "Before you start, you need GDWeave installed in your game folder.\n"
            "Do you already have GDWeave installed?"
        )
        label = ttk.Label(frame, text=flavor, wraplength=370, justify="left", foreground=self.text_color, font=self.text_font)
        label.pack(pady=(0, 20))
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=(10, 0))

        # Don't show again checkbox
        dont_show_var = tk.BooleanVar(value=False)
        dont_show_chk = ttk.Checkbutton(frame, text="Don't show this again", variable=dont_show_var)
        dont_show_chk.pack(pady=(10, 0))

        def on_yes():
            if dont_show_var.get():
                self.config["suppress_welcome_popup"] = True
                self.save_config(self.config)
            popup.destroy()
            overlay.destroy()

        def on_no():
            if dont_show_var.get():
                self.config["suppress_welcome_popup"] = True
                self.save_config(self.config)
            popup.destroy()
            overlay.destroy()
            self.install_gdweave()

        yes_btn = ttk.Button(button_frame, text="Yes, I have GDWeave", command=on_yes, style='Accent.TButton')
        yes_btn.pack(side=tk.LEFT, padx=(0, 10))
        no_btn = ttk.Button(button_frame, text="No, install it for me", command=on_no, style='Secondary.TButton')
        no_btn.pack(side=tk.LEFT)

        # Make sure popup is modal
        popup.wait_window()

    def save_dont_ask_again(self, config_path):
        """Save the 'don't ask again' flag to config file."""
        try:
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
            config["dont_ask_gdweave"] = True
            with open(config_path, "w") as f:
                json.dump(config, f)
        except Exception:
            pass
    def configure_styles(self):
        """Configure ttk styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Base styles
        style.configure('.', 
                    background=self.bg_color,
                    foreground=self.text_color,
                    font=self.text_font,
                    borderwidth=0,
                    relief=tk.FLAT)
        
        # Custom styles
        style.configure('Card.TFrame',
                      borderwidth=1,
                      relief=tk.RAISED)
        
        style.configure('Title.TLabel',
                      font=self.title_font,
                      background=self.bg_color,
                      foreground=self.accent_color)
        
        style.configure('TEntry',
                      fieldbackground=self.card_bg,
                      foreground=self.text_color,
                      insertcolor=self.text_color,
                      borderwidth=0,
                      relief=tk.FLAT,
                      padding=5)
        
        style.configure('TCombobox',
                      fieldbackground=self.card_bg,
                      foreground=self.text_color,
                      selectbackground=self.accent_color,
                      selectforeground=self.text_color,
                      borderwidth=0,
                      relief=tk.FLAT,
                      padding=5)
        
        style.map('TCombobox',
                fieldbackground=[('readonly', self.card_bg)],
                selectbackground=[('readonly', self.accent_color)],
                selectforeground=[('readonly', self.text_color)])
        
        style.configure('TButton',
                      font=self.button_font,
                      background=self.secondary_color,
                      foreground=self.text_color,
                      borderwidth=0,
                      focusthickness=3,
                      focuscolor=self.accent_color,
                      padding=6)
        
        style.configure('Accent.TButton',
                      background=self.accent_color,
                      foreground=self.text_color)
        
        style.configure('Secondary.TButton',
                      background=self.secondary_color,
                      foreground=self.text_color)
        
        style.configure('Treeview',
                      background=self.card_bg,
                      foreground=self.text_color,
                      fieldbackground=self.card_bg,
                      borderwidth=0,
                      relief=tk.FLAT,
                      rowheight=25)
        
        style.map('Treeview',
                background=[('selected', self.accent_color)],
                foreground=[('selected', '#ffffff')])
        
        style.configure('Vertical.TScrollbar',
                      background=self.secondary_color,
                      troughcolor=self.bg_color,
                      bordercolor=self.bg_color,
                      arrowcolor=self.text_color,
                      gripcount=0)
        
        style.configure('Horizontal.TScrollbar',
                      background=self.secondary_color,
                      troughcolor=self.bg_color,
                      bordercolor=self.bg_color,
                      arrowcolor=self.text_color,
                      gripcount=0)
        
        style.configure('Horizontal.TProgressbar',
                      background=self.accent_color,
                      troughcolor=self.secondary_color,
                      bordercolor=self.bg_color,
                      thickness=10)

    def create_ui(self):
        """Create the main application UI"""
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, 
                text="WebFishing Mod Manager", 
                style='Title.TLabel').pack(side=tk.LEFT)


        launch_frame = ttk.Frame(header_frame)
        launch_frame.pack(side=tk.RIGHT, padx=(0, 5), pady=0)


        launch_steam_button = ttk.Button(
            launch_frame,
            text="Launch Steam",
            command=self.launch_steam,
            style='Secondary.TButton'
        )
        launch_steam_button.pack(side=tk.LEFT, padx=(0, 5))


        launch_button = ttk.Button(
            launch_frame,
            text="Launch WebFishing!",
            command=self.launch_webfishing,
            style='Accent.TButton'
        )
        launch_button.pack(side=tk.LEFT)


        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.create_mod_browser_sidebar(content_frame)
        

        self.create_configuration_panel(content_frame)
        

        self.create_console_panel(content_frame)

    def create_mod_browser_sidebar(self, parent):
        """Create the mod browser sidebar with improved scrollable mod details"""
        browser_sidebar = ttk.Frame(parent, width=300)
        browser_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        browser_sidebar.pack_propagate(False)

        browser_card = ttk.LabelFrame(browser_sidebar, text="WebFishing Mod Browser", style='Card.TFrame')
        browser_card.pack(fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(browser_card)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self.search_mods())
        
        search_button = ttk.Button(search_frame, text="🔍", command=self.search_mods, 
                                style='Secondary.TButton', width=3)
        search_button.pack(side=tk.LEFT)
        
        category_frame = ttk.Frame(browser_card)
        category_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(category_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(category_frame, textvariable=self.category_var, 
                                            values=["Popular", "Recently Updated", "Newest"])
        self.category_combobox.pack(fill=tk.X, expand=True)
        self.category_combobox.set("Popular")
        self.category_combobox.bind("<<ComboboxSelected>>", lambda e: self.search_mods())
        
        mod_list_frame = ttk.Frame(browser_card)
        mod_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.mod_tree = ttk.Treeview(mod_list_frame, columns=("name", "author"), 
                                show="headings", height=8)
        self.mod_tree.heading("name", text="Mod Name")
        self.mod_tree.heading("author", text="Author")
        self.mod_tree.column("name", width=150, anchor="w")
        self.mod_tree.column("author", width=100, anchor="w")

        mod_list_vsb = ttk.Scrollbar(mod_list_frame, orient="vertical", command=self.mod_tree.yview)
        self.mod_tree.configure(yscrollcommand=mod_list_vsb.set)
        
        self.mod_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mod_list_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.mod_tree.bind("<<TreeviewSelect>>", self.show_mod_details)
        

        self.mod_details_frame = ttk.LabelFrame(browser_card, text="Mod Details")
        self.mod_details_frame.pack(fill=tk.BOTH, pady=(5, 0))
        

        details_main_frame = ttk.Frame(self.mod_details_frame)
        details_main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.details_canvas = tk.Canvas(
            details_main_frame,
            bg=self.card_bg,
            highlightthickness=0
        )
        

        self.details_scrollbar = ttk.Scrollbar(
            details_main_frame,
            orient="vertical",
            command=self.details_canvas.yview
        )
        

        self.scrollable_details_frame = ttk.Frame(
            self.details_canvas,
        )

        self.canvas_window = self.details_canvas.create_window(
            (0, 0),
            window=self.scrollable_details_frame,
            anchor="nw"
        )
        
        self.details_canvas.configure(yscrollcommand=self.details_scrollbar.set)
        

        self.details_canvas.pack(side="left", fill="both", expand=True)
        self.details_scrollbar.pack(side="right", fill="y")
        

        def configure_scrollable_frame(event):

            self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
            

            canvas_width = event.width
            self.details_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_details_frame.bind("<Configure>", configure_scrollable_frame)
        

        def _on_mousewheel(event):
            self.details_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            self.details_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            self.details_canvas.unbind_all("<MouseWheel>")
        
        self.details_canvas.bind('<Enter>', _bind_mousewheel)
        self.details_canvas.bind('<Leave>', _unbind_mousewheel)
        

        def configure_canvas_window(event):
            canvas_width = event.width
            self.details_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.details_canvas.bind('<Configure>', configure_canvas_window)
        

        self.mod_image_label = ttk.Label(self.scrollable_details_frame, width=15, text="")
        self.mod_image_label.pack(pady=5)
        

        self.create_placeholder_image()
        

        self.mod_name_label = ttk.Label(self.scrollable_details_frame, font=self.title_font)
        self.mod_name_label.pack(pady=(0, 2))
        
        self.mod_author_label = ttk.Label(self.scrollable_details_frame, foreground=self.secondary_color)
        self.mod_author_label.pack(pady=(0, 2))
        
        self.mod_version_label = ttk.Label(self.scrollable_details_frame)
        self.mod_version_label.pack(pady=(0, 2))
        
        self.mod_downloads_label = ttk.Label(self.scrollable_details_frame)
        self.mod_downloads_label.pack(pady=(0, 2))
        
        self.mod_description_label = ttk.Label(
            self.scrollable_details_frame,
            wraplength=240,
            justify=tk.LEFT
        )
        self.mod_description_label.pack(pady=5, padx=5)
        

        self.mod_requirements_label = ttk.Label(
            self.scrollable_details_frame,
            wraplength=240,
            justify=tk.LEFT,
            foreground=self.warning_color
        )
        self.mod_requirements_label.pack(pady=(0, 5), padx=5)

        button_frame = ttk.Frame(self.scrollable_details_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.add_button = ttk.Button(
            button_frame,
            text="Add to List",
            command=self.add_selected_mod,
            style='Accent.TButton'
        )
        self.add_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.view_button = ttk.Button(
            button_frame,
            text="View In Thunderstore",
            command=self.view_mod_on_web,
            style='Secondary.TButton'
        )
        self.view_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        self.clear_mod_details()

    def clear_mod_details(self):
        """Clear the mod details display"""
        self.mod_name_label.config(text="Select a WebFishing mod")
        self.mod_author_label.config(text="")
        self.mod_version_label.config(text="")
        self.mod_downloads_label.config(text="")
        self.mod_description_label.config(text="Browse and select a mod from the list above to view details.")
        self.mod_requirements_label.config(text="")


        self.mod_image_label.config(image=self.placeholder_image, text='')
        self.mod_image_label.image = self.placeholder_image

        self.add_button.config(state='disabled')
        self.view_button.config(state='disabled')

        self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))

    def _update_canvas_after_clear(self):
        """Helper method to update canvas size after clearing content"""
        self.details_canvas.update_idletasks()

        self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        

        canvas_height = self.details_canvas.winfo_height()
        self.details_canvas.itemconfig(self.canvas_window, height=max(canvas_height, 280))

    def create_placeholder_image(self):
        """Create a placeholder image that maintains consistent size"""
        try:

            placeholder_img = Image.new('RGBA', (120, 120), (self.secondary_color.lstrip('#'), 0))
            

            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(placeholder_img)

            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            

            text = "No Image"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = (120 - text_width) // 2
            text_y = (120 - text_height) // 2
            

            draw.rectangle([10, 10, 110, 110], fill=(60, 60, 60, 128), outline=(100, 100, 100, 255))

            draw.text((text_x, text_y), text, fill=(200, 200, 200, 255), font=font)
            
            self.placeholder_image = ImageTk.PhotoImage(placeholder_img)
            
        except Exception as e:

            placeholder_img = Image.new('RGB', (120, 120), (60, 60, 60))
            self.placeholder_image = ImageTk.PhotoImage(placeholder_img)

    def load_mod_image(self, image_url):
        """Load and display the mod's icon image with fixed size placeholder"""

        self.mod_image_label.config(image=self.placeholder_image, text='')
        self.mod_image_label.image = self.placeholder_image
        
        if not image_url:
            return

        if image_url in self.current_mod_images:
            img = self.current_mod_images[image_url]
            self.mod_image_label.config(image=img, text='')
            self.mod_image_label.image = img
            return
            
        def fetch_image():
            try:
                response = requests.get(image_url, timeout=10, 
                                    headers={'User-Agent': 'WebFishing Mod Manager/1.0'})
                
                if response.status_code == 200:
                    image_data = response.content
                    img = Image.open(io.BytesIO(image_data))
                    

                    img = img.resize((120, 120), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    

                    self.current_mod_images[image_url] = photo_img
                    

                    self.root.after(0, lambda: self.update_mod_image(photo_img))
                else:

                    pass
                    
            except Exception as e:

                self.log(f"Failed to load mod image: {str(e)}", "warning")

    def update_mod_image(self, photo_img):
        """Update the mod image on the main thread"""
        self.mod_image_label.config(image=photo_img, text='')
        self.mod_image_label.image = photo_img

    def clear_mod_details(self):
        """Clear the mod details display"""
        self.mod_name_label.config(text="Select a WebFishing mod")
        self.mod_author_label.config(text="")
        self.mod_version_label.config(text="")
        self.mod_downloads_label.config(text="")
        self.mod_description_label.config(text="Browse and select a mod from the list above to view details.")
        self.mod_requirements_label.config(text="", image='')

        self.add_button.config(state='disabled')
        self.view_button.config(state='disabled')

        self.details_canvas.configure(bg=self.card_bg)
        self.scrollable_details_frame.configure()
        self.details_canvas.update_idletasks()
        self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))

    def _update_canvas_after_clear(self):
        """Helper method to update canvas size after clearing content"""
        self.details_canvas.update_idletasks()
        bbox = self.details_canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]

            new_height = min(max(content_height, 100), 300)
            self.details_canvas.configure(height=new_height)
        else:

            self.details_canvas.configure(height=100)

        self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))

    def create_configuration_panel(self, parent):
        """Create the configuration and mod list panel"""
        left_panel = ttk.Frame(parent)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        

        config_card = ttk.LabelFrame(left_panel, text="Configuration")
        config_card.pack(fill=tk.X, pady=(0, 10))
        
        folder_frame = ttk.Frame(config_card)
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_frame, text="Mods Folder:").pack(side=tk.LEFT, padx=(5, 5))
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.download_folder)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        folder_button = ttk.Button(folder_frame, text="Browse...", command=self.browse_folder, style='Secondary.TButton')
        folder_button.pack(side=tk.LEFT)

        url_card = ttk.LabelFrame(left_panel, text="Add WebFishing Mods")
        url_card.pack(fill=tk.X, pady=(0, 10))
        
        url_entry_frame = ttk.Frame(url_card)
        url_entry_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(url_entry_frame, text="Mod URL:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.url_entry = ttk.Entry(url_entry_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.url_entry.bind("<Return>", lambda e: self.add_url())
        
        add_button = ttk.Button(url_entry_frame, text="Add Mod", command=self.add_url, style='Secondary.TButton')
        add_button.pack(side=tk.LEFT)
        

        import_zip_button = ttk.Button(
            url_entry_frame,
            text="Import .zip",
            command=self.import_zip,
            style='Secondary.TButton'
        )
        import_zip_button.pack(side=tk.LEFT, padx=(5, 0))
        
        help_text = "Enter WebFishing mod URLs or browse and add from the sidebar"
        ttk.Label(url_card, text=help_text, foreground=self.secondary_color).pack(anchor="w")
        

        list_card = ttk.LabelFrame(left_panel, text="WebFishing Mod List")
        list_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tree_container = ttk.Frame(list_card)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.url_tree = ttk.Treeview(tree_container, columns=("url", "name"), show="headings")
        self.url_tree.heading("url", text="Mod URL")
        self.url_tree.heading("name", text="Mod Name")
        self.url_tree.column("url", width=400, anchor="w")
        self.url_tree.column("name", width=150, anchor="w")
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.url_tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.url_tree.xview)
        self.url_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.url_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)
        

        action_frame = ttk.Frame(left_panel)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        left_actions = ttk.Frame(action_frame)
        left_actions.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.gdweave_button = ttk.Button(
            left_actions,
            text="Install GDWeave",
            command=self.install_gdweave,
            style='Secondary.TButton'
        )
        self.gdweave_button.pack(side=tk.LEFT, padx=(0, 5))

        load_preset_button = ttk.Button(left_actions, text="Load Preset", command=self.load_preset, style='Secondary.TButton')
        load_preset_button.pack(side=tk.LEFT, padx=(0, 5))

        save_preset_button = ttk.Button(left_actions, text="Save Preset", command=self.save_preset_as, style='Secondary.TButton')
        save_preset_button.pack(side=tk.LEFT, padx=(0, 5))

        remove_button = ttk.Button(left_actions, text="Remove Selected", command=self.remove_selected, style='Secondary.TButton')
        remove_button.pack(side=tk.LEFT, padx=(0, 5))

        clear_button = ttk.Button(left_actions, text="Clear All", command=self.clear_list, style='Secondary.TButton')
        clear_button.pack(side=tk.LEFT)
        
        self.download_button = ttk.Button(
            left_panel, 
            text="⬇️ Download Mods", 
            command=self.start_download,
            style='Accent.TButton'
        )
        self.download_button.pack(fill=tk.X, pady=(0, 5), padx=(0, 5))
        

        ttk.Frame(left_panel, height=5).pack(fill=tk.X) 
        

        progress_frame = ttk.Frame(left_panel)
        progress_frame.pack(fill=tk.X)

        self.progress = ttk.Progressbar(
            progress_frame, 
            orient="horizontal", 
            mode="determinate", 
            style='Horizontal.TProgressbar'
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(progress_frame, text="  ").pack(side=tk.LEFT)
    def install_gdweave(self):
            """Special handler for installing GDWeave"""

            game_folder = r"C:\Program Files (x86)\Steam\steamapps\common\WEBFISHING"
            

            if not os.path.exists(game_folder):
                messagebox.showerror(
                    "Game Folder Not Found",
                    f"Could not find WebFishing game folder at:\n{game_folder}\n"
                    "Please make sure the game is installed and the path is correct.",
                    parent=self.root
                )
                return
            

            while True:
                response = self.modern_popup(
                    "Install GDWeave",
                    f"GDWeave will be installed to your game folder:\n{game_folder}\n\n"
                    "This will add:\n"
                    "winmm.dll to the game directory\n"
                    "GDWeave folder with core files\n\n"
                    "Continue?",
                    popup_type="question",
                    buttons=("Continue", "Cancel", "Change Installation Path")
                )
                if response == "Continue":
                    break
                elif response == "Cancel":
                    return
                elif response == "Change Installation Path":

                    new_folder = filedialog.askdirectory(
                        title="Select WebFishing Game Folder",
                        initialdir=game_folder,
                        parent=self.root
                    )
                    if new_folder:
                        game_folder = new_folder

                    continue
            
            try:

                temp_folder = os.path.join(game_folder, "temp_gdweave")
                os.makedirs(temp_folder, exist_ok=True)
                

                author = "GDWeave"
                mod_name = "GDWeave"
                gdweave_url = f"https://thunderstore.io/c/webfishing/p/NotNet/GDWeave/"
                
                self.log(f"\n=== Starting GDWeave Installation ===", "info")
                self.log(f"Game Folder: {game_folder}", "info")
                
                session = requests.Session()
                session.headers.update({
                    "User-Agent": "WebFishing Mod Manager/1.0",
                    "Accept": "application/json"
                })

                download_url = None
                filename = f"{author}-{mod_name}.zip"
                

                try:
                    api_url = f"https://thunderstore.io/api/v1/package/{author}/{mod_name}/"
                    response = session.get(api_url, timeout=15)
                    if response.status_code == 200:
                        package_data = response.json()
                        versions = package_data.get('versions', [])
                        if not versions and 'latest' in package_data:
                            versions = [package_data['latest']]
                        
                        if versions:
                            download_url = versions[0].get("download_url")
                            filename = versions[0].get("filename", filename)
                            self.log("✅ Found download URL via API", "success")
                except Exception as e:
                    self.log(f"⚠️ API attempt failed: {str(e)}", "warning")

                if not download_url:
                    try:
                        page_response = session.get(gdweave_url, timeout=15)
                        if page_response.status_code == 200:
                            page_content = page_response.text
                            

                            patterns = [
                                r'href="(https://[^"]*thunderstore[^"]*download[^"]*)"',
                                r'"download_url":"([^"]*)"',
                                r'data-download-url="([^"]*)"',
                                r'/package/download/GDWeave/GDWeave/([^/"]+)',
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, page_content, re.IGNORECASE)
                                if matches:
                                    download_url = matches[0]
                                    if isinstance(download_url, tuple):
                                        download_url = matches[0][0]
                                    
                                    if not download_url.startswith('http'):
                                        download_url = f"https://thunderstore.io{download_url}"
                                    
                                    self.log("✅ Found download URL via page scrape", "success")
                                    break
                    except Exception as e:
                        self.log(f"⚠️ Page scrape failed: {str(e)}", "warning")

                if not download_url:
                    try:

                        version = "1.0.0" 
                        version_match = re.search(r'"version_number":"([^"]+)"', page_content)
                        if version_match:
                            version = version_match.group(1)
                        
                        download_url = f"https://thunderstore.io/package/download/GDWeave/GDWeave/{version}/"
                        self.log("⚠️ Using fallback download URL", "warning")
                    except:
                        pass
                
                if not download_url:
                    self.log("❌ Could not find GDWeave download URL", "error")
                    messagebox.showerror(
                        "Download Error",
                        "Failed to find GDWeave download URL.\n"
                        "Please check your internet connection or try again later.",
                        parent=self.root
                    )
                    return
                

                zip_path = os.path.join(temp_folder, filename)
                self.log(f"📥 Downloading GDWeave from: {download_url}", "info")
                
                try:
                    with session.get(download_url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        total_size = int(r.headers.get('content-length', 0))
                        downloaded_size = 0
                        
                        with open(zip_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if total_size > 0 and int((downloaded_size / total_size) * 100) % 25 == 0:
                                        self.log(f"    Progress: {int((downloaded_size / total_size) * 100)}%", "info")
                    
                    self.log(f"✅ Downloaded: {filename} ({downloaded_size} bytes)", "success")
                    
                except Exception as download_error:
                    self.log(f"❌ Download failed: {str(download_error)}", "error")
                    messagebox.showerror(
                        "Download Failed",
                        f"Failed to download GDWeave:\n{str(download_error)}",
                        parent=self.root
                    )
                    return

                try:
                    with zipfile.ZipFile(zip_path, 'r') as test_zip:
                        test_zip.testzip()
                    self.log("✅ Zip file verified", "info")
                except Exception as zip_error:
                    self.log(f"❌ Invalid zip file: {str(zip_error)}", "error")
                    try:
                        os.remove(zip_path)
                    except:
                        pass
                    return
                

                self.log("📦 Extracting GDWeave...", "info")
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_folder)
                    
                    winmm_src = None
                    gdweave_src = None
                    mods_src = None
                    
                    for root, dirs, files in os.walk(temp_folder):
                        if "winmm.dll" in files:
                            winmm_src = os.path.join(root, "winmm.dll")
                        if "GDWeave" in dirs:
                            gdweave_src = os.path.join(root, "GDWeave")
                        if "mods" in dirs:
                            mods_src = os.path.join(root, "mods")
                        
                        if winmm_src and gdweave_src:
                            break
                    
                    if not winmm_src or not gdweave_src:
                        self.log("❌ Could not find winmm.dll or GDWeave folder in download", "error")
                        messagebox.showerror(
                            "Installation Error",
                            "The downloaded GDWeave package is missing required files.\n"
                            "Please try again or contact the mod author.",
                            parent=self.root
                        )
                        return
                    
                    winmm_dest = os.path.join(game_folder, "winmm.dll")
                    gdweave_dest = os.path.join(game_folder, "GDWeave")
                    mods_dest = os.path.join(gdweave_dest, "mods")
                    
                    if os.path.exists(winmm_dest):
                        backup_path = winmm_dest + ".bak"
                        shutil.copy2(winmm_dest, backup_path)
                        self.log(f"🔁 Backed up existing winmm.dll to {backup_path}", "info")
                    
                    if os.path.exists(gdweave_dest):
                        backup_path = gdweave_dest + ".bak"
                        shutil.copytree(gdweave_dest, backup_path)
                        self.log(f"🔁 Backed up existing GDWeave folder to {backup_path}", "info")
                        shutil.rmtree(gdweave_dest)
                    
                    shutil.copy2(winmm_src, winmm_dest)
                    shutil.copytree(gdweave_src, gdweave_dest)
                    
                    if mods_src and os.path.exists(mods_src):

                        if not os.path.exists(mods_dest):
                            shutil.copytree(mods_src, mods_dest)
                            self.log(f"✅ Copied mods folder from package to: {mods_dest}", "info")
                        else:

                            for item in os.listdir(mods_src):
                                src_item = os.path.join(mods_src, item)
                                dest_item = os.path.join(mods_dest, item)
                                if not os.path.exists(dest_item):
                                    if os.path.isdir(src_item):
                                        shutil.copytree(src_item, dest_item)
                                    else:
                                        shutil.copy2(src_item, dest_item)
                            self.log(f"✅ Merged mods folder content to: {mods_dest}", "info")
                    else:

                        if not os.path.exists(mods_dest):
                            os.makedirs(mods_dest)
                            self.log(f"📁 Created empty mods folder at: {mods_dest}", "info")
                    
                    self.log("✅ Successfully installed GDWeave!", "success")
                    self.log(f"• winmm.dll installed to: {winmm_dest}", "info")
                    self.log(f"• GDWeave folder installed to: {gdweave_dest}", "info")
                    self.log(f"• Mods folder ready at: {mods_dest}", "info")
                    
                    self.modern_popup(
                        "GDWeave Installed!",
                        f"✅ GDWeave has been successfully installed to your game folder:\n\n"
                        f"{game_folder}\n\n"
                        "The following were added:\n"
                        "• winmm.dll to the game directory\n"
                        "• GDWeave folder with core files\n"
                        f"• Mods folder ready at:\n  {game_folder}/GDWeave/mods",
                        popup_type="info",
                        buttons=("OK",),
                        parent=self.root
                    )

                    gdweave_mods_folder = os.path.join(game_folder, "GDWeave", "mods")
                    reversed_folder = gdweave_mods_folder.replace("\\", "/")[::-1].replace("-", "-", 1)[::-1]
                    response = self.modern_popup2(
                        "Set Mods Folder?",
                        f"Would you like to set your mod folder destination to:\n{reversed_folder}?",
                        popup_type="question",
                        buttons=("Yes", "No"),
                        parent=self.root
                    )
                    if response == "Yes":
                        self.download_folder.set(gdweave_mods_folder)
                        
                except Exception as e:

                    error_msg = f"Failed to install GDWeave:\n{str(e)}"
                    import traceback
                    tb = traceback.format_exc()
                    full_msg = f"{error_msg}\n\nDetails:\n{tb}"
                    if len(full_msg) > 400:

                        err_win = tk.Toplevel(self.root)
                        err_win.title("Installation Error")
                        err_win.configure(bg="#23272e")
                        err_win.geometry("600x400")
                        err_win.resizable(True, True)
                        tk.Label(err_win, text="❌ Error installing GDWeave", font=self.title_font, bg="#23272e", fg=self.error_color).pack(pady=(10, 0))
                        st = scrolledtext.ScrolledText(err_win, wrap=tk.WORD, font=self.text_font, bg="#23272e", fg=self.text_color, insertbackground=self.text_color)
                        st.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
                        st.insert(tk.END, full_msg)
                        st.config(state=tk.DISABLED)
                        ttk.Button(err_win, text="Close", command=err_win.destroy, style='Accent.TButton').pack(pady=(0, 12))
                        err_win.transient(self.root)
                        err_win.grab_set()
                        err_win.wait_window()
                    else:
                        self.modern_popup("Installation Error", full_msg, popup_type="error", buttons=("OK",), parent=self.root)
                    self.log(f"Error details:\n{tb}", "error")
                try:
                    shutil.rmtree(temp_folder)
                except Exception as e:
                    self.log(f"⚠️ Could not clean up temp folder: {str(e)}", "warning")
            
            except Exception as e:
                self.log(f"💥 Critical error during GDWeave installation: {str(e)}", "error")
                messagebox.showerror(
                    "Critical Error",
                    f"A critical error occurred during GDWeave installation:\n{str(e)}",
                    parent=self.root
                )

    def create_console_panel(self, parent):
        """Create the console output panel"""
        right_panel = ttk.Frame(parent)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        console_card = ttk.LabelFrame(right_panel, text="Console Output", style='Card.TFrame')
        console_card.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(
            console_card, 
            height=8, 
            wrap=tk.WORD,
            bg=self.card_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=self.console_font,
            relief=tk.FLAT
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.config(state=tk.DISABLED)

    def search_mods(self):
        """Search specifically for WebFishing mods with proper filtering"""
        search_term = self.search_entry.get().strip().lower()
        category = self.category_var.get()
        
        for item in self.mod_tree.get_children():
            self.mod_tree.delete(item)
        
        self.clear_mod_details()
        
        if not hasattr(self, 'current_mods') or not self.current_mods:
            self.log("No mods available to search. Refreshing mod list...", "info")
            self.refresh_mod_browser()
            return
        
        try:
            filtered_mods = []
            
            if search_term:
                for mod in self.current_mods:
                    mod_name = mod.get('name', '').lower()
                    author = mod.get('owner', '').lower()
                    description = mod.get('description', '').lower()
                    
                    if (search_term in mod_name or 
                        search_term in author or 
                        search_term in description):
                        filtered_mods.append(mod)
            else:
                filtered_mods = self.current_mods.copy()
            
            if category == "Popular":
                filtered_mods.sort(key=lambda x: x.get('downloads', 0), reverse=True)
            elif category == "Recently Updated":
                filtered_mods.sort(key=lambda x: x.get('date_updated', ''), reverse=True)
            elif category == "Newest":
                filtered_mods.sort(key=lambda x: x.get('date_created', ''), reverse=True)
            
            for mod in filtered_mods:
                mod_name = mod['name']
                author = mod['owner']
                mod_url = f"https://thunderstore.io/c/webfishing/p/{author}/{mod_name}/"
                
                self.mod_tree.insert("", tk.END, 
                                values=(mod_name, author),
                                tags=(mod_url, json.dumps(mod)))
            
            self.log(f"Displaying {len(filtered_mods)} WebFishing mods", "success")
            
        except Exception as e:
            self.log(f"Failed to filter WebFishing mods: {str(e)}", "error")

    def refresh_mod_browser(self):
        """Refresh the mod browser with default search"""
        try:

            api_url = "https://thunderstore.io/c/webfishing/api/v1/package/"
            params = {
                "page": 1,
                "page_size": 50,
                "ordering": "-downloads" 
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            mods_data = response.json()
            

            if isinstance(mods_data, dict) and "results" in mods_data:
                self.current_mods = mods_data["results"]
            else:
                self.current_mods = mods_data

            self.search_mods()
            
        except Exception as e:
            self.log(f"Failed to fetch WebFishing mods: {str(e)}", "error")
            self.current_mods = []

    def show_mod_details(self, event=None):
        """Show details for the selected WebFishing mod"""
        selected = self.mod_tree.selection()
        if not selected:
            self.clear_mod_details()
            return
        
        try:
            item = self.mod_tree.item(selected[0])
            mod_data = json.loads(item['tags'][1])
            

            mod_name = mod_data.get('name', 'Unknown Mod')
            author = mod_data.get('owner', 'Unknown Author')
            

            latest_version = mod_data.get('latest', {})
            if not latest_version and 'versions' in mod_data and mod_data['versions']:
                latest_version = mod_data['versions'][0]
            
            version = str(latest_version.get('version_number', 'Unknown'))  
            description = latest_version.get('description', 'No description available.')
            icon_url = latest_version.get('icon', '')
            

            downloads = mod_data.get('downloads', 0)
            downloads_text = f"Downloads: {downloads:,}" if isinstance(downloads, int) else f"Downloads: {downloads}"
            

            self.mod_name_label.config(text=str(mod_name)) 
            self.mod_author_label.config(text=f"by {str(author)}")  
            self.mod_version_label.config(text=f"Version: {version}")
            self.mod_downloads_label.config(text=downloads_text)
            

            if description:
                description = re.sub(r'<[^>]+>', '', str(description)) 
                if len(description) > 200:
                    description = description[:200].rsplit(' ', 1)[0] + "..."
            else:
                description = "No description available."
                
            self.mod_description_label.config(text=description)
            

            if icon_url:
                self.load_mod_image(str(icon_url)) 
            else:
                self.mod_image_label.config(text="No Image", image='')
                
            requirements = []
            if "dependencies" in latest_version:
                requirements = [str(dep) for dep in latest_version.get('dependencies', [])]
            elif "dependencies" in mod_data:
                requirements = [str(dep) for dep in mod_data.get('dependencies', [])]
            elif "requirements" in mod_data:
                requirements = [str(req) for req in mod_data.get('requirements', [])]  

            if requirements:
                req_text = "Requires:\n" + "\n".join(f"• {req}" for req in requirements)
            else:
                req_text = "Requires: None"
            self.mod_requirements_label.config(text=req_text)
            
            self.add_button.config(state='normal')
            self.view_button.config(state='normal')
            
            self.log(f"Selected WebFishing mod: {mod_name} by {author}", "info")
            
        except Exception as e:
            self.log(f"Error displaying mod details: {str(e)}", "error")
            self.clear_mod_details()

    def load_mod_image(self, image_url):
        """Load and display the mod's icon image with better error handling"""
        if not image_url:
            self.mod_image_label.config(text="No Image", image='')
            return
            

        if image_url in self.current_mod_images:
            img = self.current_mod_images[image_url]
            self.mod_image_label.config(image=img, text='')
            self.mod_image_label.image = img 
            return
            
        def fetch_image():
            try:
                self.root.after(0, lambda: self.mod_image_label.config(text="Loading...", image=''))
                
                response = requests.get(image_url, timeout=10, 
                                    headers={'User-Agent': 'WebFishing Mod Manager/1.0'})
                
                if response.status_code == 200:
                    image_data = response.content
                    img = Image.open(io.BytesIO(image_data))
                    
                    img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    
                    self.current_mod_images[image_url] = photo_img
                    
                    self.root.after(0, lambda: self.update_mod_image(photo_img))
                else:
                    self.root.after(0, lambda: self.mod_image_label.config(text="Image\nUnavailable", image=''))
                    
            except Exception as e:
                self.root.after(0, lambda: self.mod_image_label.config(text="No Image", image=''))
                self.log(f"Failed to load mod image: {str(e)}", "warning")

        threading.Thread(target=fetch_image, daemon=True).start()

    def update_mod_image(self, photo_img):
        """Update the mod image on the main thread"""
        self.mod_image_label.config(image=photo_img, text='')
        self.mod_image_label.image = photo_img 

    def clear_mod_details(self):
        """Clear the mod details display"""
        self.mod_name_label.config(text="Select a WebFishing mod")
        self.mod_author_label.config(text="")
        self.mod_version_label.config(text="")
        self.mod_downloads_label.config(text="")
        self.mod_description_label.config(text="Browse and select a mod from the list above to view details.")
        self.mod_requirements_label.config(text="", image='')
        

        self.add_button.config(state='disabled')
        self.view_button.config(state='disabled')
        

        self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))

    def add_selected_mod(self, event=None):
        """Add the currently selected mod to the download list"""
        selected = self.mod_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a mod first.")
            return

        item = self.mod_tree.item(selected[0])
        mod_url = item['tags'][0]
        mod_data = json.loads(item['tags'][1])


        latest_version = mod_data.get('latest', {})
        if not latest_version and 'versions' in mod_data and mod_data['versions']:
            latest_version = mod_data['versions'][0]
            
        requirements = []
        if "dependencies" in latest_version:
            requirements = [
                dep['package_name'] if isinstance(dep, dict) and 'package_name' in dep else str(dep)
                for dep in latest_version.get('dependencies', [])
            ]
        elif "dependencies" in mod_data:
            requirements = [str(dep) for dep in mod_data.get('dependencies', [])]
        elif "requirements" in mod_data:
            requirements = [str(req) for req in mod_data.get('requirements', [])]

        current_mods = set()
        for item_id in self.url_tree.get_children():
            values = self.url_tree.item(item_id)["values"]
            url = values[0]
            mod_info = self.extract_mod_info_from_url(url)
            if mod_info and mod_info.get("author") and mod_info.get("name"):
                current_mods.add(f"{mod_info['author']}-{mod_info['name']}")

        missing_deps = []
        for dep in requirements:
            dep_base = dep.split('-')
            if len(dep_base) >= 2:
                author = dep_base[0].strip().lower()
                name = dep_base[1].strip().lower()

                if (author == "gdweave" and name == "gdweave") or (author == "notnet" and name == "gdweave"):
                    continue
                dep_id = f"{dep_base[0]}-{dep_base[1]}"
                if dep_id not in current_mods and dep_id not in missing_deps:
                    missing_deps.append(dep_id)

        already_in_list = False
        for item_id in self.url_tree.get_children():
            if self.url_tree.item(item_id)["values"][0] == mod_url:
                already_in_list = True
                break
        if not already_in_list:
            mod_info = self.extract_mod_info_from_url(mod_url)
            if mod_info:
                self.url_tree.insert("", tk.END, values=(mod_url, mod_info["name"]))
                self.log(f"Added WebFishing mod: {mod_info['name']} ({mod_url})", "success")

        if missing_deps:
            dep_list_str = "\n".join(missing_deps)
            result = self.modern_popup(
                "Add Dependencies?",
                f"The following dependencies are required and not install already or in your list:\n\n{dep_list_str}\n\nWould you like to add them to your download list?",
                popup_type="question",
                buttons=("Add All", "Cancel")
            )
            if result == "Add All":
                for dep_id in missing_deps:
                    dep_url = None
                    for mod in self.current_mods:
                        author = mod.get('owner')
                        name = mod.get('name')
                        if f"{author}-{name}" == dep_id:
                            dep_url = f"https://thunderstore.io/c/webfishing/p/{author}/{name}/"
                            break
                    if dep_url:
                        already = False
                        for item_id in self.url_tree.get_children():
                            if self.url_tree.item(item_id)["values"][0] == dep_url:
                                already = True
                                break
                        if not already:
                            self.url_tree.insert("", tk.END, values=(dep_url, dep_id))
                            self.log(f"Added dependency: {dep_id}", "info")
                    else:
                        self.log(f"Dependency not found in mod browser: {dep_id}", "warning")
        """Add the currently selected mod to the download list"""
        selected = self.mod_tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a mod first.")
            return
        
        item = self.mod_tree.item(selected[0])
        mod_url = item['tags'][0]
        
        for item_id in self.url_tree.get_children():
            if self.url_tree.item(item_id)["values"][0] == mod_url:
                self.log(f"Mod already in list: {mod_url}", "warning")
                return
        
        mod_info = self.extract_mod_info_from_url(mod_url)
        if mod_info:
            self.url_tree.insert("", tk.END, values=(mod_url, mod_info["name"]))
            self.log(f"Added WebFishing mod: {mod_info['name']} ({mod_url})", "success")

    def view_mod_on_web(self):
        """Open the selected mod in web browser"""
        selected = self.mod_tree.selection()
        if not selected:
            return
        
        item = self.mod_tree.item(selected[0])
        mod_url = item['tags'][0]
        webbrowser.open_new_tab(mod_url)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder.get())
        if folder:
            self.download_folder.set(folder)
    
    def extract_mod_info_from_url(self, url):
        """Extract WebFishing mod info from URL"""
        parsed_url = urlparse(url)
        
        if "thunderstore.io" not in parsed_url.netloc:
            return None
            
        path_parts = [p for p in parsed_url.path.split("/") if p]
        
        if len(path_parts) >= 5 and path_parts[0] == "c" and path_parts[1] == "webfishing" and path_parts[2] == "p":
            return {
                "community": "webfishing",
                "author": path_parts[3],
                "name": path_parts[4],
                "full_name": f"{path_parts[3]}-{path_parts[4]}"
            }
        
        return None
    
    def add_url(self):
        """Add a WebFishing mod URL to the download list"""
        url = self.url_entry.get().strip()
        if not url:
            return
            
        for item_id in self.url_tree.get_children():
            if self.url_tree.item(item_id)["values"][0] == url:
                self.log(f"Mod URL already in list: {url}", "warning")
                self.url_entry.delete(0, tk.END)
                return
        
        mod_info = self.extract_mod_info_from_url(url)
        if not mod_info:
            messagebox.showerror("Invalid URL", 
                "Please enter a valid WebFishing Thunderstore mod URL.\n"
                "Example: https://thunderstore.io/c/webfishing/p/TeamLure/LureRefreshed/")
            return
            
        self.url_tree.insert("", tk.END, values=(url, mod_info["name"]))
        self.log(f"Added WebFishing mod: {mod_info['name']} ({url})", "success")
        
        self.url_entry.delete(0, tk.END)
        
        mod_info = self.extract_mod_info_from_url(url)
        if not mod_info:
            messagebox.showerror("Invalid URL", 
                "Please enter a valid WebFishing Thunderstore mod URL.\n"
                "Example: https://thunderstore.io/c/webfishing/p/TeamLure/LureRefreshed/")
            return
            
        self.url_tree.insert("", tk.END, values=(url, mod_info["name"]))
        self.log(f"Added WebFishing mod: {mod_info['name']} ({url})", "success")
        
        self.url_entry.delete(0, tk.END)
    
    def remove_selected(self):
        selected = self.url_tree.selection()
        if not selected:
            return
            
        for item_id in selected:
            url = self.url_tree.item(item_id)["values"][0]
            self.url_tree.delete(item_id)
            self.log(f"Removed mod: {url}", "info")
    
    def clear_list(self):
        if not self.url_tree.get_children():
            return
            
        if messagebox.askyesno("Clear List", "Are you sure you want to clear all mods from the list?"):
            for item_id in self.url_tree.get_children():
                self.url_tree.delete(item_id)
            self.log("Cleared mod list", "info")
        
    def log(self, message, msg_type="info"):
        """Add message to console with type-based coloring"""
        self.console.config(state=tk.NORMAL)
        
        self.console.tag_config("success", foreground=self.success_color)
        self.console.tag_config("error", foreground=self.error_color)
        self.console.tag_config("warning", foreground=self.warning_color)
        self.console.tag_config("info", foreground=self.text_color)
        
        self.console.insert(tk.END, message + "\n", msg_type)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
        
        
    def start_download(self):
        """Start downloading WebFishing mods"""
        if self.is_downloading:
            return
            
        mod_urls = []
        for item_id in self.url_tree.get_children():
            url = self.url_tree.item(item_id)["values"][0]
            mod_urls.append(url)
            
        if not mod_urls:
            messagebox.showinfo("No Mods", "Please add some WebFishing mods to download first.")
            return
            
        download_folder = self.download_folder.get()
        
        if not download_folder:
            messagebox.showerror("Missing Information", "Please specify a download folder.")
            return
            
        os.makedirs(download_folder, exist_ok=True)
        
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.progress["value"] = 0
        
        self.download_thread = threading.Thread(
            target=self.download_mods,
            args=(mod_urls, download_folder)
        )
        self.download_thread.daemon = True
        self.download_thread.start()
        
        self.root.after(100, self.check_download_thread)
        
    def check_download_thread(self):
        """Monitor the download thread"""
        if self.download_thread and self.download_thread.is_alive():
            self.root.after(100, self.check_download_thread)
        else:
            self.download_button.config(state=tk.NORMAL)
            self.is_downloading = False
            self.progress["value"] = 100
            self.log("\nDownload process completed!", "success")
        
    def download_mods(self, mod_urls, download_folder):
        """Download WebFishing mods"""
        try:
            self.log(f"\n=== Starting WebFishing Mod Download ===", "info")
            self.log(f"Download Folder: {download_folder}", "info")
            self.log(f"Mods to download: {len(mod_urls)}", "info")
            
            has_gdweave = any("gdweave" in url.lower() for url in mod_urls)
            
            if has_gdweave:
                mod_urls = [url for url in mod_urls if "gdweave" not in url.lower()]
                self.log("⚠️ GDWeave detected - it will be handled separately", "warning")
                self.install_gdweave() 
            
            session = requests.Session()
            session.headers.update({
                "User-Agent": "WebFishing Mod Manager/1.0",
                "Accept": "application/json"
            })
            
            successful = 0
            failed = 0
            skipped = 0
            downloaded_mods = set()
            
            temp_folder = os.path.join(download_folder, "temp_extract")
            os.makedirs(temp_folder, exist_ok=True)
            
            for index, mod_url in enumerate(mod_urls, 1):
                self.progress["value"] = (index / len(mod_urls)) * 100
                
                mod_info = self.extract_mod_info_from_url(mod_url)
                if not mod_info:
                    self.log(f"\n[{index}/{len(mod_urls)}] ❌ Invalid WebFishing mod URL: {mod_url}", "error")
                    failed += 1
                    continue
                
                self.log(f"\n[{index}/{len(mod_urls)}] 🔍 Processing: {mod_info['name']}", "info")
                
                try:
                    mod_folder = os.path.join(download_folder, mod_info["full_name"])
                    if os.path.exists(mod_folder):
                        self.log(f"  ⏩ Already installed: {mod_info['name']}", "warning")
                        skipped += 1
                        continue
                    
                    api_url = f"https://thunderstore.io/api/v1/package/{mod_info['author']}/{mod_info['name']}/"
                    download_url = None
                    filename = f"{mod_info['full_name']}.zip"
                    
                    try:
                        response = session.get(api_url, timeout=15)
                        if response.status_code == 200:
                            package_data = response.json()
                            versions = package_data.get('versions', [])
                            if not versions and 'latest' in package_data:
                                versions = [package_data['latest']]
                            
                            if versions:
                                download_url = versions[0].get("download_url")
                                filename = versions[0].get("filename", filename)
                    except Exception as e:
                        self.log(f"  API attempt failed: {str(e)}", "info")
                    
                    if not download_url:
                        download_url = self.get_download_url_from_page(session, mod_url, mod_info)
                    
                    if not download_url:
                        self.log(f"  ❌ No download URL found for WebFishing mod", "error")
                        failed += 1
                        continue
                    
                    self.log(f"  📥 Downloading from: {download_url}", "info")
                    zip_path = os.path.join(temp_folder, filename)
                    
                    try:
                        with session.get(download_url, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            total_size = int(r.headers.get('content-length', 0))
                            downloaded_size = 0
                            
                            with open(zip_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded_size += len(chunk)
                                        if total_size > 0 and int((downloaded_size / total_size) * 100) % 25 == 0:
                                            self.log(f"    Progress: {int((downloaded_size / total_size) * 100)}%", "info")
                        
                        self.log(f"  ✅ Downloaded: {filename} ({downloaded_size} bytes)", "success")
                        
                    except Exception as download_error:
                        self.log(f"  ❌ Download failed: {str(download_error)}", "error")
                        failed += 1
                        continue
                    
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as test_zip:
                            test_zip.testzip()
                        self.log(f"  ✅ Zip file verified", "info")
                    except Exception as zip_error:
                        self.log(f"  ❌ Invalid zip file: {str(zip_error)}", "error")
                        try:
                            os.remove(zip_path)
                        except:
                            pass
                        failed += 1
                        continue
                    
                    self.log(f"  📦 Extracting {filename}...", "info")
                    extract_path = os.path.join(temp_folder, f"extract_{mod_info['full_name']}")
                    os.makedirs(extract_path, exist_ok=True)
                    
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_path)
                    except Exception as extract_error:
                        self.log(f"  ❌ Extraction failed: {str(extract_error)}", "error")
                        failed += 1
                        continue
                    
                    mod_source_folder = self.find_mod_folder(extract_path)
                    
                    if not mod_source_folder:
                        self.log(f"  ❌ No mod folder found with .dll, .pck, or .json files", "error")
                        failed += 1
                        continue
                    
                    actual_mod_folder_name = os.path.basename(mod_source_folder)
                    final_mod_folder = os.path.join(download_folder, actual_mod_folder_name)
                    
                    try:
                        os.makedirs(final_mod_folder, exist_ok=True)
                        
                        for item in os.listdir(mod_source_folder):
                            source_item = os.path.join(mod_source_folder, item)
                            dest_item = os.path.join(final_mod_folder, item)
                            
                            if os.path.isdir(source_item):
                                shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
                            else:
                                shutil.copy2(source_item, dest_item)
                        
                        self.log(f"  ✅ Installed WebFishing mod '{actual_mod_folder_name}' to: {final_mod_folder}", "success")
                        successful += 1
                        downloaded_mods.add(actual_mod_folder_name)
                        
                    except Exception as install_error:
                        self.log(f"  ❌ Installation failed: {str(install_error)}", "error")
                        failed += 1
                        continue
                    
                    try:
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                        if os.path.exists(extract_path):
                            shutil.rmtree(extract_path)
                    except Exception as clean_error:
                        self.log(f"  ⚠️ Cleanup failed: {str(clean_error)}", "warning")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    import traceback
                    self.log(f"  ❌ Error processing WebFishing mod {mod_info['name']}: {str(e)}", "error")
                    self.log(f"  Error details:\n{traceback.format_exc()}", "error")
                    failed += 1
            
            try:
                if os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder)
            except Exception as e:
                self.log(f"  ⚠️ Could not clean up temp folder: {str(e)}", "warning")
            
            summary = {
                "successful_downloads": successful,
                "failed_downloads": failed,
                "skipped_downloads": skipped,
                "downloaded_mods": list(downloaded_mods),
                "download_folder": download_folder,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.save_preset_auto(download_folder, downloaded_mods)
            
            try:
                summary_file = os.path.join(download_folder, "download_summary.json")
                with open(summary_file, "w") as f:
                    json.dump(summary, f, indent=2)
                self.log(f"\n📋 Summary saved to: {summary_file}", "info")
            except Exception as e:
                self.log(f"\n⚠️ Could not save summary: {str(e)}", "warning")
            
            self.log("\n" + "="*40, "info")
            self.log("=== DOWNLOAD SUMMARY ===", "info")
            self.log("="*40, "info")
            
            if successful > 0:
                self.log(f"✅ Successfully installed: {successful} WebFishing mods", "success")
            if skipped > 0:
                self.log(f"⏩ Already installed: {skipped} WebFishing mods", "warning")
            if failed > 0:
                self.log(f"❌ Failed to install: {failed} WebFishing mods", "error")
                
            self.log(f"📁 Total unique mods in folder: {len(downloaded_mods)}", "info")
            self.log(f"📂 Installation directory: {Path(download_folder).absolute()}", "info")
            
            if successful > 0:
                self.log(f"\n🎉 WebFishing mod download completed successfully!", "success")
            elif failed == len(mod_urls):
                self.log(f"\n💥 All WebFishing mod downloads failed. Check the URLs and try again.", "error")
            else:
                self.log(f"\n⚠️ Download completed with some issues.", "warning")
            
        except Exception as e:
            import traceback
            self.log(f"\n💥 Critical error during download process: {str(e)}", "error")
            self.log(f"Error details:\n{traceback.format_exc()}", "error")

    def find_mod_folder(self, root_path):
        """Find the innermost folder containing mod files"""
        mod_folders = []
        for root, dirs, files in os.walk(root_path):
            if any(file.endswith(('.dll', '.pck', '.json')) for file in files):
                mod_folders.append(root)
        
        if mod_folders:
            mod_folders.sort(key=lambda x: -len(x.split(os.sep)))
            return mod_folders[0]
        return None

    def get_download_url_from_page(self, session, mod_url, mod_info):
        """Get download URL from mod page"""
        try:
            page_response = session.get(mod_url, timeout=15)
            if page_response.status_code != 200:
                return None
                
            page_content = page_response.text
            
            patterns = [
                r'href="(https://[^"]*thunderstore[^"]*download[^"]*)"',
                r'"download_url":"([^"]*)"',
                r'data-download-url="([^"]*)"',
                rf'/package/download/{re.escape(mod_info["author"])}/{re.escape(mod_info["name"])}([^/"]+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    download_url = matches[0]
                    if isinstance(download_url, tuple):
                        download_url = matches[0][0]
                    
                    if not download_url.startswith('http'):
                        download_url = f"https://thunderstore.io{download_url}"
                    
                    return download_url
            
            version_match = re.search(r'"version_number":"([^"]+)"', page_content)
            if version_match:
                version = version_match.group(1)
                return f"https://thunderstore.io/package/download/{mod_info['author']}/{mod_info['name']}/{version}/"
            
            return None
            
        except Exception as e:
            self.log(f"  ❌ Error parsing mod page: {str(e)}", "error")
            return None

    def load_preset(self):
        """Load a JSON preset file"""
        preset_file = filedialog.askopenfilename(
            title="Select Preset File",
            filetypes=[("JSON Preset", "*.json"), ("All Files", "*.*")],
            initialdir=self.download_folder.get()
        )
        
        if not preset_file:
            return
        
        try:
            with open(preset_file, 'r') as f:
                preset_data = json.load(f)
                
            if "mod_urls" not in preset_data:
                messagebox.showerror("Invalid Preset", "The selected file is not a valid mod preset.")
                return
                
            for item_id in self.url_tree.get_children():
                self.url_tree.delete(item_id)
            
            added_count = 0
            for url in preset_data["mod_urls"]:
                mod_info = self.extract_mod_info_from_url(url)
                if mod_info:
                    self.url_tree.insert("", tk.END, values=(url, mod_info["name"]))
                    added_count += 1
                    
            self.log(f"Loaded preset: {os.path.basename(preset_file)}", "success")
            self.log(f"• {added_count} WebFishing mods added to list", "info")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {str(e)}")
            self.log(f"Failed to load preset: {str(e)}", "error")

    def save_preset_as(self):
        """Save the current mod list as a named preset"""
        mod_urls = []
        for item_id in self.url_tree.get_children():
            url = self.url_tree.item(item_id)["values"][0]
            mod_urls.append(url)
            
        if not mod_urls:
            messagebox.showwarning("No Mods", "There are no WebFishing mods in the list to save as a preset.")
            return
            
        preset_name = simpledialog.askstring("Preset Name", "Enter a name for your WebFishing mod preset:", parent=self.root)
        if not preset_name:
            return
            
        preset_name = "".join(c for c in preset_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not preset_name:
            messagebox.showerror("Invalid Name", "Please enter a valid preset name.")
            return
            
        preset_file = filedialog.asksaveasfilename(
            title="Save Preset As",
            initialdir=self.download_folder.get(),
            initialfile=f"{preset_name}.json",
            defaultextension=".json",
            filetypes=[("JSON Preset", "*.json"), ("All Files", "*.*")]
        )
        
        if not preset_file:
            return
            
        preset_data = {
            "name": preset_name,
            "mod_urls": mod_urls,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": "WebFishing Mod Manager"
        }
        
        try:
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
                
            self.log(f"WebFishing mod preset saved successfully: {preset_file}", "success")
            messagebox.showinfo("Preset Saved", f"Your WebFishing mod preset '{preset_name}' was saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preset: {str(e)}")
            self.log(f"Failed to save preset: {str(e)}", "error")

    def save_preset_auto(self, download_folder, downloaded_mods):
        """Automatically save a preset file"""
        preset_path = os.path.join(download_folder, "webfishing_mod_preset.json")
        
        preset_data = {
            "name": "Auto Preset",
            "downloaded_mods": list(downloaded_mods),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": "WebFishing Mod Manager"
        }
        
        try:
            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2)
        except Exception as e:
            self.log(f"\n⚠️ Could not save auto-preset: {str(e)}", "error")

    def launch_webfishing(self):
        """Launch the WebFishing game executable, waiting for Steam to be fully ready (but not launching Steam)."""
        import subprocess

        if not self.config.get("suppress_launch_popup", False):
            popup = tk.Toplevel(self.root)
            popup.title("Before Launching")
            popup.configure(bg="#23272e")
            popup.resizable(False, False)
            w, h = 420, 200
            popup.geometry(f"{w}x{h}+{self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (w // 2)}+{self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (h // 2)}")

            frame = ttk.Frame(popup)
            frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
            label = ttk.Label(frame, text="Please ensure Steam is running and you are logged in before launching WebFishing.\n\nIf Steam is not running, the game will not start.", wraplength=370, justify="left", foreground=self.text_color, font=self.text_font)
            label.pack(pady=(0, 10))
            dont_show_var = tk.BooleanVar(value=False)
            dont_show_chk = ttk.Checkbutton(frame, text="Don't show this again", variable=dont_show_var)
            dont_show_chk.pack(pady=(10, 0))
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=(10, 0))
            def do_ok():
                if dont_show_var.get():
                    self.config["suppress_launch_popup"] = True
                    self.save_config(self.config)
                popup.destroy()
            def do_cancel():
                popup.destroy()
                self.log("launch cancelled.", "warning")
            ok_btn = ttk.Button(btn_frame, text="OK", command=do_ok, style='Accent.TButton')
            ok_btn.pack(side=tk.LEFT, padx=(0, 10))
            cancel_btn = ttk.Button(btn_frame, text="Cancel", command=do_cancel, style='Secondary.TButton')
            cancel_btn.pack(side=tk.LEFT)
            popup.transient(self.root)
            popup.grab_set()
            popup.wait_window()
            if not popup.winfo_exists():
                if hasattr(self, 'log') and hasattr(self, 'config') and self.config.get("suppress_launch_popup", False) is False:
                    return

        game_exe = r"C:\Program Files (x86)\Steam\steamapps\common\WEBFISHING\WebFishing.exe"

        def is_steam_running():
            try:
                import psutil
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and 'steam.exe' in proc.info['name'].lower():
                        return True
            except ImportError:
                return False
            return False

        def is_steam_ready():
            try:
                import ctypes
                user32 = ctypes.windll.user32
                EnumWindows = user32.EnumWindows
                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                titles = []
                def foreach_window(hwnd, lParam):
                    length = user32.GetWindowTextLengthW(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "steam" in title.lower():
                        titles.append(title)
                    return True
                EnumWindows(EnumWindowsProc(foreach_window), 0)
                return bool(titles)
            except Exception:
                return False

        if not os.path.exists(game_exe):
            response = messagebox.askyesno(
                "Game Not Found",
                f"Could not find WebFishing executable at:\n"
                f"{game_exe}\n\n"
               
                "It looks like you do not own or have not installed WebFishing on this PC.\n"
                "Would you like to open the Steam store page for WebFishing?",
                parent=self.root
            )
            if response:
                webbrowser.open_new_tab("https://store.steampowered.com/app/2854530/WebFishing/")
            return

        import time
        max_wait = 10
        waited = 0
        self.log("Checking if Steam is running...", "info")
        while not is_steam_running() and waited < max_wait:
            time.sleep(1)
            waited += 1

        if not is_steam_running():
            self.log("Steam is not running. Please launch Steam and log in, then try again.", "error")
            messagebox.showerror(
                "Steam Not Running",
                "Steam is not running. Please launch Steam and log in, then try again.",
                parent=self.root
            )
            return

        waited = 0
        while not is_steam_ready() and waited < max_wait:
            time.sleep(1)
            waited += 1
        if not is_steam_ready():
            self.log("Steam client window not detected. Waiting for user login...", "warning")
            messagebox.showerror(
                "Steam Not Ready",
                "Steam is running, but not fully ready. Please log in to Steam and wait until the main Steam window is open, then try again.",
                parent=self.root
            )
            return

        self.log("Steam should now be ready. Launching WebFishing...", "info")
        time.sleep(1)

        try:
            subprocess.Popen([game_exe], cwd=os.path.dirname(game_exe))
            self.log("Launched WebFishing directly!", "success")
        except Exception as e:
            self.log(f"Failed to launch WebFishing: {str(e)}", "error")
            messagebox.showerror(
                "Launch Failed",
                f"Failed to launch WebFishing:\n{str(e)}",
                parent=self.root
            )
    
    def launch_steam(self):
        """Launch the Steam client."""
        import subprocess
        steam_exe = r"C:\Program Files (x86)\Steam\Steam.exe"
        if not os.path.exists(steam_exe):
            messagebox.showerror(
                "Steam Not Found",
                f"Could not find Steam executable at:\n{steam_exe}\n"
                "Please make sure Steam is installed.",
                parent=self.root
            )
            return
        try:
            subprocess.Popen([steam_exe])
            self.log("Launched Steam client.", "success")
        except Exception as e:
            self.log(f"Failed to launch Steam: {str(e)}", "error")
            messagebox.showerror(
                "Launch Failed",
                f"Failed to launch Steam:\n{str(e)}",
                parent=self.root
            )

    def modern_popup(self, title, message, popup_type="info", buttons=("OK",), default=None, parent=None):
        """
        Show a modern styled popup.
        popup_type: "info", "warning", "error", "yesno", "question", "input"
        buttons: tuple of button labels (e.g., ("Yes", "No"))
        Returns: button label pressed, or input string if popup_type=="input"
        """
        result = [None]
        parent = parent or self.root

        overlay = tk.Toplevel(parent)
        overlay.overrideredirect(True)
        overlay.geometry(f"{parent.winfo_width()}x{parent.winfo_height()}+{parent.winfo_rootx()}+{parent.winfo_rooty()}")
        overlay.attributes("-alpha", 0.5)
        overlay.configure(bg="#000000")
        overlay.lift()
        overlay.transient(parent)
        overlay.grab_set()

        popup = tk.Toplevel(parent)
        popup.overrideredirect(True)  
        popup.configure(bg="#23272e")
        popup.lift(overlay)
        popup.transient(overlay)
        popup.grab_set()
        popup.resizable(False, False)

        popup.update_idletasks()
        min_w, min_h = 360, 420
        max_w, max_h = 600, 600
        lines = message.split('\n')
        longest_line = max(lines, key=len) if lines else ""
        char_width = 7
        est_w = min(max(len(longest_line) * char_width + 80, min_w), max_w)
        line_height = 22
        num_lines = len(lines) + (2 if popup_type == "input" else 0)
        est_h = min(max(180 + num_lines * line_height, min_h), max_h)
        w, h = int(est_w), int(est_h)
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        def close_popup():
            popup.destroy()
            overlay.destroy()
        close_btn = tk.Button(
            popup,
            text="✕",
            command=close_popup,
            bg="#23272e",
            fg="#888",
            borderwidth=0,
            font=("Segoe UI", 12, "bold"),
            activebackground="#23272e",
            activeforeground="#fff",
            cursor="hand2"
        )
        close_btn.place(x=w-32, y=8, width=24, height=24)
        def on_enter(event):
            close_btn.config(fg="#ff4444")
        def on_leave(event):
            close_btn.config(fg="#888")
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)


        icon_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "question": "❓",
            "yesno": "❓",
            "input": "✏️"
        }
        icon = icon_map.get(popup_type, "ℹ️")
        icon_label = tk.Label(popup, text=icon, font=("Segoe UI Emoji", 32), bg="#23272e", fg="#4a8fe7")
        icon_label.pack(pady=(18, 0))


        title_label = tk.Label(popup, text=title, font=self.title_font, bg="#23272e", fg=self.accent_color)
        title_label.pack(pady=(8, 0))


        msg_label = tk.Label(popup, text=message, font=self.text_font, bg="#23272e", fg=self.text_color, wraplength=340, justify="center")
        msg_label.pack(padx=24, pady=(8, 18))


        entry = None
        if popup_type == "input":
            entry = tk.Entry(popup, font=self.text_font, bg="#3a3a3a", fg=self.text_color, insertbackground=self.text_color, relief=tk.FLAT)
            entry.pack(padx=24, pady=(0, 18), fill=tk.X)
            entry.focus_set()
            if default:
                entry.insert(0, default)


        btn_frame = tk.Frame(popup, bg="#23272e")
        btn_frame.pack(pady=(0, 18))

        def on_press(val=None):
            if popup_type == "input":
                result[0] = entry.get()
            else:
                result[0] = val
            popup.destroy()
            overlay.destroy()


        for i, btn in enumerate(buttons):
            style = 'Accent.TButton' if (btn.lower() in ("ok", "yes", "continue")) else 'Secondary.TButton'
            b = ttk.Button(btn_frame, text=btn, style=style, command=lambda v=btn: on_press(v))
            b.pack(side=tk.LEFT, padx=8)
            if i == 0:
                popup.bind("<Return>", lambda e: on_press(btn))


        popup.bind("<Escape>", lambda e: on_press())

        popup.wait_window()
        return result[0]
    
    
    def modern_popup2(self, title, message, popup_type="info", buttons=("OK",), default=None, parent=None):
        """
        Show a modern styled popup.
        popup_type: "info", "warning", "error", "yesno", "question", "input"
        buttons: tuple of button labels (e.g., ("Yes", "No"))
        Returns: button label pressed, or input string if popup_type=="input"
        """
        result = [None]
        parent = parent or self.root

        # --- Shadow overlay ---
        overlay = tk.Toplevel(parent)
        overlay.overrideredirect(True)
        overlay.geometry(f"{parent.winfo_width()}x{parent.winfo_height()}+{parent.winfo_rootx()}+{parent.winfo_rooty()}")
        overlay.attributes("-alpha", 0.5)
        overlay.configure(bg="#000000")
        overlay.lift()
        overlay.transient(parent)
        overlay.grab_set()


        popup = tk.Toplevel(parent)
        popup.overrideredirect(True)
        popup.configure(bg="#23272e")
        popup.lift(overlay)
        popup.transient(overlay)
        popup.grab_set()
        popup.resizable(False, False)


        popup.update_idletasks()
        min_w, min_h = 360, 300
        max_w, max_h = 600, 600
        lines = message.split('\n')
        longest_line = max(lines, key=len) if lines else ""
        char_width = 7
        est_w = min(max(len(longest_line) * char_width + 80, min_w), max_w)
        line_height = 22
        num_lines = len(lines) + (2 if popup_type == "input" else 0)
        est_h = min(max(180 + num_lines * line_height, min_h), max_h)
        w, h = int(est_w), int(est_h)
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")


        def close_popup():
            popup.destroy()
            overlay.destroy()
        close_btn = tk.Button(
            popup,
            text="✕",
            command=close_popup,
            bg="#23272e",
            fg="#888",
            borderwidth=0,
            font=("Segoe UI", 12, "bold"),
            activebackground="#23272e",
            activeforeground="#fff",
            cursor="hand2"
        )
        close_btn.place(x=w-32, y=8, width=24, height=24)
        def on_enter(event):
            close_btn.config(fg="#ff4444")
        def on_leave(event):
            close_btn.config(fg="#888")
        close_btn.bind("<Enter>", on_enter)
        close_btn.bind("<Leave>", on_leave)


        icon_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "question": "❓",
            "yesno": "❓",
            "input": "✏️"
        }
        icon = icon_map.get(popup_type, "ℹ️")
        icon_label = tk.Label(popup, text=icon, font=("Segoe UI Emoji", 32), bg="#23272e", fg="#4a8fe7")
        icon_label.pack(pady=(18, 0))


        title_label = tk.Label(popup, text=title, font=self.title_font, bg="#23272e", fg=self.accent_color)
        title_label.pack(pady=(8, 0))


        msg_label = tk.Label(popup, text=message, font=self.text_font, bg="#23272e", fg=self.text_color, wraplength=340, justify="center")
        msg_label.pack(padx=24, pady=(8, 18))


        entry = None
        if popup_type == "input":
            entry = tk.Entry(popup, font=self.text_font, bg="#3a3a3a", fg=self.text_color, insertbackground=self.text_color, relief=tk.FLAT)
            entry.pack(padx=24, pady=(0, 18), fill=tk.X)
            entry.focus_set()
            if default:
                entry.insert(0, default)


        btn_frame = tk.Frame(popup, bg="#23272e")
        btn_frame.pack(pady=(0, 18))

        def on_press(val=None):
            if popup_type == "input":
                result[0] = entry.get()
            else:
                result[0] = val
            popup.destroy()
            overlay.destroy()


        for i, btn in enumerate(buttons):
            style = 'Accent.TButton' if (btn.lower() in ("ok", "yes", "continue")) else 'Secondary.TButton'
            b = ttk.Button(btn_frame, text=btn, style=style, command=lambda v=btn: on_press(v))
            b.pack(side=tk.LEFT, padx=8)
            if i == 0:
                popup.bind("<Return>", lambda e: on_press(btn))


        popup.bind("<Escape>", lambda e: on_press())

        popup.wait_window()
        return result[0]
        

    def import_zip(self):
        """Import a mod from a .zip file and extract only the innermost mod folder to the mods folder."""
        zip_path = filedialog.askopenfilename(
            title="Select Mod Zip File",
            filetypes=[("Zip Files", "*.zip"), ("All Files", "*.*")]
        )
        if not zip_path:
            return

        extract_to = self.download_folder.get()
        if not os.path.isdir(extract_to):
            os.makedirs(extract_to, exist_ok=True)

        import tempfile
        import shutil

        temp_extract = tempfile.mkdtemp(prefix="modimport_")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)

            mod_folder = None
            max_depth = 0
            for root, dirs, files in os.walk(temp_extract):

                if files and len(root.split(os.sep)) > max_depth:
                    mod_folder = root
                    max_depth = len(root.split(os.sep))

            if not mod_folder:
                self.modern_popup(
                    "Import Failed",
                    "Could not find a valid mod folder in the zip.",
                    popup_type="error",
                    buttons=("OK",),
                    parent=self.root
                )
                return

            dest_folder = os.path.join(extract_to, os.path.basename(mod_folder))
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            shutil.copytree(mod_folder, dest_folder)

            self.log(f"Imported mod from zip: {zip_path} → {dest_folder}", "success")
            self.modern_popup(
                "Import Complete",
                f"Mod zip imported and extracted to:\n{dest_folder}",
                popup_type="info",
                buttons=("OK",),
                parent=self.root
            )
        except Exception as e:
            self.log(f"Failed to import zip: {str(e)}", "error")
            self.modern_popup(
                "Import Failed",
                f"Could not import zip:\n{str(e)}",
                popup_type="error",
                buttons=("OK",),
                parent=self.root
            )
        finally:
            shutil.rmtree(temp_extract, ignore_errors=True)

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    app = WebFishingModManager(root)
    root.mainloop()