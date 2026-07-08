"""Module handling the visual layout and widget definitions for the YOLO Annotator."""

import tkinter as tk
from tkinter import ttk

class LayoutManager:
    """Creates and arranges all UI widgets for the application."""

    def __init__(self, root, app):
        self.root = root
        self.app = app 

    def build_ui(self):
        """Assembles the left, center, and right side panels."""
        self.app.left_panel = tk.Frame(self.root, width=280, bg="#141419", padx=10, pady=10)
        self.app.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.app.left_panel.pack_propagate(False)

        btn_folder = tk.Button(self.app.left_panel, text="📁 Select Folder", command=self.app.select_directory, 
                               bg="#007bff", fg="white", font=("Segoe UI", 10, "bold"), 
                               bd=0, cursor="hand2", activebackground="#0056b3", activeforeground="white",
                               pady=8, relief=tk.FLAT)
        btn_folder.pack(fill=tk.X, pady=(0, 10))
        
        self.app.lbl_file_count = tk.Label(self.app.left_panel, text="Images: 0/0", bg="#141419", fg="#a0a0a5", font=("Segoe UI", 9, "bold"))
        self.app.lbl_file_count.pack(fill=tk.X, pady=5)

        self.app.file_listbox = tk.Listbox(self.app.left_panel, height=25, bg="#1e1e24", fg="#ffffff", 
                                           selectbackground="#007bff", selectforeground="white",
                                           bd=0, highlightthickness=1, highlightbackground="#2a2a35",
                                           font=("Segoe UI", 9), activestyle="none")
        self.app.file_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        self.app.center_panel = tk.Frame(self.root, bg="#1e1e24", padx=10, pady=10)
        self.app.center_panel.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        self.app.mode_frame = tk.Frame(self.app.center_panel, bg="#1e1e24", pady=5)
        self.app.mode_frame.pack(fill=tk.X)
        
        from config.config import DRAW_MODE_RECT, DRAW_MODE_POLY, MODE_BATCH_DEL
        ttk.Radiobutton(self.app.mode_frame, text="Rectangle", variable=self.app.mode_var, value=DRAW_MODE_RECT, command=self.app.change_mode, style="Dark.TRadiobutton").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.app.mode_frame, text="Polygon", variable=self.app.mode_var, value=DRAW_MODE_POLY, command=self.app.change_mode, style="Dark.TRadiobutton").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.app.mode_frame, text="Delete", variable=self.app.mode_var, value=MODE_BATCH_DEL, command=self.app.change_mode, style="Dark.TRadiobutton").pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.app.mode_frame, text="|  💡 Tip: Click over a shape to drag or resize instantly!", bg="#1e1e24", fg="#ffc107", font=("Segoe UI", 9, "italic")).pack(side=tk.LEFT, padx=10)

        self.app.canvas = tk.Canvas(self.app.center_panel, bg="#0d0d11", highlightthickness=1, highlightbackground="#2a2a35")
        self.app.canvas.pack(fill=tk.BOTH, expand=True, pady=5)

        self.app.right_panel = tk.Frame(self.root, width=320, bg="#141419", padx=10, pady=10)
        self.app.right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.app.right_panel.pack_propagate(False)
        
        tk.Label(self.app.right_panel, text="Labels (ID: Name)", font=("Segoe UI", 10, "bold"), bg="#141419", fg="#ffffff").pack(anchor=tk.W, pady=(0, 5))
        
        self.app.class_listbox = tk.Listbox(self.app.right_panel, height=10, bg="#1e1e24", fg="#ffffff", 
                                            selectbackground="#28a745", selectforeground="white",
                                            bd=0, highlightthickness=1, highlightbackground="#2a2a35",
                                            font=("Consolas", 10), activestyle="none")
        self.app.class_listbox.pack(fill=tk.X, pady=5)

        btn_frame = tk.Frame(self.app.right_panel, bg="#141419")
        btn_frame.pack(fill=tk.X, pady=5)
        
        button_style = {"font": ("Segoe UI", 8, "bold"), "fg": "white", "bd": 0, "cursor": "hand2", "pady": 4}
        tk.Button(btn_frame, text="➕ Add", command=self.app.add_label, bg="#28a745", activebackground="#218838", **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="✏️ Edit", command=self.app.edit_label, bg="#ffc107", activebackground="#e0a800", **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="❌ Remove", command=self.app.remove_label, bg="#dc3545", activebackground="#c82333", **button_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        tk.Label(self.app.right_panel, text="Editable YOLO TXT Content", font=("Segoe UI", 10, "bold"), bg="#141419", fg="#ffffff").pack(anchor=tk.W, pady=(15, 5))
        
        self.app.txt_display = tk.Text(self.app.right_panel, height=22, bg="#0d0d11", fg="#a9b7c6", 
                                       insertbackground="white", font=("Consolas", 9),
                                       bd=0, highlightthickness=1, highlightbackground="#2a2a35",
                                       padx=5, pady=5)
        self.app.txt_display.pack(fill=tk.BOTH, expand=True, pady=5)

        nav_frame = tk.Frame(self.app.left_panel, bg="#141419")
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        nav_btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "bg": "#2a2a35", "bd": 0, "cursor": "hand2", "pady": 6, "activebackground": "#3e3e4f", "activeforeground": "white"}
        tk.Button(nav_frame, text="◀ Previous", command=self.app.prev_image, **nav_btn_style).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(nav_frame, text="Next ▶", command=self.app.next_image, **nav_btn_style).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))