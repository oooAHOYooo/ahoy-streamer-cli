"""Stable script entry for standalone executable builds."""

import os

from ahoy_streamer_cli.cli import main


if __name__ == "__main__":
    if os.environ.get("AHOY_STANDALONE_IMPORT_DIAGNOSTICS") == "1":
        import miniaudio
        import cv2
        print(miniaudio.__version__, cv2.__version__)
        raise SystemExit(0)
    raise SystemExit(main())
