# Repository and release checklist

## Hosted repository

Created and pushed: https://github.com/oooAHOYooo/ahoy-streamer-cli (private).
Local main tracks origin/main. GitHub CLI authentication works as oooAHOYooo;
network sandbox restrictions can make an authentication check appear to fail.

Private is an initial planning default; public visibility and a license should be
selected deliberately before outreach. Do not assume this project inherits the
platform's license. Do not publish to PyPI until package name ownership is checked.

## Public launch after T05

- Choose license and confirm branding/media usage rights for any recorded demo.
- Verify macOS/Linux install and mpv instructions with exact tested versions.
- Check redirects/playable media handling and subprocess cleanup.
- Publish a small tagged release with honest support/limitations notes.
- Record a short search → audio → terminal video demo using authorized media.
- Include copyable agent examples and a concise bug report template.
- Measure usefulness through issues/install feedback; no telemetry by default.

Avoid Homebrew, MCP servers, installers, accounts, or paid distribution before the
core CLI has repeat users. Popularity is a hypothesis, not a release acceptance test.
