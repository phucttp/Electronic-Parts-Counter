# -*- coding: utf-8 -*-
"""
config.py - Luu/doc cau hinh GUI (token Kaggle, username) vao file local.
File: cloud_kaggle/secrets.json  (nen gitignore - chua token bi mat).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent   # linhkien_tool/
SECRETS = ROOT / "cloud_kaggle" / "secrets.json"


def load():
    if SECRETS.exists():
        try:
            return json.loads(SECRETS.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save(data):
    SECRETS.parent.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_token():
    return load().get("kaggle_token", "")


def get_user():
    """Username tu config; neu trong thi thu doc tu kaggle.json (legacy)."""
    u = load().get("kaggle_user", "")
    if u:
        return u
    kj = pathlib.Path.home() / ".kaggle" / "kaggle.json"
    if kj.exists():
        try:
            return json.loads(kj.read_text(encoding="utf-8")).get("username", "")
        except Exception:
            pass
    return ""


def set_kaggle(token, user=""):
    d = load()
    if token:
        d["kaggle_token"] = token.strip()
    if user:
        d["kaggle_user"] = user.strip()
    save(d)
