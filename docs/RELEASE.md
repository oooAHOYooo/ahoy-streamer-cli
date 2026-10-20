# Repository and release checklist

## Hosted repository

Created and pushed: https://github.com/oooAHOYooo/ahoy-streamer-cli (public for early testing).
The `codex/streamer-tui-first-draft` branch contains the current runnable draft. The Python
package is not published to PyPI. No license has been selected; choose one before accepting
contributions or redistributing the code. Do not assume this project inherits the platform's
license. Check package-name ownership before any PyPI release.

## Public launch after T05

The manual `.github/workflows/standalone-build.yml` workflow builds one-file test
executables for Windows x64, macOS Intel/Apple Silicon, and Linux x64 with PyInstaller.
It uploads workflow artifacts only; it does not create a GitHub release or package.
Verify each artifact on a clean machine, especially audio/video backends, before
linking it as an end-user download. Select a license and review third-party notices,
then sign/notarize artifacts as appropriate for distribution.

- Choose license and confirm branding/media usage rights for any recorded demo.
- Verify macOS/Linux install and mpv instructions with exact tested versions.
- Check redirects/playable media handling and subprocess cleanup.
- Publish a small tagged release with honest support/limitations notes.
- Record a short search → audio → terminal video demo using authorized media.
- Include copyable agent examples and a concise bug report template.
- Measure usefulness through issues/install feedback; no telemetry by default.

Avoid Homebrew, MCP servers, installers, accounts, or paid distribution before the
core CLI has repeat users. Popularity is a hypothesis, not a release acceptance test.
