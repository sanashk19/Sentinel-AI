#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import xml.etree.ElementTree as ET


CLASS_MAP = {
    "signature": 0,
    "stamp": 1,
}


def _safe_float(v: str, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def voc_to_yolo_line(class_id: int, xmin: float, ymin: float, xmax: float, ymax: float, img_w: float, img_h: float) -> str:
    x_center = ((xmin + xmax) / 2.0) / img_w
    y_center = ((ymin + ymax) / 2.0) / img_h
    bw = (xmax - xmin) / img_w
    bh = (ymax - ymin) / img_h

    x_center = _clamp01(x_center)
    y_center = _clamp01(y_center)
    bw = _clamp01(bw)
    bh = _clamp01(bh)

    return f"{class_id} {x_center:.6f} {y_center:.6f} {bw:.6f} {bh:.6f}"


def parse_voc_xml(xml_path: Path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    filename_el = root.find("filename")
    filename = filename_el.text.strip() if filename_el is not None and filename_el.text else ""

    size_el = root.find("size")
    img_w = None
    img_h = None
    if size_el is not None:
        w_el = size_el.find("width")
        h_el = size_el.find("height")
        img_w = _safe_float(w_el.text, None) if w_el is not None and w_el.text else None
        img_h = _safe_float(h_el.text, None) if h_el is not None and h_el.text else None

    objects = []
    for obj in root.findall("object"):
        name_el = obj.find("name")
        label = name_el.text.strip().lower() if name_el is not None and name_el.text else ""
        if label not in CLASS_MAP:
            continue

        bbox = obj.find("bndbox")
        if bbox is None:
            continue

        xmin = _safe_float((bbox.findtext("xmin") or "").strip(), None)
        ymin = _safe_float((bbox.findtext("ymin") or "").strip(), None)
        xmax = _safe_float((bbox.findtext("xmax") or "").strip(), None)
        ymax = _safe_float((bbox.findtext("ymax") or "").strip(), None)

        if None in (xmin, ymin, xmax, ymax):
            continue

        objects.append((CLASS_MAP[label], xmin, ymin, xmax, ymax))

    return filename, img_w, img_h, objects


def convert_split(dataset_root: Path, split: str):
    split_dir = dataset_root / split
    ann_dir = split_dir / "annotations"
    img_dir = split_dir / "images"
    label_dir = split_dir / "labels"
    label_dir.mkdir(parents=True, exist_ok=True)

    if not ann_dir.exists():
        raise FileNotFoundError(f"Missing annotations folder: {ann_dir}")
    if not img_dir.exists():
        raise FileNotFoundError(f"Missing images folder: {img_dir}")

    total_images_processed = 0
    total_labels_created = 0

    for xml_path in sorted(ann_dir.glob("*.xml")):
        try:
            filename, img_w, img_h, objects = parse_voc_xml(xml_path)
        except Exception:
            continue

        if not objects:
            continue

        if not img_w or not img_h:
            continue

        stem = xml_path.stem
        if filename:
            stem = Path(filename).stem

        out_txt = label_dir / f"{stem}.txt"

        lines = []
        for class_id, xmin, ymin, xmax, ymax in objects:
            lines.append(voc_to_yolo_line(class_id, xmin, ymin, xmax, ymax, img_w, img_h))

        if not lines:
            continue

        out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        total_labels_created += 1
        total_images_processed += 1

    return total_images_processed, total_labels_created


def main():
    parser = argparse.ArgumentParser(description="Convert Pascal VOC XML annotations to YOLO format")
    parser.add_argument(
        "--dataset-root",
        default=str(Path(__file__).resolve().parents[1] / "stamp_signature_dataset"),
        help="Dataset root containing train/ and val/ (default: stamp_signature_dataset)",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).resolve()
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found: {dataset_root}")

    total_images = 0
    total_labels = 0

    for split in ("train", "val"):
        if not (dataset_root / split).exists():
            continue
        images_processed, labels_created = convert_split(dataset_root, split)
        total_images += images_processed
        total_labels += labels_created

    print("Total images processed:", total_images)
    print("Total labels created:", total_labels)


if __name__ == "__main__":
    main()
