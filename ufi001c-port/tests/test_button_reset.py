"""Offline tests for the button-hold factory reset (ext4 rootfs).

The scripts are exercised with stubbed logger/reboot/sync and a fake
/etc, so no test ever touches the real system or reboots anything.
"""
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = HERE.parent
import sys
sys.path.insert(0, str(PORT))
import check_rootfs

PKG = PORT / 'overlay/package/openstick/ufi001c-button-reset/files'
HOTPLUG = PKG / 'etc/hotplug.d/button/10-ufi001c-reset'
RESET = PKG / 'usr/sbin/ufi001c-factory-reset'
SNAPSHOT = PKG / 'etc/uci-defaults/99-ufi001c-factory-snapshot'


def stub_bin(directory, out):
    """logger/reboot/sync stubs that record calls instead of acting."""
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('logger', 'reboot', 'sync'):
        script = directory / name
        script.write_text('#!/bin/sh\necho "%s $*" >> "$STUB_OUT"\n' % name)
        script.chmod(0o755)


class ButtonResetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        self.bin = self.p / 'bin'
        self.out = self.p / 'calls.log'
        stub_bin(self.bin, self.out)
        self.env = dict(os.environ, PATH=str(self.bin) + ':/usr/bin:/bin',
                        STUB_OUT=str(self.out))

    def run_script(self, script, extra_env):
        env = dict(self.env, **extra_env)
        return subprocess.run(['/bin/sh', str(script)], env=env,
                              capture_output=True, text=True, timeout=60)

    def fake_etc(self):
        etc = self.p / 'etc'
        (etc / 'config').mkdir(parents=True)
        (etc / 'config' / 'network').write_text('user network\n')
        (etc / 'config' / 'wireless').write_text(
            "config wifi-device 'radio0'\n\toption disabled '0'\n")
        (etc / 'config' / 'system').write_text('user system\n')
        (etc / 'config' / 'luci').write_text(
            "config core 'main'\n\toption mediaurlbase '/luci-static/bootstrap'\n")
        (etc / 'shadow').write_text('root:$6$us3rhash:0:0:99999:7:::\n'
                                    'daemon:*:0:0:99999:7:::\n')
        (etc / 'dropbear').mkdir()
        (etc / 'dropbear' / 'dropbear_rsa_host_key').write_text('key\n')
        (etc / 'uhttpd.crt').write_text('cert\n')
        (etc / 'crontabs').mkdir()
        (etc / 'crontabs' / 'root').write_text('cron\n')
        return etc

    def make_snapshot_files(self, files):
        import shutil
        factory = self.p / 'factory'
        shutil.rmtree(factory, ignore_errors=True)
        (factory / 'config').mkdir(parents=True)
        for name, content in files.items():
            (factory / 'config' / name).write_text(content)
        snap = self.p / 'factory-config.tar.gz'
        with tarfile.open(snap, 'w:gz') as tar:
            tar.add(factory / 'config', arcname='config')
        return snap

    def make_snapshot(self, etc):
        return self.make_snapshot_files({
            'network': 'factory network\n',
            'wireless': "config wifi-device 'radio0'\n\toption disabled '0'\n",
            'system': 'factory system\n',
            'luci': "config core 'main'\n\toption mediaurlbase '/luci-static/bootstrap'\n",
        })

    def test_reset_restores_factory_config_and_clears_password(self):
        etc = self.fake_etc()
        snap = self.make_snapshot(etc)
        result = self.run_script(RESET, {'UFI001C_ETC': str(etc),
                                  'UFI001C_SNAP': str(snap)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((etc / 'config' / 'network').read_text(), 'factory network\n')
        self.assertIn("wifi-device", (etc / 'config' / 'wireless').read_text())
        self.assertEqual((etc / 'config' / 'system').read_text(), 'factory system\n')
        self.assertIn('mediaurlbase', (etc / 'config' / 'luci').read_text())
        shadow = (etc / 'shadow').read_text()
        self.assertTrue(shadow.startswith('root::'), shadow)
        self.assertIn('daemon:*:', shadow)
        self.assertFalse((etc / 'dropbear').exists())
        self.assertFalse((etc / 'uhttpd.crt').exists())
        self.assertFalse((etc / 'crontabs').exists())
        self.assertIn('reboot', self.out.read_text())
        self.assertFalse(list(etc.glob('.ufi001c-reset-tmp-*')))

    def test_reset_refuses_incomplete_snapshot_and_keeps_config(self):
        etc = self.fake_etc()
        snap = self.make_snapshot_files({
            'network': 'factory network\n',
            'system': 'factory system\n',
            'luci': "config core 'main'\n\toption mediaurlbase '/luci-static/bootstrap'\n",
        })
        result = self.run_script(RESET, {'UFI001C_ETC': str(etc),
                                  'UFI001C_SNAP': str(snap)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((etc / 'config' / 'network').read_text(), 'user network\n')
        self.assertIn("wifi-device", (etc / 'config' / 'wireless').read_text())
        self.assertIn('mediaurlbase', (etc / 'config' / 'luci').read_text())
        self.assertTrue((etc / 'dropbear').exists())
        self.assertNotIn('reboot', self.out.read_text())
        self.assertFalse(list(etc.glob('.ufi001c-reset-tmp-*')))

    def test_reset_refuses_snapshot_without_mediaurlbase(self):
        etc = self.fake_etc()
        snap = self.make_snapshot_files({
            'network': 'factory network\n',
            'wireless': "config wifi-device 'radio0'\n",
            'system': 'factory system\n',
            'luci': "config core 'main'\n\toption lang 'ru'\n",
        })
        result = self.run_script(RESET, {'UFI001C_ETC': str(etc),
                                  'UFI001C_SNAP': str(snap)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((etc / 'config' / 'network').read_text(), 'user network\n')
        self.assertIn('mediaurlbase', (etc / 'config' / 'luci').read_text())
        self.assertNotIn('reboot', self.out.read_text())

    def test_reset_refuses_without_snapshot_and_changes_nothing(self):
        etc = self.fake_etc()
        result = self.run_script(RESET, {'UFI001C_ETC': str(etc),
                                  'UFI001C_SNAP': str(self.p / 'nope.tar.gz')})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((etc / 'config' / 'network').read_text(), 'user network\n')
        self.assertTrue((etc / 'dropbear').exists())
        self.assertNotIn('reboot', self.out.read_text())

    def test_reset_refuses_corrupt_snapshot_and_changes_nothing(self):
        etc = self.fake_etc()
        snap = self.p / 'bad.tar.gz'
        snap.write_bytes(b'not a gzip tarball')
        result = self.run_script(RESET, {'UFI001C_ETC': str(etc),
                                  'UFI001C_SNAP': str(snap)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((etc / 'config' / 'network').read_text(), 'user network\n')
        self.assertNotIn('reboot', self.out.read_text())

    def test_hotplug_fires_only_on_long_hold_release(self):
        stub = self.p / 'reset-stub'
        stub.write_text('#!/bin/sh\necho reset-called >> "$STUB_OUT"\n')
        stub.chmod(0o755)
        cases = [
            ({'ACTION': 'released', 'SEEN': '10'}, True),
            ({'ACTION': 'released', 'SEEN': '120'}, True),
            ({'ACTION': 'released', 'SEEN': '9'}, False),
            ({'ACTION': 'pressed', 'SEEN': '30'}, False),
            ({'ACTION': 'released', 'SEEN': '9999'}, False),
            ({'ACTION': 'released'}, False),
        ]
        for extra, expected in cases:
            self.out.unlink(missing_ok=True)
            self.run_script(HOTPLUG, dict(extra, UFI001C_RESET=str(stub)))
            called = self.out.exists() and 'reset-called' in self.out.read_text()
            self.assertEqual(called, expected, extra)

    def test_snapshot_captures_factory_config(self):
        etc = self.fake_etc()
        board = self.p / 'board_name'
        board.write_text('thwc,ufi001c')
        snap_dir = self.p / 'snap'
        result = self.run_script(SNAPSHOT, {'UFI001C_ETC': str(etc),
                                     'UFI001C_SNAP_DIR': str(snap_dir),
                                     'UFI001C_BOARD_FILE': str(board)})
        self.assertEqual(result.returncode, 0, result.stderr)
        snap = snap_dir / 'factory-config.tar.gz'
        self.assertTrue(snap.is_file())
        with tarfile.open(snap) as tar:
            names = tar.getnames()
        self.assertIn('config/network', names)
        self.assertIn('config/wireless', names)
        self.assertIn('config/system', names)
        self.assertIn('config/luci', names)

    def test_snapshot_discards_incomplete_config(self):
        etc = self.fake_etc()
        (etc / 'config' / 'wireless').unlink()
        board = self.p / 'board_name'
        board.write_text('thwc,ufi001c')
        snap_dir = self.p / 'snap'
        result = self.run_script(SNAPSHOT, {'UFI001C_ETC': str(etc),
                                     'UFI001C_SNAP_DIR': str(snap_dir),
                                     'UFI001C_BOARD_FILE': str(board)})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((snap_dir / 'factory-config.tar.gz').exists())

    def test_package_wiring(self):
        fragment = (PORT / 'clean/ufi001c.config').read_text()
        self.assertIn('CONFIG_PACKAGE_ufi001c-button-reset=y', fragment)
        self.assertIn('CONFIG_PACKAGE_kmod-button-hotplug=y', fragment)
        makefile = (PKG.parent / 'Makefile').read_text()
        self.assertIn('DEPENDS:=+kmod-button-hotplug', makefile)
        self.assertIn('hotplug.d/button', makefile)
        self.assertIn('ufi001c-factory-reset', makefile)
        self.assertIn('99-ufi001c-factory-snapshot', makefile)
        for installed in ('etc/hotplug.d/button/10-ufi001c-reset',
                          'usr/sbin/ufi001c-factory-reset',
                          'etc/uci-defaults/99-ufi001c-factory-snapshot'):
            self.assertIn(installed, check_rootfs.FILES)


if __name__ == '__main__':
    unittest.main()
