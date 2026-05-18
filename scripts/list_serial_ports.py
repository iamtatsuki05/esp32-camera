from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """List serial port candidates on macOS/Linux for ESP32 connection checks."""
    patterns = ('/dev/cu.*', '/dev/tty.*', '/dev/serial/by-id/*')
    ports = sorted({str(path) for pattern in patterns for path in Path('/').glob(pattern.removeprefix('/'))})
    if not ports:
        sys.stdout.write('No serial port candidates found.\n')
        return
    for port in ports:
        sys.stdout.write(f'{port}\n')


if __name__ == '__main__':
    main()
