#!/usr/bin/env python3
"""
PPT Master - Icon Resource Helpers

Resolve icon SVGs from project files, loose template files, or a bundled zip.

Usage:
    Imported by scripts; not intended as a standalone CLI.

Examples:
    from icon_resources import resolve_icon_resource_path, read_icon_svg

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import hashlib
import tempfile
import zipfile
from pathlib import Path


LIB_ALIASES = {'chunk': 'chunk-filled'}
ICON_BASE_SIZES = {
    'chunk-filled': 16,
    'chunk': 16,
    'tabler-filled': 24,
    'tabler-outline': 24,
    'phosphor-duotone': 256,
    'simple-icons': 24,
}
DEFAULT_ICON_BASE_SIZE = 24


def icon_bundle_for_dir(icons_dir: Path) -> Path:
    """Return the zip bundle path paired with an icons directory."""
    icons_dir = Path(icons_dir)
    return icons_dir.parent / f'{icons_dir.name}.bundle.zip'


def icon_store_available(icons_dir: Path) -> bool:
    """Return true when loose icons or the paired zip bundle is available."""
    icons_dir = Path(icons_dir)
    return icons_dir.exists() or icon_bundle_for_dir(icons_dir).is_file()


def split_icon_name(icon_name: str) -> tuple[str, str]:
    """Return normalized (library, name) for an icon identifier."""
    if '/' not in icon_name:
        return 'chunk-filled', icon_name
    lib, name = icon_name.split('/', 1)
    return LIB_ALIASES.get(lib, lib), name


def icon_base_size(icon_name: str) -> float:
    """Return the expected square base size for an icon identifier."""
    lib, _name = split_icon_name(icon_name)
    return ICON_BASE_SIZES.get(lib, DEFAULT_ICON_BASE_SIZE)


def _candidate_members(icon_name: str) -> list[str]:
    lib, name = split_icon_name(icon_name)
    members = [f'{lib}/{name}.svg']
    if '/' not in icon_name:
        members.append(f'{name}.svg')
    return members


def _resolve_loose_path(icon_name: str, icons_dir: Path) -> Path:
    lib, name = split_icon_name(icon_name)
    path = Path(icons_dir) / lib / f'{name}.svg'
    if '/' not in icon_name and not path.exists():
        path = Path(icons_dir) / f'{name}.svg'
    return path


def _bundle_members(bundle_path: Path) -> set[str]:
    if not bundle_path.is_file():
        return set()
    try:
        with zipfile.ZipFile(bundle_path) as zf:
            return set(zf.namelist())
    except zipfile.BadZipFile:
        return set()


def _find_bundle_member(icon_name: str, bundle_path: Path) -> str | None:
    members = _bundle_members(bundle_path)
    for member in _candidate_members(icon_name):
        if member in members:
            return member
    return None


def _cache_root_for_bundle(bundle_path: Path) -> Path:
    stat = bundle_path.stat()
    key_src = f'{bundle_path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}'
    key = hashlib.sha256(key_src.encode('utf-8')).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / 'ppt-master-icon-cache' / key


def _materialize_bundle_member(bundle_path: Path, member: str) -> Path:
    target = _cache_root_for_bundle(bundle_path) / member
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path) as zf:
        target.write_bytes(zf.read(member))
    return target


def read_icon_svg(icon_name: str, icons_dir: Path) -> str:
    """Read an icon SVG from loose files or the paired bundle."""
    loose_path = _resolve_loose_path(icon_name, icons_dir)
    if loose_path.is_file():
        return loose_path.read_text(encoding='utf-8')

    bundle_path = icon_bundle_for_dir(icons_dir)
    member = _find_bundle_member(icon_name, bundle_path)
    if member is None:
        raise FileNotFoundError(f'icon not found: {icon_name}')
    with zipfile.ZipFile(bundle_path) as zf:
        return zf.read(member).decode('utf-8')


def resolve_icon_resource_path(icon_name: str, icons_dir: Path) -> Path:
    """Return a real file path for an icon, materializing zip entries on demand."""
    loose_path = _resolve_loose_path(icon_name, icons_dir)
    if loose_path.is_file():
        return loose_path

    bundle_path = icon_bundle_for_dir(icons_dir)
    member = _find_bundle_member(icon_name, bundle_path)
    if member is not None:
        return _materialize_bundle_member(bundle_path, member)
    return loose_path


def suggest_icon_name_in_store(icon_name: str, icons_dir: Path) -> str | None:
    """Return the exact identifier when only casing differs."""
    expected_library, expected_name = split_icon_name(icon_name)
    expected_filename = f'{expected_name}.svg'.casefold()

    icons_dir = Path(icons_dir)
    search_dirs: list[Path] = []
    if '/' in icon_name:
        library_dir = icons_dir / expected_library
        if not library_dir.is_dir() and icons_dir.is_dir():
            library_dir = next(
                (
                    path for path in icons_dir.iterdir()
                    if path.is_dir()
                    and path.name.casefold() == expected_library.casefold()
                ),
                library_dir,
            )
        search_dirs.append(library_dir)
    else:
        search_dirs.extend((icons_dir / 'chunk-filled', icons_dir))

    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        matches = sorted(
            path for path in search_dir.iterdir()
            if path.is_file()
            and path.suffix.casefold() == '.svg'
            and path.name.casefold() == expected_filename
        )
        if len(matches) != 1:
            continue
        relative = matches[0].relative_to(icons_dir).with_suffix('')
        return relative.as_posix()

    members = _bundle_members(icon_bundle_for_dir(icons_dir))
    candidates = [
        member for member in members
        if member.casefold() == f'{expected_library}/{expected_name}.svg'.casefold()
    ]
    if '/' not in icon_name:
        candidates.extend(
            member for member in members
            if member.casefold() == f'{expected_name}.svg'.casefold()
        )
    if len(candidates) != 1:
        return None
    return str(Path(candidates[0]).with_suffix('')).replace('\\', '/')
