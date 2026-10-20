"""Fault injection for the ModemManager wedge recovery watchdog.

Scenario from the 19.10.2026 boot log: the modem subsystem resets during the
first enable, ModemManager ends with the modem in "failed" state (sim-missing)
and netifd gives up. Only a fresh ModemManager enumeration recovers it. All
system-affecting commands are stateful fakes; the production shell logic runs
unchanged apart from relocated data paths.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PORT = Path(__file__).resolve().parents[1]
PKG = PORT / 'overlay/package/openstick/ufi-modem-watchdog/files'

STATE = {
    'cfg': {'network.modem.proto': 'modemmanager', 'network.modem.device': 'qcom-soc',
            'ufi-modem-watchdog.main.enabled': '1',
            'ufi-modem-watchdog.main.allow_reboot': '1'},
    'modem': {'modem': {'generic': {'state': 'failed',
                                     'state-failed-reason': 'sim-missing'}}},
    'calls': [],
}

FAKE = r'''import json, os, pathlib, sys
p = pathlib.Path(os.environ['TEST_STATE']); s = json.loads(p.read_text())
cmd = pathlib.Path(sys.argv[0]).name; a = sys.argv[1:]; rc = 0
s['calls'].append([cmd] + a)
if cmd == 'uci':
    key = a[-1]
    if key in s['cfg']: print(s['cfg'][key])
    else: rc = 1
elif cmd == 'mmcli':
    if '--output-json' in a: print(json.dumps(s['modem']))
    else: raise AssertionError(a)
elif cmd in ('logger', 'reboot', 'sync'):
    pass
else: raise AssertionError((cmd, a))
p.write_text(json.dumps(s)); sys.exit(rc)
'''


class ModemWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.tmp = Path(self.tmpdir.name)
        self.path = self.tmp / 'state.json'
        self.state = copy.deepcopy(STATE)
        self.save()
        self.env = dict(os.environ, TEST_STATE=str(self.path),
                        PATH=str(self.tmp) + os.pathsep + os.environ['PATH'])
        for name in ('uci', 'mmcli', 'logger', 'reboot', 'sync'):
            p = self.tmp / name
            p.write_text('#!' + sys.executable + '\n' + FAKE)
            p.chmod(0o755)
        (self.tmp / 'board').write_text('thwc,ufi001c\n')
        (self.tmp / 'uptime').write_text('1000.00 500.00\n')
        self.mm_init = self.tmp / 'modemmanager-init'
        self.mm_init.write_text('#!/bin/sh\necho "$@" >> "' + str(self.tmp / 'mm-calls') + '"\n')
        self.mm_init.chmod(0o755)
        text = (PKG / 'ufi-modem-watchdog').read_text()
        for old, new in {
            '/tmp/sysinfo/board_name': self.tmp / 'board',
            '/proc/uptime': self.tmp / 'uptime',
            '/var/run/ufi-modem-watchdog': self.tmp / 'run',
            '/etc/ufi-modem-watchdog': self.tmp / 'flag',
            '/etc/init.d/modemmanager': self.mm_init,
        }.items():
            text = text.replace(old, str(new))
        self.script = self.tmp / 'watchdog.sh'
        self.script.write_text(text)

    def save(self):
        self.path.write_text(json.dumps(self.state))

    def calls(self):
        return json.loads(self.path.read_text())['calls']

    def mm_calls(self):
        f = self.tmp / 'mm-calls'
        return f.read_text() if f.exists() else ''

    def seed_run_state(self, text):
        (self.tmp / 'run.state').write_text(text)

    def run_check(self):
        return subprocess.run(['sh', str(self.script), 'check'], env=self.env,
                              capture_output=True, text=True, timeout=15)

    def test_connected_modem_is_left_alone(self):
        self.state['modem']['modem']['generic'] = {'state': 'connected'}
        self.save()
        p = self.run_check()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.mm_calls(), '')
        self.assertNotIn(['reboot'], self.calls())

    def test_failed_modem_first_sight_only_starts_timer(self):
        p = self.run_check()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.mm_calls(), '')
        self.assertEqual((self.tmp / 'run.state').read_text().split()[0], '1000')

    def test_stuck_failed_modem_restarts_modemmanager(self):
        self.seed_run_state('700 0 0 0\n')
        p = self.run_check()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.mm_calls().strip(), 'restart')
        self.assertNotIn(['reboot'], self.calls())
        fields = (self.tmp / 'run.state').read_text().split()
        self.assertEqual(fields[1], '1')

    def test_exhausted_modemmanager_budget_reboots_once(self):
        self.seed_run_state('700 3 900 700\n')
        p = self.run_check()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.mm_calls(), '')
        self.assertIn(['reboot'], self.calls())
        self.assertTrue((self.tmp / 'flag/reboot-used').exists())

    def test_reboot_flag_blocks_second_reboot(self):
        self.seed_run_state('700 3 900 700\n')
        (self.tmp / 'flag').mkdir()
        (self.tmp / 'flag/reboot-used').write_text('')
        p = self.run_check()
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertNotIn(['reboot'], self.calls())

    def test_connected_modem_clears_reboot_flag(self):
        self.state['modem']['modem']['generic'] = {'state': 'connected'}
        self.save()
        self.seed_run_state('700 3 900 700\n')
        (self.tmp / 'flag').mkdir()
        (self.tmp / 'flag/reboot-used').write_text('')
        p = self.run_check()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertFalse((self.tmp / 'flag/reboot-used').exists())

    def test_disabled_watchdog_does_nothing(self):
        self.state['cfg']['ufi-modem-watchdog.main.enabled'] = '0'
        self.save()
        self.seed_run_state('700 0 0 0\n')
        p = self.run_check()
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertEqual(self.mm_calls(), '')


if __name__ == '__main__':
    unittest.main()
