🌐 WebLoader 1.0.0

WebLoader is a desktop GUI application for downloading and managing mods from Thunderstore — specifically for the WebFishing community. Built using Python and Tkinter, WebLoader helps streamline the mod installation process with features like batch downloads, mod presets, real-time console logs, and automatic zip extraction.

Features

 * Thunderstore URL Parsing: Just paste a Thunderstore mod URL and let WebLoader handle the rest.
 * Batch Mod Downloader: Download and extract multiple mods in one click.
 * Preset Support: Save and load your mod lists.
 * Auto Folder Management: Automatically detects and installs mods to appropriate folders.
 * Smart Extraction: Finds innermost folders containing .dll, .pck, or .json files.
 * Modern UI: Dark mode-themed Tkinter interface with styled widgets.
 * Verbose Console Output: See what’s happening under the hood in real time.
 * Fallback Strategies: Uses API, HTML parsing, and heuristics to find mod download links.

▶ Run the App
🖼 Usage

  Launch the app.
  Choose your desired mods folder.
  Paste mod URLs from Thunderstore 
  (e.g. https://thunderstore.io/c/webfishing/p/Author/ModName/).
  Click Add Mod.
  Click Download Mods.
  Optionally save/load mod presets.

Presets

Presets are saved as JSON files containing lists of mod URLs. You can:

  Save Preset — to reuse mod lists across installs.

  Load Preset — to quickly rehydrate mod collections.

API + HTML Parsing

  Uses Thunderstore APIs (/api/experimental/package/...) for download URLs.
  Falls back to HTML scraping and common version guessing if APIs fail.

📄 Download Summary

After each run, a download_summary.json file is saved in your mods folder. This includes:

  List of downloaded mods
  Success/failure/skipped counts
  Download timestamp

• GDWeave
• FishingSeason
• GrowthHelper

  Known Issues

Thunderstore API downtime may cause fallback to HTML parsing.
Mods with non-standard folder structures might not extract correctly.
GUI responsiveness may lag slightly during heavy extraction (runs in thread but still Tkinter-based).

MIT License

Contributing
Pull requests are welcome! If you spot bugs or want to improve functionality, feel free to open issues or contribute.

Credits

Developed using:

  Python
  Tkinter
  Thunderstore API
