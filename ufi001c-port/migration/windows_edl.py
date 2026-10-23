#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Adapter for B. Kerler's unmodified, pinned GPLv3 EDL client.
from pathlib import Path
import os
import runpy
import sys


def _ensure_usb_backend(windows):
    """Warn with an actionable message instead of a cryptic traceback.

    The frozen exe ships libusb-1.0.dll next to it and patches
    ctypes.util.find_library (see main()). If the DLL is missing on the
    user's PC (antivirus quarantine, partial archive extraction) or cannot
    be loaded, pyusb reports "NoBackendError: No backend available" deep
    inside the upstream client. Print what to check here.

    Never aborts: on locked-down machines (e.g. CI runners) the DLL may
    exist but refuse to load, while --self-test/--help still work fine.
    """
    dll = windows / 'libusb-1.0.dll'
    if not dll.is_file():
        sys.stderr.write(
            'ПРЕДУПРЕЖДЕНИЕ: не найден libusb-1.0.dll в каталоге программы.\n'
            'Проверьте, что ZIP-архив распакован ПОЛНОСТЬЮ (включая подкаталог\n'
            "'_internal'), и что антивирус не отправил DLL в карантин.\n"
            f'Ожидаемый путь: {dll}\n'
        )
        return 0
    import usb.backend.libusb1
    try:
        backend_ok = usb.backend.libusb1.get_backend() is not None
    except Exception:
        backend_ok = False
    if not backend_ok:
        sys.stderr.write(
            'ПРЕДУПРЕЖДЕНИЕ: libusb-1.0.dll найден, но pyusb не смог его загрузить\n'
            '(обычно блокирует антивирус или SmartScreen).\n'
            f'Путь: {dll}\n'
            'Добавьте каталог программы в исключения антивируса и\n'
            'разблокируйте DLL в свойствах файла при необходимости.\n'
        )
    return 0


def main():
    sys.dont_write_bytecode = True
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace', line_buffering=True, write_through=True)
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    # PyInstaller >= 6 extracts to _MEIPASS with bundled data files under
    # _internal/. The DLL was silently not found when only the old layout
    # was checked, causing "NoBackendError: No backend available" even
    # though libusb-1.0.dll ships with the kit.
    _candidates = [root / 'edlclient/Windows', root / '_internal/edlclient/Windows']
    windows = next((c for c in _candidates if (c / 'libusb-1.0.dll').is_file()),
                   _candidates[0])
    handle = os.add_dll_directory(str(windows)) if os.name == 'nt' else None
    os.environ['PATH'] = str(windows) + os.pathsep + os.environ.get('PATH', '')
    # pyusb discovers libusb via ctypes.util.find_library, which does NOT see
    # directories added with os.add_dll_directory. Without this patch the frozen
    # client fails with "usb.core.NoBackendError: No backend available" even
    # though libusb-1.0.dll is bundled next to it. Point the lookup at the
    # bundled DLL explicitly before the unmodified upstream edl.py runs.
    if os.name == 'nt':
        dll = windows / 'libusb-1.0.dll'
        if dll.is_file():
            import ctypes.util
            _orig_find_library = ctypes.util.find_library

            def _find_library(name, _orig=_orig_find_library, _dll=str(dll)):
                if name in ('usb-1.0', 'libusb-1.0', 'libusb'):
                    return _dll
                return _orig(name)

            ctypes.util.find_library = _find_library
    if sys.argv[1:] == ['--self-test']:
        import usb.backend.libusb1
        import usb.core
        import serial
        import docopt
        import Crypto.Cipher.AES
        import Cryptodome.Cipher.AES
        import lxml.etree
        import edlclient.Library.sahara
        import edlclient.Library.firehose_client
        backend = usb.backend.libusb1.get_backend(find_library=lambda name: str(windows / 'libusb-1.0.dll'))
        if backend is None or not list((root / 'Loaders').rglob('007050e1*.bin')):
            raise ValueError('EDL USB backend/loader database missing')
        # Also verify the default discovery path used by the unmodified upstream
        # edl.py (no explicit find_library): it must find the bundled DLL via
        # the ctypes.util.find_library patch above, otherwise the real client
        # fails with "NoBackendError: No backend available".
        default_backend = usb.backend.libusb1.get_backend()
        if default_backend is None:
            raise ValueError('EDL USB backend not discoverable via default find_library patch')
        print('PORTABLE_EDL_SELF_TEST_OK (no USB commands performed)')
        return 0
    if os.name == 'nt':
        rc = _ensure_usb_backend(windows)
        if rc:
            return rc
    sys.argv[0] = str(root / 'edl.py')
    # The upstream code and Firehose command implementation are not patched.
    runpy.run_path(sys.argv[0], run_name='__main__')
    return 0


if __name__ == '__main__':
    sys.exit(main())
