from Sources.DexKeeper_Bot.moderation_rules import (
    ModerationRule,
    any_rule_matches,
    legacy_words_to_rules,
)


def test_whole_word_rule_avoids_substring_false_positive():
    rule = ModerationRule("bad", mode="whole_word")
    assert rule.matches("that is bad")
    assert not rule.matches("that badge is fine")


def test_substring_rule_preserves_legacy_behavior():
    rule = ModerationRule("bad", mode="substring")
    assert rule.matches("badge")


def test_regex_rule_matches_pattern():
    rule = ModerationRule(r"b[ae]d", mode="regex")
    assert rule.matches("bad")
    assert rule.matches("bed")


def test_case_sensitive_rule():
    rule = ModerationRule("BAD", mode="whole_word", case_sensitive=True)
    assert rule.matches("BAD")
    assert not rule.matches("bad")


def test_legacy_words_to_rules_uses_substring_mode():
    rules = legacy_words_to_rules(["bad", ""])
    assert rules == [ModerationRule(pattern="bad", mode="substring")]


def test_any_rule_matches():
    rules = [ModerationRule("alpha"), ModerationRule("beta")]
    assert any_rule_matches("beta here", rules)
    assert not any_rule_matches("gamma here", rules)
