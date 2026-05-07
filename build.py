"""Build script — generates voice_dictate.exe in dist/."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PYTHON = sys.executable


def step(msg: str) -> None:
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def run(*cmd, **kw) -> None:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kw)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:
    step("1/2  Generating icon")
    run(PYTHON, ROOT / "scripts" / "gen_icon.py")

    step("2/2  Building exe with PyInstaller")
    run(
        PYTHON, "-m", "PyInstaller",
        "--clean", "--noconfirm",
        str(ROOT / "voice_dictate.spec"),
        cwd=ROOT,
    )

    exe = ROOT / "dist" / "voice_dictate.exe"
    if exe.exists():
        print(f"\n[OK] Build successful: {exe}")
        print(f"   Size: {exe.stat().st_size / 1_048_576:.1f} MB")
        print(f"\nTo install:\n  {exe} --install\n\nTo run without installing:\n  {exe}\n")
    else:
        print("\n[FAIL] Build failed -- exe not found")
        sys.exit(1)


if __name__ == "__main__":
    main()
