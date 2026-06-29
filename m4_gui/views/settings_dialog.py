# -*- coding: utf-8 -*-
"""
settings_dialog.py - Hop thoai cai dat Kaggle (token + username).
Nguoi dung cuoi nhap token o day, khong can dung env var/CLI.
"""
import webbrowser
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

from core_bridge import config

TOKEN_PAGE = "https://www.kaggle.com/settings/api"


def open_settings(parent):
    win = tk.Toplevel(parent)
    win.title("Cài đặt Kaggle")
    win.geometry("460x340")
    win.transient(parent)
    win.grab_set()

    ttk.Label(win, text="Cấu hình Kaggle (để Train Cloud)",
              font=("Segoe UI", 12, "bold")).pack(pady=(12, 4))
    ttk.Label(win, text="1) Mở trang token → API Tokens → Generate New Token\n"
                        "2) Copy chuỗi token rồi dán vào ô dưới → Lưu",
              foreground="#555", justify="left").pack(padx=14, anchor="w")

    ttk.Button(win, text="🔗 Mở trang lấy token Kaggle",
               command=lambda: webbrowser.open(TOKEN_PAGE)).pack(pady=8)

    frm = ttk.Frame(win)
    frm.pack(fill="x", padx=14, pady=4)

    ttk.Label(frm, text="Token:").grid(row=0, column=0, sticky="w", pady=4)
    token_var = tk.StringVar(value=config.get_token())
    token_entry = ttk.Entry(frm, textvariable=token_var, width=38, show="•")
    token_entry.grid(row=0, column=1, pady=4, padx=4)

    show = tk.BooleanVar(value=False)
    ttk.Checkbutton(frm, text="Hiện", variable=show,
                    command=lambda: token_entry.config(show="" if show.get() else "•")
                    ).grid(row=0, column=2)

    ttk.Label(frm, text="Username:").grid(row=1, column=0, sticky="w", pady=4)
    user_var = tk.StringVar(value=config.get_user())
    ttk.Entry(frm, textvariable=user_var, width=38).grid(row=1, column=1, pady=4, padx=4)

    msg = ttk.Label(win, text="", foreground="#888")
    msg.pack(pady=4)

    def do_save():
        if not token_var.get().strip():
            messagebox.showwarning("Thiếu token", "Hãy dán token vào trước."); return
        config.set_kaggle(token_var.get(), user_var.get())
        msg.config(text="✓ Đã lưu vào cloud_kaggle/secrets.json", foreground="green")

    def do_test():
        tok = token_var.get().strip()
        if not tok:
            messagebox.showwarning("Thiếu token", "Hãy dán token trước."); return
        msg.config(text="Đang kiểm tra...", foreground="#888"); win.update()
        import os
        env = os.environ.copy(); env["KAGGLE_API_TOKEN"] = tok
        try:
            r = subprocess.run(["kaggle", "datasets", "list", "--mine"],
                               capture_output=True, text=True, env=env, timeout=40)
            ok = (r.returncode == 0)
            msg.config(text=("✓ Token hợp lệ — kết nối Kaggle OK" if ok
                             else "✗ Token sai / lỗi kết nối"),
                       foreground=("green" if ok else "red"))
        except Exception as e:
            msg.config(text=f"✗ Lỗi: {e}", foreground="red")

    btns = ttk.Frame(win)
    btns.pack(pady=10)
    ttk.Button(btns, text="Kiểm tra kết nối", command=do_test).pack(side="left", padx=6)
    ttk.Button(btns, text="Lưu", command=do_save).pack(side="left", padx=6)
    ttk.Button(btns, text="Đóng", command=win.destroy).pack(side="left", padx=6)
