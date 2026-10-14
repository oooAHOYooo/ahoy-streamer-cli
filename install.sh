#!/usr/bin/env bash
set -euo pipefail

python_bin="${PYTHON:-python3}"
install_root="${AHOY_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/ahoy-streamer-cli}"
local_bin="$HOME/.local/bin"

fail() {
    printf 'ahoy-streamer installer: %s\n' "$*" >&2
    exit 1
}

install_with_system_privileges() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        fail "Installing Linux prerequisites requires root or sudo: $*"
    fi
}

install_linux_bootstrap() {
    if command -v omarchy >/dev/null 2>&1; then
        omarchy pkg add git python python-pip
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
            install_with_system_privileges pacman -S --needed git python python-pip
            ;;
        debian|ubuntu|linuxmint|pop)
            install_with_system_privileges apt-get update
            install_with_system_privileges apt-get install -y git python3 python3-venv python3-pip
            ;;
        fedora|rhel|centos|rocky|almalinux)
            install_with_system_privileges dnf install -y git python3 python3-pip
            ;;
        opensuse*|sles)
            install_with_system_privileges zypper --non-interactive install git python3 python3-pip
            ;;
        *)
            fail "Git or Python's venv/pip support is missing. Install git and your Linux distribution's Python venv/pip packages, then rerun this installer."
            ;;
    esac
}

if ! command -v "$python_bin" >/dev/null 2>&1; then
    printf 'Python is missing; installing Linux prerequisites.\n'
    install_linux_bootstrap
fi
command -v "$python_bin" >/dev/null 2>&1 || fail "Python 3.11 or newer is required (could not find $python_bin)."
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
    fail "Python 3.11 or newer is required."

arch="$(uname -m)"
case "$arch" in
    x86_64|aarch64) ;;
    *) fail "Linux video wheels are supported on x86_64 and aarch64, not $arch." ;;
esac

# Running ./install.sh from a checkout installs that checkout. Piping this script
# into bash instead installs the public main branch under the user's data directory.
script_path="${BASH_SOURCE[0]:-}"
script_dir=""
if [ -n "$script_path" ] && [ "$script_path" != "-" ] && [ -f "$script_path" ]; then
    script_dir="$(cd -- "$(dirname -- "$script_path")" && pwd)"
fi

if [ -n "$script_dir" ] && [ -f "$script_dir/pyproject.toml" ]; then
    repo_dir="$script_dir"
else
    if ! command -v git >/dev/null 2>&1; then
        printf 'Git is missing; installing Linux prerequisites.\n'
        install_linux_bootstrap
    fi
    if [ -d "$install_root/.git" ]; then
        origin="$(git -C "$install_root" remote get-url origin)"
        [ "$origin" = "https://github.com/oooAHOYooo/ahoy-streamer-cli.git" ] || \
            fail "Existing install has an unexpected Git origin: $origin"
        branch="$(git -C "$install_root" branch --show-current)"
        [ "$branch" = "main" ] || fail "Existing install is on '$branch', not main."
        [ -z "$(git -C "$install_root" status --porcelain)" ] || \
            fail "Existing install has local changes; review them before rerunning the installer."
        git -C "$install_root" pull --ff-only origin main
    elif [ -e "$install_root" ]; then
        fail "Install directory already exists and is not an Ahoy Streamer checkout: $install_root"
    else
        mkdir -p "$(dirname -- "$install_root")"
        git clone --depth 1 --branch main \
            https://github.com/oooAHOYooo/ahoy-streamer-cli.git "$install_root"
    fi
    repo_dir="$install_root"
fi

venv_dir="$repo_dir/.venv"
if ! "$python_bin" -m venv "$venv_dir"; then
    printf 'Python venv/pip support is missing; installing the Linux bootstrap package.\n'
    install_linux_bootstrap
    if [ -x "$venv_dir/bin/python" ]; then
        "$python_bin" -m venv --upgrade "$venv_dir"
    else
        "$python_bin" -m venv "$venv_dir"
    fi
fi

"$venv_dir/bin/python" -m pip install --editable "$repo_dir"

mkdir -p "$local_bin"
launcher="$local_bin/ahoy-streamer"
player="$venv_dir/bin/ahoy-streamer"
if [ -e "$launcher" ] && [ ! -L "$launcher" ]; then
    fail "Refusing to overwrite an existing file: $launcher"
fi
if [ -L "$launcher" ] && [ "$(readlink -f -- "$launcher")" != "$(readlink -f -- "$player")" ]; then
    fail "A different ahoy-streamer launcher already exists at $launcher; move it aside and rerun."
fi
ln -sfn "$player" "$launcher"

printf '\nInstalled ahoy-streamer with Linux video support.\n'
case ":${PATH:-}:" in
    *":$local_bin:"*) printf 'Run it with: ahoy-streamer\n' ;;
    *) printf 'Run it with: %s\nAdd %s to PATH to use the short command.\n' "$launcher" "$local_bin" ;;
esac
if ! command -v mpv >/dev/null 2>&1; then
    printf 'mpv is not installed; terminal video will be silent. Install mpv with your Linux package manager for video soundtracks.\n'
fi
