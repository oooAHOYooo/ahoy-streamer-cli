#!/usr/bin/env bash
set -euo pipefail

install_root="${XDG_DATA_HOME:-$HOME/.local/share}/ahoy-streamer-cli"
local_bin="$HOME/.local/bin"
launcher="$local_bin/ahoy-streamer"
uninstaller="$local_bin/ahoy-streamer-uninstall"
expected_origin="https://github.com/oooAHOYooo/ahoy-streamer-cli.git"

fail() {
    printf 'ahoy-streamer uninstaller: %s\n' "$*" >&2
    exit 1
}

script_path="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/$(basename -- "${BASH_SOURCE[0]}")"
[ -L "$script_path" ] && script_path="$(readlink "$script_path")"
[ "$script_path" = "$install_root/uninstall.sh" ] || \
    fail "This command does not point to the managed installation at $install_root."
[ -d "$install_root/.git" ] || fail "Managed app checkout not found at $install_root."

origin="$(git -C "$install_root" remote get-url origin)"
[ "$origin" = "$expected_origin" ] || fail "Unexpected Git origin; refusing to remove $install_root."
branch="$(git -C "$install_root" branch --show-current)"
[ "$branch" = main ] || fail "Installation is on '$branch', not main; refusing to remove it."
changes="$(git -C "$install_root" status --porcelain --untracked-files=all)"
[ -z "$changes" ] || fail "The installation has local files or changes. Review them before removing $install_root."

if [ -L "$launcher" ]; then
    [ "$(readlink "$launcher")" = "$install_root/.venv/bin/ahoy-streamer" ] || \
        fail "The ahoy-streamer launcher points somewhere else; refusing to remove it."
elif [ -e "$launcher" ]; then
    fail "The ahoy-streamer launcher is not a symlink; refusing to remove it."
fi
if [ -L "$uninstaller" ]; then
    [ "$(readlink "$uninstaller")" = "$script_path" ] || \
        fail "The uninstaller launcher points somewhere else; refusing to remove it."
elif [ -e "$uninstaller" ]; then
    fail "The uninstaller launcher is not a symlink; refusing to remove it."
fi

[ -r /dev/tty ] || fail "Run this command from an interactive terminal to confirm removal."
printf 'Remove Ahoy Streamer and its Python environment from:\n  %s\n' "$install_root"
printf 'This leaves Git, Python, and other OS packages installed. Continue? [y/N] '
answer=""
IFS= read -r answer </dev/tty || true
case "$answer" in
    y|Y|yes|YES|Yes) ;;
    *) printf 'Uninstall cancelled.\n'; exit 0 ;;
esac

rm -f -- "$launcher" "$uninstaller"
rm -rf -- "$install_root"
printf 'Ahoy Streamer removed.\n'
