# -*- coding: utf-8 -*-
"""
build_zip.py - Dong goi data.zip de upload Kaggle.
Tu loc bo loai bi AN (xoa mem) + don id qua core.build_clean_dataset,
KHONG dung nhan goc trong dataset/.
"""
import os
import sys
import zipfile
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent   # linhkien_tool/
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402


def main():
    out_dir = ROOT / "cloud_kaggle" / "upload"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_zip = out_dir / "data.zip"

    # src = DATASET goc (neu khong an gi) hoac ban sach (neu co loai bi an)
    src = core.build_clean_dataset(ROOT / "cloud_kaggle" / "_clean_view")

    n = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for folder in ("images", "labels"):
            for root, _, files in os.walk(src / folder):
                for f in files:
                    fp = pathlib.Path(root) / f
                    z.write(fp, fp.relative_to(src).as_posix())
                    n += 1
        dy = src / "data.yaml"
        if dy.exists():
            z.write(dy, "data.yaml")
            n += 1
    print(f"[build_zip] files={n} | nguon={src}")


if __name__ == "__main__":
    main()
