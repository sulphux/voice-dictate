"""Entry point: python -m voice_dictate [--install | --uninstall]"""
from __future__ import annotations

import argparse
import sys


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
    from voice_dictate.app import run
    sys.exit(run())


if __name__ == "__main__":
    main()
