#!/usr/bin/env python3
"""
PPT Master - Zip Engine Pack

Create an engine pack zip with UTF-8 filename metadata.

Usage:
    python3 engine/zip_engine_pack.py <pack_dir> <output_zip>

Examples:
    python3 engine/zip_engine_pack.py dist-engine/ppt-master-engine-darwin-arm64 dist-engine/ppt-master-engine-darwin-arm64.zip

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
import zipfile
from pathlib import Path
from typing import Optional


DOS_EPOCH = (1980, 1, 1, 0, 0, 0)
UTF8_FLAG = 0x800


def _zipinfo_for(path: Path, arcname: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(arcname, date_time=DOS_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    mode = path.lstat().st_mode
    info.external_attr = (mode & 0xFFFF) << 16
    if any(ord(ch) > 127 for ch in arcname):
        info.flag_bits |= UTF8_FLAG
    return info


def write_engine_zip(pack_dir: Path, output_zip: Path) -> int:
    """Write pack_dir into output_zip, preserving symlinks and UTF-8 names."""
    pack_dir = pack_dir.resolve()
    if not pack_dir.is_dir():
        print(f'[ERROR] pack directory not found: {pack_dir}', file=sys.stderr)
        return 1

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    output_zip.unlink(missing_ok=True)

    root_parent = pack_dir.parent
    entries = sorted(pack_dir.rglob('*'), key=lambda path: path.as_posix())
    with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path in entries:
            arcname = path.relative_to(root_parent).as_posix()
            if path.is_symlink():
                info = _zipinfo_for(path, arcname)
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                zf.writestr(info, os.readlink(path), compress_type=zipfile.ZIP_DEFLATED)
            elif path.is_file():
                info = _zipinfo_for(path, arcname)
                zf.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)

    print(f'[OK] wrote {output_zip} ({output_zip.stat().st_size} bytes)', file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Create an engine pack zip with UTF-8 filename metadata.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('pack_dir', type=Path, help='Engine pack directory')
    parser.add_argument('output_zip', type=Path, help='Output zip path')
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return write_engine_zip(args.pack_dir, args.output_zip)


if __name__ == '__main__':
    raise SystemExit(main())
