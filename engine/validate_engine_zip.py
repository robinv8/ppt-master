#!/usr/bin/env python3
"""
PPT Master - Validate Engine Zip

Check engine pack zip filenames decode as UTF-8 and avoid mojibake.

Usage:
    python3 engine/validate_engine_zip.py <engine_zip>

Examples:
    python3 engine/validate_engine_zip.py dist-engine/ppt-master-engine-darwin-arm64.zip

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional


UTF8_FLAG = 0x800
EXPECTED_UTF8_PATH_PARTS = ('中国电信', '中国电建', '中汽研')
MOJIBAKE_MARKERS = ('Σ╕', 'σ¢', 'τö', 'σ╗', '╜')


def _has_non_ascii(value: str) -> bool:
    return any(ord(ch) > 127 for ch in value)


def validate_engine_zip(zip_path: Path) -> int:
    """Validate UTF-8 filename flags and extracted Chinese template paths."""
    if not zip_path.is_file():
        print(f'[ERROR] zip not found: {zip_path}', file=sys.stderr)
        return 1

    errors: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]

        for info in infos:
            if _has_non_ascii(info.filename) and not (info.flag_bits & UTF8_FLAG):
                errors.append(f'missing UTF-8 flag: {info.filename}')
            if any(marker in info.filename for marker in MOJIBAKE_MARKERS):
                errors.append(f'mojibake filename: {info.filename}')

        for expected in EXPECTED_UTF8_PATH_PARTS:
            if not any(expected in name for name in names):
                errors.append(f'missing expected UTF-8 path segment: {expected}')

        with tempfile.TemporaryDirectory(prefix='ppt-engine-zip-') as tmpdir:
            zf.extractall(tmpdir)
            extracted = [path.as_posix() for path in Path(tmpdir).rglob('*')]
            for expected in EXPECTED_UTF8_PATH_PARTS:
                if not any(expected in path for path in extracted):
                    errors.append(f'extract check failed for path segment: {expected}')
            for path in extracted:
                if any(marker in path for marker in MOJIBAKE_MARKERS):
                    errors.append(f'extracted mojibake path: {path}')

    if errors:
        for error in errors:
            print(f'[ERROR] {error}', file=sys.stderr)
        return 1
    print(f'[OK] UTF-8 zip filename validation passed: {zip_path}', file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Validate engine zip UTF-8 filename metadata.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('engine_zip', type=Path, help='Engine zip path')
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return validate_engine_zip(args.engine_zip)


if __name__ == '__main__':
    raise SystemExit(main())
