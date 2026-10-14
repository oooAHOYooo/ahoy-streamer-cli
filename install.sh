#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_dir="$repo_dir/.venv"
python_bin="${PYTHON:-python3}"

fail() {
    printf 'ahoy-streamer installer: %s\n' "$*" >&2
    exit 1
}

command -v "$python_bin" >/dev/null 2>&1 || fail "Python 3.11 or newer is required (could not find $python_bin)."
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
    fail "Python 3.11 or newer is required."

arch="$(uname -m)"
case "$arch" in
    x86_64|aarch64) ;;
    *) fail "Linux video wheels are supported on x86_64 and aarch64, not $arch." ;;
esac

install_python_bootstrap() {
    if command -v omarchy >/dev/null 2>&1; then
        omarchy pkg add python-pip
        return
    fi

    if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
    else
        ID=""
    fi

    case "${ID:-}" in
        arch|manjaro|endeavouros)
            install_with_system_privileges pacman -S --needed python-pip
            ;;
        debian|ubuntu|linuxmint|pop)
            install_with_system_privileges apt-get update
            install_with_system_privileges apt-get install -y python3-venv python3-pip
            ;;
        fedora|rhel|centos|rocky|almalinux)
            install_with_system_privileges dnf install -y python3-pip
            ;;
        opensuse*|sles)
            install_with_system_privileges zypper --non-interactive install python3-pip
            ;;
        *)
            fail "Python's venv/pip bootstrap is missing. Install your Linux distribution's Python venv and pip packages, then rerun this installer."
            ;;
    esac
}

install_with_system_privileges() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        fail "Installing Python setup packages requires root or sudo: $*"
    fi
}

if ! "$python_bin" -m venv "$venv_dir"; then
    printf 'Python venv/pip support is missing; installing the distro bootstrap package.\n'
    install_python_bootstrap
    if [ -x "$venv_dir/bin/python" ]; then
        "$python_bin" -m venv --upgrade "$venv_dir"
    else
        "$python_bin" -m venv "$venv_dir"
    fi
fi
"$venv_dir/bin/python" -m pip install --editable "$repo_dir"

printf '\nInstalled ahoy-streamer with the Linux video decoder in:\n  %s\n' "$venv_dir"
printf 'Run it with:\n  %s/bin/ahoy-streamer\n' "$venv_dir"
if ! command -v mpv >/dev/null 2>&1; then
    printf 'mpv is not installed; terminal video will be silent. Install mpv with your Linux package manager for video soundtracks.\n'
fi
