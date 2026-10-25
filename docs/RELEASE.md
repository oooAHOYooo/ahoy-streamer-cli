# Repository and release checklist

The public repository is https://github.com/oooAHOYooo/ahoy-streamer-cli. The Python
package is not published to PyPI. The latest published release is the prerelease
[`v0.1.0-standalone-preview.2`](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/tag/v0.1.0-standalone-preview.2).
It contains Windows x64, macOS Intel/Apple Silicon, and Linux x64 standalone ZIPs.

## Follow-up preview

Preview.2 includes the moonlit terminal ship artwork in the source installer and
standalone ZIP `START_HERE.txt`. The build workflow runs on pushes to `main` and can be
started manually. It runs offline tests and startup/backend checks, then uploads one ZIP
artifact per platform. Publishing the GitHub release remains a manual step after all four
build jobs pass.

Keep it marked as a prerelease. The binaries are unsigned on macOS, Linux was built on
Ubuntu 22.04, and live playback has not been verified on clean target devices. The app
uses public media and branding; confirm distribution rights for any recorded demo.
Choose and publish a project license before accepting contributions or describing the
source as open source.

Before a stable release:

- Verify live audio and video on clean macOS, Windows, and Linux systems.
- Check macOS 13 and older Linux support and document tested versions.
- Check redirects and subprocess cleanup.
- Include honest support notes, copyable agent examples, and a concise bug report template.
- Keep telemetry off by default.
