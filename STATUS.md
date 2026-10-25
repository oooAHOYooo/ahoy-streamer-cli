# Current handoff

- Stage: public standalone preview is available; Python package is not published to PyPI.
- Current branch: `main` at `5091e8e` (on `origin/main`).
- Latest published release: [`v0.1.0-standalone-preview.2`](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/tag/v0.1.0-standalone-preview.2), with Windows x64, macOS Intel/Apple Silicon, and Linux x64 ZIPs.
- Preview.2 was built from main commit `5091e8e`. All four Actions jobs passed; all four ZIPs were downloaded and inspected to confirm the startup guide, executable, and artwork.
- Installer and ZIP `START_HERE.txt` now show the same moonlit ASCII ship, AHOY wordmark, and tagline. Installer color is disabled for redirected output, `NO_COLOR`, and `TERM=dumb`; setup has five clear steps.
- `.github/workflows/standalone-build.yml` now runs on `main` pushes as well as manual dispatch. It runs offline tests and executable checks, then uploads four platform ZIPs. GitHub release publishing remains manual.
- Fastest install is still download, extract, and run. macOS builds are unsigned; Linux is built on Ubuntu 22.04; live playback has not been verified on clean target devices. Keep the next release marked prerelease.
- Checks: `python3 -m unittest discover -s tests -q` — 33 tests, 1 skipped, pass. `bash -n install.sh uninstall.sh`, `python3 -m py_compile packaging/make_release_bundle.py`, and `git diff --check` — pass. Synthetic bundle check confirmed the artwork is in `START_HERE.txt`.
- Package wheel check could not run because system Python has no `pip`. The full installer and live cross-platform playback were not run.
- Changed files: `.github/workflows/standalone-build.yml`, `README.md`, `STATUS.md`, `docs/RELEASE.md`, `install.sh`, `packaging/make_release_bundle.py`.
- Checksums are recorded in the GitHub release notes. The release remains a prerelease; stable release still needs clean-device playback validation and a project license decision.
