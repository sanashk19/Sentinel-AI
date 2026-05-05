#!/usr/bin/env python3

import argparse
from pathlib import Path


def check_split(dataset_root: Path, split: str):
    split_dir = dataset_root / split
    img_dir = split_dir / "images"
    label_dir = split_dir / "labels"

    if not split_dir.exists():
        return {
            "split": split,
            "images": 0,
            "missing_labels": [],
            "missing_images": [],
            "labels_dir_exists": False,
            "images_dir_exists": False,
        }

    images_dir_exists = img_dir.exists()
    labels_dir_exists = label_dir.exists()

    images = sorted(img_dir.glob("*.png")) if images_dir_exists else []
    labels = sorted(label_dir.glob("*.txt")) if labels_dir_exists else []

    label_by_stem = {p.stem: p for p in labels}

    missing_labels = []
    for img in images:
        if img.stem not in label_by_stem:
            missing_labels.append(img.name)

    image_by_stem = {p.stem: p for p in images}
    missing_images = []
    for lab in labels:
        if lab.stem not in image_by_stem:
            missing_images.append(lab.name)

    return {
        "split": split,
        "images": len(images),
        "missing_labels": missing_labels,
        "missing_images": missing_images,
        "labels_dir_exists": labels_dir_exists,
        "images_dir_exists": images_dir_exists,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate stamp/signature dataset structure and image-label pairing")
    parser.add_argument(
        "--dataset-root",
        default=str(Path(__file__).resolve().parents[1] / "stamp_signature_dataset"),
        help="Dataset root containing train/ and val/ (default: stamp_signature_dataset)",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).resolve()
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found: {dataset_root}")

    train = check_split(dataset_root, "train")
    val = check_split(dataset_root, "val")

    print("Total train images:", train["images"])
    print("Total val images:", val["images"])

    if not train["labels_dir_exists"]:
        print("Missing train labels folder:", str(dataset_root / "train" / "labels"))
    if not val["labels_dir_exists"]:
        print("Missing val labels folder:", str(dataset_root / "val" / "labels"))

    if train["missing_labels"]:
        print("Train images missing labels:", len(train["missing_labels"]))
        for name in train["missing_labels"][:50]:
            print("-", name)
        if len(train["missing_labels"]) > 50:
            print("... truncated")

    if val["missing_labels"]:
        print("Val images missing labels:", len(val["missing_labels"]))
        for name in val["missing_labels"][:50]:
            print("-", name)
        if len(val["missing_labels"]) > 50:
            print("... truncated")

    if train["missing_images"]:
        print("Train labels missing images:", len(train["missing_images"]))
        for name in train["missing_images"][:50]:
            print("-", name)
        if len(train["missing_images"]) > 50:
            print("... truncated")

    if val["missing_images"]:
        print("Val labels missing images:", len(val["missing_images"]))
        for name in val["missing_images"][:50]:
            print("-", name)
        if len(val["missing_images"]) > 50:
            print("... truncated")


if __name__ == "__main__":
    main()
