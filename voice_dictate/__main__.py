"""Entry point: python -m voice_dictate [--install | --uninstall]"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import traceback

# Log to APPDATA\VoiceDictate\app.log
_log_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "VoiceDictate")
os.makedirs(_log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(_log_dir, "app.log"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    encoding="utf-8",
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="voice-dictate",
        description="Voice dictation widget for Windows",
    )
    parser.add_argument("--install", action="store_true", help="Install to user Programs directory")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall from user Programs directory")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()

    from voice_dictate import __version__

    if args.version:
        print(f"voice-dictate {__version__}")
        return

    if args.install:
        from voice_dictate.installer import install
        install()
        return

    if args.uninstall:
        from voice_dictate.installer import uninstall
        uninstall()
        return

    # Normal GUI run
    logging.info("Starting Voice Dictate GUI")
    try:
        from voice_dictate.app import run
        sys.exit(run())
    except Exception:
        logging.exception("Fatal error in run()")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Fatal error in main()")
        raise
