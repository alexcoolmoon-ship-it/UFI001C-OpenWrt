"""Bind the portable Windows tools to the source being released."""
import hashlib
import json
from pathlib import Path, PurePosixPath


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def source_hashes(source):
    from stock_install import PACKAGE_FILES
    return {name: digest(Path(source) / name) for name in PACKAGE_FILES}


def inventory(root):
    root = Path(root)
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink in portable runtime')
        if not path.is_file() or path == root / 'runtime-manifest.json':
            continue
        files[path.relative_to(root).as_posix()] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
    return files


def verify_portable_runtime(root):
    """Verify a portable runtime at install time, without source files.

    verify_runtime() above needs the migration source tree (INSTALL.cmd,
    *.py) to compare source hashes, but a frozen installer only has the
    tools/ folder of the ZIP, not the migration tree. This check therefore
    covers what actually decides whether the EDL next to the installer
    belongs to this kit: the manifest version, the smoke-test result and
    the full file inventory (every runtime file, including edl/UFI-EDL.exe
    and its _internal/ tree, hashed). A runtime from another version, or
    one partially overwritten by extracting a new ZIP over an old folder,
    fails here instead of silently running a stale EDL.
    """
    from stock_install import VERSION
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Missing portable Windows runtime')
    try:
        manifest = json.loads((root / 'runtime-manifest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('Portable runtime из другого комплекта или повреждён: '
                         'нет runtime-manifest.json. Распакуйте USB-ZIP заново в пустую папку.')
    if (manifest.get('format') != 1 or manifest.get('version') != VERSION or
            manifest.get('platform') != 'windows-x86_64' or
            manifest.get('smoke_tests') != {'installer': 'passed', 'edl': 'passed', 'edl_help': 'passed'}):
        raise ValueError(
            f"Portable runtime из другого комплекта: runtime версии {manifest.get('version')}, "
            f"а установщик версии {VERSION}. Распакуйте USB-ZIP заново в пустую папку, "
            'не поверх старого комплекта.')
    files = manifest.get('files')
    if not isinstance(files, dict) or not 4 <= len(files) <= 5000:
        raise ValueError('Invalid portable runtime inventory')
    for name in files:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('Invalid runtime path')
    if files != inventory(root):
        raise ValueError(
            'Portable runtime не совпадает со своим манифестом (файлы изменены или '
            'комплект распакован поверх старого). Распакуйте USB-ZIP заново в пустую папку.')
    for name in ['UFI001C-Installer.exe', 'edl/UFI-EDL.exe', 'Drivers/zadig-2.8.exe']:
        path = root / name
        if name not in files or path.stat().st_size < 512:
            raise ValueError('Missing Windows executable: ' + name)
        with path.open('rb') as f:
            if f.read(2) != b'MZ':
                raise ValueError('Not a Windows executable: ' + name)
    if 'EDL-SOURCE.zip' not in files:
        raise ValueError('Missing corresponding EDL source archive')
    return manifest


def verify_runtime(root, source, commit=None):
    from stock_install import VERSION
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Missing portable Windows runtime')
    manifest = json.loads((root / 'runtime-manifest.json').read_text(encoding='utf-8'))
    if (manifest.get('format') != 1 or manifest.get('version') != VERSION or
            manifest.get('platform') != 'windows-x86_64' or
            manifest.get('smoke_tests') != {'installer': 'passed', 'edl': 'passed', 'edl_help': 'passed'}):
        raise ValueError('Portable runtime Windows smoke tests/version did not pass')
    if commit is not None and manifest.get('source_commit') != commit:
        raise ValueError('Portable runtime is from another source commit')
    if manifest.get('source_sha256') != source_hashes(source):
        raise ValueError('Portable runtime is from different installer source')
    files = manifest.get('files')
    if not isinstance(files, dict) or not 4 <= len(files) <= 5000:
        raise ValueError('Invalid portable runtime inventory')
    for name in files:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('Invalid runtime path')
    if files != inventory(root):
        raise ValueError('Portable runtime checksum/file-list mismatch')
    for name in ['UFI001C-Installer.exe', 'edl/UFI-EDL.exe', 'Drivers/zadig-2.8.exe']:
        path = root / name
        if name not in files or path.stat().st_size < 512:
            raise ValueError('Missing Windows executable: ' + name)
        with path.open('rb') as f:
            if f.read(2) != b'MZ':
                raise ValueError('Not a Windows executable: ' + name)
    if 'EDL-SOURCE.zip' not in files:
        raise ValueError('Missing corresponding EDL source archive')
    return manifest
