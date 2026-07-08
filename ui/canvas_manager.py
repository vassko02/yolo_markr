"""Module for handling complex Tkinter Canvas drawing and real-time interactions."""

from config.config import COLOR_PALETTE, DRAW_MODE_RECT, DRAW_MODE_POLY

class CanvasManager:
    def __init__(self, canvas):
        self.canvas = canvas
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def update_scales(self, cw, ch, iw, ih):
        ratio = min(cw / iw, ch / ih)
        nw, nh = int(iw * ratio), int(ih * ratio)
        self.scale_x, self.scale_y = nw / iw, nh / ih
        self.offset_x, self.offset_y = (cw - nw) // 2, (ch - nh) // 2
        return nw, nh

    def get_orig_coords(self, cx, cy):
        return (cx - self.offset_x) / self.scale_x, (cy - self.offset_y) / self.scale_y

    def get_canvas_coords(self, ix, iy):
        return ix * self.scale_x + self.offset_x, iy * self.scale_y + self.offset_y

    def find_annotation_at(self, img_x, img_y, annotations):
        """Finds shape under cursor for instant editing without explicit edit mode."""
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

    def draw_all(self, annotations, selected_idx, current_poly_points, current_class_idx, mouse_pos=None):
        """Draws static annotations, handles, and live rubber-band preview lines for polygon."""
        self.canvas.delete("ann")
        
        for idx, ann in enumerate(annotations):
            base_c = COLOR_PALETTE[ann["class_idx"] % len(COLOR_PALETTE)]
            is_selected = (idx == selected_idx)
            outline_color = "#FFC107" if is_selected else base_c
            dash_pattern = (4, 4) if is_selected else None
            width_spec = 3 if is_selected else 2

            if ann["type"] == DRAW_MODE_RECT:
                x1, y1 = self.get_canvas_coords(ann["points"][0], ann["points"][1])
                x2, y2 = self.get_canvas_coords(ann["points"][2], ann["points"][3])
                self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color, dash=dash_pattern, width=width_spec, tags="ann")
                
                if is_selected:
                    for hx, hy in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
                        self.canvas.create_rectangle(hx - 4, hy - 4, hx + 4, hy + 4, fill="#FFFFFF", outline="#000", tags="ann")
            else:
                c_pts = []
                for i in range(0, len(ann["points"]), 2):
                    c_pts.extend(self.get_canvas_coords(ann["points"][i], ann["points"][i + 1]))
                self.canvas.create_polygon(c_pts, outline=outline_color, fill="", dash=dash_pattern, width=width_spec, tags="ann")

        if current_poly_points:
            curr_c = COLOR_PALETTE[current_class_idx % len(COLOR_PALETTE)]
            canvas_poly_pts = [self.get_canvas_coords(pt[0], pt[1]) for pt in current_poly_points]
            
            for i in range(len(canvas_poly_pts) - 1):
                self.canvas.create_line(canvas_poly_pts[i][0], canvas_poly_pts[i][1], 
                                        canvas_poly_pts[i+1][0], canvas_poly_pts[i+1][1], 
                                        fill=curr_c, width=2, tags="ann")
            
            if mouse_pos:
                mx, my = mouse_pos
                self.canvas.create_line(canvas_poly_pts[-1][0], canvas_poly_pts[-1][1], mx, my, fill=curr_c, width=1, dash=(2, 2), tags="ann")
                self.canvas.create_line(mx, my, canvas_poly_pts[0][0], canvas_poly_pts[0][1], fill=curr_c, width=1, dash=(2, 2), tags="ann")