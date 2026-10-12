"""Self-contained Windows installer UI for US AI.

The built installer embeds the application executable and runs without
PowerShell, Python, or an external installer framework on the target PC.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_NAME = "US AI"
DEFAULT_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / "US-AI"
ACCENT = "#1476D4"
NAVY = "#10243D"
TEXT = "#162638"
MUTED = "#68788A"


def payload_path(name: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / "payload" / name


def start_menu_dir() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME


def create_start_menu_entries(install_dir: Path) -> None:
    menu_dir = start_menu_dir()
    menu_dir.mkdir(parents=True, exist_ok=True)
    target = install_dir / "US-AI.exe"
    launch = menu_dir / "US AI.exe"
    try:
        if launch.exists():
            launch.unlink()
        os.link(target, launch)
    except OSError:
        shutil.copy2(target, launch)
    shutil.copy2(install_dir / "uninstall.exe", menu_dir / "Uninstall US AI.exe")


def register_uninstall(install_dir: Path) -> None:
    if sys.platform != "win32":
        return
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\US-AI"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        values = {
            "DisplayName": APP_NAME,
            "DisplayVersion": "1.0.0",
            "Publisher": APP_NAME,
            "InstallLocation": str(install_dir),
            "UninstallString": str(install_dir / "uninstall.exe"),
        }
        for name, value in values.items():
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)


class Installer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("US AI Setup")
        self.geometry("560x430")
        self.resizable(False, False)
        self.configure(bg="#F4F7FA")
        self.install_dir = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self.run_after = tk.BooleanVar(value=True)
        self.page_index = 0
        self.pages: list[tk.Frame] = []
        self._configure_styles()
        self._build_ui()
        self._show_page(0)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 9), padding=(13, 7), borderwidth=0)
        style.configure("Accent.TButton", background=ACCENT, foreground="white", font=("Segoe UI", 9, "bold"), padding=(16, 8))
        style.map("Accent.TButton", background=[("active", "#0A4D91"), ("disabled", "#AFC7DE")])
        style.configure("Back.TButton", background="#E7EDF3", foreground=TEXT, padding=(13, 7))
        style.map("Back.TButton", background=[("active", "#D8E2EC"), ("disabled", "#EEF2F5")])
        style.configure("TEntry", fieldbackground="white", foreground=TEXT, padding=7)
        style.configure("Horizontal.TProgressbar", troughcolor="#DCE5EE", background=ACCENT, bordercolor="#DCE5EE", lightcolor=ACCENT, darkcolor=ACCENT)
        style.configure("TCheckbutton", background="white", foreground=TEXT, font=("Segoe UI", 9))

    def _build_ui(self) -> None:
        header = tk.Frame(self, height=92, bg=NAVY)
        header.pack(fill="x")
        header.pack_propagate(False)
        logo = tk.Canvas(header, width=48, height=48, bg=NAVY, highlightthickness=0)
        logo.place(x=26, y=21)
        logo.create_oval(3, 3, 45, 45, fill="#1D456D", outline="#4FC7F7", width=2)
        logo.create_oval(12, 12, 36, 36, fill="#EAFBFF", outline="")
        logo.create_oval(18, 14, 32, 28, fill="#55C8F0", outline="")
        tk.Label(header, text="US AI", fg="white", bg=NAVY, font=("Segoe UI", 16, "bold")).place(x=88, y=20)
        tk.Label(header, text="Desktop assistant setup", fg="#B7CBE0", bg=NAVY).place(x=90, y=50)

        body = tk.Frame(self, bg="white")
        body.pack(fill="both", expand=True)
        for builder in (self._welcome_page, self._location_page, self._install_page):
            page = tk.Frame(body, bg="white")
            page.place(x=0, y=0, relwidth=1, relheight=1)
            builder(page)
            self.pages.append(page)

        buttons = tk.Frame(self, height=58, bg="#EEF2F6")
        buttons.pack(fill="x", side="bottom")
        buttons.pack_propagate(False)
        self.step_label = tk.Label(buttons, text="Step 1 of 3", fg=MUTED, bg="#EEF2F6", font=("Segoe UI", 8))
        self.step_label.place(x=26, y=21)
        self.back_button = ttk.Button(buttons, text="‹  Back", style="Back.TButton", command=self._back)
        self.back_button.place(x=298, y=12, width=78, height=34)
        self.next_button = ttk.Button(buttons, text="Next  ›", style="Accent.TButton", command=self._next)
        self.next_button.place(x=384, y=12, width=88, height=34)
        self.cancel_button = ttk.Button(buttons, text="Cancel", style="Back.TButton", command=self.destroy)
        self.cancel_button.place(x=480, y=12, width=68, height=34)

    def _welcome_page(self, page: tk.Frame) -> None:
        tk.Label(page, text="Welcome to the US AI Setup Wizard", font=("Segoe UI", 12, "bold"), bg="white").place(x=26, y=20)
        text = "This wizard will install US AI on your computer.\n\nUS AI provides voice interaction, local AI responses, memory, desktop controls, and a convenient system-tray companion.\n\nClick Next to choose the installation folder."
        tk.Label(page, text=text, justify="left", anchor="nw", bg="white", wraplength=438).place(x=27, y=61, width=438, height=145)

    def _location_page(self, page: tk.Frame) -> None:
        tk.Label(page, text="Choose Install Location", font=("Segoe UI", 12, "bold"), bg="white").place(x=26, y=20)
        tk.Label(page, text="Choose the folder in which to install US AI.", bg="white").place(x=27, y=52)
        ttk.Entry(page, textvariable=self.install_dir).place(x=28, y=112, width=345, height=25)
        ttk.Button(page, text="Browse...", command=self._browse).place(x=382, y=110, width=90, height=28)
        tk.Label(page, text="Space required: approximately 350 MB\nSpace available: Windows-managed", fg="#555555", bg="white", justify="left").place(x=28, y=164)

    def _install_page(self, page: tk.Frame) -> None:
        self.install_heading = tk.Label(page, text="Installing US AI", font=("Segoe UI", 12, "bold"), bg="white")
        self.install_heading.place(x=26, y=20)
        self.status = tk.Label(page, text="Please wait while US AI is being installed.", anchor="w", bg="white")
        self.status.place(x=27, y=56, width=445)
        self.progress = ttk.Progressbar(page, maximum=100, mode="determinate")
        self.progress.place(x=27, y=94, width=445, height=12)
        self.finish_heading = tk.Label(page, text="Completing US AI Setup", font=("Segoe UI", 12, "bold"), bg="white")
        self.finish_heading.place(x=26, y=20)
        self.finish_heading.place_forget()
        self.finish_text = tk.Label(page, text="US AI has been installed on your computer.\n\nClick Finish to close Setup.", justify="left", anchor="nw", bg="white")
        self.finish_text.place_forget()
        self.run_check = ttk.Checkbutton(page, text="Run US AI", variable=self.run_after)
        self.run_check.place_forget()

    def _show_page(self, index: int) -> None:
        self.page_index = index
        self.pages[index].tkraise()
        completed = index == 2 and self.progress["value"] >= 100
        self.step_label.configure(text="Complete" if completed else f"Step {index + 1} of 3")
        self.back_button.configure(state="normal" if index == 1 and not completed else "disabled")
        self.next_button.configure(text="Finish" if completed else ("Install" if index == 1 else "Next  ›"))
        self.cancel_button.configure(state="disabled" if completed else "normal")

    def _browse(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.install_dir.get(), title="Choose the US AI installation folder")
        if selected:
            self.install_dir.set(selected)

    def _back(self) -> None:
        if self.page_index == 1:
            self._show_page(0)

    def _next(self) -> None:
        if self.page_index == 0:
            self._show_page(1)
        elif self.page_index == 1:
            self._install()
        else:
            if self.run_after.get():
                subprocess.Popen([str(Path(self.install_dir.get()) / "US-AI.exe")], cwd=self.install_dir.get())
            self.destroy()

    def _install(self) -> None:
        target = Path(self.install_dir.get()).expanduser().resolve()
        marker = target / ".us-ai-install-root"
        if target.exists() and any(target.iterdir()) and not marker.exists():
            messagebox.showerror("US AI Setup", "The chosen folder already contains files and is not a US AI installation.")
            return
        try:
            self._show_page(2)
            self.update_idletasks()
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(payload_path("US-AI.exe"), target / "US-AI.exe")
            self.progress["value"] = 65
            self.update_idletasks()
            shutil.copy2(payload_path("uninstall.exe"), target / "uninstall.exe")
            marker.write_text(str(target), encoding="utf-8")
            create_start_menu_entries(target)
            register_uninstall(target)
            self.progress["value"] = 100
            self.status.configure(text="Installation complete.")
            self.install_heading.place_forget()
            self.progress.place_forget()
            self.finish_heading.place(x=26, y=20)
            self.finish_text.place(x=27, y=56, width=445, height=54)
            self.run_check.place(x=27, y=132)
            self._show_page(2)
        except Exception as exc:
            self._show_page(1)
            messagebox.showerror("US AI Setup", str(exc))


if __name__ == "__main__":
    Installer().mainloop()
