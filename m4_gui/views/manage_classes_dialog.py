# -*- coding: utf-8 -*-
"""
manage_classes_dialog.py - An/Hien loai linh kien (XOA MEM).
Khong dung nhan goc -> hoan tac duoc. Train lai se bo loai bi an.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from core_bridge import status


def open_manage(parent, on_change=None):
    win = tk.Toplevel(parent)
    win.title("Quản lý loại linh kiện")
    win.geometry("470x360")
    win.transient(parent)
    win.grab_set()

    ttk.Label(win, text="Quản lý loại linh kiện",
              font=("Segoe UI", 12, "bold")).pack(pady=(10, 2))
    ttk.Label(win, text="• Ẩn: tạm giấu, GIỮ data, hoàn tác được (train lại sẽ bỏ khỏi model)\n"
                        "• Xóa hẳn: xóa luôn ảnh + nhãn của loại — KHÔNG hoàn tác",
              foreground="#666", justify="left").pack(pady=(0, 8))

    frame = ttk.Frame(win)
    frame.pack(fill="both", expand=True, padx=12)

    def toggle(name, disable):
        if disable and not messagebox.askyesno(
                "Ẩn loại", f"Ẩn loại '{name}'?\n"
                           "(Data giữ nguyên, bấm 'Hiện lại' để khôi phục.\n"
                           "Train lại sẽ bỏ loại này khỏi model.)"):
            return
        status.set_disabled(name, disable)
        refresh()
        if on_change:
            on_change()

    def hard_delete(name, imgs, boxes):
        if not messagebox.askyesno(
                "XÓA HẲN", f"XÓA HẲN loại '{name}'?\n\n"
                           f"Sẽ xóa luôn {imgs} ảnh + {boxes} box của loại này.\n"
                           "KHÔNG hoàn tác được!\n\n(Chỉ muốn ẩn tạm thì bấm 'Không' rồi dùng nút Ẩn.)",
                icon="warning"):
            return
        if not messagebox.askyesno("Xác nhận lần cuối",
                                   f"Chắc chắn xóa vĩnh viễn '{name}'?"):
            return
        r = status.delete_class(name)
        if r.get("ok"):
            messagebox.showinfo("Đã xóa",
                                f"Đã xóa '{name}': {r['imgs_deleted']} ảnh, "
                                f"{r['boxes_removed']} box.\nCòn lại: {r['classes_left']}")
        else:
            messagebox.showerror("Lỗi", r.get("reason", "Không xóa được"))
        refresh()
        if on_change:
            on_change()

    def refresh():
        for w in frame.winfo_children():
            w.destroy()
        s = status.get_status()
        if not s["per"]:
            ttk.Label(frame, text="(chưa có loại nào — hãy gán nhãn)").pack(pady=10)
            return
        for name, imgs, boxes, hidden in s["per"]:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3)
            label = f"{name}  ({imgs} ảnh, {boxes} box)" + ("  [ẨN]" if hidden else "")
            ttk.Label(row, text=label).pack(side="left")
            ttk.Button(row, text="Xóa hẳn", width=8,
                       command=lambda n=name, i=imgs, b=boxes: hard_delete(n, i, b)
                       ).pack(side="right", padx=(3, 0))
            ttk.Button(row, text=("Hiện lại" if hidden else "Ẩn"), width=8,
                       command=lambda n=name, h=hidden: toggle(n, not h)).pack(side="right")

    refresh()
    ttk.Button(win, text="Đóng", command=win.destroy).pack(pady=10)
