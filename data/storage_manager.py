"""Module for handling file system operations and YOLO data serialization."""

import os

class StorageManager:
    """Manages loading and saving of images and YOLO format annotations."""

    def __init__(self):
        self.image_dir = ""
        self.labels_dir = ""
        self.image_files = []

    def setup_directories(self, selected_dir):
        """Sets up image and labels directories based on the chosen path."""
        self.image_dir = selected_dir
        self.labels_dir = os.path.join(self.image_dir, "labels")
        if not os.path.exists(self.labels_dir):
            os.makedirs(self.labels_dir)

        valid_exts = (".jpg", ".jpeg", ".png", ".bmp")
        self.image_files = [f for f in os.listdir(self.image_dir) if f.lower().endswith(valid_exts)]
        self.image_files.sort()
        return self.image_files

    def is_image_labeled(self, img_name):
        """Checks if a valid non-empty annotation file exists for the image."""
        base = os.path.splitext(img_name)[0]
        txt_path = os.path.join(self.labels_dir, f"{base}.txt")
        return os.path.exists(txt_path) and os.path.getsize(txt_path) > 0

    def get_txt_content(self, img_name):
        """Returns the raw content of the YOLO text file."""
        base = os.path.splitext(img_name)[0]
        txt_path = os.path.join(self.labels_dir, f"{base}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def save_labels(self, img_name, annotations, img_w, img_h):
        """Writes the current annotations into a YOLO compatible text file."""
        base = os.path.splitext(img_name)[0]
        txt_path = os.path.join(self.labels_dir, f"{base}.txt")

        if not annotations:
            if os.path.exists(txt_path):
                os.remove(txt_path)
            return

        with open(txt_path, "w", encoding="utf-8") as f:
            for ann in annotations:
                cid = ann["class_idx"]
                if ann["type"] == "rectangle":
                    x1, y1, x2, y2 = ann["points"]
                    w, h = x2 - x1, y2 - y1
                    f.write(f"{cid} {(x1 + w / 2) / img_w:.6f} {(y1 + h / 2) / img_h:.6f} {w / img_w:.6f} {h / img_h:.6f}\n")
                else:
                    pts = ann["points"]
                    norm = [f"{pts[i] / img_w:.6f} {pts[i + 1] / img_h:.6f}" for i in range(0, len(pts), 2)]
                    f.write(f"{cid} " + " ".join(norm) + "\n")

    def load_labels(self, img_name, img_w, img_h):
        """Parses a YOLO text file and returns denormalized annotations."""
        annotations = []
        base = os.path.splitext(img_name)[0]
        txt_path = os.path.join(self.labels_dir, f"{base}.txt")
        if not os.path.exists(txt_path):
            return annotations

        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = list(map(float, line.strip().split()))
                if not parts:
                    continue
                cid = int(parts[0])
                coords = parts[1:]
                if len(coords) == 4:
                    xc, yc, w, h = coords
                    x1, y1 = (xc - w / 2) * img_w, (yc - h / 2) * img_h
                    x2, y2 = (xc + w / 2) * img_w, (yc + h / 2) * img_h
                    annotations.append({"type": "rectangle", "class_idx": cid, "points": [x1, y1, x2, y2]})
                else:
                    denorm = []
                    for i in range(0, len(coords), 2):
                        denorm.extend([coords[i] * img_w, coords[i + 1] * img_h])
                    annotations.append({"type": "polygon", "class_idx": cid, "points": denorm})
        return annotations
    
    def save_classes(self, classes):
        """Saves the current classes list directly into the image source directory."""
        if not hasattr(self, 'image_dir') or not self.image_dir:
            return
        
        classes_path = os.path.join(self.image_dir, "classes.txt")
        with open(classes_path, "w", encoding="utf-8") as f:
            for cls in classes:
                f.write(f"{cls}\n")

    def load_classes(self):
        """Loads classes from classes.txt if it exists directly in the image source directory."""
        if not hasattr(self, 'image_dir') or not self.image_dir:
            return None
            
        classes_path = os.path.join(self.image_dir, "classes.txt")
        
        if os.path.exists(classes_path):
            with open(classes_path, "r", encoding="utf-8") as f:
                classes = [line.strip() for line in f if line.strip()]
            return classes
        return None