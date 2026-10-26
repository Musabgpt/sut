# AGENTS — SUT

## Project
- Python 3.10+ desktop app: Tkinter UI + SQLite.
- Arabic UI, Syrian pound, offline only.
- Entry point: `sut/__main__.py`; UI: `sut/app.py`; data: `sut/db.py`.

## Commands
- Run from source: `python3 -m sut` or `bash run.sh`.
- Tests (DB only): `python3 -m unittest discover -s tests -v`.
- Tests (UI, headless): `xvfb-run -a python3 -m unittest discover -s tests -v`.
- Build DEB: `bash packaging/build_deb.sh`.
- Install DEB: `sudo dpkg -i dist/sut_0.1.0_all.deb`.
- Launcher: `/usr/bin/sut`; desktop entry: `/usr/share/applications/sut.desktop`.

## Data
- Database: `~/.local/share/sut/sut.db`.
- Override for tests: `SUT_DB_PATH=/path/to/file.db`.
- Sales snapshot product name/price; deleting a product keeps sales history.

## Release
- Repo: https://github.com/Musabgpt/sut
- Keep `DEBIAN/control` version, README release link and dist filename in sync.
- CI: `.github/workflows/ci.yml` runs tests under Xvfb, builds and installs the DEB.
