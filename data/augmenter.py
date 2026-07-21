"""Module for handling advanced pipeline data augmentation with nested label structures and original file inclusion."""

import os
import random
import shutil
from PIL import Image, ImageEnhance

class DataAugmenter:
    """Handles randomized image enhancements, nested coordinate transformations, and baseline dataset replication."""

    @staticmethod
    def augment_dataset(image_path, label_path, output_dir, options):
        """
        Applies multiples and combinations of augmentations. 
        Saves labels nested INSIDE the augmented images directory,
        and includes the original baseline image and label in the output.
        """
        if not os.path.exists(image_path):
            return 0

        # Mappastruktúra definiálása: augmented_images/ és augmented_images/labels/
        out_img_dir = os.path.join(output_dir, "augmented_images")
        out_lbl_dir = os.path.join(out_img_dir, "labels")
        
        os.makedirs(out_img_dir, exist_ok=True)
        os.makedirs(out_lbl_dir, exist_ok=True)

        img_name = os.path.basename(image_path)
        base_name = os.path.splitext(img_name)[0]
        ext = os.path.splitext(image_path)[1]
        lbl_name = f"{base_name}.txt"

        # --- 1. AZ EREDETI FÁJLOK MÁSOLÁSA (Baseline) ---
        # Eredeti kép átmásolása
        dest_orig_img = os.path.join(out_img_dir, img_name)
        if not os.path.exists(dest_orig_img):
            shutil.copy(image_path, dest_orig_img)
            
        # Eredeti label átmásolása (ha létezik)
        if label_path and os.path.exists(label_path):
            dest_orig_lbl = os.path.join(out_lbl_dir, lbl_name)
            if not os.path.exists(dest_orig_lbl):
                shutil.copy(label_path, dest_orig_lbl)

        # Baseline annotációk betöltése a generáláshoz
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

        # --- 2. AZ AUGMENTÁLT VARIÁCIÓK GENERÁLÁSA ---
        for idx in range(multiplier):
            img = Image.open(image_path)
            annotations = [(cid, list(coords)) for cid, coords in orig_annotations]

            modified = False

            # --- COMBINATORIAL PIPELINE ---
            
            # 1. Random Brightness Change
            b_var = options.get("bright_var", 0.0)
            if b_var > 0.0:
                factor = random.uniform(1.0 - b_var, 1.0 + b_var)
                img = ImageEnhance.Brightness(img).enhance(factor)
                modified = True

            # 2. Random Contrast Change
            c_var = options.get("contrast_var", 0.0)
            if c_var > 0.0:
                factor = random.uniform(1.0 - c_var, 1.0 + c_var)
                img = ImageEnhance.Contrast(img).enhance(factor)
                modified = True

            # 3. Random Horizontal Flip
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

            # 4. Random Vertical Flip
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

            if not modified and multiplier == 1:
                continue

            # --- UTÓTAGOK ÉS MENTÉS ---
            suffix = f"_aug_{idx + 1}"
            aug_img_name = f"{base_name}{suffix}{ext}"
            aug_lbl_name = f"{base_name}{suffix}.txt"

            # Augmentált kép mentése
            img.save(os.path.join(out_img_dir, aug_img_name))
            
            # Augmentált label mentése
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