"""Configuration constants for the YOLO Annotation Tool."""

DRAW_MODE_RECT = "rectangle"
DRAW_MODE_POLY = "polygon"
MODE_BATCH_DEL = "batch_delete"

COLOR_PALETTE = [
    "#FF0000", "#00FF00", "#0000FF", "#FFFF00", 
    "#FF00FF", "#00FFFF", "#FFA500", "#800080"
]

THEMES = {
    "dark": {
        "bg_main": "#1f2430",
        "bg_panel": "#24283b",
        "bg_canvas": "#1b1f2a",
        "bg_text": "#1f2430",
        "fg_text": "#e6edf7",
        "fg_label": "#f8fafc",
        "fg_sub": "#8da0bb",
        "border": "#3d4757",
        "btn_nav": "#2d3445",
        "btn_nav_active": "#39455a",
        "accent_blue": "#4f8cff",
        "accent_blue_dark": "#3478f6",
        "accent_green": "#34d399",
        "accent_green_dark": "#10b981",
        "accent_purple": "#8b5cf6",
        "accent_purple_dark": "#7c3aed",
        "accent_orange": "#f59e0b",
        "accent_orange_dark": "#d97706",
        "accent_red": "#f87171",
        "accent_red_dark": "#ef4444",
        "accent_warning": "#fbbf24",
        "hint_text": "#fbbf24",
        "selection_bg": "#4f8cff",
        "selection_fg": "#ffffff"
    },
    "light": {
        "bg_main": "#f5f7fb",
        "bg_panel": "#ffffff",
        "bg_canvas": "#eef2f7",
        "bg_text": "#ffffff",
        "fg_text": "#1f2937",
        "fg_label": "#111827",
        "fg_sub": "#64748b",
        "border": "#d7e0ea",
        "btn_nav": "#eef2f7",
        "btn_nav_active": "#dde5ef",
        "accent_blue": "#2563eb",
        "accent_blue_dark": "#1d4ed8",
        "accent_green": "#16a34a",
        "accent_green_dark": "#15803d",
        "accent_purple": "#7c3aed",
        "accent_purple_dark": "#6d28d9",
        "accent_orange": "#ea580c",
        "accent_orange_dark": "#c2410c",
        "accent_red": "#dc2626",
        "accent_red_dark": "#b91c1c",
        "accent_warning": "#d97706",
        "hint_text": "#b45309",
        "selection_bg": "#2563eb",
        "selection_fg": "#ffffff"
    }
}