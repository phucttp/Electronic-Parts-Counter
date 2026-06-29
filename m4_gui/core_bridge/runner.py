# -*- coding: utf-8 -*-
"""
runner.py - Chay cac module khac qua subprocess (nhu user go lenh).
GUI khong nhung logic -> sua module nao khong vo GUI.
"""
import os
import sys
import subprocess
import pathlib

from core_bridge import config

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent   # linhkien_tool/
PY = sys.executable

# Co the mo cua so console rieng (Windows) de xem log train/import
_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)


def _popen(args, new_console=False):
    flags = _NEW_CONSOLE if new_console else 0
    return subprocess.Popen(args, cwd=str(ROOT), creationflags=flags)


def run_annotate(source, name, assist=False):
    """Mo cong cu gan nhan (cua so OpenCV rieng). assist=True -> bat auto-label."""
    args = [PY, str(ROOT / "m1_annotate" / "annotate.py"), "--source", source, "--name", name]
    if assist:
        args.append("--assist")
    return _popen(args)


def run_detect(source, conf=0.4):
    """Mo cong cu nhan dien (cua so OpenCV rieng)."""
    return _popen([PY, str(ROOT / "m3_detect" / "detect.py"),
                   "--source", source, "--conf", str(conf)])


def run_import(src_dir):
    """Import data YOLO co san -> chay trong console de xem ket qua."""
    return _popen([PY, str(ROOT / "m1_annotate" / "import_labels.py"),
                   "--src", src_dir], new_console=True)


def run_train_local():
    """Train tren CPU may nay -> console rieng (lau)."""
    return _popen([PY, str(ROOT / "m2_train" / "train.py")], new_console=True)


def run_train_cloud():
    """Train tren Kaggle GPU qua run_kaggle.ps1 -> console rieng.
    Lay token + username tu config (GUI) va truyen vao subprocess."""
    ps1 = ROOT / "cloud_kaggle" / "run_kaggle.ps1"
    args = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)]
    user = config.get_user()
    if user:
        args += ["-KaggleUser", user]

    env = os.environ.copy()
    token = config.get_token()
    if token:
        env["KAGGLE_API_TOKEN"] = token   # uu tien token tu GUI config

    return subprocess.Popen(args, cwd=str(ROOT), creationflags=_NEW_CONSOLE, env=env)


def has_kaggle_token():
    """Co token (tu config hoac env) chua -> de GUI nhac nguoi dung."""
    return bool(config.get_token() or os.environ.get("KAGGLE_API_TOKEN"))
