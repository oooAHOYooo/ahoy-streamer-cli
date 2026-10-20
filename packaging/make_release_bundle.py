"""Package a checked standalone executable with available dependency notices."""

import argparse
import importlib.metadata
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


DEPENDENCIES = (
    "miniaudio", "opencv-python-headless", "numpy", "cffi", "pycparser",
    "pyinstaller", "pyinstaller-hooks-contrib", "windows-curses",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    exe = args.executable
    if not exe.is_file():
        parser.error(f"executable not found: {exe}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    start = (
        "AHOY Streamer 0.1.0 standalone preview\n\n"
        "Run ahoy-streamer.exe from PowerShell on Windows, or ./ahoy-streamer "
        "from a terminal on macOS/Linux. On macOS/Linux, use chmod +x ahoy-streamer "
        "if extraction did not preserve execute permission.\n\n"
        "Run the same file with doctor to check local playback backends. Browsing "
        "needs internet access. Terminal video soundtracks use separately installed "
        "mpv on macOS/Linux; Windows terminal video is silent. This preview is "
        "unsigned and live playback has not been verified on every target.\n\n"
        "Python is bundled. Third-party license files are in licenses/. The app's "
        "source and current limitations are at "
        "https://github.com/oooAHOYooo/ahoy-streamer-cli.\n"
    )
    with ZipFile(args.output, "w", ZIP_DEFLATED) as bundle:
        bundle.write(exe, exe.name)
        bundle.writestr("START_HERE.txt", start)
        bundle.write("docs/DEPENDENCIES.md", "DEPENDENCIES.md")
        for filename in ("LICENSE", "LICENSE.txt"):
            python_license = Path(sys.base_prefix) / filename
            if python_license.is_file():
                bundle.write(python_license, f"licenses/Python/{filename}")
                break
        for name in DEPENDENCIES:
            try:
                distribution = importlib.metadata.distribution(name)
            except importlib.metadata.PackageNotFoundError:
                continue
            for file in distribution.files or ():
                filename = Path(str(file)).name.lower()
                if not filename.startswith(("license", "licence", "copying", "notice")):
                    continue
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    bundle.write(source, f"licenses/{distribution.metadata['Name']}/{file}")
    print(args.output)


if __name__ == "__main__":
    main()
