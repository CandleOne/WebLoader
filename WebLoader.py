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

class ModDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WebLoader 1.0.0")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        
        self.bg_color = "#2d2d2d"
        self.card_bg = "#3a3a3a"
        self.text_color = "#ffffff"
        self.accent_color = "#4a8fe7"
        self.secondary_color = "#5e5e5e"
        self.success_color = "#4CAF50"
        self.error_color = "#F44336"
        self.warning_color = "#FFC107"
        
        self.root.configure(bg=self.bg_color)
        
        self.title_font = Font(family="Segoe UI", size=12, weight="bold")
        self.text_font = Font(family="Segoe UI", size=10)
        self.button_font = Font(family="Segoe UI", size=10, weight="bold")
        self.console_font = Font(family="Consolas", size=9)
        
        self.download_folder = tk.StringVar(value=os.path.join(os.getcwd(), "webfishing_mods"))
        self.mod_urls = []
        self.download_thread = None
        self.is_downloading = False
        
        self.configure_styles()
        
        self.create_ui()
        
    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('.', 
                        background=self.bg_color,
                        foreground=self.text_color,
                        font=self.text_font,
                        borderwidth=0,
                        relief=tk.FLAT)
        
        style.configure('Card.TFrame',
                        borderwidth=2,
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
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, 
                text="WebLoader 1.0.0", 
                style='Title.TLabel').pack(side=tk.LEFT)
        
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        config_card = ttk.LabelFrame(left_panel, text="Configuration", style='Card.TFrame')
        config_card.pack(fill=tk.X, pady=(0, 10))
        
        folder_frame = ttk.Frame(config_card)
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_frame, text="Mods Folder:").pack(side=tk.LEFT, padx=(5, 5))
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.download_folder)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        folder_button = ttk.Button(folder_frame, text="Browse...", command=self.browse_folder, style='Secondary.TButton')
        folder_button.pack(side=tk.LEFT)
        
        url_card = ttk.LabelFrame(left_panel, text="Add Mods", style='Card.TFrame')
        url_card.pack(fill=tk.X, pady=(0, 10))
        
        url_entry_frame = ttk.Frame(url_card)
        url_entry_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(url_entry_frame, text="Mod URL:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.url_entry = ttk.Entry(url_entry_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.url_entry.bind("<Return>", lambda e: self.add_url())
        
        add_button = ttk.Button(url_entry_frame, text="Add Mod", command=self.add_url, style='Secondary.TButton')
        add_button.pack(side=tk.LEFT)
        
        help_text = "Enter Thunderstore mod URLs like:\n• https://thunderstore.io/c/webfishing/p/TeamLure/LureRefreshed/"
        ttk.Label(url_card, text=help_text, foreground=self.secondary_color).pack(anchor="w")
        
        list_card = ttk.LabelFrame(left_panel, text="Mod List", style='Card.TFrame')
        list_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tree_container = ttk.Frame(list_card)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.url_tree = ttk.Treeview(tree_container, columns=("url", "name"), show="headings")
        self.url_tree.heading("url", text="Mod URL")
        self.url_tree.heading("name", text="Mod Name")
        self.url_tree.column("url", width=500, anchor="w")
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

        load_preset_button = ttk.Button(left_actions, text="Load Preset", command=self.load_preset, style='Secondary.TButton')
        load_preset_button.pack(side=tk.LEFT, padx=(0, 5))

        save_preset_button = ttk.Button(left_actions, text="Save Preset", command=self.save_preset_as, style='Secondary.TButton')
        save_preset_button.pack(side=tk.LEFT, padx=(0, 5))

        remove_button = ttk.Button(left_actions, text="Remove Selected", command=self.remove_selected, style='Secondary.TButton')
        remove_button.pack(side=tk.LEFT, padx=(0, 5))

        clear_button = ttk.Button(left_actions, text="Clear All", command=self.clear_list, style='Secondary.TButton')
        clear_button.pack(side=tk.LEFT)

        right_actions = ttk.Frame(action_frame)
        right_actions.pack(side=tk.RIGHT)
        
        self.download_button = ttk.Button(
            left_panel, 
            text="⬇️ Download Mods", 
            command=self.start_download,
            style='Accent.TButton'
        )
        self.download_button.pack(fill=tk.X, pady=(0, 10))
        
        self.progress = ttk.Progressbar(left_panel, orient="horizontal", mode="determinate", style='Horizontal.TProgressbar')
        self.progress.pack(fill=tk.X)
        
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
        
        self.status_bar = ttk.Frame(main_container, style='Card.TFrame', height=25)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready", foreground=self.secondary_color)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder.get())
        if folder:
            self.download_folder.set(folder)
            self.update_status(f"Mods folder set to: {folder}")
    
    def extract_mod_info_from_url(self, url):
        """Extract mod info from Thunderstore URL"""
        parsed_url = urlparse(url)
        
        if "thunderstore.io" not in parsed_url.netloc:
            return None
            
        path_parts = [p for p in parsed_url.path.split("/") if p]
        
        if len(path_parts) >= 5 and path_parts[0] == "c" and path_parts[2] == "p":
            return {
                "community": path_parts[1],
                "author": path_parts[3],
                "name": path_parts[4],
                "full_name": f"{path_parts[3]}-{path_parts[4]}"
            }
        
        return None
    
    def add_url(self):
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
            messagebox.showerror("Invalid URL", "Please enter a valid Thunderstore mod URL.\nExample: https://thunderstore.io/c/webfishing/p/TeamLure/LureRefreshed/")
            return
            
        self.url_tree.insert("", tk.END, values=(url, mod_info["name"]))
        self.log(f"Added mod: {mod_info['name']} ({url})", "success")
        
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
            
            if msg_type in ("error", "success"):
                self.update_status(message)
        
    def update_status(self, message):
        """Update the status bar text"""
        self.status_label.config(text=message)
        
    def start_download(self):
        """Start the download process in a separate thread"""
        if self.is_downloading:
            return
            
        mod_urls = []
        for item_id in self.url_tree.get_children():
            url = self.url_tree.item(item_id)["values"][0]
            mod_urls.append(url)
            
        if not mod_urls:
            messagebox.showinfo("No Mods", "Please add some mods to download first.")
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
        """Monitor the download thread and update UI"""
        if self.download_thread and self.download_thread.is_alive():

            self.root.after(100, self.check_download_thread)
        else:
            self.download_button.config(state=tk.NORMAL)
            self.is_downloading = False
            self.progress["value"] = 100
            self.log("\nDownload process completed!", "success")
        
    def download_mods(self, mod_urls, download_folder):
        """Download the mods (runs in a separate thread)"""
        try:
            self.log(f"\n=== Starting Download ===", "info")
            self.log(f"Download Folder: {download_folder}", "info")
            self.log(f"Mods to download: {len(mod_urls)}", "info")
            
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
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
                    self.log(f"\n[{index}/{len(mod_urls)}] ❌ Invalid URL: {mod_url}", "error")
                    failed += 1
                    continue
                
                self.log(f"\n[{index}/{len(mod_urls)}] 🔍 Processing: {mod_info['name']}", "info")
                
                try:
                    mod_folder = os.path.join(download_folder, mod_info["full_name"])
                    if os.path.exists(mod_folder):
                        self.log(f"  ⏩ Already installed: {mod_info['name']}", "warning")
                        skipped += 1
                        continue
                    
                    download_url = None
                    filename = f"{mod_info['full_name']}.zip"
                    
                    api_endpoints = [
                        f"https://thunderstore.io/api/experimental/package/{mod_info['author']}/{mod_info['name']}/",
                        f"https://thunderstore.io/api/v1/package/{mod_info['author']}/{mod_info['name']}/",
                        f"https://thunderstore.io/api/v1/package/{mod_info['author']}-{mod_info['name']}/"
                    ]
                    
                    for api_url in api_endpoints:
                        if download_url:
                            break
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
                            self.log(f"  API attempt failed ({api_url}): {str(e)}", "info")
                    
                    if not download_url:
                        download_url = self.enhanced_html_parsing(session, mod_url, mod_info)
                    
                    if not download_url:
                        self.log(f"  ❌ No download URL found after trying all methods", "error")
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
                    
                    def find_innermost_mod_folder(root_path):
                        mod_folders = []
                        for root, dirs, files in os.walk(root_path):
                            if any(file.endswith(('.dll', '.pck', '.json')) for file in files):
                                mod_folders.append(root)
                        
                        if mod_folders:
                            mod_folders.sort(key=lambda x: -len(x.split(os.sep)))
                            return mod_folders[0]
                        return None
                    
                    mod_source_folder = find_innermost_mod_folder(extract_path)
                    
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
                        
                        self.log(f"  ✅ Installed mod folder '{actual_mod_folder_name}' to: {final_mod_folder}", "success")
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
                    self.log(f"  ❌ Error processing {mod_info['name']}: {str(e)}", "error")
                    self.log(f"  Error details:\n{traceback.format_exc()}", "error")
                    failed += 1
            
            try:
                if os.path.exists(temp_folder):
                    for item in os.listdir(temp_folder):
                        item_path = os.path.join(temp_folder, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    try:
                        os.rmdir(temp_folder)
                    except:
                        pass
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
                self.log(f"✅ Successfully installed: {successful} mods", "success")
            if skipped > 0:
                self.log(f"⏩ Already installed: {skipped} mods", "warning")
            if failed > 0:
                self.log(f"❌ Failed to install: {failed} mods", "error")
                
            self.log(f"📁 Total unique mods in folder: {len(downloaded_mods)}", "info")
            self.log(f"📂 Installation directory: {Path(download_folder).absolute()}", "info")
            
            if successful > 0:
                self.log(f"\n🎉 Download completed successfully!", "success")
            elif failed == len(mod_urls):
                self.log(f"\n💥 All downloads failed. Check the URLs and try again.", "error")
            else:
                self.log(f"\n⚠️ Download completed with some issues.", "warning")
            
        except Exception as e:
            import traceback
            self.log(f"\n💥 Critical error during download process: {str(e)}", "error")
            self.log(f"Error details:\n{traceback.format_exc()}", "error")

    def enhanced_html_parsing(self, session, mod_url, mod_info):
        """Enhanced HTML parsing with multiple strategies for finding download links"""
        try:
            import re
            from urllib.parse import urljoin, urlparse
            
            self.log(f"  📄 Enhanced HTML parsing for: {mod_info['name']}", "info")
            
            page_response = session.get(mod_url, timeout=15)
            
            if page_response.status_code != 200:
                self.log(f"  ❌ Failed to fetch mod page: {page_response.status_code}", "error")
                return None
                
            page_content = page_response.text
            
            download_patterns = [
                r'href="(https://[^"]*thunderstore[^"]*download[^"]*)"',
                r'href="(https://[^"]*\.zip)"',
                r'"downloadUrl":"([^"]*)"',
                r'"download_url":"([^"]*)"',
                r'data-download-url="([^"]*)"',
                r'data-href="([^"]*download[^"]*)"',
                
                r'href="(/api/[^"]*download[^"]*)"',
                r'href="(/package/download/[^"]*)"',
                r'/package/download/([^/]+)/([^/]+)/([^/"]+)',
                
                rf'href="([^"]*{re.escape(mod_info["author"])}/[^"]*{re.escape(mod_info["name"])}/[^"]*download[^"]*)"',
                rf'/package/download/{re.escape(mod_info["author"])}/{re.escape(mod_info["name"])}/([^/"]+)',
            ]
            
            download_url = None
            for pattern in download_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        if len(matches[0]) == 3:
                            author, name, version = matches[0]
                            download_url = f"https://thunderstore.io/package/download/{author}/{name}/{version}/"
                        else:
                            download_url = matches[0][0] if matches[0][0] else matches[0]
                    else:
                        download_url = matches[0]
                    
                    if download_url:
                        if not download_url.startswith('http'):
                            download_url = urljoin('https://thunderstore.io', download_url)
                        
                        if any(keyword in download_url.lower() for keyword in ['download', '.zip', '/package/']):
                            self.log(f"  ✅ Found download URL with pattern: {pattern[:50]}...", "success")
                            self.log(f"  🔗 URL: {download_url}", "info")
                            return download_url
            
            version_patterns = [
                r'"version_number":"([^"]+)"',
                r'"latest_version":"([^"]+)"',
                r'data-version="([^"]*)"',
                rf'/{re.escape(mod_info["author"])}/{re.escape(mod_info["name"])}/([0-9.]+)',
            ]
            
            for pattern in version_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    version = matches[0]
                    constructed_url = f"https://thunderstore.io/package/download/{mod_info['author']}/{mod_info['name']}/{version}/"
                    self.log(f"  🔧 Constructed download URL with version {version}: {constructed_url}", "info")
                    return constructed_url
            
            uuid_patterns = [
                r'"uuid4":"([^"]+)"',
                r'"package_uuid":"([^"]+)"',
                r'data-package-uuid="([^"]*)"',
            ]
            
            for pattern in uuid_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    uuid = matches[0]
                    uuid_url = f"https://thunderstore.io/package/download/{uuid}/"
                    self.log(f"  🆔 Found package UUID, trying: {uuid_url}", "info")
                    return uuid_url
            
            js_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__PACKAGE_DATA__\s*=\s*({.*?});',
                r'var\s+packageData\s*=\s*({.*?});',
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, page_content, re.DOTALL)
                if matches:
                    try:
                        import json
                        js_data = json.loads(matches[0])
                        
                        possible_paths = [
                            ['package', 'latest', 'download_url'],
                            ['latest', 'download_url'],
                            ['download_url'],
                            ['package', 'versions', 0, 'download_url'],
                            ['versions', 0, 'download_url'],
                        ]
                        
                        for path in possible_paths:
                            data = js_data
                            try:
                                for key in path:
                                    if isinstance(key, int):
                                        data = data[key]
                                    else:
                                        data = data[key]
                                if isinstance(data, str) and ('download' in data or '.zip' in data):
                                    self.log(f"  📊 Found download URL in JavaScript data", "success")
                                    return data
                            except (KeyError, IndexError, TypeError):
                                continue
                                
                    except json.JSONDecodeError:
                        continue
            
            meta_patterns = [
                r'<meta[^>]*property="og:url"[^>]*content="([^"]*)"',
                r'<link[^>]*rel="canonical"[^>]*href="([^"]*)"',
            ]
            
            for pattern in meta_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    canonical_url = matches[0]
                    if '/p/' in canonical_url:
                        version_match = re.search(r'/([0-9.]+)/?$', canonical_url)
                        if version_match:
                            version = version_match.group(1)
                            download_url = f"https://thunderstore.io/package/download/{mod_info['author']}/{mod_info['name']}/{version}/"
                            self.log(f"  🔗 Constructed URL from canonical link", "info")
                            return download_url
            
            common_versions = ['1.0.0', '1.0.1', '1.1.0', '2.0.0', '0.1.0', 'latest']
            for version in common_versions:
                test_url = f"https://thunderstore.io/package/download/{mod_info['author']}/{mod_info['name']}/{version}/"
                try:
                    head_response = session.head(test_url, timeout=5)
                    if head_response.status_code == 200:
                        self.log(f"  🎯 Found working download URL by testing common versions", "success")
                        return test_url
                except:
                    continue
            
            self.log(f"  ❌ All HTML parsing strategies failed", "error")
            return None
            
        except Exception as e:
            self.log(f"  ❌ HTML parsing error: {str(e)}", "error")
            return None

    def load_preset(self):
            """Load a JSON preset file and populate the mod list"""
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
                self.log(f"• {added_count} mods added to list", "info")
                
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
                messagebox.showwarning("No Mods", "There are no mods in the list to save as a preset.")
                return
                
            preset_name = simpledialog.askstring("Preset Name", "Enter a name for your preset:", parent=self.root)
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
                "created_by": "WebLoader 1.0.0"
            }
            
            try:
                with open(preset_file, 'w') as f:
                    json.dump(preset_data, f, indent=2)
                    
                self.log(f"Preset saved successfully: {preset_file}", "success")
                messagebox.showinfo("Preset Saved", f"Your preset '{preset_name}' was saved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save preset: {str(e)}")
                self.log(f"Failed to save preset: {str(e)}", "error")

    def save_preset_auto(self, download_folder, downloaded_mods):
            """Automatically save a preset file in the download folder"""
            preset_path = os.path.join(download_folder, "mod_preset.json")
            
            preset_data = {
                "name": "Auto Preset",
                "downloaded_mods": list(downloaded_mods),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": "WebLoader 1.0.0"
            }
            
            try:
                with open(preset_path, 'w') as f:
                    json.dump(preset_data, f, indent=2)
                self.log(f"\n💾 Auto-preset saved to: {preset_path}", "success")
            except Exception as e:
                self.log(f"\n⚠️ Could not save auto-preset: {str(e)}", "error")

if __name__ == "__main__":
    root = tk.Tk()
    app = ModDownloaderApp(root)
    root.mainloop()