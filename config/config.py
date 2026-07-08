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
        "bg_main": "#1e1e24",
        "bg_panel": "#141419",
        "bg_canvas": "#0d0d11",
        "bg_text": "#0d0d11",
        "fg_text": "#a9b7c6",
        "fg_label": "#ffffff",
        "fg_sub": "#a0a0a5",
        "border": "#2a2a35",
        "btn_nav": "#2a2a35",
        "btn_nav_active": "#3e3e4f"
    },
    "light": {
        "bg_main": "#f0f2f5",
        "bg_panel": "#ffffff",
        "bg_canvas": "#e4e6eb",
        "bg_text": "#ffffff",
        "fg_text": "#1c1e21",
        "fg_label": "#1c1e21",
        "fg_sub": "#606770",
        "border": "#ccd0d5",
        "btn_nav": "#e4e6eb",
        "btn_nav_active": "#d8dadf"
    }
}