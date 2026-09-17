# Ritm

A minimal, single-file Windows 10/11 GUI utility that cleans up temporary and junk files.

![platform](https://img.shields.io/badge/platform-Windows-blue)
![license](https://img.shields.io/badge/license-MIT-green)

🇷🇺 [Читать на русском](README.ru.md)

## What it cleans

- `%TEMP%`, `%TMP%`, `C:\Windows\Temp`
- Windows Update cache (`SoftwareDistribution\Download`, `DeliveryOptimization`)
- Windows Error Reporting (WER) reports and crash dumps (`CrashDumps`, `Minidump`, `MEMORY.DMP`)
- DirectX shader cache (`D3DSCache`)
- Explorer thumbnail cache
- Windows setup/upgrade logs (`Panther`)
- `.log` files under `C:\Windows\Logs`
- Recycle Bin
- Prefetch folder (optional, off by default)

Built-in safety check: the app will never touch top-level system folders
(`C:\`, `C:\Windows`, `C:\Program Files`, `C:\Users`, `C:\ProgramData`, etc.),
even if an environment variable is missing or points somewhere unexpected.

## Requirements

- Windows 10/11
- Python 3.8+ (only if running from source — no third-party packages needed)
- Administrator rights (requested automatically via UAC)

## Run from source

```bash
python ritm.py
```

## Build a standalone .exe

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=app.ico ritm.py
```

The executable will appear in the `dist/` folder.

## Error log

If something couldn't be deleted (e.g. a file was in use), the app writes
details to:

```
%LocalAppData%\Ritm\ritm_errors.log
```

The file is overwritten on every run, so it always reflects the last cleanup.

## ⚠️ Important

This app **permanently deletes files** (no Recycle Bin involved for most
targets, and it empties the Recycle Bin too). Make sure you understand what
will be removed before clicking the button. Use at your own risk — the
author is not responsible for any data loss.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and pull requests are welcome. Before submitting a PR, please:
- keep the code style consistent with the rest of the file;
- avoid adding external dependencies without a good reason (currently the
  project uses only the Python standard library);
- describe what your change does and why.
