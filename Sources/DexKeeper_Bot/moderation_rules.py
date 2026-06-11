"""Message matching helpers for DexKeeper moderation rules."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

MatchMode = Literal["whole_word", "substring", "regex"]


@dataclass(frozen=True)
class ModerationRule:
    pattern: str
    mode: MatchMode = "whole_word"
    case_sensitive: bool = False

    def matches(self, text: str) -> bool:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        if self.mode == "substring":
            haystack = text if self.case_sensitive else text.lower()
            needle = self.pattern if self.case_sensitive else self.pattern.lower()
            return needle in haystack
        if self.mode == "regex":
            return re.search(self.pattern, text, flags=flags) is not None
        escaped = re.escape(self.pattern)
        return re.search(rf"(?<!\w){escaped}(?!\w)", text, flags=flags) is not None


def legacy_words_to_rules(words: list[str]) -> list[ModerationRule]:
    return [ModerationRule(pattern=word, mode="substring") for word in words if word]


def any_rule_matches(text: str, rules: list[ModerationRule]) -> bool:
    return any(rule.matches(text) for rule in rules)
