#!/usr/bin/env python3

import torch
import os
import shutil
from pathlib import Path


_original_torch_load = torch.load


def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _patched_load


def _build_filtered_dataset(src_root: Path, dst_root: Path) -> None:
    for split in ("train", "val"):
        src_split = src_root / split
        src_img = src_split / "images"
        src_lbl = src_split / "labels"

        dst_img = dst_root / split / "images"
        dst_lbl = dst_root / split / "labels"
        dst_img.mkdir(parents=True, exist_ok=True)
        dst_lbl.mkdir(parents=True, exist_ok=True)

        if not src_img.exists() or not src_lbl.exists():
            continue

        label_files = sorted(src_lbl.glob("*.txt"))
        for lab in label_files:
            img = src_img / f"{lab.stem}.png"
            if not img.exists():
                img = src_img / f"{lab.stem}.jpg"
            if not img.exists():
                continue

            shutil.copy2(lab, dst_lbl / lab.name)
            shutil.copy2(img, dst_img / img.name)


def _write_ultralytics_yaml(yaml_path: Path, dataset_root: Path) -> None:
    train_images = (dataset_root / "train" / "images").resolve()
    val_images = (dataset_root / "val" / "images").resolve()

    content = "\n".join(
        [
            f"path: {dataset_root.resolve()}",
            "",
            f"train: {train_images}",
            f"val: {val_images}",
            "",
            "names:",
            "  0: signature",
            "  1: stamp",
            "",
        ]
    )
    yaml_path.write_text(content, encoding="utf-8")


def main():
    try:
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit("ultralytics is not installed. Run: pip install ultralytics")

    project_root = Path(__file__).resolve().parent

    src_dataset = project_root / "stamp_signature_dataset"
    filtered_dataset = project_root / "stamp_signature_dataset_filtered"
    if filtered_dataset.exists():
        shutil.rmtree(filtered_dataset)
    filtered_dataset.mkdir(parents=True, exist_ok=True)

    _build_filtered_dataset(src_dataset, filtered_dataset)
    data_yaml = filtered_dataset / "dataset.ultralytics.yaml"
    _write_ultralytics_yaml(data_yaml, filtered_dataset)

    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(data_yaml),
        epochs=40,
        imgsz=640,
        batch=8,
        device="cpu",
    )

    save_dir = None
    try:
        save_dir = getattr(results, "save_dir", None)
    except Exception:
        save_dir = None
    if save_dir:
        best = Path(save_dir) / "weights" / "best.pt"
    else:
        best = project_root / "runs" / "detect" / "train" / "weights" / "best.pt"
    out_dir = project_root / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "stamp_signature.pt"

    if not best.exists():
        raise FileNotFoundError(f"Best weights not found at: {best}")

    shutil.copyfile(best, out_path)
    print("Saved model to:", out_path)


if __name__ == "__main__":
    main()
