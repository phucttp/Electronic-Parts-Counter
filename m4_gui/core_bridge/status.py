# -*- coding: utf-8 -*-
"""
status.py - Doc trang thai dataset/model qua m0_core (chi DOC, khong sua).
"""
import sys
import pathlib

# Cho phep import m0_core (ROOT = linhkien_tool/)
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from m0_core import core  # noqa: E402


def get_status():
    """Tra ve dict: classes, per-class (ten, so anh, so box, bi_an), model, disabled."""
    core.ensure_dirs()
    classes = core.load_classes()
    dis = core.load_disabled()
    per = [
        (name, core.count_images_of_class(i), core.count_boxes_of_class(i), name in dis)
        for i, name in enumerate(classes)
    ]
    return {
        "classes": classes,
        "per": per,
        "disabled": sorted(dis),
        "has_model": core.BEST.exists(),
        "best_path": str(core.BEST),
        "metrics": core.load_metrics(),
    }


def list_classes():
    return core.load_classes()


def set_disabled(name, disabled=True):
    """An/Hien 1 loai (xoa mem). Khong dung nhan goc."""
    return core.set_disabled(name, disabled)


def delete_class(name):
    """XOA HAN 1 loai (xoa data that, khong hoan tac)."""
    return core.delete_class(name)


def load_roi():
    return core.load_roi()


def save_roi(points_norm):
    core.save_roi(points_norm)


def clear_roi():
    core.clear_roi()
