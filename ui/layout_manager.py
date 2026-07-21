"""Module handling the visual layout and widget definitions for the YOLO Annotator."""

import tkinter as tk
from tkinter import ttk
from config.config import THEMES

class LayoutManager:
    """Creates and arranges all UI widgets for the application."""

    def __init__(self, root, app):
        self.root = root
        self.app = app

    def build_ui(self):
        """Assembles the left, center, and right side panels with dynamic theme bindings."""
        c = THEMES[self.app.current_theme]

        # --- LEFT PANEL ---
        self.app.left_panel = tk.Frame(self.root, width=280, bg=c["bg_panel"], padx=10, pady=10)
        self.app.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.app.left_panel.pack_propagate(False)

        self.btn_theme = tk.Button(self.app.left_panel, text="🌓 Switch Theme", command=self.app.toggle_theme,
                                   bg=c["btn_nav"], fg=c["fg_label"], font=("Segoe UI", 9, "bold"),
                                   bd=0, cursor="hand2", activebackground=c["btn_nav_active"], activeforeground=c["fg_label"],
                                   pady=4, relief=tk.FLAT)
        self.btn_theme.pack(fill=tk.X, pady=(0, 15))

        btn_folder = tk.Button(self.app.left_panel, text="📁 Select Folder", command=self.app.select_directory, 
                               bg="#007bff", fg="white", font=("Segoe UI", 10, "bold"), 
                               bd=0, cursor="hand2", activebackground="#0056b3", activeforeground="white",
                               pady=8, relief=tk.FLAT)
        btn_folder.pack(fill=tk.X, pady=(0, 10))

        # NEW: Data Augmentation Button
        self.btn_aug = tk.Button(self.app.left_panel, text="✨ Data Augmentation", command=self.app.open_augmentation_dialog, 
                                 bg="#6f42c1", fg="white", font=("Segoe UI", 10, "bold"), 
                                 bd=0, cursor="hand2", activebackground="#5a32a3", activeforeground="white",
                                 pady=8, relief=tk.FLAT)
        self.btn_aug.pack(fill=tk.X, pady=(0, 10))

        filter_frame = tk.Frame(self.app.left_panel, bg=c["bg_panel"])
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(filter_frame, text="Search:", font=("Segoe UI", 8, "bold"), bg=c["bg_panel"], fg=c["fg_sub"]).grid(row=0, column=0, sticky=tk.W)
        self.app.ent_search = tk.Entry(filter_frame, bg=c["bg_main"], fg=c["fg_label"], bd=0, highlightthickness=1, highlightbackground=c["border"], font=("Segoe UI", 9))
        self.app.ent_search.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0))
        
        tk.Label(filter_frame, text="Status:", font=("Segoe UI", 8, "bold"), bg=c["bg_panel"], fg=c["fg_sub"]).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.app.cmb_filter = ttk.Combobox(filter_frame, values=["All", "Labeled (✔)", "Unlabeled"], state="readonly", font=("Segoe UI", 9), width=15)
        self.app.cmb_filter.current(0)
        self.app.cmb_filter.grid(row=1, column=1, sticky=tk.EW, padx=(5, 0), pady=5)
        
        filter_frame.columnconfigure(1, weight=1)
        
        self.app.lbl_file_count = tk.Label(self.app.left_panel, text="Images: 0/0", bg=c["bg_panel"], fg=c["fg_sub"], font=("Segoe UI", 9, "bold"))
        self.app.lbl_file_count.pack(fill=tk.X, pady=2)

        self.app.file_listbox = tk.Listbox(self.app.left_panel, height=20, bg=c["bg_main"], fg=c["fg_label"], 
                                           selectbackground="#007bff", selectforeground="white",
                                           bd=0, highlightthickness=1, highlightbackground=c["border"],
                                           font=("Segoe UI", 9), activestyle="none")
        self.app.file_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- CENTER PANEL ---
        self.app.center_panel = tk.Frame(self.root, bg=c["bg_main"], padx=10, pady=10)
        self.app.center_panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        self.app.mode_frame = tk.Frame(self.app.center_panel, bg=c["bg_main"], pady=5)
        self.app.mode_frame.pack(fill=tk.X)
        
        from config.config import DRAW_MODE_RECT, DRAW_MODE_POLY, MODE_BATCH_DEL
        
        toggle_style = {
            "variable": self.app.mode_var,
            "command": self.app.change_mode,
            "indicatoron": False,
            "bd": 0,
            "padx": 12,
            "pady": 6,
            "font": ("Segoe UI", 9, "bold"),
            "cursor": "hand2",
            "relief": tk.FLAT,
            "overrelief": tk.FLAT
        }

        self.btn_rect = tk.Radiobutton(self.app.mode_frame, text="Rectangle Mode", value=DRAW_MODE_RECT,
                                       bg=c["btn_nav"], fg=c["fg_label"], selectcolor="#007bff", activebackground="#007bff", activeforeground="white", **toggle_style)
        self.btn_rect.pack(side=tk.LEFT, padx=3)

        self.btn_poly = tk.Radiobutton(self.app.mode_frame, text="Polygon Mode", value=DRAW_MODE_POLY,
                                       bg=c["btn_nav"], fg=c["fg_label"], selectcolor="#28a745", activebackground="#28a745", activeforeground="white", **toggle_style)
        self.btn_poly.pack(side=tk.LEFT, padx=3)

        self.btn_batch = tk.Radiobutton(self.app.mode_frame, text="🗑️ Batch Delete", value=MODE_BATCH_DEL,
                                        bg=c["btn_nav"], fg=c["fg_label"], selectcolor="#dc3545", activebackground="#dc3545", activeforeground="white", **toggle_style)
        self.btn_batch.pack(side=tk.LEFT, padx=3)
        
        self.lbl_hint = tk.Label(self.app.mode_frame, text="| Ctrl+Scroll: Zoom | Middle Mouse/Grip: Pan | Ctrl+C/V: Duplicate", bg=c["bg_main"], fg="#ffc107", font=("Segoe UI", 9, "italic"))
        self.lbl_hint.pack(side=tk.LEFT, padx=10)

        self.app.canvas = tk.Canvas(self.app.center_panel, bg=c["bg_canvas"], highlightthickness=1, highlightbackground=c["border"])
        self.app.canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- RIGHT PANEL ---
        self.app.right_panel = tk.Frame(self.root, width=320, bg=c["bg_panel"], padx=10, pady=10)
        self.app.right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.app.right_panel.pack_propagate(False)
        
        self.lbl_labels_title = tk.Label(self.app.right_panel, text="Labels (ID: Name)", font=("Segoe UI", 10, "bold"), bg=c["bg_panel"], fg=c["fg_label"])
        self.lbl_labels_title.pack(anchor=tk.W, pady=(0, 5))
        
        self.app.class_listbox = tk.Listbox(self.app.right_panel, height=10, bg=c["bg_main"], fg=c["fg_label"], 
                                            selectbackground="#28a745", selectforeground="white",
                                            bd=0, highlightthickness=1, highlightbackground=c["border"],
                                            font=("Consolas", 10), activestyle="none")
        self.app.class_listbox.pack(fill=tk.X, pady=5)

        btn_frame = tk.Frame(self.app.right_panel, bg=c["bg_panel"])
        btn_frame.pack(fill=tk.X, pady=5)
        
        button_style = {"font": ("Segoe UI", 8, "bold"), "fg": "white", "bd": 0, "cursor": "hand2", "pady": 4}
        tk.Button(btn_frame, text="➕ Add", command=self.app.add_label, bg="#28a745", activebackground="#218838", **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="✏️ Edit", command=self.app.edit_label, bg="#ffc107", activebackground="#e0a800", **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="❌ Remove", command=self.app.remove_label, bg="#dc3545", activebackground="#c82333", **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.lbl_txt_title = tk.Label(self.app.right_panel, text="Editable YOLO TXT Content", font=("Segoe UI", 10, "bold"), bg=c["bg_panel"], fg=c["fg_label"])
        self.lbl_txt_title.pack(anchor=tk.W, pady=(15, 5))
        
        self.app.txt_display = tk.Text(self.app.right_panel, height=22, bg=c["bg_text"], fg=c["fg_text"], 
                                       insertbackground=c["fg_label"], font=("Consolas", 9),
                                       bd=0, highlightthickness=1, highlightbackground=c["border"],
                                       padx=5, pady=5)
        self.app.txt_display.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- NAVIGATION PANEL ---
        self.nav_frame = tk.Frame(self.app.left_panel, bg=c["bg_panel"])
        self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.btn_prev_widget = tk.Button(self.nav_frame, text="◀ Previous", command=self.app.prev_image, font=("Segoe UI", 10, "bold"), fg="white", bg=c["btn_nav"], bd=0, cursor="hand2", pady=6, activebackground=c["btn_nav_active"], activeforeground="white")
        self.btn_prev_widget.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        
        self.btn_next_widget = tk.Button(self.nav_frame, text="Next ▶", command=self.app.next_image, font=("Segoe UI", 10, "bold"), fg="white", bg=c["btn_nav"], bd=0, cursor="hand2", pady=6, activebackground=c["btn_nav_active"], activeforeground="white")
        self.btn_next_widget.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

    def refresh_theme_styles(self):
        """Dynamically applies colors from the newly selected theme to all widgets."""
        c = THEMES[self.app.current_theme]
        
        self.app.left_panel.configure(bg=c["bg_panel"])
        self.app.center_panel.configure(bg=c["bg_main"])
        self.app.right_panel.configure(bg=c["bg_panel"])
        self.app.mode_frame.configure(bg=c["bg_main"])
        self.nav_frame.configure(bg=c["bg_panel"])
        
        self.app.lbl_file_count.configure(bg=c["bg_panel"], fg=c["fg_sub"])
        self.lbl_hint.configure(bg=c["bg_main"])
        self.lbl_labels_title.configure(bg=c["bg_panel"], fg=c["fg_label"])
        self.lbl_txt_title.configure(bg=c["bg_panel"], fg=c["fg_label"])

        self.app.file_listbox.configure(bg=c["bg_main"], fg=c["fg_label"], highlightbackground=c["border"])
        self.app.class_listbox.configure(bg=c["bg_main"], fg=c["fg_label"], highlightbackground=c["border"])
        self.app.txt_display.configure(bg=c["bg_text"], fg=c["fg_text"], insertbackground=c["fg_label"], highlightbackground=c["border"])
        self.app.canvas.configure(bg=c["bg_canvas"], highlightbackground=c["border"])
        self.app.ent_search.configure(bg=c["bg_main"], fg=c["fg_label"], highlightbackground=c["border"])

        self.btn_rect.configure(bg=c["btn_nav"], fg=c["fg_label"])
        self.btn_poly.configure(bg=c["btn_nav"], fg=c["fg_label"])
        self.btn_batch.configure(bg=c["btn_nav"], fg=c["fg_label"])

        self.btn_theme.configure(bg=c["btn_nav"], fg=c["fg_label"], activebackground=c["btn_nav_active"])
        self.btn_prev_widget.configure(bg=c["btn_nav"], activebackground=c["btn_nav_active"])
        self.btn_next_widget.configure(bg=c["btn_nav"], activebackground=c["btn_nav_active"])
        
        # New button style dynamic refresh (keeps text white but handles container updates if any)
        self.btn_aug.configure(activeforeground="white")