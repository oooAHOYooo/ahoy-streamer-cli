# Repository and release checklist

## Hosted repository

Created and pushed: https://github.com/oooAHOYooo/ahoy-streamer-cli (public for early testing).
The `codex/streamer-tui-first-draft` branch contains the current runnable draft. The Python
package is not published to PyPI. Project source code is licensed under MIT in the root
`LICENSE` file. This does not grant rights to AHOY trademarks, media, or third-party materials;
verify rights to any such material before redistribution or public demos. Check package-name
ownership before any PyPI release.

## Public launch after T05

- Confirm all included source code can be distributed under MIT and confirm branding/media usage rights for any recorded demo.
- Verify macOS/Linux install and mpv instructions with exact tested versions.
- Check redirects/playable media handling and subprocess cleanup.
- Publish a small tagged release with honest support/limitations notes.
- Record a short search → audio → terminal video demo using authorized media.
- Include copyable agent examples and a concise bug report template.
- Measure usefulness through issues/install feedback; no telemetry by default.

Avoid Homebrew, MCP servers, installers, accounts, or paid distribution before the
core CLI has repeat users. Popularity is a hypothesis, not a release acceptance test.
