#!/usr/bin/env python3
"""
PPT Master - Build Icon Bundle

Pack the loose template icon library into templates/icons.bundle.zip.

Usage:
    python3 scripts/build_icon_bundle.py [--icons-dir templates/icons] [--output templates/icons.bundle.zip]

Examples:
    python3 scripts/build_icon_bundle.py
    python3 scripts/build_icon_bundle.py --output /tmp/icons.bundle.zip

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

DEFAULT_ICONS_DIR = Path(__file__).resolve().parent.parent / 'templates' / 'icons'
DEFAULT_OUTPUT = DEFAULT_ICONS_DIR.parent / 'icons.bundle.zip'


def build_icon_bundle(icons_dir: Path, output_path: Path) -> int:
    """Create a deterministic zip bundle from all SVG files under icons_dir."""
    if not icons_dir.is_dir():
        print(f'[ERROR] icon directory not found: {icons_dir}', file=sys.stderr)
        return 1

    svg_files = sorted(
        path for path in icons_dir.rglob('*.svg')
        if path.is_file()
    )
    if not svg_files:
        print(f'[ERROR] no SVG icons found under: {icons_dir}', file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_path,
        mode='w',
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zf:
        for path in svg_files:
            arcname = path.relative_to(icons_dir).as_posix()
            info = zipfile.ZipInfo(arcname)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.date_time = (1980, 1, 1, 0, 0, 0)
            with path.open('rb') as src:
                zf.writestr(info, src.read(), compress_type=zipfile.ZIP_DEFLATED)

    print(
        f'[OK] wrote {len(svg_files)} icons to {output_path}',
        file=sys.stderr,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Pack template icon SVGs into a deterministic bundle.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--icons-dir',
        type=Path,
        default=DEFAULT_ICONS_DIR,
        help=f'Loose icon library directory (default: {DEFAULT_ICONS_DIR})',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f'Output zip path (default: {DEFAULT_OUTPUT})',
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return build_icon_bundle(args.icons_dir, args.output)


if __name__ == '__main__':
    raise SystemExit(main())
