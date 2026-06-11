"""Runtime privacy and retention helpers for DexKeeper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from typing import Iterable

TOKEN_RE = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b")
BOT_API_RE = re.compile(r"https://api\.telegram\.org/bot[^/\s]+", re.IGNORECASE)


def redact_secrets(text: object) -> str:
    """Return text with Telegram bot tokens and Bot API URLs redacted."""
    value = str(text)
    value = TOKEN_RE.sub("[REDACTED_TELEGRAM_BOT_TOKEN]", value)
    value = BOT_API_RE.sub("https://api.telegram.org/bot[REDACTED]", value)
    return value


@dataclass(frozen=True)
class RetentionPolicy:
    history_days: int = 0
    notes_days: int = 0

    def enabled(self) -> bool:
        return self.history_days > 0 or self.notes_days > 0


def utc_cutoff(days: int) -> str:
    if days <= 0:
        raise ValueError("retention days must be positive")
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")


def retention_cleanup_statements(policy: RetentionPolicy) -> list[tuple[str, tuple[object, ...]]]:
    statements: list[tuple[str, tuple[object, ...]]] = []
    if policy.history_days > 0:
        statements.append(("DELETE FROM history WHERE timestamp < ?", (utc_cutoff(policy.history_days),)))
    if policy.notes_days > 0:
        statements.append(("DELETE FROM notes WHERE created_at < ?", (utc_cutoff(policy.notes_days),)))
    return statements


def forget_user_statements(user_id: int) -> list[tuple[str, tuple[object, ...]]]:
    uid = int(user_id)
    return [
        ("DELETE FROM pending_requests WHERE user_id = ?", (uid,)),
        ("DELETE FROM notes WHERE user_id = ?", (uid,)),
        ("DELETE FROM tags WHERE user_id = ?", (uid,)),
        ("DELETE FROM history WHERE user_id = ?", (uid,)),
        ("DELETE FROM users WHERE user_id = ?", (uid,)),
    ]


def summarize_user_ids(user_ids: Iterable[int], max_visible: int = 5) -> str:
    ids = [str(int(item)) for item in user_ids]
    if len(ids) <= max_visible:
        return ", ".join(ids)
    return ", ".join(ids[:max_visible]) + f", ... (+{len(ids) - max_visible} more)"
