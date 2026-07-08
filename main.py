"""Main entry point for the YOLO Annotation Tool coordinating layouts and events."""

import os
import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import ttk
from PIL import Image, ImageTk

from config.config import DRAW_MODE_RECT, DRAW_MODE_POLY, COLOR_PALETTE
from data.storage_manager import StorageManager
from ui.canvas_manager import CanvasManager
from ui.layout_manager import LayoutManager

class YoloAnnotatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO Markr - YOLO Annotation Tool")
        self.root.geometry("1420x900")
        self.root.configure(bg="#1e1e24")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Dark.TRadiobutton", background="#1e1e24", foreground="#ffffff", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.map("Dark.TRadiobutton", background=[("selected", "#2a2a35"), ("active", "#2a2a35")], foreground=[("selected", "#007bff")])

        self.storage = StorageManager()
        self.canvas_mgr = None

        self.classes = ["person", "car", "chair", "dog", "bottle"]
        self.current_idx = -1
        self.current_class_idx = 0
        self.draw_mode = DRAW_MODE_RECT
        self.mode_var = tk.StringVar(value=DRAW_MODE_RECT)

        self.orig_image = None
        self.display_image = None
        self.annotations = []
        self.current_poly_points = []

        self.start_x = None
        self.start_y = None
        self.current_rect_id = None
        self.selected_ann_idx = None
        self.is_dragging = False
        self.active_handle = None
        self.drag_start_img_x = 0
        self.drag_start_img_y = 0

        self.layout_mgr = LayoutManager(self.root, self)
        self.layout_mgr.build_ui()

        self.canvas_mgr = CanvasManager(self.canvas)
        self.update_class_listbox()

        self.root.bind("<Delete>", self.delete_selected_annotation)
        self.root.bind("<Key>", self.on_key_press)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        self.class_listbox.bind("<<ListboxSelect>>", self.on_class_select)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Double-Button-1>", self.finish_polygon)
        self.txt_display.bind("<KeyRelease>", self.on_txt_modified)

    def change_mode(self):
        self.draw_mode = self.mode_var.get()
        self.current_poly_points = []
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)

    def update_class_listbox(self):
        self.class_listbox.delete(0, tk.END)
        for i, cls in enumerate(self.classes):
            self.class_listbox.insert(tk.END, f" {i:2} : {cls}")
        self.class_listbox.selection_set(self.current_class_idx)

    def on_class_select(self, event):
        selection = self.class_listbox.curselection()
        if selection:
            self.current_class_idx = selection[0]
            if self.selected_ann_idx is not None:
                self.annotations[self.selected_ann_idx]["class_idx"] = self.current_class_idx
                self.save_current_state()

    def add_label(self):
        name = simpledialog.askstring("New Label", "Label name:")
        if name:
            self.classes.append(name.strip())
            self.update_class_listbox()

    def edit_label(self):
        idx = self.current_class_idx
        old_name = self.classes[idx]
        new_name = simpledialog.askstring("Edit Label", "New name:", initialvalue=old_name)
        if new_name:
            self.classes[idx] = new_name.strip()
            self.update_class_listbox()

    def remove_label(self):
        if len(self.classes) > 1:
            self.classes.pop(self.current_class_idx)
            self.current_class_idx = 0
            self.update_class_listbox()

    def select_directory(self):
        selected = filedialog.askdirectory()
        if not selected: return
        self.storage.setup_directories(selected)
        self.refresh_file_list()
        if self.storage.image_files:
            self.current_idx = 0
            self.load_image()

    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for f in self.storage.image_files:
            prefix = "✔ " if self.storage.is_image_labeled(f) else "  "
            self.file_listbox.insert(tk.END, prefix + f)
            if "✔" in prefix:
                self.file_listbox.itemconfig(tk.END, fg="#28a745")
        self.lbl_file_count.config(text=f"Images: {self.current_idx + 1}/{len(self.storage.image_files)}")

    def load_image(self):
        if self.current_idx < 0 or not self.storage.image_files: return
        img_name = self.storage.image_files[self.current_idx]
        path = os.path.join(self.storage.image_dir, img_name)
        self.orig_image = Image.open(path)
        self.current_poly_points = []
        self.selected_ann_idx = None

        cw, ch = self.canvas.winfo_width() or 800, self.canvas.winfo_height() or 600
        iw, ih = self.orig_image.size
        nw, nh = self.canvas_mgr.update_scales(cw, ch, iw, ih)

        img_resized = self.orig_image.resize((nw, nh), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.display_image)

        self.annotations = self.storage.load_labels(img_name, iw, ih)
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)
        self.update_txt_preview()

    def save_current_state(self):
        img_name = self.storage.image_files[self.current_idx]
        iw, ih = self.orig_image.size
        self.storage.save_labels(img_name, self.annotations, iw, ih)
        self.update_txt_preview()
        self.refresh_file_list()
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)

    def update_txt_preview(self):
        self.txt_display.delete("1.0", tk.END)
        if self.current_idx >= 0 and self.storage.image_files:
            content = self.storage.get_txt_content(self.storage.image_files[self.current_idx])
            self.txt_display.insert(tk.END, content)

    def on_txt_modified(self, event):
        if self.current_idx < 0 or not self.orig_image: return
        raw_text = self.txt_display.get("1.0", tk.END)
        img_name = self.storage.image_files[self.current_idx]
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
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)

    def on_mouse_move(self, event):
        if self.current_poly_points:
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, (event.x, event.y))

    def on_mouse_click(self, event):
        if not self.orig_image: return
        img_x, img_y = self.canvas_mgr.get_orig_coords(event.x, event.y)
        from config.config import MODE_BATCH_DEL

        if self.draw_mode == MODE_BATCH_DEL:
            self.start_x, self.start_y = event.x, event.y
            self.current_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#dc3545", dash=(4, 4), width=2)
            return

        if self.selected_ann_idx is not None:
            handle = self.canvas_mgr.get_handle_at_pos(event.x, event.y, self.annotations[self.selected_ann_idx])
            if handle:
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
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)
            return

        self.selected_ann_idx = None
        
        if self.draw_mode == DRAW_MODE_RECT:
            self.start_x, self.start_y = event.x, event.y
            color = COLOR_PALETTE[self.current_class_idx % len(COLOR_PALETTE)]
            self.current_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline=color, width=2)
        elif self.draw_mode == DRAW_MODE_POLY:
            self.current_poly_points.append((img_x, img_y))
            
        self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx, (event.x, event.y))

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
                dx, dy = img_x - self.drag_start_img_x, img_y - self.drag_start_img_y
                if ann["type"] == DRAW_MODE_RECT:
                    ann["points"] = [ann["points"][0] + dx, ann["points"][1] + dy, ann["points"][2] + dx, ann["points"][3] + dy]
                elif ann["type"] == DRAW_MODE_POLY:
                    ann["points"] = [ann["points"][i] + (dx if i % 2 == 0 else dy) for i in range(len(ann["points"]))]
                self.drag_start_img_x, self.drag_start_img_y = img_x, img_y
            self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)
        elif self.draw_mode == DRAW_MODE_RECT and self.current_rect_id:
            self.canvas.coords(self.current_rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_release(self, event):
        from config.config import MODE_BATCH_DEL
        
        if self.draw_mode == MODE_BATCH_DEL and self.start_x is not None:
            img_x1, img_y1 = self.canvas_mgr.get_orig_coords(self.start_x, self.start_y)
            img_x2, img_y2 = self.canvas_mgr.get_orig_coords(event.x, event.y)
            min_x, max_x = min(img_x1, img_x2), max(img_x1, img_x2)
            min_y, max_y = min(img_y1, img_y2), max(img_y1, img_y2)
            
            if (max_x - min_x) > 5 and (max_y - min_y) > 5:
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
                pts = [min(img_x1, img_x2), min(img_y1, img_y2), max(img_x1, img_x2), max(img_y1, img_y2)]
                self.annotations.append({"type": DRAW_MODE_RECT, "class_idx": self.current_class_idx, "points": pts})
                self.save_current_state()
            self.start_x = None
        elif self.is_dragging:
            self.save_current_state()
            self.is_dragging = False
            self.active_handle = None

    def finish_polygon(self, event):
        if self.draw_mode == DRAW_MODE_POLY and len(self.current_poly_points) >= 2:
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
            self.annotations.pop(self.selected_ann_idx)
            self.selected_ann_idx = None
            self.save_current_state()

    def on_key_press(self, event):
        focused_widget = self.root.focus_get()
        if focused_widget == self.txt_display: return

        if event.char.isdigit():
            target_idx = int(event.char)
            if target_idx < len(self.classes):
                self.current_class_idx = target_idx
                self.class_listbox.selection_clear(0, tk.END)
                self.class_listbox.selection_set(self.current_class_idx)
                if self.selected_ann_idx is not None:
                    self.annotations[self.selected_ann_idx]["class_idx"] = self.current_class_idx
                    self.save_current_state()
                else:
                    self.canvas_mgr.draw_all(self.annotations, self.selected_ann_idx, self.current_poly_points, self.current_class_idx)

    def on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if sel:
            self.current_idx = sel[0]
            self.load_image()

    def next_image(self):
        if self.current_idx < len(self.storage.image_files) - 1:
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