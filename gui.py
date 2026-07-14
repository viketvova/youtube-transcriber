#!/usr/bin/env python3
"""YouTube Video Transcriber - Modern GUI"""

import os, re, sys, threading, tempfile, shutil, time
from pathlib import Path
from tkinter import (
    Tk, Label, Entry, Button, StringVar, OptionMenu, Listbox,
    Frame, LabelFrame, Text, Scrollbar, messagebox, END, IntVar, Menu, Checkbutton, BooleanVar
)
from tkinter import ttk

from transcribe import (
    download_video, prepare_audio, transcribe_audio,
    format_output, parse_time, format_timestamp
)

# === Color Themes ===
THEMES = {
    "dark": {
        "bg": "#1e1e2e", "fg": "#cdd6f4", "accent": "#89b4fa",
        "surface": "#313244", "surface2": "#45475a", "surface3": "#585b70",
        "green": "#a6e3a1", "red": "#f38ba8", "yellow": "#f9e2af",
        "blue": "#89b4fa", "muted": "#6c7086", "border": "#45475a",
        "entry_bg": "#313244", "entry_fg": "#cdd6f4",
        "btn_bg": "#89b4fa", "btn_fg": "#1e1e2e",
        "btn_hover": "#b4d0fb", "btn_disabled": "#45475a",
        "listbox_bg": "#313244", "listbox_fg": "#cdd6f4",
        "listbox_select": "#45475a", "highlight_bg": "#f9e2af40",
    },
    "light": {
        "bg": "#eff1f5", "fg": "#4c4f69", "accent": "#1e66f5",
        "surface": "#ccd0da", "surface2": "#bcc0cc", "surface3": "#acb0be",
        "green": "#40a02b", "red": "#d20f39", "yellow": "#df8e1d",
        "blue": "#1e66f5", "muted": "#7c7f93", "border": "#bcc0cc",
        "entry_bg": "#ffffff", "entry_fg": "#4c4f69",
        "btn_bg": "#1e66f5", "btn_fg": "#ffffff",
        "btn_hover": "#4d8af7", "btn_disabled": "#ccd0da",
        "listbox_bg": "#ffffff", "listbox_fg": "#4c4f69",
        "listbox_select": "#ccd0da", "highlight_bg": "#df8e1d40",
    },
}


class TranscriberGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title("YouTube Transcriber")
        self.root.geometry("950x780")
        self.root.minsize(750, 600)
        self.root.resizable(True, True)
        
        self.is_processing = False
        self.start_time_epoch = 0
        self.transcriptions_dir = os.path.join(os.getcwd(), "transcriptions")
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        
        self.theme_name = BooleanVar(value=False)  # False=dark, True=light
        self.theme = THEMES["dark"]
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.setup_ui()
        self.apply_theme()
        self.refresh_history()
    
    def setup_ui(self):
        # Main container
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        
        # === Top Bar ===
        self.top_bar = Frame(self.main_frame)
        self.top_bar.pack(fill="x", padx=16, pady=(12, 0))
        
        Label(self.top_bar, text="YouTube Transcriber", font=("Segoe UI Semibold", 16)).pack(side="left")
        
        # Theme toggle
        self.theme_frame = Frame(self.top_bar)
        self.theme_frame.pack(side="right")
        
        self.theme_label = Label(self.theme_frame, text="Dark", font=("Segoe UI", 9))
        self.theme_label.pack(side="left", padx=(0, 6))
        
        self.theme_switch = ttk.Checkbutton(self.theme_frame, variable=self.theme_name,
                                             style="Switch.TCheckbutton",
                                             command=self.toggle_theme)
        self.theme_switch.pack(side="left")
        
        self.theme_label2 = Label(self.theme_frame, text="Light", font=("Segoe UI", 9))
        self.theme_label2.pack(side="left", padx=(6, 0))
        
        # === Content Area ===
        content = Frame(self.main_frame)
        content.pack(fill="both", expand=True, padx=16, pady=12)
        
        # -- Left column: controls --
        left = Frame(content, width=420)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)
        
        # URL
        self._make_section(left, "YouTube URL")
        url_frame = Frame(left)
        url_frame.pack(fill="x", pady=(0, 12))
        
        self.url_var = StringVar()
        self.url_entry = Entry(url_frame, textvariable=self.url_var, font=("Segoe UI", 11))
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.url_entry.bind("<Control-v>", self._on_ctrl_v)
        self.url_entry.bind("<Control-V>", self._on_ctrl_v)
        
        self.paste_btn = Button(url_frame, text="Paste", command=self.paste_url,
                                font=("Segoe UI", 10, "bold"), width=7, relief="flat")
        self.paste_btn.pack(side="left", padx=(6, 0))
        
        # Time Range
        self._make_section(left, "Time Range (optional)")
        time_frame = Frame(left)
        time_frame.pack(fill="x", pady=(0, 12))
        
        Label(time_frame, text="From", font=("Segoe UI", 9)).pack(side="left")
        self.start_var = StringVar()
        self.start_entry = Entry(time_frame, textvariable=self.start_var, width=9,
                                 font=("Consolas", 11), justify="center")
        self.start_entry.pack(side="left", padx=(4, 12))
        
        Label(time_frame, text="To", font=("Segoe UI", 9)).pack(side="left")
        self.end_var = StringVar()
        self.end_entry = Entry(time_frame, textvariable=self.end_var, width=9,
                               font=("Consolas", 11), justify="center")
        self.end_entry.pack(side="left", padx=(4, 12))
        
        Label(time_frame, text="HH:MM:SS", font=("Segoe UI", 8)).pack(side="left")
        
        # Settings row
        self._make_section(left, "Settings")
        settings_frame = Frame(left)
        settings_frame.pack(fill="x", pady=(0, 12))
        
        # Language
        lang_frame = Frame(settings_frame)
        lang_frame.pack(side="left", padx=(0, 16))
        Label(lang_frame, text="Language", font=("Segoe UI", 8)).pack(anchor="w")
        self.lang_var = StringVar(value="ru")
        self.lang_menu = OptionMenu(lang_frame, self.lang_var, "ru", "en", "uk")
        self.lang_menu.config(width=4, font=("Segoe UI", 10))
        self.lang_menu.pack()
        
        # Chunk
        chunk_frame = Frame(settings_frame)
        chunk_frame.pack(side="left", padx=(0, 16))
        Label(chunk_frame, text="Chunk min", font=("Segoe UI", 8)).pack(anchor="w")
        self.chunk_var = StringVar(value="5")
        self.chunk_menu = OptionMenu(chunk_frame, self.chunk_var, "1", "3", "5", "10", "15")
        self.chunk_menu.config(width=4, font=("Segoe UI", 10))
        self.chunk_menu.pack()
        
        # Model
        model_frame = Frame(settings_frame)
        model_frame.pack(side="left")
        Label(model_frame, text="Model", font=("Segoe UI", 8)).pack(anchor="w")
        self.model_var = StringVar(value="medium")
        self.model_menu = OptionMenu(model_frame, self.model_var, "tiny", "base", "small", "medium", "large")
        self.model_menu.config(width=7, font=("Segoe UI", 10))
        self.model_menu.pack()
        
        # Progress
        self.progress_var = IntVar(value=0)
        self.progress_bar = ttk.Progressbar(left, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(0, 4))
        
        status_frame = Frame(left)
        status_frame.pack(fill="x", pady=(0, 12))
        self.status_var = StringVar(value="Ready")
        self.status_label = Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 9))
        self.status_label.pack(side="left")
        self.time_left_var = StringVar(value="")
        self.time_left_label = Label(status_frame, textvariable=self.time_left_var, font=("Segoe UI", 9))
        self.time_left_label.pack(side="right")
        
        # Buttons
        btn_frame = Frame(left)
        btn_frame.pack(fill="x", pady=(0, 4))
        
        self.start_btn = Button(btn_frame, text="Start Transcription",
                                command=self.start_transcription,
                                font=("Segoe UI", 11, "bold"), relief="flat", pady=6, padx=20)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        
        self.stop_btn = Button(btn_frame, text="Stop", command=self.stop_transcription,
                               font=("Segoe UI", 10), relief="flat", state="disabled", pady=6, padx=12)
        self.stop_btn.pack(side="left")
        
        # History list (compact, below buttons)
        self._make_section(left, "History")
        hist_top = Frame(left)
        hist_top.pack(fill="x", pady=(0, 4))
        
        self.hist_search_var = StringVar()
        self.hist_search_entry = Entry(hist_top, textvariable=self.hist_search_var,
                                       font=("Segoe UI", 9), width=20)
        self.hist_search_entry.pack(side="left", fill="x", expand=True)
        self.hist_search_var.trace_add("write", lambda *a: self.filter_history())
        
        self.history_listbox = Listbox(left, font=("Consolas", 9), height=6, relief="flat",
                                       activestyle="none", selectmode="single")
        self.history_listbox.pack(fill="both", expand=True, pady=(0, 4))
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)
        
        hist_btns = Frame(left)
        hist_btns.pack(fill="x")
        Button(hist_btns, text="Open Transcriptions", command=self.open_transcriptions_folder,
               font=("Segoe UI", 8), relief="flat").pack(side="left", padx=(0, 4))
        Button(hist_btns, text="Open Downloads", command=self.open_downloads_folder,
               font=("Segoe UI", 8), relief="flat").pack(side="left")
        
        # -- Right column: tabs (Log / Result / Preview) --
        right = Frame(content)
        right.pack(side="right", fill="both", expand=True)
        
        # Search bar
        search_frame = Frame(right)
        search_frame.pack(fill="x", pady=(0, 4))
        
        self.search_var = StringVar()
        self.search_entry = Entry(search_frame, textvariable=self.search_var,
                                  font=("Segoe UI", 10), width=22)
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<Return>", lambda e: self.search_in_result())
        
        self.search_btn = Button(search_frame, text="Find", command=self.search_in_result,
                                 font=("Segoe UI", 9), relief="flat", padx=10)
        self.search_btn.pack(side="left", padx=(0, 4))
        
        Button(search_frame, text="Clear", command=self.clear_search,
               font=("Segoe UI", 9), relief="flat", padx=8).pack(side="left")
        
        self.search_status = StringVar(value="")
        self.search_status_label = Label(search_frame, textvariable=self.search_status,
                                         font=("Segoe UI", 8))
        self.search_status_label.pack(side="left", padx=(12, 0))
        
        # Tabs
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        
        # Log
        log_frame = Frame(self.tabs)
        self.tabs.add(log_frame, text="  Log  ")
        self.log_text = Text(log_frame, font=("Consolas", 9), wrap="word",
                             undo=False, insertwidth=0, highlightthickness=0, relief="flat")
        log_scroll = Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        self.log_text.config(state="disabled")
        self.log_text.tag_config("success", foreground="#a6e3a1")
        self.log_text.tag_config("error", foreground="#f38ba8")
        self.log_text.tag_config("info", foreground="#89b4fa")
        
        # Result
        result_frame = Frame(self.tabs)
        self.tabs.add(result_frame, text="  Result  ")
        self.result_text = Text(result_frame, font=("Consolas", 10), wrap="word",
                                undo=False, insertwidth=0, highlightthickness=0, relief="flat")
        result_scroll = Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.config(yscrollcommand=result_scroll.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        result_scroll.pack(side="right", fill="y")
        self.result_text.tag_config("highlight", background="#f9e2af", foreground="#1e1e2e")
        self.result_text.bind("<Key>", lambda e: "break")
        self.result_text.bind("<Control-a>", lambda e: self.result_text.tag_add("sel", "1.0", END) or "break")
        
        result_menu = Menu(self.result_text, tearoff=0)
        result_menu.add_command(label="Copy Selected", command=self.copy_selected_result)
        result_menu.add_command(label="Copy All", command=self.copy_result)
        self.result_text.bind("<Button-3>", lambda e: result_menu.tk_popup(e.x_root, e.y_root))
        
        # Preview (History)
        preview_frame = Frame(self.tabs)
        self.tabs.add(preview_frame, text="  Preview  ")
        self.history_preview = Text(preview_frame, font=("Consolas", 10), wrap="word",
                                    undo=False, insertwidth=0, highlightthickness=0, relief="flat")
        preview_scroll = Scrollbar(preview_frame, command=self.history_preview.yview)
        self.history_preview.config(yscrollcommand=preview_scroll.set)
        self.history_preview.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")
        self.history_preview.bind("<Key>", lambda e: "break")
        self.history_preview.bind("<Control-a>", lambda e: self.history_preview.tag_add("sel", "1.0", END) or "break")
        
        prev_menu = Menu(self.history_preview, tearoff=0)
        prev_menu.add_command(label="Copy Selected", command=self.copy_selected_history)
        prev_menu.add_command(label="Copy All", command=self.copy_history_preview)
        self.history_preview.bind("<Button-3>", lambda e: prev_menu.tk_popup(e.x_root, e.y_root))
        
        # Bind Ctrl+F
        self.root.bind("<Control-f>", lambda e: self.focus_search())
        self.root.bind("<Control-F>", lambda e: self.focus_search())
    
    def _make_section(self, parent, title):
        Label(parent, text=title, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 4))
    
    # === Theme ===
    def toggle_theme(self):
        self.theme = THEMES["light"] if self.theme_name.get() else THEMES["dark"]
        self.apply_theme()
    
    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])
        self.main_frame.configure(bg=t["bg"])
        self.top_bar.configure(bg=t["bg"])
        
        for w in self.top_bar.winfo_children():
            if isinstance(w, Label):
                w.configure(bg=t["bg"], fg=t["fg"])
        
        self.theme_frame.configure(bg=t["bg"])
        self.theme_label.configure(bg=t["bg"], fg=t["muted"])
        self.theme_label2.configure(bg=t["bg"], fg=t["muted"])
        
        # Style widgets
        self.style.configure(".", background=t["bg"], foreground=t["fg"], fieldbackground=t["entry_bg"],
                             borderwidth=0, troughcolor=t["surface"])
        self.style.configure("TCheckbutton", background=t["bg"], foreground=t["fg"])
        self.style.map("TCheckbutton", background=[("active", t["bg"])])
        
        # Switch style
        self.style.configure("Switch.TCheckbutton", background=t["bg"], troughcolor=t["surface"],
                             indicatorcolor=t["surface3"])
        self.style.map("Switch.TCheckbutton",
                       indicatorcolor=[("selected", t["accent"])])
        
        # Progress bar
        self.style.configure("TProgressbar", background=t["accent"], troughcolor=t["surface"],
                             borderwidth=0, lightcolor=t["accent"], darkcolor=t["accent"])
        
        # Notebook
        self.style.configure("TNotebook", background=t["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=t["surface"], foreground=t["fg"],
                             padding=[12, 6], font=("Segoe UI", 9))
        self.style.map("TNotebook.Tab",
                       background=[("selected", t["surface2"])],
                       foreground=[("selected", t["accent"])])
        
        # Labels
        for frame in [self.main_frame, self.top_bar]:
            for w in frame.winfo_children():
                try:
                    if isinstance(w, Label):
                        w.configure(bg=t["bg"], fg=t["fg"])
                except:
                    pass
        
        # Apply to all sub-frames recursively
        self._apply_to_all(self.main_frame, t)
    
    def _apply_to_all(self, widget, t):
        try:
            wtype = widget.winfo_class()
            if wtype == "Frame":
                widget.configure(bg=t["bg"])
            elif wtype == "Label":
                fg = t["fg"]
                try:
                    txt = widget.cget("text")
                    if txt in ("Dark", "Light"):
                        fg = t["muted"]
                except:
                    pass
                widget.configure(bg=t["bg"], fg=fg)
            elif wtype == "Entry":
                widget.configure(bg=t["entry_bg"], fg=t["entry_fg"],
                                 insertbackground=t["fg"], relief="flat")
            elif wtype == "Button":
                widget.configure(bg=t["surface2"], fg=t["fg"], activebackground=t["surface3"],
                                 activeforeground=t["fg"], relief="flat")
            elif wtype == "Text":
                widget.configure(bg=t["surface"], fg=t["fg"], insertbackground=t["fg"],
                                 selectbackground=t["accent"], selectforeground=t["btn_fg"],
                                 relief="flat")
            elif wtype == "Listbox":
                widget.configure(bg=t["listbox_bg"], fg=t["listbox_fg"],
                                 selectbackground=t["listbox_select"], selectforeground=t["fg"],
                                 relief="flat", highlightbackground=t["border"])
            elif wtype == "Menubutton":
                widget.configure(bg=t["surface2"], fg=t["fg"], activebackground=t["surface3"],
                                 activeforeground=t["fg"], relief="flat")
        except:
            pass
        
        for child in widget.winfo_children():
            self._apply_to_all(child, t)
    
    # === Clipboard ===
    def _on_ctrl_v(self, event=None):
        try:
            text = self.root.clipboard_get()
            self.url_entry.delete(0, END)
            self.url_entry.insert(0, text.strip())
        except:
            pass
        return "break"
    
    def paste_url(self):
        try:
            self.url_var.set(self.root.clipboard_get().strip())
        except:
            pass
    
    def copy_log(self):
        self.log_text.config(state="normal")
        text = self.log_text.get("1.0", END).strip()
        self.log_text.config(state="disabled")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
    
    def copy_result(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.result_text.get("1.0", END).strip())
    
    def copy_selected_result(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.result_text.get("sel.first", "sel.last"))
        except:
            pass
    
    def copy_history_preview(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.history_preview.get("1.0", END).strip())
    
    def copy_selected_history(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.history_preview.get("sel.first", "sel.last"))
        except:
            pass
    
    # === Log ===
    def log(self, message, tag=None):
        self.log_text.config(state="normal")
        if tag:
            self.log_text.insert(END, message + "\n", tag)
        else:
            self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state="disabled")
    
    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", END)
        self.log_text.config(state="disabled")
        self.result_text.delete("1.0", END)
        self.tabs.select(0)
    
    def show_result(self, text):
        self.result_text.delete("1.0", END)
        self.result_text.insert("1.0", text)
        self.tabs.select(1)
    
    # === Search ===
    def focus_search(self):
        self.tabs.select(1)
        self.search_entry.focus_set()
        self.search_entry.select_range(0, END)
    
    def search_in_result(self):
        query = self.search_var.get().strip()
        if not query:
            return
        self.result_text.tag_remove("highlight", "1.0", END)
        count = 0
        start = "1.0"
        while True:
            pos = self.result_text.search(query, start, stopindex=END, nocase=True)
            if not pos:
                break
            self.result_text.tag_add("highlight", pos, f"{pos}+{len(query)}c")
            count += 1
            start = f"{pos}+{len(query)}c"
        self.search_status.set(f"{count} found")
        if count > 0:
            first = self.result_text.search(query, "1.0", stopindex=END, nocase=True)
            if first:
                self.result_text.see(first)
    
    def clear_search(self):
        self.search_var.set("")
        self.search_status.set("")
        self.result_text.tag_remove("highlight", "1.0", END)
    
    # === History ===
    def refresh_history(self):
        self._all_history = []
        self.history_listbox.delete(0, END)
        if not os.path.isdir(self.transcriptions_dir):
            return
        for f in sorted(Path(self.transcriptions_dir).glob("*.txt"), key=os.path.getmtime, reverse=True):
            self._all_history.append((f.stem, str(f)))
        self.filter_history()
    
    def filter_history(self):
        query = self.hist_search_var.get().strip().lower()
        self.history_listbox.delete(0, END)
        self._history_files = []
        for name, path in self._all_history:
            if query and query not in name.lower():
                continue
            self.history_listbox.insert(END, name)
            self._history_files.append(path)
    
    def on_history_select(self, event=None):
        sel = self.history_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._history_files):
            try:
                with open(self._history_files[idx], "r", encoding="utf-8") as f:
                    content = f.read()
                self.history_preview.delete("1.0", END)
                self.history_preview.insert("1.0", content)
                self.tabs.select(2)  # Switch to Preview tab
            except Exception as e:
                self.history_preview.delete("1.0", END)
                self.history_preview.insert("1.0", f"Error: {e}")
    
    def open_transcriptions_folder(self):
        os.startfile(self.transcriptions_dir)
    
    def open_downloads_folder(self):
        d = os.path.join(os.path.dirname(__file__), "downloads")
        os.makedirs(d, exist_ok=True)
        os.startfile(d)
    
    # === Progress ===
    def set_progress(self, value, status=None, time_left=None):
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        if time_left is not None:
            self.time_left_var.set(time_left)
        self.root.update_idletasks()
    
    def set_processing(self, state):
        self.is_processing = state
        self.start_btn.config(state="disabled" if state else "normal")
        self.stop_btn.config(state="normal" if state else "disabled")
    
    def validate_url(self, url):
        return bool(re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)', url))
    
    def stop_transcription(self):
        self.is_processing = False
        self.log("Stopping...", "info")
    
    # === Transcription ===
    def start_transcription(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL")
            return
        if not self.validate_url(url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return
        self.clear_log()
        self.set_progress(0, "Starting...", "")
        self.set_processing(True)
        self.start_time_epoch = time.time()
        threading.Thread(target=self.run_transcription, args=(url,), daemon=True).start()
    
    def update_time_left(self, progress):
        if progress > 0:
            elapsed = time.time() - self.start_time_epoch
            remaining = elapsed / (progress / 100) - elapsed
            if remaining > 0:
                self.time_left_var.set(f"~{int(remaining//60)}m {int(remaining%60)}s left")
            else:
                self.time_left_var.set("")
    
    def run_transcription(self, url):
        lang = self.lang_var.get()
        model = self.model_var.get()
        chunk = int(self.chunk_var.get())
        start_sec = parse_time(self.start_var.get().strip()) if self.start_var.get().strip() else 0.0
        end_sec = parse_time(self.end_var.get().strip()) if self.end_var.get().strip() else 0.0
        
        lang_names = {"ru": "Russian", "en": "English", "uk": "Ukrainian"}
        self.log(f"URL: {url}", "info")
        self.log(f"Language: {lang_names.get(lang, lang)} | Model: {model} | Chunk: {chunk}min", "info")
        if start_sec > 0 or end_sec > 0:
            self.log(f"Time: {format_timestamp(start_sec)} - {format_timestamp(end_sec) if end_sec > 0 else 'end'}", "info")
        self.log("-" * 50)
        
        downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix="yt_", dir=downloads_dir)
        
        try:
            self.set_progress(5, "Downloading...", "")
            self.log("[1/3] Downloading video...")
            try:
                video_path = download_video(url, temp_dir)
            except Exception as e:
                self.log(f"Download error: {e}", "error")
                return
            if not video_path:
                self.log("Download failed", "error")
                return
            if not self.is_processing:
                return
            
            self.set_progress(35, "Preparing audio...", "")
            self.log("[2/3] Preparing audio...")
            audio_path = prepare_audio(video_path, temp_dir, start_sec, end_sec)
            if not audio_path:
                self.log("Audio preparation failed", "error")
                return
            if not self.is_processing:
                return
            
            self.set_progress(45, "Loading model...", "")
            self.log(f"[3/3] Transcribing ({model})...")
            
            def progress_callback(done, _):
                self.set_progress(min(45 + int(done * 0.5), 95), f"Segments: {done}", "")
                self.update_time_left(min(45 + int(done * 0.5), 95))
            
            segments = transcribe_audio(audio_path, model_size=model, language=lang,
                                        time_offset=start_sec, progress_callback=progress_callback)
            if not segments:
                self.log("Transcription failed", "error")
                return
            
            self.set_progress(98, "Saving...", "")
            output_text = format_output(segments, url, chunk)
            
            # Get title
            try:
                import subprocess, json
                r = subprocess.run([sys.executable, "-m", "yt_dlp", "--dump-json", "--skip-download", url],
                                   capture_output=True, text=True, timeout=30)
                title = json.loads(r.stdout).get("title", "") if r.returncode == 0 else ""
            except:
                title = ""
            
            if title:
                safe = re.sub(r'[<>:"/\\|?*]', '_', title)[:80]
                filename = f"{safe}.txt"
            else:
                vid = re.search(r'(?:v=|youtu\.be/)([^&?]+)', url)
                filename = f"transcript_{vid.group(1)[:11]}.txt" if vid else "transcript.txt"
            
            output_path = os.path.join(self.transcriptions_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            
            elapsed = time.time() - self.start_time_epoch
            self.set_progress(100, "Done!", f"{int(elapsed//60)}m {int(elapsed%60)}s")
            self.log("-" * 50)
            self.log(f"Saved: {filename}", "success")
            self.log(f"Segments: {len(segments)} | Time: {int(elapsed//60)}m {int(elapsed%60)}s", "success")
            
            self.show_result(output_text)
            self.refresh_history()
        except Exception as e:
            self.log(f"Error: {e}", "error")
            self.set_progress(0, "Error", "")
        finally:
            self.set_processing(False)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = TranscriberGUI()
        app.run()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        with open(os.path.join(os.path.dirname(__file__), "error.log"), "w") as f:
            f.write(tb)
        input("Press Enter to exit...")
