from Sources.DexKeeper_Bot.first_run_wizard import write_env_file


def test_write_env_file_writes_local_config(tmp_path):
    env_path = tmp_path / ".env"
    write_env_file(env_path, "token-value", "12345")
    text = env_path.read_text(encoding="utf-8")
    assert "BOT_TOKEN=token-value" in text
    assert "ADMIN_ID=12345" in text
