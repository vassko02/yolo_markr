"""Module for handling advanced pipeline data augmentation with nested label structures and original file inclusion.

This module contains tools to apply randomized or deterministic geometric and color space 
augmentations to images and their corresponding normalized label structures (e.g., bounding boxes or polygons).

Classes:
    DataAugmenter: Handles randomized image enhancements, nested coordinate transformations, and baseline dataset replication.
"""

import os
import random
import shutil
from PIL import Image, ImageEnhance

class DataAugmenter:
    """Handles randomized image enhancements, nested coordinate transformations, and baseline dataset replication.
    
    Attributes:
        No instance attributes. Contains static processing methods.
        
    Methods:
        augment_dataset: Core pipeline to multiply, transform, and structure image and label datasets.
    """

    @staticmethod
    def augment_dataset(image_path, label_path, output_dir, options):
        """Applies multiples and combinations of augmentations including color adjustments, flips, and rotations.

        Saves labels nested INSIDE the augmented images directory,
        and includes the original baseline image and label in the output.

        Parameters:
            image_path (str): File system path to the source image.
            label_path (str): File system path to the source label file.
            output_dir (str): Base destination directory for generated outputs.
            options (dict): Configuration mapping containing multiplier, bright_var, contrast_var,
                            flip_horizontal, flip_vertical, rotate_orthogonal, and labels_too keys.

        Returns:
            int: Total count of mutated variation files successfully generated and committed to disk.
        """
        if not os.path.exists(image_path):
            return 0

        out_img_dir = os.path.join(output_dir, "augmented_images")
        out_lbl_dir = os.path.join(out_img_dir, "labels")
        
        os.makedirs(out_img_dir, exist_ok=True)
        os.makedirs(out_lbl_dir, exist_ok=True)

        img_name = os.path.basename(image_path)
        base_name = os.path.splitext(img_name)[0]
        ext = os.path.splitext(image_path)[1]
        lbl_name = f"{base_name}.txt"

        dest_orig_img = os.path.join(out_img_dir, img_name)
        if not os.path.exists(dest_orig_img):
            shutil.copy(image_path, dest_orig_img)
            
        if label_path and os.path.exists(label_path):
            dest_orig_lbl = os.path.join(out_lbl_dir, lbl_name)
            if not os.path.exists(dest_orig_lbl):
                shutil.copy(label_path, dest_orig_lbl)

        orig_annotations = []
        augment_labels = options.get("labels_too", True)
        
        if augment_labels and label_path and os.path.exists(label_path):
            with open(label_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        orig_annotations.append((int(parts[0]), [float(x) for x in parts[1:]]))

        multiplier = options.get("multiplier", 1)
        generated_count = 0

        has_bright = options.get("bright_var", 0.0) > 0.0
        has_contrast = options.get("contrast_var", 0.0) > 0.0
        has_flip_h = options.get("flip_horizontal", False)
        has_flip_v = options.get("flip_vertical", False)
        has_rotate = options.get("rotate_orthogonal", False)
        
        any_augmentation_enabled = has_bright or has_contrast or has_flip_h or has_flip_v or has_rotate

        if not any_augmentation_enabled:
            return 0

        for idx in range(multiplier):
            modified = False
            max_attempts = 10
            attempt = 0
            
            while not modified and attempt < max_attempts:
                attempt += 1
                img = Image.open(image_path)
                current_w, current_h = img.size
                annotations = [(cid, list(coords)) for cid, coords in orig_annotations]

                b_var = options.get("bright_var", 0.0)
                if b_var > 0.0 and random.choice([True, False]):
                    factor = random.uniform(1.0 - b_var, 1.0 + b_var)
                    img = ImageEnhance.Brightness(img).enhance(factor)
                    modified = True

                c_var = options.get("contrast_var", 0.0)
                if c_var > 0.0 and random.choice([True, False]):
                    factor = random.uniform(1.0 - c_var, 1.0 + c_var)
                    img = ImageEnhance.Contrast(img).enhance(factor)
                    modified = True

                if options.get("flip_horizontal", False) and random.choice([True, False]):
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    if augment_labels:
                        for ann in annotations:
                            coords = ann[1]
                            if len(coords) == 4:
                                coords[0] = 1.0 - coords[0]
                            else:
                                for i in range(0, len(coords), 2):
                                    coords[i] = 1.0 - coords[i]
                    modified = True

                if options.get("flip_vertical", False) and random.choice([True, False]):
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                    if augment_labels:
                        for ann in annotations:
                            coords = ann[1]
                            if len(coords) == 4:
                                coords[1] = 1.0 - coords[1]
                            else:
                                for i in range(1, len(coords), 2):
                                    coords[i] = 1.0 - coords[i]
                    modified = True

                # 5. Random Orthogonal Rotation (90, 180, 270 degrees)
                if options.get("rotate_orthogonal", False) and random.choice([True, False]):
                    angle = random.choice([90, 180, 270])
                    w_orig, h_orig = img.size  # A kép aktuális szélessége és magassága a forgatás ELŐTT

                    if angle == 90:
                        img = img.transpose(Image.ROTATE_90)
                        if augment_labels:
                            for ann in annotations:
                                coords = ann[1]
                                if len(coords) == 4:
                                    x, y, w, h = coords
                                    # Helyes normalizált YOLO 90 fokos forgatás (PIL ROTATE_90-hez igazítva)
                                    coords[0] = y
                                    coords[1] = 1.0 - x
                                    coords[2] = h * (h_orig / w_orig)
                                    coords[3] = w * (w_orig / h_orig)
                                else:
                                    # Poligon / OBB koordináták helyes forgatása (óra járásával ellentétesen)
                                    num_points = len(coords) // 2
                                    for i in range(num_points):
                                        x_old = coords[2*i]
                                        y_old = coords[2*i + 1]
                                        coords[2*i] = y_old
                                        coords[2*i + 1] = 1.0 - x_old
                        modified = True
                        
                    elif angle == 180:
                        img = img.transpose(Image.ROTATE_180)
                        if augment_labels:
                            for ann in annotations:
                                coords = ann[1]
                                if len(coords) == 4:
                                    coords[0] = 1.0 - coords[0]
                                    coords[1] = 1.0 - coords[1]
                                    # A szélesség és magasság nem változik, mert a tengelyek nem cserélődtek fel
                                else:
                                    for i in range(0, len(coords), 2):
                                        coords[i] = 1.0 - coords[i]
                                        coords[i+1] = 1.0 - coords[i+1]
                        modified = True
                        
                    elif angle == 270:
                        img = img.transpose(Image.ROTATE_270)
                        if augment_labels:
                            for ann in annotations:
                                coords = ann[1]
                                if len(coords) == 4:
                                    x, y, w, h = coords
                                    # Helyes normalizált YOLO 270 fokos forgatás (PIL ROTATE_270-hez igazítva)
                                    coords[0] = 1.0 - y
                                    coords[1] = x
                                    coords[2] = h * (h_orig / w_orig)
                                    coords[3] = w * (w_orig / h_orig)
                                else:
                                    # Poligon / OBB koordináták helyes forgatása (óra járásával megegyezően)
                                    num_points = len(coords) // 2
                                    for i in range(num_points):
                                        x_old = coords[2*i]
                                        y_old = coords[2*i + 1]
                                        coords[2*i] = 1.0 - y_old
                                        coords[2*i + 1] = x_old
                        modified = True
            if not modified:
                continue

            suffix = f"_aug_{idx + 1}"
            aug_img_name = f"{base_name}{suffix}{ext}"
            aug_lbl_name = f"{base_name}{suffix}.txt"

            img.save(os.path.join(out_img_dir, aug_img_name))
            aug_lbl_path = os.path.join(out_lbl_dir, aug_lbl_name)

            if augment_labels and annotations:
                with open(aug_lbl_path, "w", encoding="utf-8") as f:
                    for cid, coords in annotations:
                        coord_str = " ".join(f"{c:.6f}" for c in coords)
                        f.write(f"{cid} {coord_str}\n")
            elif not augment_labels and label_path and os.path.exists(label_path):
                shutil.copy(label_path, aug_lbl_path)

            generated_count += 1

        return generated_count