from Sources.DexKeeper_Bot.privacy_retention_runtime import (
    RetentionPolicy,
    forget_user_statements,
    redact_secrets,
    retention_cleanup_statements,
    summarize_user_ids,
)


def test_redact_secrets_hides_token_and_api_url():
    token = "123456789" + ":" + "ABCdefGHIjklMNOpqrsTUVwxyz"
    text = "bad " + token + " and https://api.telegram.org/bot" + token + "/getMe"
    out = redact_secrets(text)
    assert "ABCdef" not in out
    assert "[REDACTED_TELEGRAM_BOT_TOKEN]" in out
    assert "bot[REDACTED]" in out


def test_forget_user_statements_cover_local_tables():
    statements = forget_user_statements(123)
    sql = "\n".join(item[0] for item in statements)
    for table in ["pending_requests", "notes", "tags", "history", "users"]:
        assert f"DELETE FROM {table}" in sql


def test_retention_policy_disabled_when_zero():
    assert not RetentionPolicy().enabled()
    assert retention_cleanup_statements(RetentionPolicy()) == []


def test_retention_statements_generated():
    statements = retention_cleanup_statements(RetentionPolicy(history_days=30, notes_days=90))
    assert len(statements) == 2
    assert statements[0][0].startswith("DELETE FROM history")
    assert statements[1][0].startswith("DELETE FROM notes")


def test_summarize_user_ids_truncates():
    assert summarize_user_ids([1, 2, 3], max_visible=5) == "1, 2, 3"
    assert summarize_user_ids([1, 2, 3, 4], max_visible=2) == "1, 2, ... (+2 more)"
