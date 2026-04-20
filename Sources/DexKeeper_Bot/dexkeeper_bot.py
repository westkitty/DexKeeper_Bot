#!/usr/bin/env python3
"""
DexKeeper Bot - V8 Production (The Full-Stack Community Manager)
FINAL MERGED BUILD - "DexKeeper" Rebrand
"""

import os
import re
import csv
import json
import html
import uuid
import time
import asyncio
import logging
import datetime
import functools
import collections
import sys
import threading

# subprocess used with fixed, trusted commands
import subprocess  # nosec B404
import webbrowser
import urllib.request
import urllib.error
import aiohttp  # Added aiohttp
from pathlib import Path
from typing import (
    Optional,
    List,
    Dict,
    Tuple,
    Any,
    DefaultDict,
    cast,
    Protocol,
)

# Python version check
if sys.version_info < (3, 9):
    print("❌ ERROR: Python 3.9+ required")
    print(
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    sys.exit(1)

import aiosqlite
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
    Message,
)
from telegram.helpers import escape_markdown
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    Defaults,
    ApplicationHandlerStop,
    TypeHandler,
)
from telegram.error import TelegramError

# === CONFIGURATION ===

APP_NAME = "DexKeeper"


def _in_docker() -> bool:
    """Detect if running in Docker container"""
    return (
        os.getenv("DOCKER_CONTAINER") == "1"
        or os.getenv("container") is not None
        or os.path.exists("/.dockerenv")
        or os.path.exists("/app/dexkeeper_bot.py")
    )


def _get_data_dir() -> Path:
    override = os.getenv("DEXKEEPER_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if _in_docker():
        return Path("/app/data")
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    xdg = os.getenv("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def _init_data_dir() -> Path:
    path = _get_data_dir()
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        fallback = Path.cwd() / ".dexkeeper_data"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            print(
                f"⚠️ DexKeeper: failed to use data dir {path} ({e}); using {fallback}",
                file=sys.stderr,
            )
            return fallback
        except Exception as fallback_error:
            print(
                f"⚠️ DexKeeper: failed to create fallback data dir {fallback} ({fallback_error})",
                file=sys.stderr,
            )
            return path


DATA_DIR = _init_data_dir()
ENV_PATH = DATA_DIR / ".env"
LOG_PATH = Path(os.getenv("DEXKEEPER_LOG_PATH", str(DATA_DIR / "dexkeeper.log")))


def _build_log_handlers(log_path: Path) -> List[logging.Handler]:
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if os.getenv("DEXKEEPER_DISABLE_FILE_LOG", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return handlers
    try:
        handlers.insert(0, logging.FileHandler(log_path, encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ DexKeeper: file logging disabled ({e})", file=sys.stderr)
    return handlers


logging.basicConfig(
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=_build_log_handlers(LOG_PATH),
)
logger = logging.getLogger("DexKeeper")

APP_INSTANCE = None
TRAY_ICON = None
LAST_UPDATE_NOTICE = None
PAUSED = False
SILENT_MODE = False
HEARTBEAT_ONLINE = False
LAST_HEARTBEAT = None
RESTART_JOB = None

RELEASES_URL = "https://github.com/westkitty/DexKeeper_Bot/releases/latest"
RELEASES_API = "https://api.github.com/repos/westkitty/DexKeeper_Bot/releases/latest"


def _parse_admin_id(value: Optional[str]) -> int:
    """Parse ADMIN_ID with validation"""
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    if text.isdigit():
        return int(text)
    logger.warning("Invalid ADMIN_ID value; expected numeric Telegram user ID.")
    return 0


def _resource_path(rel_path: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / rel_path


def _tray_enabled() -> bool:
    if os.getenv("DEXKEEPER_TRAY", "1").lower() in ("0", "false", "no", "off"):
        return False
    if _in_docker():
        return False
    if sys.platform.startswith("linux") and not os.getenv("DISPLAY"):
        return False
    return True


def _runtime_settings_path() -> Path:
    return DATA_DIR / "runtime_settings.json"


def _load_runtime_settings() -> Dict[str, Any]:
    try:
        return json.loads(_runtime_settings_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_runtime_settings(data: Dict[str, Any]) -> None:
    try:
        _runtime_settings_path().write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.warning("Failed to save runtime settings: %s", e)


def _request_stop():
    logger.info("Stopping DexKeeper...")
    global TRAY_ICON
    if TRAY_ICON:
        try:
            TRAY_ICON.stop()
        except Exception:
            logger.debug("Failed to stop tray icon", exc_info=True)
    app = APP_INSTANCE
    if app and hasattr(app, "stop_running"):
        try:
            app.stop_running()
            return
        except Exception:
            logger.debug("Failed to stop application instance", exc_info=True)
    logger.warning("Graceful stop failed; no application instance to stop.")


def _restart():
    try:
        args = [sys.executable] + sys.argv[1:]
        # controlled args
        subprocess.Popen(args)  # noqa: S603  # nosec B603
    except Exception as e:
        logger.warning("Restart failed: %s", e)
        return
    _request_stop()


def _open_admin_panel():
    token = BOT_TOKEN
    if not token:
        logger.warning("BOT_TOKEN missing; cannot open admin panel.")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        # fixed https URL
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
        username = data.get("result", {}).get("username")
        if username:
            webbrowser.open(f"https://t.me/{username}")
        else:
            logger.warning("Bot username not found.")
    except urllib.error.URLError:
        logger.warning("Failed to open admin panel: network error")
    except Exception:
        # Don't log exception details to avoid token exposure
        logger.warning("Failed to open admin panel: API error")


def _open_path(path: Path):
    try:
        if sys.platform.startswith("win"):
            # system file opener
            os.startfile(str(path))  # noqa: S606  # nosec B606
        elif sys.platform == "darwin":
            # system file opener
            subprocess.Popen(["/usr/bin/open", str(path)])  # noqa: S603  # nosec B603
        else:
            # system file opener
            subprocess.Popen(["xdg-open", str(path)])  # noqa: S603, S607  # nosec B603 B607
    except Exception as e:
        logger.warning("Failed to open path %s: %s", path, e)


def _hide_tray():
    global TRAY_ICON
    if TRAY_ICON:
        try:
            TRAY_ICON.visible = False
        except Exception:
            try:
                TRAY_ICON.stop()
            except Exception:
                logger.debug("Failed to stop tray icon", exc_info=True)
    logger.info(
        "Tray icon hidden. To show it again, restart with DEXKEEPER_TRAY=1 or run with --show-tray."
    )


def _get_launch_command() -> List[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable] + sys.argv[1:]
    return [sys.executable, str(Path(__file__).resolve())] + sys.argv[1:]


def _is_autostart_enabled() -> bool:
    try:
        if sys.platform.startswith("win"):
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            )
            winreg.QueryValueEx(key, "DexKeeper")
            return True
        if sys.platform == "darwin":
            return (
                Path.home() / "Library" / "LaunchAgents" / "com.dexkeeper.bot.plist"
            ).exists()
        return (Path.home() / ".config" / "autostart" / "dexkeeper.desktop").exists()
    except Exception:
        return False


def _set_autostart(enabled: bool):
    try:
        if sys.platform.startswith("win"):
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            if enabled:
                cmd = " ".join(
                    [f'"{c}"' if " " in c else c for c in _get_launch_command()]
                )
                winreg.SetValueEx(key, "DexKeeper", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "DexKeeper")
                except FileNotFoundError:
                    pass
            return
        if sys.platform == "darwin":
            plist_path = (
                Path.home() / "Library" / "LaunchAgents" / "com.dexkeeper.bot.plist"
            )
            if enabled:
                plist_path.parent.mkdir(parents=True, exist_ok=True)
                args = _get_launch_command()
                plist = f"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n  <key>Label</key>\n  <string>com.dexkeeper.bot</string>\n  <key>ProgramArguments</key>\n  <array>\n    {"".join([f"<string>{a}</string>" for a in args])}\n  </array>\n  <key>RunAtLoad</key>\n  <true/>\n</dict>\n</plist>\n"""
                plist_path.write_text(plist, encoding="utf-8")
                # system service manager
                subprocess.Popen(["/bin/launchctl", "load", str(plist_path)])  # noqa: S603  # nosec B603
            else:
                if plist_path.exists():
                    # system service manager
                    subprocess.Popen(["/bin/launchctl", "unload", str(plist_path)])  # noqa: S603  # nosec B603
                    plist_path.unlink(missing_ok=True)
            return
        # linux
        autostart_path = Path.home() / ".config" / "autostart" / "dexkeeper.desktop"
        if enabled:
            autostart_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = " ".join([f'"{c}"' if " " in c else c for c in _get_launch_command()])
            desktop = f"""[Desktop Entry]
Type=Application
Name=DexKeeper
Exec={cmd}
X-GNOME-Autostart-enabled=true
"""
            autostart_path.write_text(desktop, encoding="utf-8")
        else:
            autostart_path.unlink(missing_ok=True)
    except Exception as e:
        logger.warning("Failed to set autostart: %s", e)


def _toggle_autostart():
    _set_autostart(not _is_autostart_enabled())


def _toggle_pause():
    global PAUSED
    PAUSED = not PAUSED
    status = "paused" if PAUSED else "resumed"
    logger.info("DexKeeper %s.", status)
    if TRAY_ICON and hasattr(TRAY_ICON, "notify") and not SILENT_MODE:
        try:
            TRAY_ICON.notify(f"DexKeeper {status}", "DexKeeper")
        except Exception:
            logger.debug("Tray notification failed", exc_info=True)


def _toggle_silent():
    global SILENT_MODE
    SILENT_MODE = not SILENT_MODE
    data = _load_runtime_settings()
    data["silent_mode"] = SILENT_MODE
    _save_runtime_settings(data)
    logger.info("Silent mode %s.", "enabled" if SILENT_MODE else "disabled")


def _status_text() -> str:
    if LAST_HEARTBEAT:
        ts = datetime.datetime.fromtimestamp(LAST_HEARTBEAT).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    else:
        ts = "never"
    state = "Online" if HEARTBEAT_ONLINE else "Offline"
    return f"Status: {state}\\nLast heartbeat: {ts}"


def _show_status():
    msg = _status_text()
    logger.info(msg.replace("\\n", " | "))
    if SILENT_MODE:
        return
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("DexKeeper Status", msg)
        root.destroy()
    except Exception:
        logger.debug("Failed to show status popup", exc_info=True)


def _schedule_restart_enabled() -> bool:
    return _load_runtime_settings().get("daily_restart", False)


def _set_daily_restart(enabled: bool):
    data = _load_runtime_settings()
    data["daily_restart"] = enabled
    _save_runtime_settings(data)
    _apply_restart_schedule()


def _toggle_daily_restart():
    _set_daily_restart(not _schedule_restart_enabled())


async def _restart_job(context: ContextTypes.DEFAULT_TYPE):
    """Async callback for scheduled restarts"""
    try:
        _restart()
    except Exception as e:
        logger.error(f"Scheduled restart failed: {e}")


def _apply_restart_schedule():
    global RESTART_JOB
    if not APP_INSTANCE:
        return
    if RESTART_JOB:
        try:
            RESTART_JOB.schedule_removal()
        except Exception:
            logger.debug("Failed to cancel restart job", exc_info=True)
        RESTART_JOB = None
    if _schedule_restart_enabled():
        time_obj = datetime.time(hour=3, minute=0)
        RESTART_JOB = APP_INSTANCE.job_queue.run_daily(_restart_job, time=time_obj)


def _get_current_version() -> str:
    try:
        return _resource_path("VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0"


def _parse_version(v: str) -> Tuple[int, ...]:
    v = v.strip()
    if v.startswith("v"):
        v = v[1:]
    parts = []
    for chunk in v.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num or 0))
    return tuple(parts)


async def _check_for_updates() -> Optional[Dict[str, str]]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(RELEASES_API, timeout=5) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        latest_tag = data.get("tag_name", "")
        if not latest_tag:
            return None
        current = _parse_version(_get_current_version())
        latest = _parse_version(latest_tag)
        if latest > current:
            return {"tag": latest_tag, "url": RELEASES_URL}
    except Exception as e:
        logger.debug("Update check failed: %s", e)
    return None


def _show_update_popup_thread(msg: str):
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("DexKeeper Update", f"{msg}. Open download page?"):
            webbrowser.open(RELEASES_URL)
        root.destroy()
    except Exception:
        logger.debug("Update popup failed", exc_info=True)


async def _update_check_job(context: ContextTypes.DEFAULT_TYPE):
    global LAST_UPDATE_NOTICE
    if os.getenv("DEXKEEPER_AUTO_UPDATE", "1").lower() in ("0", "false", "no", "off"):
        return

    info = await _check_for_updates()
    if not info:
        return

    tag = info["tag"]
    if LAST_UPDATE_NOTICE == tag:
        return
    LAST_UPDATE_NOTICE = tag

    msg = f"Update available: {tag}"
    logger.info(msg)

    # Tray Notification
    if TRAY_ICON and hasattr(TRAY_ICON, "notify") and not SILENT_MODE:
        try:
            TRAY_ICON.notify(msg, "DexKeeper")
        except Exception:
            logger.debug("Tray notification failed", exc_info=True)

    # GUI Popup (Threaded)
    if not SILENT_MODE:
        threading.Thread(
            target=_show_update_popup_thread, args=(msg,), daemon=True
        ).start()


# start_update_check removed (using job queue)


async def _heartbeat_job(context):
    global HEARTBEAT_ONLINE, LAST_HEARTBEAT
    try:
        await context.bot.get_me()
        HEARTBEAT_ONLINE = True
        LAST_HEARTBEAT = time.time()
    except Exception:
        HEARTBEAT_ONLINE = False
        LAST_HEARTBEAT = time.time()


async def _cleanup_spam_cache_job(context):
    """Periodic cleanup of old spam cache entries to prevent memory leaks"""
    global SPAM_CACHE, SPAM_LOCKS
    now = time.time()

    # Clean up users inactive for more than 1 hour
    inactive_threshold = now - 3600
    users_to_remove = []

    for user_id, timestamps in list(SPAM_CACHE.items()):
        if not timestamps or (timestamps and max(timestamps) < inactive_threshold):
            users_to_remove.append(user_id)

    for user_id in users_to_remove:
        SPAM_CACHE.pop(user_id, None)
        SPAM_LOCKS.pop(user_id, None)

    if users_to_remove:
        logger.debug(
            f"Cleaned up {len(users_to_remove)} inactive users from spam cache"
        )


def start_tray(app):
    global TRAY_ICON
    if not _tray_enabled():
        return
    try:
        import pystray  # type: ignore[import-untyped]
        from PIL import Image
    except Exception as e:
        logger.warning("Tray icon disabled: %s", e)
        return

    icon_path = _resource_path("assets/DexKeeper_Bot_icon.png")
    try:
        image = Image.open(icon_path)
    except Exception as e:
        logger.warning("Tray icon image missing: %s", e)
        return

    menu = pystray.Menu(
        pystray.MenuItem("Open Data Folder", lambda icon, item: _open_path(DATA_DIR)),
        pystray.MenuItem("Open Logs", lambda icon, item: _open_path(LOG_PATH)),
        pystray.MenuItem("Open Admin Panel", lambda icon, item: _open_admin_panel()),
        pystray.MenuItem("View Status", lambda icon, item: _show_status()),
        pystray.MenuItem(
            "Start on Login",
            lambda icon, item: _toggle_autostart(),
            checked=lambda item: _is_autostart_enabled(),
        ),
        pystray.MenuItem(
            "Pause Bot", lambda icon, item: _toggle_pause(), checked=lambda item: PAUSED
        ),
        pystray.MenuItem(
            "Silent Mode",
            lambda icon, item: _toggle_silent(),
            checked=lambda item: SILENT_MODE,
        ),
        pystray.MenuItem(
            "Schedule Daily Restart (3:00 AM)",
            lambda icon, item: _toggle_daily_restart(),
            checked=lambda item: _schedule_restart_enabled(),
        ),
        pystray.MenuItem("Restart DexKeeper", lambda icon, item: _restart()),
        pystray.MenuItem(
            "Check for Updates", lambda icon, item: webbrowser.open(RELEASES_URL)
        ),
        pystray.MenuItem("Hide Tray Icon", lambda icon, item: _hide_tray()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Stop DexKeeper", lambda icon, item: _request_stop()),
    )
    TRAY_ICON = pystray.Icon("DexKeeper", image, "DexKeeper", menu)
    try:
        if hasattr(TRAY_ICON, "run_detached"):
            TRAY_ICON.run_detached()
        else:

            def run_icon():
                try:
                    TRAY_ICON.run()
                except Exception as e:
                    logger.warning("Tray icon failed: %s", e)

            t = threading.Thread(target=run_icon, daemon=True)
            t.start()
    except Exception as e:
        logger.warning("Tray icon failed: %s", e)


def _load_env():
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    load_dotenv(override=False)


_load_env()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = _parse_admin_id(os.getenv("ADMIN_ID"))
DB_PATH = os.getenv("DB_PATH") or str(DATA_DIR / "dexkeeper.db")

# Rate Limiting & Anti-Spam Cache
SPAM_CACHE: DefaultDict[int, List[float]] = collections.defaultdict(list)
# Use factory function to create locks on-demand without race condition
SPAM_LOCKS: DefaultDict[int, asyncio.Lock] = collections.defaultdict(asyncio.Lock)
LAST_BROADCAST: Dict[int, float] = {}
BROADCAST_LOCKS: DefaultDict[int, asyncio.Lock] = collections.defaultdict(asyncio.Lock)

# === DATABASE SCHEMA ===

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value JSON
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    language TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSON,
    admin_id INTEGER
);

CREATE TABLE IF NOT EXISTS pending_requests (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    request_data JSON,
    answers JSON,
    captcha_answer TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    admin_id INTEGER,
    note TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    user_id INTEGER,
    tag TEXT,
    PRIMARY KEY (user_id, tag)
);
"""

# === I18N SYSTEM ===


class I18n:
    def __init__(self):
        self.defaults = {
            "welcome": "Welcome! I am DexKeeper. Please answer a few questions to join.",
            "approved": "✅ Approved. Welcome!",
            "declined": "❌ Declined. Thanks for your time.",
            "captcha_prompt": "🔢 Security check: What is {a} + {b}?",
            "captcha_failed": "❌ Incorrect answer. Request declined.",
            "lockdown": "🚨 New member requests are currently paused.",
            "rate_limited": "⏳ Too many requests. Please try again later.",
        }

    def get(self, key, lang="en", **kwargs):
        # Placeholder for real multi-lang DB lookup
        tmpl = self.defaults.get(key, key)
        return tmpl.format(**kwargs)


i18n = I18n()

# === HELPERS ===


class _HasDB(Protocol):
    db_conn: aiosqlite.Connection


def _get_db(context: ContextTypes.DEFAULT_TYPE) -> aiosqlite.Connection:
    app = cast(_HasDB, context.application)
    return app.db_conn


async def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user:
        return False
    if user.id == ADMIN_ID:
        return True
    try:
        admins = await get_setting(_get_db(context), "admins", [])
    except Exception:
        return False
    return user.id in admins


async def _require_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    alert: bool = True,
) -> bool:
    if await _is_admin(update, context):
        return True
    if update.callback_query:
        await update.callback_query.answer("⛔ Admin only.", show_alert=alert)
    elif update.effective_message:
        await update.effective_message.reply_text("⛔ Access Denied: Admin only.")
    return False


async def get_setting(conn, key: str, default: Any = None) -> Any:
    async with conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ) as cursor:
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else default


async def set_setting(conn, key: str, value: Any):
    """Set a setting with proper error handling and rollback."""
    try:
        await conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        await conn.commit()
    except Exception as e:
        await conn.rollback()
        logger.error(f"Failed to set setting '{key}': {e}")
        raise


async def log_action(conn, request_id, action, user_id, details=None, admin_id=None):
    """Log an action with proper error handling and rollback."""
    if details is None:
        details = {}
    try:
        await conn.execute(
            "INSERT INTO history (id, user_id, action, details, admin_id) VALUES (?, ?, ?, ?, ?)",
            (
                request_id or str(uuid.uuid4()),
                user_id,
                action,
                json.dumps(details),
                admin_id,
            ),
        )
        await conn.commit()
    except Exception as e:
        await conn.rollback()
        logger.error(f"Failed to log action '{action}' for user {user_id}: {e}")
        raise


def sanitize(text: str) -> str:
    return html.escape(str(text)[:1000]) if text else ""


def _parse_poll_options(text: str) -> List[str]:
    return [option.strip() for option in text.split(",") if option.strip()]


def _parse_schedule_minutes(text: str) -> Optional[int]:
    try:
        mins = int(text)
    except (TypeError, ValueError):
        return None
    if mins < 1 or mins > 60 * 24 * 7:
        return None
    return mins


def _unrestricted_permissions() -> ChatPermissions:
    return ChatPermissions(
        can_send_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
    )


def _chat_is_group(chat: Any) -> bool:
    return getattr(chat, "type", None) in ("group", "supergroup")


async def _upsert_user(
    conn: aiosqlite.Connection,
    user: Any,
    *,
    status: Optional[str] = None,
) -> None:
    if not user or getattr(user, "id", None) is None:
        return
    base_values = (
        user.id,
        getattr(user, "username", None),
        getattr(user, "full_name", None) or getattr(user, "name", None) or "",
        getattr(user, "language_code", None),
    )
    if status is None:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, full_name, language)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                language = excluded.language
            """,
            base_values,
        )
    else:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, full_name, language, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                language = excluded.language,
                status = excluded.status
            """,
            base_values + (status,),
        )
    await conn.commit()


async def _remember_managed_chat(
    context: ContextTypes.DEFAULT_TYPE, chat: Any
) -> Optional[int]:
    if not chat or not _chat_is_group(chat):
        return None
    chat_id = getattr(chat, "id", None)
    if chat_id is None:
        return None
    bot_data = cast(Dict[str, Any], context.bot_data)
    if bot_data.get("managed_chat_id") == chat_id:
        return chat_id
    bot_data["managed_chat_id"] = chat_id
    await set_setting(_get_db(context), "managed_chat_id", chat_id)
    return chat_id


async def _resolve_target_chat_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Optional[int]:
    chat = update.effective_chat
    if chat and _chat_is_group(chat):
        return await _remember_managed_chat(context, chat)

    bot_data = cast(Dict[str, Any], context.bot_data)
    cached_chat_id = bot_data.get("managed_chat_id")
    if isinstance(cached_chat_id, int):
        return cached_chat_id

    stored_chat_id = await get_setting(_get_db(context), "managed_chat_id")
    if isinstance(stored_chat_id, int):
        bot_data["managed_chat_id"] = stored_chat_id
        return stored_chat_id
    return None


# === PAUSE HANDLER ===


async def paused_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PAUSED:
        raise ApplicationHandlerStop()


# === FIRST-RUN CONFIG ===


def _write_env(token: str, admin_id: str = "") -> None:
    lines = [f"BOT_TOKEN={token}"]
    if admin_id and admin_id.isdigit():
        lines.append(f"ADMIN_ID={admin_id}")
    elif admin_id:
        logger.warning("ADMIN_ID must be numeric; skipping invalid value.")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Set restrictive file permissions (owner read/write only)
    try:
        ENV_PATH.chmod(0o600)
    except Exception as e:
        logger.warning(f"Failed to set .env permissions: {e}")


def _prompt_console() -> Tuple[Optional[str], Optional[str]]:
    try:
        token = input("Enter BOT_TOKEN: ").strip()
        admin = input("Enter ADMIN_ID (optional): ").strip()
        return token or None, admin or None
    except EOFError:
        return None, None


def _prompt_gui() -> Tuple[Optional[str], Optional[str]]:
    try:
        import tkinter as tk
        from tkinter import messagebox
    except Exception:
        return None, None

    root = tk.Tk()
    root.title("DexKeeper Setup")
    root.resizable(False, False)

    token_var = tk.StringVar()
    admin_var = tk.StringVar()
    status_var = tk.StringVar()
    status_var.set("Enter your Telegram BOT_TOKEN.")

    tk.Label(root, text="Telegram BOT_TOKEN (required):").grid(
        row=0, column=0, sticky="w", padx=10, pady=6
    )
    tk.Entry(root, textvariable=token_var, width=50).grid(row=1, column=0, padx=10)
    tk.Label(root, text="ADMIN_ID (optional):").grid(
        row=2, column=0, sticky="w", padx=10, pady=6
    )
    tk.Entry(root, textvariable=admin_var, width=50).grid(row=3, column=0, padx=10)
    tk.Label(root, textvariable=status_var, fg="#555").grid(
        row=4, column=0, sticky="w", padx=10, pady=6
    )

    result = {"token": None, "admin": None}

    def test_token():
        token = token_var.get().strip()
        if not token:
            messagebox.showerror("DexKeeper", "BOT_TOKEN is required.")
            return
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            # fixed https URL
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310  # nosec B310
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                status_var.set("✅ Token verified.")
            else:
                status_var.set("❌ Token invalid.")
        except urllib.error.URLError:
            status_var.set("❌ Token check failed: network error")
        except Exception:
            status_var.set("❌ Token check failed")

    def on_save():
        token = token_var.get().strip()
        if not token:
            messagebox.showerror("DexKeeper", "BOT_TOKEN is required.")
            return
        result["token"] = token
        result["admin"] = admin_var.get().strip() or None
        root.destroy()

    def on_close():
        root.destroy()

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=5, column=0, pady=10)
    tk.Button(btn_frame, text="Test Token", command=test_token).grid(
        row=0, column=0, padx=6
    )
    tk.Button(btn_frame, text="Save & Start", command=on_save).grid(
        row=0, column=1, padx=6
    )
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    return result["token"], result["admin"]


def ensure_config() -> bool:
    global BOT_TOKEN, ADMIN_ID, DB_PATH

    if BOT_TOKEN:
        return True

    if sys.stdin and sys.stdin.isatty():
        token, admin = _prompt_console()
    else:
        token, admin = _prompt_gui()

    if not token:
        print("❌ CRITICAL: BOT_TOKEN missing in .env")
        return False

    _write_env(token, admin or "")
    os.environ["BOT_TOKEN"] = token
    if admin:
        os.environ["ADMIN_ID"] = admin

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = _parse_admin_id(os.getenv("ADMIN_ID"))
    DB_PATH = os.getenv("DB_PATH") or str(DATA_DIR / "dexkeeper.db")
    return True


# === DECORATORS ===


def admin_only(func):
    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        if not await _require_admin(update, context):
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


# === ZOOM ENFORCER LOGIC (Module B) ===


class ZoomStyles:
    PROFESSIONAL = "professional"
    MASCOT = "mascot"
    MINIMAL = "minimal"
    CUSTOM = "custom"

    @staticmethod
    def get_style_names():
        return {
            ZoomStyles.PROFESSIONAL: "👔 Professional",
            ZoomStyles.MASCOT: "🦊 Mascot",
            ZoomStyles.MINIMAL: "⚡ Minimal",
            ZoomStyles.CUSTOM: "✨ Custom Template",
        }

    @staticmethod
    def label(style: str) -> str:
        return ZoomStyles.get_style_names().get(style, style)


async def handle_zoom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Regex scan for Zoom links"""
    if not update.message or not update.message.text:
        return
    chat = update.effective_chat
    if not chat:
        return

    text = update.message.text
    # Basic Zoom Regex
    zoom_pattern = r"(https?://(?:[a-zA-Z0-9-]+\.)?zoom\.us/(?:j|my)/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?)"
    match = re.search(zoom_pattern, text)

    if match:
        conn = _get_db(context)
        style = await get_setting(conn, "zoom_style", ZoomStyles.PROFESSIONAL)

        if style == "off":
            return

        full_url, meeting_id, passcode = match.groups()
        # Safe access to effective_user (may be None in channel posts)
        user_name = "Unknown"
        if update.effective_user and update.effective_user.name:
            user_name = update.effective_user.name
        host = escape_markdown(user_name, version=2)

        # Delete original
        try:
            await update.message.delete()
        except TelegramError as e:
            logger.debug(f"Could not delete Zoom message: {e}")

        # Format Card
        msg_text = ""
        if style == ZoomStyles.PROFESSIONAL:
            msg_text = (
                f"🎥 **Meeting Started**\\nHosted by {host}\\n\\n"
                f"🆔 ID: `{meeting_id}`\\n"
                + (f"🔐 Passcode: `{passcode}`\\n" if passcode else "")
                + f"\\n[Join Meeting]({full_url})"
            )
        elif style == ZoomStyles.MASCOT:
            msg_text = (
                f"🦊 **DexKeeper Zoom\\-In\\!**\\n{host} opened a portal\\!\\n\\n"
                f"🌟 **ID:** `{meeting_id}`\\n"
                + (f"🔑 **Code:** `{passcode}`\\n" if passcode else "")
                + f"\\n🚀 [Jump In]({full_url})"
            )
        elif style == ZoomStyles.MINIMAL:
            msg_text = f"**Zoom:** [Join Now]({full_url}) \\(ID: `{meeting_id}`\\)"
        elif style == ZoomStyles.CUSTOM:
            tmpl = await get_setting(conn, "custom_zoom_template", "{url}")
            msg_text = (
                tmpl.replace("{url}", full_url)
                .replace("{id}", meeting_id)
                .replace("{passcode}", passcode or "")
                .replace("{host}", host)
            )

        await context.bot.send_message(
            chat_id=chat.id, text=msg_text, parse_mode="MarkdownV2"
        )


# === ADMIN DASHBOARD (Module C) ===

# States for ConversationHandler
(
    MENU,
    INPUT_BAN,
    INPUT_PROMOTE,
    INPUT_POLL_QUESTION,
    INPUT_POLL_OPTIONS,
    INPUT_SCHEDULE_TIME,
    INPUT_SCHEDULE_TEXT,
    INPUT_TOPIC,
    INPUT_WELCOME,
    INPUT_FILTER,
    WAITING_FOR_TEMPLATE,
    INPUT_BROADCAST,
) = range(12)


@admin_only
async def admin_panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry Point for Admin Dashboard"""
    if update.effective_user:
        await _upsert_user(_get_db(context), update.effective_user, status="active")
    await show_admin_menu(update, context, "root")
    return MENU


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        await _upsert_user(_get_db(context), update.effective_user, status="active")
    if not update.effective_message:
        return

    if await _is_admin(update, context):
        text = "DexKeeper is online. Use /admin here to manage the connected group."
    else:
        text = (
            "DexKeeper is online. Keep this DM started if an admin wants to send you announcements."
        )
    await update.effective_message.reply_text(text)


async def show_admin_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, menu_type: str
):
    """Render Hierarchical Menus"""
    # Menu Definitions
    keyboards = {
        "root": [
            [
                InlineKeyboardButton("👥 User Management", callback_data="menu:users"),
                InlineKeyboardButton("📢 Engagement", callback_data="menu:engage"),
            ],
            [
                InlineKeyboardButton("🔧 Group Config", callback_data="menu:config"),
                InlineKeyboardButton("🛡️ Security", callback_data="menu:security"),
            ],
            [InlineKeyboardButton("❌ Close Panel", callback_data="admin:close")],
        ],
        "users": [
            [
                InlineKeyboardButton("🔨 Ban User", callback_data="action:ban_start"),
                InlineKeyboardButton(
                    "🏳️ Unban User", callback_data="action:unban_start"
                ),
            ],
            [
                InlineKeyboardButton("🔍 View User", callback_data="action:view_start"),
                InlineKeyboardButton(
                    "👮 Promote Admin", callback_data="action:promote_start"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📥 Export Users (CSV)", callback_data="action:export_csv"
                )
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="menu:root")],
        ],
        "engage": [
            [
                InlineKeyboardButton(
                    "📊 Create Poll", callback_data="action:poll_start"
                ),
                InlineKeyboardButton(
                    "📂 New Topic", callback_data="action:topic_start"
                ),
            ],
            [
                InlineKeyboardButton(
                    "👋 Edit Welcome", callback_data="action:welcome_start"
                ),
                InlineKeyboardButton(
                    "⏳ Schedule Msg", callback_data="action:schedule_start"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast All", callback_data="action:broadcast_start"
                )
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="menu:root")],
        ],
        "config": [
            [InlineKeyboardButton("📝 Zoom Config", callback_data="admin:zoom_menu")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu:root")],
        ],
        "security": [
            [
                InlineKeyboardButton(
                    "🔒 Toggle Lockdown", callback_data="action:lockdown_toggle"
                ),
                InlineKeyboardButton(
                    "🤬 Bad Words Filter", callback_data="action:filter_start"
                ),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="menu:root")],
        ],
    }

    text = f"🛡️ **DexKeeper Admin: {menu_type.upper()}**"
    markup = InlineKeyboardMarkup(keyboards.get(menu_type, keyboards["root"]))

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=markup, parse_mode="Markdown"
        )
    elif update.message:
        await update.message.reply_text(
            text, reply_markup=markup, parse_mode="Markdown"
        )
    else:
        return


async def admin_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main Switchboard for Dashboard Buttons"""
    query = update.callback_query
    if not query or query.data is None:
        return MENU
    if not await _require_admin(update, context):
        return ConversationHandler.END
    await query.answer()
    data = str(query.data)

    # Navigation
    if data.startswith("menu:"):
        parts = data.split(":", 1)
        if len(parts) == 2:
            await show_admin_menu(update, context, parts[1])
        else:
            await query.answer("Invalid menu selection", show_alert=True)
        return MENU

    # Zoom Style Setter (Fix for Wiring Check)
    if data.startswith("set_zoom_style:"):
        parts = data.split(":", 1)
        if len(parts) != 2:
            await query.answer("Invalid style selection", show_alert=True)
            return MENU
        new_style = parts[1]
        conn = _get_db(context)
        await set_setting(conn, "zoom_style", new_style)

        style_name = ZoomStyles.label(new_style)
        await query.answer(f"Style set to: {style_name}")
        await zoom_config_menu(update, context)  # Refresh menu
        return MENU

    # Cancel Button Markup for Inputs
    cancel_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel_input")]]
    )
    user_data = cast(Dict[str, Any], context.user_data)

    # Module A: User Actions
    if data == "action:ban_start":
        user_data["action_type"] = "ban"
        await query.edit_message_text(
            "🔨 **Ban User**\nSend User ID:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_BAN
    if data == "action:unban_start":
        user_data["action_type"] = "unban"
        await query.edit_message_text(
            "🏳️ **Unban User**\nSend User ID:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_BAN
    if data == "action:view_start":
        user_data["action_type"] = "view"
        await query.edit_message_text(
            "🔍 **View User**\nSend User ID:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_BAN
    if data == "action:promote_start":
        await query.edit_message_text(
            "👮 **Promote**\nSend User ID to promote:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_PROMOTE
    if data == "action:export_csv":
        await export_data_handler(update, context)
        return MENU

    # Module C: Engagement Actions
    if data == "action:poll_start":
        await query.edit_message_text(
            "📊 **New Poll**\nSend the Question:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_POLL_QUESTION
    if data == "action:topic_start":
        await query.edit_message_text(
            "📂 **New Topic**\nSend Topic Name:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_TOPIC
    if data == "action:welcome_start":
        curr = await get_setting(_get_db(context), "welcome_message", "Welcome!")
        await query.edit_message_text(
            f"👋 **Edit Welcome**\nCurrent: `{curr}`\n\nSend new text:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_WELCOME
    if data == "action:schedule_start":
        await query.edit_message_text(
            "⏳ **Schedule**\nSend delay in minutes:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_SCHEDULE_TIME
    if data == "action:broadcast_start":
        await query.edit_message_text(
            "📢 **Broadcast**\nSend message to broadcast to ALL users:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_BROADCAST

    # Security Actions
    if data == "action:filter_start":
        words = await get_setting(_get_db(context), "auto_decline_words", [])
        await query.edit_message_text(
            f"🤬 **Bad Words**\nCurrent: {', '.join(words)}\n\nSend word to Add/Remove:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_FILTER
    if data == "action:lockdown_toggle":
        conn = _get_db(context)
        curr = await get_setting(conn, "lockdown_mode", False)
        await set_setting(conn, "lockdown_mode", not curr)
        await query.answer(
            f"Lockdown {'ENABLED' if not curr else 'DISABLED'}", show_alert=True
        )
        await show_admin_menu(update, context, "security")
        return MENU

    # Zoom Config
    if data == "admin:zoom_menu":
        await zoom_config_menu(update, context)
        return MENU

    if data == "admin:close":
        msg = query.message
        if msg:
            await cast(Message, msg).delete()
        return ConversationHandler.END

    return MENU


# === INPUT HANDLERS (WIZARDS) ===


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Universal Cancel"""
    query = update.callback_query
    if query:
        await query.answer("Operation Cancelled")
        await show_admin_menu(update, context, "root")
        return MENU
    if update.message:
        await update.message.reply_text("Operation Cancelled")
        await show_admin_menu(update, context, "root")
        return MENU
    return MENU


async def handle_broadcast_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wizard for Broadcast with rate limiting"""
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.effective_user or not update.message or not update.message.text:
        if update.message:
            await update.message.reply_text("❌ Invalid message.")
        return MENU
    admin_id = update.effective_user.id
    now = time.time()

    # Rate limit: 60 seconds between broadcasts (with lock to prevent race condition)
    async with BROADCAST_LOCKS[admin_id]:
        if admin_id in LAST_BROADCAST and now - LAST_BROADCAST[admin_id] < 60:
            remaining = int(60 - (now - LAST_BROADCAST[admin_id]))
            await update.message.reply_text(
                f"⏳ Please wait {remaining}s between broadcasts"
            )
            await show_admin_menu(update, context, "engage")
            return MENU

        LAST_BROADCAST[admin_id] = now
    message = update.message.text
    conn = _get_db(context)
    await _upsert_user(conn, update.effective_user, status="active")

    async with conn.execute("SELECT user_id FROM users ORDER BY joined_at ASC") as cursor:
        users = list(await cursor.fetchall())

    sent = 0
    start = time.time()
    progress_msg = await update.message.reply_text(
        f"📢 Sending to {len(users)} users..."
    )

    for row in users:
        uid = row[0]
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
            await asyncio.sleep(0.05)
        except TelegramError as e:
            logger.debug(f"Could not send broadcast to {uid}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected broadcast error for {uid}: {e}")

    await progress_msg.edit_text(
        f"✅ **Broadcast Done**\nSent: {sent}\nTime: {time.time() - start:.1f}s",
        parse_mode="Markdown",
    )
    await show_admin_menu(update, context, "engage")
    return MENU


async def export_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate CSV Export"""
    if not await _require_admin(update, context):
        return ConversationHandler.END
    chat = update.effective_chat
    if not chat:
        return MENU
    conn = _get_db(context)
    filename = DATA_DIR / f"dexkeeper_users_{int(time.time())}.csv"

    async with conn.execute("SELECT * FROM users") as cursor:
        rows = await cursor.fetchall()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["User ID", "Username", "Name", "Language", "Joined", "Status"])
        for r in rows:
            writer.writerow(list(r))

    try:
        with open(filename, "rb") as f:
            await context.bot.send_document(
                chat_id=chat.id,
                document=f,
                caption="📊 **DexKeeper User Export**",
            )
    finally:
        try:
            os.remove(filename)
        except Exception as e:
            logger.warning(f"Failed to remove temp CSV file: {e}")

    if update.callback_query:
        await show_admin_menu(update, context, "users")
    return MENU


async def handle_id_action_real(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid input")
            await show_admin_menu(update, context, "users")
        return MENU
    uid_str = update.message.text.strip()
    try:
        user_id = int(uid_str)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID. Expected format: 123456789"
        )
        await show_admin_menu(update, context, "users")
        return MENU

    conn = _get_db(context)
    await _upsert_user(conn, update.effective_user, status="active")
    user_data = cast(Dict[str, Any], context.user_data)
    action = user_data.get("action_type", "ban")
    target_chat_id = None

    if action in {"ban", "unban"}:
        target_chat_id = await _resolve_target_chat_id(update, context)
        if target_chat_id is None:
            await update.message.reply_text(
                "❌ No managed group is known yet. Add the bot to a group first, then send a message there before using this action from DM."
            )
            await show_admin_menu(update, context, "users")
            return MENU

    try:
        if action == "ban":
            # Use transaction to prevent TOCTOU race condition
            await conn.execute("BEGIN IMMEDIATE")
            try:
                bl = await get_setting(conn, "blacklist", [])
                if user_id not in bl:
                    bl.append(user_id)
                    # set_setting will commit; we need to handle it specially
                    await conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        ("blacklist", json.dumps(bl)),
                    )
                await conn.commit()

                # Kick happens after DB commit succeeds
                api_success = True
                try:
                    await context.bot.ban_chat_member(target_chat_id, user_id)
                except TelegramError as e:
                    api_success = False
                    logger.warning(f"Ban API call failed (user blacklisted in DB): {e}")

                if api_success:
                    await update.message.reply_text(f"🚫 Banned {user_id}")
                else:
                    await update.message.reply_text(
                        f"⚠️ User {user_id} added to blacklist, but bot lacks permission to ban from chat"
                    )
            except Exception:
                await conn.rollback()
                raise

        elif action == "unban":
            await conn.execute("BEGIN IMMEDIATE")
            try:
                bl = await get_setting(conn, "blacklist", [])
                if user_id in bl:
                    bl.remove(user_id)
                    await conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                        ("blacklist", json.dumps(bl)),
                    )
                await conn.commit()
                await context.bot.unban_chat_member(
                    target_chat_id, user_id, only_if_banned=True
                )
                await update.message.reply_text(f"✅ Unbanned {user_id}")
            except Exception:
                await conn.rollback()
                raise

        elif action == "view":
            async with conn.execute(
                """
                SELECT user_id, username, full_name, language, joined_at, status
                FROM users
                WHERE user_id = ?
                """,
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()

            admins = await get_setting(conn, "admins", [])
            blacklist = await get_setting(conn, "blacklist", [])
            if row:
                text = (
                    f"👤 User {row['user_id']}\n"
                    f"Username: @{row['username'] or 'unknown'}\n"
                    f"Name: {row['full_name'] or 'unknown'}\n"
                    f"Language: {row['language'] or 'unknown'}\n"
                    f"Joined: {row['joined_at']}\n"
                    f"Status: {row['status']}\n"
                    f"Admin: {'yes' if user_id in admins else 'no'}\n"
                    f"Blacklisted: {'yes' if user_id in blacklist else 'no'}"
                )
            else:
                text = (
                    f"👤 User {user_id}\n"
                    "No stored profile yet. The user has not been seen in a tracked join or DM."
                )
            await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Action '{action}' failed for user {user_id}: {e}")
        await update.message.reply_text(f"❌ Operation failed: {type(e).__name__}")

    await show_admin_menu(update, context, "users")
    return MENU


async def handle_poll_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid question.")
        return MENU
    user_data = cast(Dict[str, Any], context.user_data)
    user_data["poll_q"] = update.message.text
    cancel_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel_input")]]
    )
    await update.message.reply_text(
        "📝 **Options**\nSend comma-separated options:",
        reply_markup=cancel_markup,
        parse_mode="Markdown",
    )
    return INPUT_POLL_OPTIONS


async def handle_poll_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid options.")
        return INPUT_POLL_OPTIONS
    user_data = cast(Dict[str, Any], context.user_data)
    question = user_data.get("poll_q")
    if not question:
        await update.message.reply_text("❌ Poll question missing. Start again.")
        return MENU
    options = _parse_poll_options(update.message.text)
    if len(options) < 2:
        await update.message.reply_text("❌ Need 2+ options. Try again.")
        return INPUT_POLL_OPTIONS
    if len(options) > 10:
        await update.message.reply_text("❌ Max 10 options. Please shorten.")
        return INPUT_POLL_OPTIONS
    target_chat_id = await _resolve_target_chat_id(update, context)
    if target_chat_id is None:
        await update.message.reply_text(
            "❌ No managed group is known yet. Add the bot to a group first, then send a message there before creating polls from DM."
        )
        return MENU
    await context.bot.send_poll(
        chat_id=target_chat_id,
        question=question,
        options=options,
    )
    await show_admin_menu(update, context, "engage")
    return MENU


async def handle_schedule_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid number.")
        return INPUT_SCHEDULE_TIME
    mins = _parse_schedule_minutes(update.message.text)
    if mins is not None:
        user_data = cast(Dict[str, Any], context.user_data)
        user_data["sched_mins"] = mins
        cancel_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel_input")]]
        )
        await update.message.reply_text(
            "📝 **Message Text**\nSend message content:",
            reply_markup=cancel_markup,
            parse_mode="Markdown",
        )
        return INPUT_SCHEDULE_TEXT
    await update.message.reply_text(
        "❌ Invalid number. Enter minutes between 1 and 10080."
    )
    return INPUT_SCHEDULE_TIME


async def _send_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    """Async callback for scheduled messages"""
    try:
        job = context.job
        if not job or not isinstance(job.data, dict):
            return
        data = cast(Dict[str, Any], job.data)
        await context.bot.send_message(
            chat_id=data["cid"],
            text=data["text"],
        )
    except Exception as e:
        logger.error(f"Failed to send scheduled message: {e}")


async def handle_schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid message.")
        return INPUT_SCHEDULE_TEXT
    user_data = cast(Dict[str, Any], context.user_data)
    mins = user_data.get("sched_mins")
    if not isinstance(mins, int):
        await update.message.reply_text("❌ Schedule time missing. Send minutes first.")
        return INPUT_SCHEDULE_TIME
    text = update.message.text
    target_chat_id = await _resolve_target_chat_id(update, context)
    if target_chat_id is None:
        await update.message.reply_text(
            "❌ No managed group is known yet. Add the bot to a group first, then send a message there before scheduling posts from DM."
        )
        return MENU
    # Job Queue Logic
    job_queue = context.job_queue
    if job_queue:
        job_queue.run_once(
            _send_scheduled_message,
            mins * 60,
            data={"cid": target_chat_id, "text": text},
            name=str(uuid.uuid4()),
        )
        await update.message.reply_text(f"✅ Scheduled in {mins}m")
    else:
        await update.message.reply_text("❌ Error: JobQueue not active.")

    await show_admin_menu(update, context, "engage")
    return MENU

async def handle_topic_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid topic name.")
        return MENU
    target_chat_id = await _resolve_target_chat_id(update, context)
    if target_chat_id is None:
        await update.message.reply_text(
            "❌ No managed group is known yet. Add the bot to a forum-enabled group first, then send a message there before creating topics from DM."
        )
        return MENU
    try:
        topic = await context.bot.create_forum_topic(
            chat_id=target_chat_id, name=update.message.text
        )
        await update.message.reply_text(f"✅ Topic Created: {topic.name}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    await show_admin_menu(update, context, "engage")
    return MENU


async def handle_welcome_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid welcome message.")
        return MENU
    await set_setting(_get_db(context), "welcome_message", update.message.text)
    await update.message.reply_text("✅ Welcome Message Updated")
    await show_admin_menu(update, context, "engage")
    return MENU


async def handle_filter_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid word.")
        return MENU
    word = update.message.text.lower()
    conn = _get_db(context)
    words = await get_setting(conn, "auto_decline_words", [])
    if word in words:
        words.remove(word)
        await update.message.reply_text(f"🗑️ Removed '{word}'")
    else:
        words.append(word)
        await update.message.reply_text(f"➕ Added '{word}'")
    await set_setting(conn, "auto_decline_words", words)
    await show_admin_menu(update, context, "security")
    return MENU


async def handle_promote_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_admin(update, context):
        return ConversationHandler.END
    if not update.message or not update.message.text:
        if update.effective_message:
            await update.effective_message.reply_text("❌ Invalid User ID.")
        return MENU
    try:
        user_id = int(update.message.text)
        admins = await get_setting(_get_db(context), "admins", [])
        if user_id not in admins:
            admins.append(user_id)
            await set_setting(_get_db(context), "admins", admins)
        await update.message.reply_text(f"✅ Promoted {user_id}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID. Expected format: 123456789"
        )
    except Exception as e:
        logger.error(f"Failed to promote user: {e}")
        await update.message.reply_text("❌ Promotion failed")
    await show_admin_menu(update, context, "users")
    return MENU


# === ZOOM CONFIG MENU ===


async def zoom_config_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "👔 Professional", callback_data="set_zoom_style:professional"
            )
        ],
        [InlineKeyboardButton("🦊 Mascot", callback_data="set_zoom_style:mascot")],
        [InlineKeyboardButton("⚡ Minimal", callback_data="set_zoom_style:minimal")],
        [InlineKeyboardButton("🔴 Disable", callback_data="set_zoom_style:off")],
        [InlineKeyboardButton("🔙 Back to Config", callback_data="menu:config")],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🎥 **Zoom Enforcer Style**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )


# === GLOBAL MIDDLEWARE (Module A: Flood & Filter) ===


async def global_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    if not user:
        return
    chat = update.effective_chat
    if not chat:
        return
    await _remember_managed_chat(context, chat)

    # I18n
    user_data = cast(Dict[str, Any], context.user_data)
    user_data["lang"] = user.language_code or "en"

    # Flood Gate with asyncio lock for concurrency safety
    uid = user.id
    # defaultdict creates lock automatically on first access (no race condition)
    async with SPAM_LOCKS[uid]:
        now = datetime.datetime.now().timestamp()
        history = SPAM_CACHE.get(uid, [])
        history = [t for t in history if now - t < 2.0]
        history.append(now)
        SPAM_CACHE[uid] = history

        if len(history) > 5:
            try:
                await update.message.delete()
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=datetime.datetime.now() + datetime.timedelta(hours=1),
                )
            except TelegramError as e:
                logger.debug(f"Flood gate action failed: {e}")

    # Word Filter
    conn = _get_db(context)
    banned = await get_setting(conn, "auto_decline_words", [])
    if any(w in update.message.text.lower() for w in banned):
        try:
            await update.message.delete()
        except TelegramError as e:
            logger.debug(f"Could not delete message with banned word: {e}")


# === ENTRY POINTS ===


async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Module B: Public Verify"""
    if not update.message or not update.message.new_chat_members:
        return
    chat = update.effective_chat
    if not chat:
        return
    await _remember_managed_chat(context, chat)
    conn = _get_db(context)
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        await _upsert_user(conn, member, status="pending")
        if await get_setting(conn, "lockdown_mode", False):
            try:
                await context.bot.ban_chat_member(chat.id, member.id)
                await context.bot.unban_chat_member(
                    chat.id, member.id, only_if_banned=True
                )
            except TelegramError as e:
                logger.warning(f"Failed to reject new member {member.id}: {e}")
                await context.bot.restrict_chat_member(
                    chat.id,
                    member.id,
                    ChatPermissions(can_send_messages=False),
                )
            await update.message.reply_text(i18n.get("lockdown"))
            continue
        if await get_setting(conn, "captcha_enabled", True):
            await context.bot.restrict_chat_member(
                chat.id,
                member.id,
                ChatPermissions(can_send_messages=False),
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🤖 I am Human", callback_data=f"verify:{member.id}"
                    )
                ]
            ]
            await update.message.reply_text(
                f"Welcome {member.name}! Verify to speak.",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            tmpl = await get_setting(conn, "welcome_message", "Welcome!")
            await update.message.reply_text(tmpl)


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or query.data is None:
        return
    chat = update.effective_chat
    if not chat:
        await query.answer("Chat not available", show_alert=True)
        return
    user = update.effective_user
    if not user:
        await query.answer("User not available", show_alert=True)
        return
    parts = str(query.data).split(":", 1)
    if len(parts) != 2:
        await query.answer("Invalid verification data", show_alert=True)
        return

    try:
        uid = int(parts[1])
    except ValueError:
        await query.answer("Invalid user ID", show_alert=True)
        return

    if user.id != uid:
        await query.answer("Not for you!", show_alert=True)
        return

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            uid,
            _unrestricted_permissions(),
        )
        msg = query.message
        if msg:
            await cast(Message, msg).delete()
        await _upsert_user(_get_db(context), user, status="active")
        tmpl = await get_setting(_get_db(context), "welcome_message", "Welcome!")
        await context.bot.send_message(chat.id, tmpl)
        await query.answer("Verified!", show_alert=False)
    except TelegramError as e:
        logger.warning(f"Failed to verify user {uid}: {e}")
        await query.answer("Verification failed", show_alert=True)


# === MAIN ===


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


async def post_init(app):
    """Initialize bot resources"""
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.commit()

    # Store connection in app context
    # Note: aiosqlite handles async concurrency internally via queueing.
    # Each await automatically serializes writes. Read-only queries can run concurrently.
    setattr(app, "db_conn", conn)

    # Schema Init
    await conn.executescript(SCHEMA)

    # Defaults
    if await get_setting(conn, "welcome_message") is None:
        await set_setting(conn, "welcome_message", "Welcome! Please read the rules.")
    managed_chat_id = await get_setting(conn, "managed_chat_id")
    if isinstance(managed_chat_id, int):
        app.bot_data["managed_chat_id"] = managed_chat_id

    # Background jobs
    app.job_queue.run_repeating(_heartbeat_job, interval=60, first=5)
    app.job_queue.run_repeating(
        _cleanup_spam_cache_job, interval=3600, first=600
    )  # Every hour, start after 10min

    logger.info("🚀 DexKeeper Systems Online")


async def post_shutdown(app):
    """Cleanup resources on shutdown"""
    try:
        conn = getattr(app, "db_conn", None)
        if conn:
            await conn.close()
            logger.info("Database connection closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


def main():
    global SILENT_MODE
    args = set(sys.argv[1:])
    if "--show-tray" in args:
        os.environ["DEXKEEPER_TRAY"] = "1"
    if "--silent" in args:
        os.environ["DEXKEEPER_SILENT"] = "1"

    if not ensure_config():
        return

    defaults = Defaults(parse_mode="Markdown", block=False)
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .defaults(defaults)
        .build()
    )
    global APP_INSTANCE
    APP_INSTANCE = app
    SILENT_MODE = os.getenv("DEXKEEPER_SILENT", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    data = _load_runtime_settings()
    if "silent_mode" in data:
        SILENT_MODE = bool(data["silent_mode"])
    start_tray(app)
    # start_update_check() -> Converted to job
    app.job_queue.run_once(_update_check_job, 10, name="update_check")
    _apply_restart_schedule()

    # Admin System
    app.add_handler(TypeHandler(Update, paused_handler), group=0)
    app.add_handler(CommandHandler("start", start_cmd))
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel_cmd)],
        states={
            MENU: [CallbackQueryHandler(admin_selection_handler)],
            INPUT_BAN: [
                MessageHandler(filters.TEXT, handle_id_action_real),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_PROMOTE: [
                MessageHandler(filters.TEXT, handle_promote_input),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_POLL_QUESTION: [
                MessageHandler(filters.TEXT, handle_poll_question),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_POLL_OPTIONS: [
                MessageHandler(filters.TEXT, handle_poll_options),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_SCHEDULE_TIME: [
                MessageHandler(filters.TEXT, handle_schedule_time),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_SCHEDULE_TEXT: [
                MessageHandler(filters.TEXT, handle_schedule_text),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_TOPIC: [
                MessageHandler(filters.TEXT, handle_topic_name),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_WELCOME: [
                MessageHandler(filters.TEXT, handle_welcome_input),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_FILTER: [
                MessageHandler(filters.TEXT, handle_filter_input),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
            INPUT_BROADCAST: [
                MessageHandler(filters.TEXT, handle_broadcast_input),
                CallbackQueryHandler(handle_cancel, pattern="^admin:cancel_input$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", handle_cancel)],
        name="admin_gui",
        conversation_timeout=300,  # 5 minutes
    )

    app.add_handler(admin_handler)

    # Module B: Join Logic
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member)
    )
    app.add_handler(CallbackQueryHandler(verify_callback, pattern=r"^verify:"))

    # Module A: Global Middleware (Flood/Filter/Zoom)
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, global_middleware),
        group=1,
    )
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_zoom_message),
        group=2,
    )

    # Helpers
    app.add_error_handler(error_handler)

    logger.info("🦊 DexKeeper (V8) Starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
