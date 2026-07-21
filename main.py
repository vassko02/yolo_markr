"""Main entry point for the YOLO Annotation Tool managing zoom, duplicate copy, and filter sorting pipelines."""

import os
import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import ttk
from PIL import Image, ImageTk

from config.config import DRAW_MODE_RECT, DRAW_MODE_POLY, COLOR_PALETTE, THEMES
from data.storage_manager import StorageManager
from ui.canvas_manager import CanvasManager
from ui.layout_manager import LayoutManager

class YoloAnnotatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Real-time Unified Annotator - yolo-markr")
        self.root.geometry("1420x900")
        
        self.current_theme = "dark"
        self.root.configure(bg=THEMES[self.current_theme]["bg_main"])

        self.style = ttk.Style()
        self.theme_use_setting = self.style.theme_use("clam")
        self.update_ttk_styles()

        self.storage = StorageManager()
        self.canvas_mgr = None

        self.classes = ["person", "car", "chair", "dog", "bottle"]
        self.current_idx = -1
        self.current_class_idx = 0
        self.draw_mode = DRAW_MODE_RECT
        self.mode_var = tk.StringVar(value=DRAW_MODE_RECT)

        # File List view memory mappings
        self.filtered_files = []

        self.orig_image = None
        self.display_image = None
        self.annotations = []
        self.current_poly_points = []
        self.copied_annotation = None  # Clipboard memory

        # Undo / Redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Interaction tracking positions
        self.start_x = None
        self.start_y = None
        self.current_rect_id = None
        self.selected_ann_idx = None
        self.is_dragging = False
        self.active_handle = None
        self.drag_start_img_x = 0
        self.drag_start_img_y = 0
        
        # Panning anchors
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.layout_mgr = LayoutManager(self.root, self)
        self.layout_mgr.build_ui()
        self.canvas_mgr = CanvasManager(self.canvas)
        self.update_class_listbox()

        # Core global shortcuts
        self.root.bind("<Delete>", self.delete_selected_annotation)
        self.root.bind("<Key>", self.on_key_press)
        self.root.bind("<Control-c>", self.copy_selected_annotation)
        self.root.bind("<Control-v>", self.paste_selected_annotation)
        
        # Undo / Redo shortcuts
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-Z>", self.undo)
        self.root.bind("<Control-y>", self.redo)
        self.root.bind("<Control-Y>", self.redo)

        # Dynamic search and status layout queries hooks
        self.ent_search.bind("<KeyRelease>", lambda e: self.refresh_file_list())
        self.cmb_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_file_list())

        # Canvas operations hooks
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        self.class_listbox.bind("<<ListboxSelect>>", self.on_class_select)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Double-Button-1>", self.finish_polygon)
        self.txt_display.bind("<KeyRelease>", self.on_txt_modified)

        # Zoom & Panning listeners hooks
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)  # Windows
        self.canvas.bind("<Control-Button-4>", self.on_zoom)    # Linux scroll up
        self.canvas.bind("<Control-Button-5>", self.on_zoom)    # Linux scroll down
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)  # Middle mouse click
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)

    def update_ttk_styles(self):
        c = THEMES[self.current_theme]
        self.style.configure("Dark.TRadiobutton", background=c["bg_main"], foreground=c["fg_label"], font=("Segoe UI", 10, "bold"), padding=6)
        self.style.map("Dark.TRadiobutton", background=[("selected", c["btn_nav_active"]), ("active", c["btn_nav_active"])], foreground=[("selected", "#007bff"), ("active", c["fg_label"])])

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.root.configure(bg=THEMES[self.current_theme]["bg_main"])
        self.update_ttk_styles()
        self.layout_mgr.refresh_theme_styles()
        self.render_canvas_image()

    def change_mode(self):
        self.draw_mode = self.mode_var.get()
        self.current_poly_points = []
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)
    
    def update_class_listbox(self):
        """Syncs the tag class array list items into the UI selector view with unique color coding."""
        self.class_listbox.delete(0, tk.END)
        for i, cls in enumerate(self.classes):
            self.class_listbox.insert(tk.END, f" {i:2} : {cls}")
            
            label_color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
            self.class_listbox.itemconfig(i, fg=label_color)
            
        self.class_listbox.selection_set(self.current_class_idx)

    def on_class_select(self, event):
        selection = self.class_listbox.curselection()
        if selection:
            target_class = selection[0]
            if self.current_class_idx != target_class or self.selected_ann_idx is not None:
                self.current_class_idx = target_class
                if self.selected_ann_idx is not None:
                    self.save_history_state()
                    self.annotations[self.selected_ann_idx]["class_idx"] = self.current_class_idx
                    self.save_current_state()

    def add_label(self):
        name = simpledialog.askstring("New Label", "Label name:")
        if name:
            self.classes.append(name.strip())
            self.update_class_listbox()
            self.storage.save_classes(self.classes)

    def edit_label(self):
        idx = self.current_class_idx
        old_name = self.classes[idx]
        new_name = simpledialog.askstring("Edit Label", "New name:", initialvalue=old_name)
        if new_name:
            self.classes[idx] = new_name.strip()
            self.update_class_listbox()
            self.storage.save_classes(self.classes)

    def remove_label(self):
        if len(self.classes) > 1:
            self.classes.pop(self.current_class_idx)
            self.current_class_idx = 0
            self.update_class_listbox()
            self.storage.save_classes(self.classes)

    def select_directory(self):
        selected = filedialog.askdirectory()
        if not selected: return
        self.storage.setup_directories(selected)
        self.refresh_file_list()
        
        loaded_classes = self.storage.load_classes()
        if loaded_classes:
            self.classes = loaded_classes
            self.current_class_idx = 0
            self.update_class_listbox()
        
        if self.filtered_files:
            self.current_idx = 0
            self.load_image()

    def refresh_file_list(self):
        """Filters the raw repository image files based on search queries and labeled tags states."""
        self.file_listbox.delete(0, tk.END)
        search_query = self.ent_search.get().lower().strip()
        status_filter = self.cmb_filter.get()

        self.filtered_files = []
        for f in self.storage.image_files:
            is_labeled = self.storage.is_image_labeled(f)
            
            if status_filter == "Labeled (✔)" and not is_labeled: continue
            if status_filter == "Unlabeled" and is_labeled: continue
            if search_query and search_query not in f.lower(): continue
            
            self.filtered_files.append(f)

        for f in self.filtered_files:
            prefix = "✔ " if self.storage.is_image_labeled(f) else "  "
            self.file_listbox.insert(tk.END, prefix + f)
            if "✔" in prefix:
                self.file_listbox.itemconfig(tk.END, fg="#28a745")

        total = len(self.storage.image_files)
        self.lbl_file_count.config(text=f"Filtered: {len(self.filtered_files)} / Total: {total}")

    def load_image(self):
        if self.current_idx < 0 or not self.filtered_files: return
        
        if self.canvas_mgr:
            self.canvas_mgr.zoom_level = 1.0
            self.canvas_mgr.pan_x = 0.0
            self.canvas_mgr.pan_y = 0.0

        img_name = self.filtered_files[self.current_idx]
        path = os.path.join(self.storage.image_dir, img_name)
        self.orig_image = Image.open(path)
        self.current_poly_points = []
        self.selected_ann_idx = None

        # Reset history stacks on image change
        self.undo_stack = []
        self.redo_stack = []

        iw, ih = self.orig_image.size
        cw, ch = self.canvas.winfo_width() or 800, self.canvas.winfo_height() or 600
        self.canvas_mgr.update_scales(cw, ch, iw, ih)
        
        self.annotations = self.storage.load_labels(img_name, iw, ih)
        self.render_canvas_image()
        self.update_txt_preview()

    # --- ENHANCED: REAL-TIME ZOOM AND PANNING RENDERING ---
    def render_canvas_image(self):
        """Dynamically re-samples the image frame matching active zoom configurations and draws it."""
        if not self.orig_image: return
        cw, ch = self.canvas.winfo_width() or 800, self.canvas.winfo_height() or 600
        iw, ih = self.orig_image.size
        
        # Base scale widths matching setup operations values
        nw, nh = int(iw * self.canvas_mgr.scale_x), int(ih * self.canvas_mgr.scale_y)
        
        # Append magnification levels adjustments matrix calculations
        zw, zh = int(nw * self.canvas_mgr.zoom_level), int(nh * self.canvas_mgr.zoom_level)
        if zw < 10 or zh < 10: return

        img_resized = self.orig_image.resize((zw, zh), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(img_resized)
        
        self.canvas.delete("all")
        # Center drawing offsets append values variables injection
        cx = cw // 2 + self.canvas_mgr.pan_x
        cy = ch // 2 + self.canvas_mgr.pan_y
        self.canvas.create_image(cx, cy, image=self.display_image)
        
        # Re-sync offsets definitions
        self.canvas_mgr.offset_x = (cw - zw) // 2
        self.canvas_mgr.offset_y = (ch - zh) // 2
        
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def save_current_state(self):
        img_name = self.filtered_files[self.current_idx]
        iw, ih = self.orig_image.size
        self.storage.save_labels(img_name, self.annotations, iw, ih)
        self.update_txt_preview()
        self.refresh_file_list()
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def save_history_state(self):
        """Saves a deep copy of the current annotations to the undo stack before any modification."""
        import copy
        if len(self.undo_stack) >= 50:
            self.undo_stack.pop(0)
        self.undo_stack.append(copy.deepcopy(self.annotations))
        self.redo_stack.clear()

    def undo(self, event=None):
        """Reverts the last annotation action (Ctrl+Z) and forces a clean canvas redraw."""
        if self.undo_stack:
            import copy
            self.redo_stack.append(copy.deepcopy(self.annotations))
            self.annotations = self.undo_stack.pop()
            
            self.selected_ann_idx = None
            self.current_poly_points = []
            
            # Save without saving another step into history
            img_name = self.filtered_files[self.current_idx]
            iw, ih = self.orig_image.size
            self.storage.save_labels(img_name, self.annotations, iw, ih)
            self.update_txt_preview()
            self.refresh_file_list()
            
            # Explicit canvas cleanup to kill ghost outlines
            self.canvas.delete("ann")
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def redo(self, event=None):
        """Re-applies the previously reverted action (Ctrl+Y) and forces a clean canvas redraw."""
        if self.redo_stack:
            import copy
            self.undo_stack.append(copy.deepcopy(self.annotations))
            self.annotations = self.redo_stack.pop()
            
            self.selected_ann_idx = None
            self.current_poly_points = []
            
            # Save without saving another step into history
            img_name = self.filtered_files[self.current_idx]
            iw, ih = self.orig_image.size
            self.storage.save_labels(img_name, self.annotations, iw, ih)
            self.update_txt_preview()
            self.refresh_file_list()
            
            # Explicit canvas cleanup to kill ghost outlines
            self.canvas.delete("ann")
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def update_txt_preview(self):
        self.txt_display.delete("1.0", tk.END)
        if self.current_idx >= 0 and self.filtered_files:
            content = self.storage.get_txt_content(self.filtered_files[self.current_idx])
            self.txt_display.insert(tk.END, content)

    def on_txt_modified(self, event):
        if self.current_idx < 0 or not self.orig_image: return
        raw_text = self.txt_display.get("1.0", tk.END)
        img_name = self.filtered_files[self.current_idx]
        base = os.path.splitext(img_name)[0]
        txt_path = os.path.join(self.storage.labels_dir, f"{base}.txt")
        
        if raw_text.strip() == "":
            if os.path.exists(txt_path): os.remove(txt_path)
        else:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(raw_text)
        
        iw, ih = self.orig_image.size
        self.annotations = self.storage.load_labels(img_name, iw, ih)
        self.refresh_file_list()
        self.canvas.delete("ann")
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    # --- ZOOM & PAN EVENT ROUTERS ---
    def on_zoom(self, event):
        """Handles focal magnification scaling variations via Ctrl+Scroll wheel ticks."""
        if not self.orig_image: return
        
        # Determine scroll direction
        if event.num == 4 or event.delta > 0:  # Zoom In
            factor = 1.15
        else:  # Zoom Out
            factor = 0.85
            
        new_zoom = self.canvas_mgr.zoom_level * factor
        if 0.2 <= new_zoom <= 15.0:
            self.canvas_mgr.zoom_level = new_zoom
            self.render_canvas_image()

    def on_pan_start(self, event):
        """Tracks coordinates on middle mouse wheel depress interactions clicks."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def on_pan_drag(self, event):
        """Displaces view matrix tracks offsets coordinates values variables shifts."""
        if not self.orig_image: return
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        self.canvas_mgr.pan_x += dx
        self.canvas_mgr.pan_y += dy
        
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.render_canvas_image()

    # --- ENHANCED: COPY PASTE CLIPBOARD ROUTINES ---
    def copy_selected_annotation(self, event=None):
        """Saves current selected shape attributes inside application instance buffer clipboards."""
        if self.selected_ann_idx is not None and self.selected_ann_idx < len(self.annotations):
            import copy
            self.copied_annotation = copy.deepcopy(self.annotations[self.selected_ann_idx])

    def paste_selected_annotation(self, event=None):
        """Duplicates cached buffer entries shifting coordinate positions slightly."""
        if self.copied_annotation and self.orig_image:
            import copy
            self.save_history_state()
            new_ann = copy.deepcopy(self.copied_annotation)
            
            # Displace bounds metrics elements configurations slightly to highlight execution instances
            if new_ann["type"] == DRAW_MODE_RECT:
                x1, y1, x2, y2 = new_ann["points"]
                shift_x = (x2 - x1) * 0.1
                shift_y = (y2 - y1) * 0.1
                new_ann["points"] = [x1 + shift_x, y1 + shift_y, x2 + shift_x, y2 + shift_y]
            else: # Polygon offsetting math routines variations configuration arrays shifting
                new_ann["points"] = [val + (5.0 if i % 2 == 0 else 5.0) for i, val in enumerate(new_ann["points"])]
            
            self.annotations.append(new_ann)
            self.selected_ann_idx = len(self.annotations) - 1
            self.save_current_state()

    def on_mouse_move(self, event):
        if self.current_poly_points:
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, (event.x, event.y), classes_list=self.classes)

    def on_mouse_click(self, event):
        if not self.orig_image: return
        img_x, img_y = self.canvas_mgr.get_orig_coords(event.x, event.y)
        from config.config import MODE_BATCH_DEL

        if self.draw_mode == MODE_BATCH_DEL:
            self.start_x, self.start_y = event.x, event.y
            self.current_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#dc3545", dash=(4, 4), width=2, tags="ann")
            return

        if self.selected_ann_idx is not None:
            handle = self.canvas_mgr.get_handle_at_pos(event.x, event.y, self.annotations[self.selected_ann_idx])
            if handle:
                self.save_history_state()  # Dragging handles changes geometry bounds
                self.active_handle = handle
                self.is_dragging = True
                return

        clicked = self.canvas_mgr.find_annotation_at(img_x, img_y, self.annotations)
        if clicked is not None:
            self.selected_ann_idx = clicked
            self.is_dragging = True
            self.active_handle = None
            self.drag_start_img_x, self.drag_start_img_y = img_x, img_y
            self.current_class_idx = self.annotations[clicked]["class_idx"]
            self.class_listbox.selection_clear(0, tk.END)
            self.class_listbox.selection_set(self.current_class_idx)
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)
            return

        self.selected_ann_idx = None
        
        if self.draw_mode == DRAW_MODE_RECT:
            self.start_x, self.start_y = event.x, event.y
            color = COLOR_PALETTE[self.current_class_idx % len(COLOR_PALETTE)]
            self.current_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=color, width=2, tags="ann")
        elif self.draw_mode == DRAW_MODE_POLY:
            self.current_poly_points.append((img_x, img_y))
            
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, (event.x, event.y), classes_list=self.classes)

    def on_mouse_drag(self, event):
        if not self.orig_image: return
        img_x, img_y = self.canvas_mgr.get_orig_coords(event.x, event.y)
        from config.config import MODE_BATCH_DEL

        if self.draw_mode == MODE_BATCH_DEL and self.current_rect_id:
            self.canvas.coords(self.current_rect_id, self.start_x, self.start_y, event.x, event.y)
            return

        if self.is_dragging and self.selected_ann_idx is not None:
            ann = self.annotations[self.selected_ann_idx]
            if self.active_handle and ann["type"] == DRAW_MODE_RECT:
                x1, y1, x2, y2 = ann["points"]
                if self.active_handle == "nw": x1, y1 = img_x, img_y
                elif self.active_handle == "ne": x2, y1 = img_x, img_y
                elif self.active_handle == "se": x2, y2 = img_x, img_y
                elif self.active_handle == "sw": x1, y2 = img_x, img_y
                ann["points"] = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
            elif not self.active_handle:
                # If dragging the entire shape, save state once at the start of drag
                if not hasattr(self, '_drag_state_saved') or not self._drag_state_saved:
                    self.save_history_state()
                    self._drag_state_saved = True
                dx, dy = img_x - self.drag_start_img_x, img_y - self.drag_start_img_y
                if ann["type"] == DRAW_MODE_RECT:
                    ann["points"] = [ann["points"][0] + dx, ann["points"][1] + dy, ann["points"][2] + dx, ann["points"][3] + dy]
                elif ann["type"] == DRAW_MODE_POLY:
                    ann["points"] = [ann["points"][i] + (dx if i % 2 == 0 else dy) for i in range(len(ann["points"]))]
                self.drag_start_img_x, self.drag_start_img_y = img_x, img_y
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)
        elif self.draw_mode == DRAW_MODE_RECT and self.current_rect_id:
            self.canvas.coords(self.current_rect_id, self.start_x, self.start_y, event.x, event.y)
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, (event.x, event.y), classes_list=self.classes, app_instance=self)

    def on_mouse_release(self, event):
        from config.config import MODE_BATCH_DEL
        
        if hasattr(self, '_drag_state_saved'):
            self._drag_state_saved = False

        if self.draw_mode == MODE_BATCH_DEL and self.start_x is not None:
            img_x1, img_y1 = self.canvas_mgr.get_orig_coords(self.start_x, self.start_y)
            img_x2, img_y2 = self.canvas_mgr.get_orig_coords(event.x, event.y)
            min_x, max_x = min(img_x1, img_x2), max(img_x1, img_x2)
            min_y, max_y = min(img_y1, img_y2), max(img_y1, img_y2)
            
            if (max_x - min_x) > 5 and (max_y - min_y) > 5:
                self.save_history_state()
                remaining_annotations = []
                for ann in self.annotations:
                    if ann["type"] == "rectangle":
                        ax1, ay1, ax2, ay2 = ann["points"]
                        cx, cy = (ax1 + ax2) / 2, (ay1 + ay2) / 2
                    else:
                        xs = ann["points"][0::2]
                        ys = ann["points"][1::2]
                        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
                    
                    if not (min_x <= cx <= max_x and min_y <= cy <= max_y):
                        remaining_annotations.append(ann)
                
                self.annotations = remaining_annotations
                self.selected_ann_idx = None
                self.save_current_state()
            
            self.start_x = None
            if self.current_rect_id:
                self.canvas.delete(self.current_rect_id)
                self.current_rect_id = None
            return

        if self.draw_mode == DRAW_MODE_RECT and self.start_x is not None:
            img_x1, img_y1 = self.canvas_mgr.get_orig_coords(self.start_x, self.start_y)
            img_x2, img_y2 = self.canvas_mgr.get_orig_coords(event.x, event.y)
            if abs(img_x1 - img_x2) > 2 and abs(img_y1 - img_y2) > 2:
                self.save_history_state()
                pts = [min(img_x1, img_x2), min(img_y1, img_y2), max(img_x1, img_x2), max(img_y1, img_y2)]
                self.annotations.append({"type": DRAW_MODE_RECT, "class_idx": self.current_class_idx, "points": pts})
                self.save_current_state()
            self.start_x = None
        elif self.is_dragging:
            self.save_current_state()
            self.is_dragging = False
            self.active_handle = None
            
            # Explicit cleanup on release
            self.canvas.delete("ann")
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def finish_polygon(self, event):
        if self.draw_mode == DRAW_MODE_POLY and len(self.current_poly_points) >= 2:
            self.save_history_state()
            img_x, img_y = self.canvas_mgr.get_orig_coords(event.x, event.y)
            self.current_poly_points.append((img_x, img_y))
            flat_pts = [coord for pt in self.current_poly_points for coord in pt]
            self.annotations.append({"type": DRAW_MODE_POLY, "class_idx": self.current_class_idx, "points": flat_pts})
            self.current_poly_points = []
            self.save_current_state()

    def delete_selected_annotation(self, event=None):
        focused_widget = self.root.focus_get()
        if focused_widget == self.txt_display: return
        if self.selected_ann_idx is not None:
            self.save_history_state()
            self.annotations.pop(self.selected_ann_idx)
            self.selected_ann_idx = None
            
            # Explicit sync write and clear canvas
            img_name = self.filtered_files[self.current_idx]
            iw, ih = self.orig_image.size
            self.storage.save_labels(img_name, self.annotations, iw, ih)
            self.update_txt_preview()
            self.refresh_file_list()
            
            self.canvas.delete("ann")
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def on_key_press(self, event):
        focused_widget = self.root.focus_get()
        if focused_widget == self.txt_display: return

        if event.char.isdigit():
            target_idx = int(event.char)
            if target_idx < len(self.classes):
                if self.current_class_idx != target_idx or self.selected_ann_idx is not None:
                    self.current_class_idx = target_idx
                    self.class_listbox.selection_clear(0, tk.END)
                    self.class_listbox.selection_set(self.current_class_idx)
                    if self.selected_ann_idx is not None:
                        self.save_history_state()
                        self.annotations[self.selected_ann_idx]["class_idx"] = self.current_class_idx
                        self.save_current_state()
                    else:
                        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, classes_list=self.classes)

    def on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if sel:
            self.current_idx = sel[0]
            self.load_image()

    def next_image(self):
        if self.current_idx < len(self.filtered_files) - 1:
            self.current_idx += 1
            self.load_image()
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_idx)

    def prev_image(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.load_image()
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.current_idx)

if __name__ == "__main__":
    root = tk.Tk()
    app = YoloAnnotatorApp(root)
    root.mainloop()