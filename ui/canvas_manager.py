"""Module for handling zoomed and panned Tkinter Canvas drawing representations."""

from config.config import COLOR_PALETTE, DRAW_MODE_RECT, DRAW_MODE_POLY
import tkinter as tk

class CanvasManager:
    def __init__(self, canvas):
        self.canvas = canvas
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def update_scales(self, cw, ch, iw, ih):
        ratio = min(cw / iw, ch / ih)
        nw, nh = int(iw * ratio), int(ih * ratio)
        self.scale_x, self.scale_y = nw / iw, nh / ih
        self.offset_x, self.offset_y = (cw - nw) // 2, (ch - nh) // 2
        return nw, nh

    def get_orig_coords(self, cx, cy):
        """Maps view screen coordinates into actual original image space using zoom factor matrices."""
        x_unzoom = (cx - self.offset_x - self.pan_x) / self.zoom_level
        y_unzoom = (cy - self.offset_y - self.pan_y) / self.zoom_level
        return x_unzoom / self.scale_x, y_unzoom / self.scale_y

    def get_canvas_coords(self, ix, iy):
        """Maps source image coordinates back into local canvas space."""
        cx = (ix * self.scale_x) * self.zoom_level + self.offset_x + self.pan_x
        cy = (iy * self.scale_y) * self.zoom_level + self.offset_y + self.pan_y
        return cx, cy

    def find_annotation_at(self, img_x, img_y, annotations):
        for idx in reversed(range(len(annotations))):
            ann = annotations[idx]
            if ann["type"] == DRAW_MODE_RECT:
                x1, y1, x2, y2 = ann["points"]
                if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                    return idx
            elif ann["type"] == DRAW_MODE_POLY:
                pts = ann["points"]
                if min(pts[0::2]) <= img_x <= max(pts[0::2]) and min(pts[1::2]) <= img_y <= max(pts[1::2]):
                    return idx
        return None

    def get_handle_at_pos(self, cx, cy, selected_ann):
        if not selected_ann or selected_ann["type"] != DRAW_MODE_RECT:
            return None
        
        x1, y1 = self.get_canvas_coords(selected_ann["points"][0], selected_ann["points"][1])
        x2, y2 = self.get_canvas_coords(selected_ann["points"][2], selected_ann["points"][3])
        
        handles = {"nw": (x1, y1), "ne": (x2, y1), "se": (x2, y2), "sw": (x1, y2)}
        r = 8
        for name, (hx, hy) in handles.items():
            if hx - r <= cx <= hx + r and hy - r <= cy <= hy + r:
                return name
        return None

    def draw_all(self, annotations, selected_idx, current_poly_points, current_class_idx, mouse_pos=None, classes_list=None, app_instance=None):
        """Renders all confirmed shapes, vectors, handles, and active draw frames with category text overlays."""
        self.canvas.delete("ann")
        
        available_classes = classes_list if classes_list else []
        curr_c = COLOR_PALETTE[current_class_idx % len(COLOR_PALETTE)]
        
        for idx, ann in enumerate(annotations):
            class_idx = ann["class_idx"]
            base_c = COLOR_PALETTE[class_idx % len(COLOR_PALETTE)]
            is_selected = (idx == selected_idx)
            outline_color = "#FFC107" if is_selected else base_c
            dash_pattern = (4, 4) if is_selected else None
            width_spec = 3 if is_selected else 2
            
            tag_name = available_classes[class_idx] if class_idx < len(available_classes) else f"ID {class_idx}"
            display_text = f"{class_idx}: {tag_name}"

            if ann["type"] == DRAW_MODE_RECT:
                x1, y1 = self.get_canvas_coords(ann["points"][0], ann["points"][1])
                x2, y2 = self.get_canvas_coords(ann["points"][2], ann["points"][3])
                self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color, dash=dash_pattern, width=width_spec, tags="ann")
                
                self.canvas.create_text(x1, y1 - 10, text=display_text, fill=base_c, font=("Segoe UI", 9, "bold"), anchor=tk.W, tags="ann")
                
                if is_selected:
                    for hx, hy in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
                        self.canvas.create_rectangle(hx - 4, hy - 4, hx + 4, hy + 4, fill="#FFFFFF", outline="#000", tags="ann")
            else:
                c_pts = []
                for i in range(0, len(ann["points"]), 2):
                    c_pts.extend(self.get_canvas_coords(ann["points"][i], ann["points"][i + 1]))
                self.canvas.create_polygon(c_pts, outline=outline_color, fill="", dash=dash_pattern, width=width_spec, tags="ann")
                
                if len(c_pts) >= 2:
                    self.canvas.create_text(c_pts[0], c_pts[1] - 10, text=display_text, fill=base_c, font=("Segoe UI", 9, "bold"), anchor=tk.W, tags="ann")

        # --- LIVE RECTANGLE PREVIEW ---
        # Ha épp Rectangle módban húzzuk az egeret (létezik start_x), akkor rajzolunk egy élő segédkeretet
        if app_instance and app_instance.draw_mode == DRAW_MODE_RECT and app_instance.start_x is not None and mouse_pos:
            mx, my = mouse_pos
            self.canvas.create_rectangle(app_instance.start_x, app_instance.start_y, mx, my, outline=curr_c, dash=(4, 4), width=2, tags="ann")

        # --- LIVE POLYGON PREVIEW ---
        if current_poly_points:
            canvas_poly_pts = [self.get_canvas_coords(pt[0], pt[1]) for pt in current_poly_points]
            
            for i in range(len(canvas_poly_pts) - 1):
                self.canvas.create_line(canvas_poly_pts[i][0], canvas_poly_pts[i][1], canvas_poly_pts[i+1][0], canvas_poly_pts[i+1][1], fill=curr_c, width=2, tags="ann")
            
            if mouse_pos:
                mx, my = mouse_pos
                self.canvas.create_line(canvas_poly_pts[-1][0], canvas_poly_pts[-1][1], mx, my, fill=curr_c, width=1, dash=(2, 2), tags="ann")
                self.canvas.create_line(mx, my, canvas_poly_pts[0][0], canvas_poly_pts[0][1], fill=curr_c, width=1, dash=(2, 2), tags="ann")