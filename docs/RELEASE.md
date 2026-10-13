# Repository and release checklist

## Hosted repository (pending authentication)

After GitHub sign-in, verify the intended account/owner and create the repository:

```sh
gh auth login -h github.com
gh repo create oooAHOYooo/ahoy-streamer-cli --private --source=. --remote=origin --push
```

Run from this folder. If that remote already exists, inspect it instead of creating
or overwriting it. No remote has been created by this planning session.
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
