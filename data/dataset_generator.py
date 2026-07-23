"""Module for partitioning labeled image datasets and generating YOLO configurations."""

import os
import random
import shutil
from pathlib import Path

class DatasetGenerator:
    """Handles splitting source image/label pairs into YOLO subfolders and exporting metadata."""

    @staticmethod
    def generate_yolo_dataset(image_files, image_dir, labels_dir, output_root, classes, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        Splits the active workspace dataset into train, val, and test partitions, then generates data.yaml.
        Everything is encapsulated inside a dedicated 'dataset' folder within the output root.

        Args:
            image_files (list): List of image filenames available in the workspace.
            image_dir (str): Path to the source images directory.
            labels_dir (str): Path to the source labels directory.
            output_root (str): Target directory where the dataset folder will be created.
            classes (list): List of active class tag names.
            train_ratio (float): Proportion of dataset for training.
            val_ratio (float): Proportion of dataset for validation.
            test_ratio (float): Proportion of dataset for testing.

        Returns:
            int: Total number of successfully paired and exported image/label sets.
        """
        if not (0.99 <= (train_ratio + val_ratio + test_ratio) <= 1.01):
            raise ValueError("The sum of train, val, and test ratios must equal 1.0.")

        out_path = Path(output_root) / "dataset"
        src_img_dir = Path(image_dir)
        src_lbl_dir = Path(labels_dir)

        valid_pairs = []
        for f in image_files:
            img_f = src_img_dir / f
            base = os.path.splitext(f)[0]
            lbl_f = src_lbl_dir / f"{base}.txt"
            if lbl_f.exists():
                valid_pairs.append((img_f, lbl_f))

        if not valid_pairs:
            return 0

        random.shuffle(valid_pairs)

        total_count = len(valid_pairs)
        train_end = int(total_count * train_ratio)
        val_end = train_end + int(total_count * val_ratio)

        splits = {
            'train': valid_pairs[:train_end],
            'val': valid_pairs[train_end:val_end],
            'test': valid_pairs[val_end:]
        }

        for split_name, pairs in splits.items():
            if not pairs:
                continue
            split_img_dir = out_path / split_name / 'images'
            split_lbl_dir = out_path / split_name / 'labels'
            
            split_img_dir.mkdir(parents=True, exist_ok=True)
            split_lbl_dir.mkdir(parents=True, exist_ok=True)

            for img, lbl in pairs:
                shutil.copy2(img, split_img_dir / img.name)
                shutil.copy2(lbl, split_lbl_dir / lbl.name)

        yaml_path = out_path / "data.yaml"
        with open(yaml_path, "w", encoding="utf-8") as y_file:
            y_file.write("train: ./train/images\n")
            y_file.write("val: ./val/images\n")
            if splits['test']:
                y_file.write("test: ./test/images\n\n")
            else:
                y_file.write("test:\n\n")
            
            y_file.write(f"nc: {len(classes)}\n")
            classes_str = ", ".join(f"'{cls}'" for cls in classes)
            y_file.write(f"names: [{classes_str}]\n")

        return total_count