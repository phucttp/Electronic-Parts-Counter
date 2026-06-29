# -*- coding: utf-8 -*-
"""
train_kernel.py - Runs ON KAGGLE GPU (not on your machine).
===========================================================
Installs ultralytics -> locates the uploaded dataset (extracting zips if
needed) -> trains YOLOv8n -> exports best.pt to /kaggle/working/best.pt.

ASCII-only (the kaggle CLI reads code files with Windows cp1252 when pushing).
"""
import os
import glob
import zipfile
import shutil

# Kaggle co the cap GPU P100 (sm_60), ma torch moi cua image (2.10) da BO sm_60.
# -> Pin torch 2.4.1 (con ho tro sm_60). Neu duoc cap T4 thi torch nay van chay.
os.system("pip install -q torch==2.4.1 torchvision==0.19.1 "
          "--index-url https://download.pytorch.org/whl/cu121")
# Cai ultralytics --no-deps de KHONG keo torch khac de len.
os.system("pip install -q --no-deps ultralytics ultralytics-thop")

import yaml  # noqa: E402
import torch  # noqa: E402
print("[i] torch", torch.__version__, "| CUDA avail:", torch.cuda.is_available(),
      "|", (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no gpu"))
from ultralytics import YOLO  # noqa: E402

EPOCHS = 100
IMGSZ = 640
PATIENCE = 25


def _locate(base):
    """Return the dir that contains images/train under `base`, else None."""
    hits = glob.glob(os.path.join(base, "**", "images", "train"), recursive=True)
    if hits:
        return os.path.dirname(os.path.dirname(hits[0]))  # .../<root>
    return None


def prepare_dataset():
    """Find dataset under /kaggle/input. If only zips are present, extract them."""
    base = "/kaggle/input"
    try:
        print("[i] /kaggle/input =", os.listdir(base))
    except Exception:
        pass

    d = _locate(base)                      # case: Kaggle already extracted
    if d:
        print("[i] Found extracted dataset at", d)
        return d

    work = "/kaggle/working/_data"          # case: extract our zips ourselves
    os.makedirs(work, exist_ok=True)
    for zp in glob.glob(os.path.join(base, "**", "*.zip"), recursive=True):
        print("[i] Extracting", zp)
        with zipfile.ZipFile(zp) as z:
            z.extractall(work)
    d = _locate(work)
    if d:
        print("[i] Found dataset (after extract) at", d)
        return d

    raise SystemExit("[!] Dataset not found. /kaggle/input = " + str(os.listdir(base)))


def read_names(data_dir):
    names = ["dien_tro"]
    y = os.path.join(data_dir, "data.yaml")
    if os.path.exists(y):
        d = yaml.safe_load(open(y, encoding="utf-8")) or {}
        n = d.get("names")
        if isinstance(n, dict):
            names = [n[k] for k in sorted(n)]
        elif isinstance(n, list) and n:
            names = n
    return names


def main():
    data_dir = prepare_dataset()
    names = read_names(data_dir)
    print("[i] Dataset:", data_dir)
    print("[i] Classes:", names)

    cfg = {"path": data_dir, "train": "images/train", "val": "images/val", "names": names}
    work_yaml = "/kaggle/working/data.yaml"
    yaml.safe_dump(cfg, open(work_yaml, "w", encoding="utf-8"), allow_unicode=True)

    model = YOLO("yolov8n.pt")
    model.train(
        data=work_yaml, epochs=EPOCHS, imgsz=IMGSZ, device=0,
        project="/kaggle/working", name="train", exist_ok=True, patience=PATIENCE,
        # Augmentation mac dinh ultralytics da du. KHONG xoay manh (degrees) vi
        # data da du goc + xoay manh tren data it lam model kem tu tin (conf tut).
        flipud=0.2,
    )

    # Ghi do chinh xac (mAP...) tu results.csv -> metrics.json (de tai ve GUI hien)
    import csv
    import json as _json
    res_csv = "/kaggle/working/train/results.csv"
    metrics = {"classes": names}
    if os.path.exists(res_csv):
        with open(res_csv) as f:
            rows = list(csv.DictReader(f))
        if rows:
            last = rows[-1]

            def col(sub):
                for k, v in last.items():
                    if k and sub in k.strip().lower():
                        try:
                            return round(float(v), 4)
                        except Exception:
                            return None
                return None

            metrics.update({"map50": col("map50("), "map5095": col("map50-95"),
                            "precision": col("precision"), "recall": col("recall")})
    with open("/kaggle/working/metrics.json", "w") as f:
        _json.dump(metrics, f)
    print("[i] metrics:", metrics)

    best = "/kaggle/working/train/weights/best.pt"
    if os.path.exists(best):
        shutil.copy(best, "/kaggle/working/best.pt")
        print("[OK] DONE -> /kaggle/working/best.pt")
    else:
        print("[!] best.pt not found, check training log above.")


if __name__ == "__main__":
    main()
