# -*- coding: utf-8 -*-
"""
roi_dialog.py - Chọn VÙNG ROI (khoanh khay) ngay trên ảnh từ video/camera.
Click trái thêm điểm, chuột phải/Hoàn tác bỏ điểm cuối, Lưu để dùng cho auto-label.
ROI lưu CHUẨN HÓA 0..1 -> dùng được ở mọi độ phân giải.
"""
import pathlib
import tkinter as tk
from tkinter import ttk, messagebox

import cv2
from PIL import Image, ImageTk

from core_bridge import status

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # linhkien_tool/
DISP_W = 760   # bề ngang ảnh hiển thị trong dialog


def _grab_frame(source):
    """Lấy 1 frame từ nguồn (webcam index hoặc video path)."""
    src = int(source) if str(source).strip().isdigit() else str(source).strip()
    if isinstance(src, str):
        p = pathlib.Path(src)
        if not p.is_absolute():
            p = (ROOT / src).resolve()
        src = str(p)
    cap = cv2.VideoCapture(src)
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None


def open_roi(parent, source):
    raw = _grab_frame(source)
    if raw is None:
        messagebox.showerror("Lỗi", f"Không lấy được hình từ nguồn:\n{source}")
        return

    win = tk.Toplevel(parent)
    win.title("Chọn vùng ROI (khoanh khay)")
    win.transient(parent)
    win.grab_set()

    state = {"raw": raw, "points": list(status.load_roi()), "photo": None, "dw": 0, "dh": 0}

    ttk.Label(win, text="Click TRÁI thêm điểm quanh khay • Chuột PHẢI bỏ điểm cuối • cần ≥3 điểm",
              foreground="#555").pack(padx=10, pady=(10, 4))

    canvas = tk.Canvas(win, highlightthickness=1, highlightbackground="#aaa", cursor="crosshair")
    canvas.pack(padx=10)

    info = ttk.Label(win, text="", foreground="#888")
    info.pack(pady=2)

    def render_image():
        h, w = state["raw"].shape[:2]
        s = DISP_W / w
        dw, dh = DISP_W, int(h * s)
        disp = cv2.resize(state["raw"], (dw, dh))
        rgb = cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)
        state["photo"] = ImageTk.PhotoImage(Image.fromarray(rgb))
        state["dw"], state["dh"] = dw, dh
        canvas.config(width=dw, height=dh)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=state["photo"])
        draw_roi()

    def draw_roi():
        canvas.delete("roi")
        pts = [(nx * state["dw"], ny * state["dh"]) for nx, ny in state["points"]]
        if len(pts) >= 2:
            flat = [c for p in pts for c in p]
            if len(pts) >= 3:
                flat += list(pts[0])   # đóng polygon
            canvas.create_line(*flat, fill="#00e0ff", width=2, tags="roi")
        for i, (x, y) in enumerate(pts, 1):
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#ff3b3b", outline="", tags="roi")
            canvas.create_text(x + 8, y - 8, text=str(i), fill="#00e0ff", tags="roi")
        info.config(text=f"{len(pts)} điểm" + (" (đủ để lưu)" if len(pts) >= 3 else " (cần ≥3)"))

    def on_left(e):
        state["points"].append((e.x / state["dw"], e.y / state["dh"]))
        draw_roi()

    def on_right(e):
        if state["points"]:
            state["points"].pop()
            draw_roi()

    canvas.bind("<Button-1>", on_left)
    canvas.bind("<Button-3>", on_right)

    def do_undo():
        if state["points"]:
            state["points"].pop(); draw_roi()

    def do_clear():
        state["points"] = []; draw_roi()

    def do_recapture():
        f = _grab_frame(source)
        if f is not None:
            state["raw"] = f; render_image()

    def do_save():
        if len(state["points"]) < 3:
            messagebox.showwarning("Thiếu điểm", "Cần ít nhất 3 điểm để tạo vùng."); return
        status.save_roi([[round(nx, 5), round(ny, 5)] for nx, ny in state["points"]])
        messagebox.showinfo("Đã lưu", "Đã lưu vùng ROI. Auto-label (mode cv) sẽ chỉ tìm trong vùng này.")

    def do_delete():
        if messagebox.askyesno("Xóa ROI", "Xóa vùng ROI đã lưu?"):
            status.clear_roi(); state["points"] = []; draw_roi()

    bar = ttk.Frame(win)
    bar.pack(pady=10)
    ttk.Button(bar, text="Hoàn tác", command=do_undo).pack(side="left", padx=3)
    ttk.Button(bar, text="Xóa hết điểm", command=do_clear).pack(side="left", padx=3)
    ttk.Button(bar, text="Chụp lại", command=do_recapture).pack(side="left", padx=3)
    ttk.Button(bar, text="Xóa ROI đã lưu", command=do_delete).pack(side="left", padx=3)
    ttk.Button(bar, text="Lưu", command=do_save).pack(side="left", padx=3)
    ttk.Button(bar, text="Đóng", command=win.destroy).pack(side="left", padx=3)

    render_image()
