"""
Ritm - simple Windows 10/11 temp-file cleaner with a minimal GUI.

Repo:    https://github.com/LogOne87/Ritm
License: MIT (see LICENSE file)
"""

__version__ = "0.0.1"

import ctypes
import os
import shutil
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox

SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004
MB_ICONERROR = 0x10

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}"', None, 1
    )
    if result <= 32:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Ritm needs administrator rights to run.\n"
            "The launch was cancelled or failed.",
            "Ritm",
            MB_ICONERROR,
        )
    sys.exit()

def set_icon(root):
    root.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
    h = ctypes.windll.shell32.ExtractIconW(
        0, r"C:\Windows\System32\shell32.dll", 24
    )
    if h > 1:
        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, h)
        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, h)

def clear_folder(path, error_log):
    if not os.path.isdir(path):
        return 0, 0
    removed, errors = 0, 0
    try:
        entries = os.listdir(path)
    except Exception as e:
        error_log.append(f"{path}: {e}")
        return 0, 1

    for name in entries:
        full_path = os.path.join(path, name)
        try:
            if os.path.isfile(full_path) or os.path.islink(full_path):
                os.unlink(full_path)
            else:
                shutil.rmtree(full_path)
            removed += 1
        except Exception as e:
            errors += 1
            error_log.append(f"{full_path}: {e}")
    return removed, errors

def clear_file(path, error_log):
    if not os.path.isfile(path):
        return 0, 0
    try:
        os.unlink(path)
        return 1, 0
    except Exception as e:
        error_log.append(f"{path}: {e}")
        return 0, 1

def clear_log_files(path, error_log):
    if not os.path.isdir(path):
        return 0, 0
    removed, errors = 0, 0
    for root_dir, dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".log"):
                full_path = os.path.join(root_dir, name)
                try:
                    os.unlink(full_path)
                    removed += 1
                except Exception as e:
                    errors += 1
                    error_log.append(f"{full_path}: {e}")
    return removed, errors

def empty_recycle_bin(error_log):
    flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
    # 0 = success, -2147418113 (0x8000FFFF) = bin was already empty, also success
    if result in (0, -2147418113):
        return True
    error_log.append(f"Recycle Bin: SHEmptyRecycleBinW failed (code {result})")
    return False

def write_error_log(localapp, errors):
    """Save error details to a log file next to app data. Returns the path, or None on failure."""
    try:
        log_dir = os.path.join(localapp, "Ritm")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "ritm_errors.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(errors))
        return log_path
    except Exception:
        return None

def clean_all(root, btn, clean_prefetch):
    btn.config(state=tk.DISABLED, text="Cleaning is underway...")

    def worker():
        total_removed, total_errors = 0, 0
        error_log = []
        localapp = os.environ.get("LOCALAPPDATA", "")

        try:
            windir = os.environ.get("SystemRoot", os.environ.get("windir", r"C:\Windows"))

            raw_targets = {
                os.path.join(windir, "Temp"),
                os.environ.get("TEMP", tempfile.gettempdir()),
                os.environ.get("TMP", tempfile.gettempdir()),
                os.path.join(windir, "SoftwareDistribution", "Download"),
                os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                             "Microsoft", "Windows", "WER"),
                os.path.join(localapp, "CrashDumps"),
                os.path.join(windir, "SoftwareDistribution", "DeliveryOptimization"),
                os.path.join(localapp, "D3DSCache"),
                os.path.join(localapp, "Microsoft", "Windows", "Explorer"),
                os.path.join(windir, "Minidump"),
                os.path.join(windir, "Panther"),
            }

            if clean_prefetch:
                raw_targets.add(os.path.join(windir, "Prefetch"))

            forbidden = {
                os.path.normpath(p).lower()
                for p in [
                    r"C:/", #I set \ because if I set / the script will give an error because it considers slash as an independent part of the code, not included in "" (/ readable)
                    windir,
                    r"C:\Program Files",
                    r"C:\Program Files (x86)",
                    r"C:\Users",
                    os.environ.get("ProgramData", r"C:\ProgramData"),
                ]
                if p
            }

            targets = {
                os.path.normpath(t)
                for t in raw_targets
                if t and os.path.isabs(t) and os.path.normpath(t).lower() not in forbidden
            }

            for t in targets:
                r, e = clear_folder(t, error_log)
                total_removed += r
                total_errors += e

            r, e = clear_log_files(os.path.join(windir, "Logs"), error_log)
            total_removed += r
            total_errors += e

            r, e = clear_file(os.path.join(windir, "MEMORY.DMP"), error_log)
            total_removed += r
            total_errors += e

            if not empty_recycle_bin(error_log):
                total_errors += 1
        except Exception as e:
            error_log.append(f"Unexpected error: {e}")

        log_path = write_error_log(localapp, error_log) if error_log else None
        root.after(0, on_done, total_removed, total_errors, log_path)

    def on_done(total_removed, total_errors, log_path):
        btn.config(state=tk.NORMAL, text="Clean out")
        message = (
            f"Deleted temporary files: {total_removed}\n"
            f"Skipped files: {total_errors}"
        )
        if log_path:
            message += f"\n\nDetails saved to:\n{log_path}"
        messagebox.showinfo("Cleaning is complete!", message)

    threading.Thread(target=worker, daemon=True).start()

def main():
    if not is_admin():
        run_as_admin()
        return

    root = tk.Tk()
    root.title(f"Ritm v{__version__}")
    root.geometry("300x150")

    set_icon(root)

    prefetch_var = tk.BooleanVar(value=False)

    chk_prefetch = tk.Checkbutton(
        root,
        text="Clear Prefetch",
        variable=prefetch_var,
    )
    chk_prefetch.pack(pady=(10, 0))

    btn = tk.Button(
        root,
        text="Clean out",
        command=lambda: clean_all(root, btn, prefetch_var.get()),
        width=25,
        height=3,
    )
    btn.pack(expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()