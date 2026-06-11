# Runtime helper integration notes

PR #1 added helper modules that are intentionally additive. They should be wired into the main runtime in small follow-up changes.

## Moderation rules

File:

```text
Sources/DexKeeper_Bot/moderation_rules.py
```

Use it to make blocked-text matching explicit instead of relying on implicit substring checks.

Recommended rollout:

1. Preserve current behavior as the default for existing settings.
2. Add an optional setting for match mode.
3. Support whole-word, substring, and regex matching.
4. Add live group validation before changing the default.

## Privacy and retention helpers

File:

```text
Sources/DexKeeper_Bot/privacy_retention_runtime.py
```

Use it for:

- log-safe redaction before writing exception text,
- local retention cleanup statements,
- local user-erasure statement generation.

Recommended rollout:

1. Wire redaction into risky exception/log paths first.
2. Add migration-backed retention settings later.
3. Keep retention disabled by default for compatibility.
4. Require explicit admin action for local user erasure.

## First-run wizard

File:

```text
Sources/DexKeeper_Bot/first_run_wizard.py
```

Use it only for interactive desktop launches. Headless service runs should fail clearly when required runtime config is missing instead of opening a GUI.
