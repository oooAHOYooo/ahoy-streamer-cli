#!/usr/bin/env bash
set -euo pipefail

repo_url="https://github.com/oooAHOYooo/ahoy-streamer-cli.git"
install_root="${XDG_DATA_HOME:-$HOME/.local/share}/ahoy-streamer-cli"
local_bin="$HOME/.local/bin"
python_bin="${PYTHON:-python3}"

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != dumb ]; then
    cyan=$'\033[36m'
    blue=$'\033[34m'
    green=$'\033[32m'
    bold=$'\033[1m'
    dim=$'\033[2m'
    reset=$'\033[0m'
else
    cyan=""
    blue=""
    green=""
    bold=""
    dim=""
    reset=""
fi

step() {
    printf '%s%s[%s/%s]%s %s\n' "$bold" "$cyan" "$1" "$2" "$reset" "$3"
}

show_banner() {
    printf '%s' "$blue"
    cat <<'ART'
          .     *            .         *
              _..._                     .
           .-'     '-.         *
          /  .     .  \
         |     ___     |              .
          \  .'   '.  /
           '-._____.-'         .
                 /|\
                / | \
          _____/_|__\________
         /       |   \       /\
        /________|____\_____/  \
            ~~~ waves ~~~
ART
    printf '%s%s         A H O Y   S T R E A M E R%s\n' "$bold" "$cyan" "$reset"
    printf '%s         a listening room for the terminal%s\n\n' "$dim" "$reset"
}

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

confirm_system_packages() {
    local manager="$1"
    shift
    local packages="$*"
    if [ "${AHOY_INSTALL_ALLOW_SYSTEM_PACKAGES:-}" = "1" ]; then
        printf 'Using AHOY_INSTALL_ALLOW_SYSTEM_PACKAGES=1 to install: %s\n' "$packages"
        return
    fi
    [ -r /dev/tty ] || fail "System packages are needed: $packages. Rerun in an interactive terminal, or set AHOY_INSTALL_ALLOW_SYSTEM_PACKAGES=1."
    printf 'This installer needs system packages: %s (%s).\n' "$packages" "$manager"
    printf 'Install them now? [Y/n] '
    local answer=""
    IFS= read -r answer </dev/tty || fail "Could not read your package-install choice."
    case "$answer" in
        n|N|no|NO|No) fail "Cancelled; no system packages were installed." ;;
    esac
}

install_linux_bootstrap() {
    local need_git="$1" need_python="$2" need_venv="$3"
    local manager="" distro_id=""
    local -a packages=()

    if command -v omarchy >/dev/null 2>&1; then
        manager="Omarchy"
        if [ "$need_git" = 1 ]; then packages+=(git); fi
        if [ "$need_python" = 1 ]; then packages+=(python); fi
        if [ "$need_venv" = 1 ] || [ "$need_python" = 1 ]; then
            packages+=(python-pip)
        fi
        confirm_system_packages "$manager" "${packages[@]}"
        omarchy pkg add "${packages[@]}"
        return
    fi

    if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        distro_id="${ID:-}"
    fi
    case "$distro_id" in
        arch|manjaro|endeavouros)
            manager="pacman"
            if [ "$need_git" = 1 ]; then packages+=(git); fi
            if [ "$need_python" = 1 ]; then packages+=(python); fi
            if [ "$need_venv" = 1 ] || [ "$need_python" = 1 ]; then
                packages+=(python-pip)
            fi
            confirm_system_packages "$manager" "${packages[@]}"
            install_with_system_privileges pacman -S --needed "${packages[@]}"
            ;;
        debian|ubuntu|linuxmint|pop)
            manager="apt"
            if [ "$need_git" = 1 ]; then packages+=(git); fi
            if [ "$need_python" = 1 ]; then packages+=(python3); fi
            if [ "$need_venv" = 1 ] || [ "$need_python" = 1 ]; then
                packages+=(python3-venv python3-pip)
            fi
            confirm_system_packages "$manager" "${packages[@]}"
            install_with_system_privileges apt-get update
            install_with_system_privileges apt-get install -y "${packages[@]}"
            ;;
        fedora|rhel|centos|rocky|almalinux)
            manager="dnf"
            if [ "$need_git" = 1 ]; then packages+=(git); fi
            if [ "$need_python" = 1 ]; then packages+=(python3); fi
            if [ "$need_venv" = 1 ] || [ "$need_python" = 1 ]; then
                packages+=(python3-pip)
            fi
            confirm_system_packages "$manager" "${packages[@]}"
            install_with_system_privileges dnf install -y "${packages[@]}"
            ;;
        opensuse*|sles)
            manager="zypper"
            if [ "$need_git" = 1 ]; then packages+=(git); fi
            if [ "$need_python" = 1 ]; then packages+=(python3); fi
            if [ "$need_venv" = 1 ] || [ "$need_python" = 1 ]; then
                packages+=(python3-pip)
            fi
            confirm_system_packages "$manager" "${packages[@]}"
            install_with_system_privileges zypper --non-interactive install "${packages[@]}"
            ;;
        *)
            fail "Missing Git or Python venv support. Install those with your Linux distribution's package manager, then rerun."
            ;;
    esac
}

probe_venv() {
    local probe_dir
    probe_dir="$(mktemp -d "${TMPDIR:-/tmp}/ahoy-streamer-preflight.XXXXXX")" || return 1
    if "$python_bin" -m venv "$probe_dir/venv" >/dev/null 2>&1 && \
       "$probe_dir/venv/bin/python" -m pip --version >/dev/null 2>&1; then
        rm -rf -- "$probe_dir"
        return 0
    fi
    rm -rf -- "$probe_dir"
    return 1
}

check_network() {
    local url="$1" label="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSIL --connect-timeout 5 --max-time 10 "$url" >/dev/null 2>&1 && return
    elif command -v wget >/dev/null 2>&1; then
        wget --spider --quiet --timeout=10 "$url" >/dev/null 2>&1 && return
    elif command -v "$python_bin" >/dev/null 2>&1; then
        "$python_bin" -c 'import sys; from urllib.request import Request, urlopen; req=Request(sys.argv[1], headers={"User-Agent":"ahoy-streamer-installer"}); response=urlopen(req, timeout=10); response.read(1); response.close()' "$url" >/dev/null 2>&1 && return
    else
        fail "Cannot check access to $label; install curl, wget, or Python and rerun."
    fi
    fail "Cannot reach $label. Check your internet connection or proxy, then rerun."
}

printf '\n'
show_banner
step 1 5 "Checking platform, Python, and install prerequisites..."
platform="$(uname -s)"
arch="$(uname -m)"
case "$platform:$arch" in
    Linux:x86_64|Linux:aarch64|Darwin:x86_64|Darwin:arm64) ;;
    *) fail "Unsupported platform: $platform $arch. See the README for supported systems." ;;
esac

script_path="${BASH_SOURCE[0]:-}"
script_dir=""
if [ -n "$script_path" ] && [ "$script_path" != "-" ] && [ -f "$script_path" ]; then
    script_dir="$(cd -- "$(dirname -- "$script_path")" && pwd)"
fi
local_install=0
if [ -n "$script_dir" ] && [ -f "$script_dir/pyproject.toml" ]; then
    local_install=1
    repo_dir="$script_dir"
else
    repo_dir="$install_root"
fi

need_git=0
if [ "$local_install" = 0 ] && ! command -v git >/dev/null 2>&1; then
    need_git=1
fi
need_python=0
need_venv=0
if ! command -v "$python_bin" >/dev/null 2>&1; then
    need_python=1
    need_venv=1
else
    "$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
        fail "Python 3.11 or newer is required; found $("$python_bin" --version 2>&1)."
    if ! probe_venv; then
        need_venv=1
    fi
fi

step 2 5 "Checking internet access..."
if [ "$local_install" = 0 ]; then
    check_network "https://github.com/oooAHOYooo/ahoy-streamer-cli" "GitHub"
fi
check_network "https://pypi.org/simple/opencv-python-headless/" "PyPI"

launcher="$local_bin/ahoy-streamer"
player="$repo_dir/.venv/bin/ahoy-streamer"
uninstaller="$local_bin/ahoy-streamer-uninstall"
check_launcher_path() {
    local path="$1" target="$2"
    if [ -e "$path" ] && [ ! -L "$path" ]; then
        fail "Refusing to overwrite an existing file: $path"
    fi
    if [ -L "$path" ] && [ "$(readlink "$path")" != "$target" ]; then
        fail "A different launcher already exists at $path."
    fi
}
check_launcher_path "$launcher" "$player"
if [ "$local_install" = 0 ]; then
    check_launcher_path "$uninstaller" "$install_root/uninstall.sh"
    if [ -e "$install_root" ] && [ ! -d "$install_root/.git" ]; then
        fail "Install directory already exists and is not an Ahoy Streamer checkout: $install_root"
    fi
    if [ -d "$install_root/.git" ]; then
        origin="$(git -C "$install_root" remote get-url origin)"
        [ "$origin" = "$repo_url" ] || fail "Existing install has an unexpected Git origin: $origin"
        branch="$(git -C "$install_root" branch --show-current)"
        [ "$branch" = main ] || fail "Existing install is on '$branch', not main."
        [ -z "$(git -C "$install_root" status --porcelain)" ] || \
            fail "Existing install has local changes; review them before rerunning the installer."
    fi
else
    [ -w "$repo_dir" ] || fail "Source checkout is not writable: $repo_dir"
fi

if [ "$need_git" = 1 ] || [ "$need_python" = 1 ] || [ "$need_venv" = 1 ]; then
    if [ "$platform" = Linux ]; then
        install_linux_bootstrap "$need_git" "$need_python" "$need_venv"
    else
        fail "Install Git and Python 3.11+ with venv/pip, then rerun. On macOS with Homebrew: brew install git python@3.13"
    fi
fi
command -v "$python_bin" >/dev/null 2>&1 || fail "Python is still unavailable; install Python 3.11+ and rerun."
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
    fail "The installed Python is older than 3.11."
probe_venv || fail "Python venv/pip setup is still unavailable. Install your distribution's Python venv package and rerun."
if [ "$local_install" = 0 ]; then
    command -v git >/dev/null 2>&1 || fail "Git is still unavailable; install Git and rerun."
fi

if [ "$local_install" = 0 ]; then
    step 3 5 "Getting the latest app source..."
    if [ -d "$install_root/.git" ]; then
        git -C "$install_root" pull --ff-only origin main
    elif [ -e "$install_root" ]; then
        fail "Install directory already exists and is not an Ahoy Streamer checkout: $install_root"
    else
        mkdir -p "$(dirname -- "$install_root")"
        git clone --depth 1 --branch main "$repo_url" "$install_root"
    fi
else
    step 3 5 "Using this source checkout..."
fi

venv_dir="$repo_dir/.venv"
step 4 5 "Installing the app and video dependencies..."
"$python_bin" -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install --disable-pip-version-check --editable "$repo_dir"

mkdir -p "$local_bin"
ln -sfn "$player" "$launcher"

if [ "$local_install" = 0 ]; then
    ln -sfn "$repo_dir/uninstall.sh" "$uninstaller"
fi

step 5 5 "Checking playback readiness..."
doctor_status=0
if doctor_json="$("$player" doctor --json 2>/dev/null)"; then
    :
else
    doctor_status=$?
fi
if [ -n "${doctor_json:-}" ]; then
    printf '%s\n' "$doctor_json" | "$venv_dir/bin/python" -c 'import json,sys; d=json.load(sys.stdin).get("data",{}); print("  Terminal video: " + ("ready" if d.get("video_backend") else "unavailable")); print("  Native audio: " + ("ready" if d.get("audio_ready") else "browser fallback")); print("  Video soundtrack (mpv): " + ("ready" if d.get("mpv_available") else "optional, not installed"))'
else
    printf '  Playback check failed (status %s); run "%s doctor" for details.\n' "$doctor_status" "$launcher"
fi

printf '\n%s%sInstallation complete.%s\nStart: %s\n' "$bold" "$green" "$reset" "$launcher"
case ":${PATH:-}:" in
    *":$local_bin:"*) printf 'Or use: ahoy-streamer\n' ;;
esac
if [ "$local_install" = 0 ]; then
    printf 'Uninstall later: %s\n' "$uninstaller"
fi
if ! command -v mpv >/dev/null 2>&1; then
    printf 'Video soundtracks need mpv; terminal video works without it.\n'
fi
