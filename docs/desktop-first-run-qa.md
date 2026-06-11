# Desktop first-run QA

Validate packaged desktop startup before release.

## Platforms

- Windows app package.
- macOS app package.
- Linux AppImage.

## Checklist

- App starts without a terminal.
- First-run setup appears when local config is missing.
- Existing local config is preserved.
- Admin identity input accepts numeric values.
- Startup preference can be changed.
- Runtime data is stored in the OS user data directory.
- Logs do not expose sensitive runtime config.
- Tray icon appears after successful startup.
- Open Logs works.
- Open Data Folder works.
- Open Admin Panel works.

## Result format

Record platform, artifact name, commit, pass/fail result, and blockers. Do not paste private runtime values into reports.
