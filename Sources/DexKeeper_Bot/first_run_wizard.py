"""Small Tkinter first-run setup wizard for DexKeeper."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.error
import urllib.request
import webbrowser


@dataclass(frozen=True)
class WizardResult:
    bot_token: str
    admin_id: str
    run_on_startup: bool
    no_disk_secrets: bool


def chmod_private(path: Path) -> None:
    if os.name != "nt":
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def write_env_file(path: Path, token: str, admin_id: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["BOT_TOKEN=" + token.strip()]
    if admin_id.strip():
        lines.append("ADMIN_ID=" + admin_id.strip())
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    chmod_private(tmp)
    tmp.replace(path)
    chmod_private(path)


def test_bot_token(token: str, timeout: int = 8) -> tuple[bool, str]:
    token = token.strip()
    if not token:
        return False, "Token is required."
    url = "https://api.telegram.org/bot" + token + "/getMe"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            if response.status == 200:
                return True, "Token works."
            return False, "Telegram rejected the token."
    except urllib.error.URLError:
        return False, "Could not reach Telegram. Check your network."
    except Exception:
        return False, "Token test failed."


def open_botfather() -> None:
    webbrowser.open("https://t.me/BotFather")


def open_bot_dm(token: str) -> None:
    ok, _ = test_bot_token(token)
    if not ok:
        return
    url = "https://api.telegram.org/bot" + token.strip() + "/getMe"
    try:
        with urllib.request.urlopen(url, timeout=8) as response:  # nosec B310
            import json

            payload = json.loads(response.read().decode("utf-8"))
        username = payload.get("result", {}).get("username")
        if username:
            webbrowser.open("https://t.me/" + username)
    except Exception:
        pass


class FirstRunWizard(tk.Tk):
    def __init__(self, env_path: Path):
        super().__init__()
        self.env_path = env_path
        self.title("DexKeeper Setup")
        self.resizable(False, False)
        self.result: WizardResult | None = None
        self.token_var = tk.StringVar()
        self.admin_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Paste your bot token, then test it.")
        self.startup_var = tk.BooleanVar(value=False)
        self.no_disk_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Set up DexKeeper", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="1. Create a Telegram bot with BotFather.").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Button(frame, text="Open BotFather", command=open_botfather).grid(row=2, column=0, sticky="w", pady=(4, 12))

        ttk.Label(frame, text="2. Paste BOT_TOKEN").grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.token_var, width=48, show="*").grid(row=4, column=0, sticky="ew", pady=(4, 4))
        ttk.Button(frame, text="Test token", command=self._test_token).grid(row=5, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.status_var).grid(row=6, column=0, sticky="w", pady=(4, 12))

        ttk.Label(frame, text="Optional ADMIN_ID").grid(row=7, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.admin_var, width=24).grid(row=8, column=0, sticky="w", pady=(4, 12))

        ttk.Checkbutton(frame, text="Run on startup", variable=self.startup_var).grid(row=9, column=0, sticky="w")
        ttk.Checkbutton(frame, text="No-disk secrets mode", variable=self.no_disk_var).grid(row=10, column=0, sticky="w")

        buttons = ttk.Frame(frame)
        buttons.grid(row=11, column=0, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Finish", command=self._finish).grid(row=0, column=1)

    def _test_token(self) -> None:
        ok, message = test_bot_token(self.token_var.get())
        self.status_var.set(("OK: " if ok else "Error: ") + message)

    def _finish(self) -> None:
        token = self.token_var.get().strip()
        admin_id = self.admin_var.get().strip()
        if not token:
            messagebox.showerror("DexKeeper Setup", "BOT_TOKEN is required.")
            return
        if admin_id and not admin_id.isdigit():
            messagebox.showerror("DexKeeper Setup", "ADMIN_ID must be numeric.")
            return
        no_disk = bool(self.no_disk_var.get())
        if not no_disk:
            write_env_file(self.env_path, token, admin_id)
        self.result = WizardResult(token, admin_id, bool(self.startup_var.get()), no_disk)
        open_bot_dm(token)
        self.destroy()


def run_first_run_wizard(env_path: Path) -> WizardResult | None:
    wizard = FirstRunWizard(env_path)
    wizard.mainloop()
    return wizard.result
