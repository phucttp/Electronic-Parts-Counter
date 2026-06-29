# -*- coding: utf-8 -*-
"""
MODULE 4 - app.py
=================
Giao dien dieu khien (Tkinter, khong can cai them gi).
Toan bo noi dung nam trong vung CUON DUOC -> cua so nho/dai deu on.

Chay:  python m4_gui/app.py
"""
import sys
import pathlib
import tkinter as tk
from tkinter import ttk

# Cho phep import core_bridge / views (m4_gui/ vao sys.path)
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from views.status_panel import StatusPanel           # noqa: E402
from views.action_panel import ActionPanel           # noqa: E402
from views.settings_dialog import open_settings      # noqa: E402
from views.manage_classes_dialog import open_manage  # noqa: E402


def make_scrollable(root):
    """Tao 1 frame con CUON DUOC ben trong root. Tra ve frame de nhet noi dung."""
    canvas = tk.Canvas(root, highlightthickness=0)
    vsb = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # scrollregion bam theo noi dung; inner rong bang canvas
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))
    # con lan chuot
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
    return inner


def main():
    root = tk.Tk()
    root.title("Nhận diện linh kiện — Bảng điều khiển")
    root.geometry("470x600")
    root.minsize(380, 300)

    body = make_scrollable(root)

    ttk.Label(body, text="LINH KIỆN TOOL", font=("Segoe UI", 14, "bold")).pack(pady=(12, 2))
    ttk.Label(body, text="Gán nhãn → Train → Nhận diện",
              foreground="#666").pack(pady=(0, 8))

    status = StatusPanel(body)
    status.pack(fill="x", padx=12, pady=6)

    actions = ActionPanel(body, on_change=status.refresh)
    actions.pack(fill="x", padx=12, pady=6)

    row = ttk.Frame(body)
    row.pack(pady=(6, 14))
    ttk.Button(row, text="Làm mới", command=status.refresh).pack(side="left", padx=3)
    ttk.Button(row, text="Quản lý loại",
               command=lambda: open_manage(root, on_change=status.refresh)).pack(side="left", padx=3)
    ttk.Button(row, text="⚙ Cài đặt Kaggle",
               command=lambda: open_settings(root)).pack(side="left", padx=3)

    root.mainloop()


if __name__ == "__main__":
    main()
