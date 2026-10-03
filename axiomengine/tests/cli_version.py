#!/usr/bin/env python3
"""tests/cli_version.py — `axiomengine --version` prints the package version (#1352).

It is answered by the Node launcher before bash is looked for, so it is checked there with no bash on PATH,
and by bin/axiomengine for a checkout. With other arguments --version is still the build option, not this.

    python3 tests/cli_version.py
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = json.load(open(os.path.join(ROOT, 'package.json')))['version']

fails, checked = [], []
def check(why, cond, detail=''):
    checked.append(why)
    print(('ok   ' if cond else 'FAIL ') + why + (f'\n     {detail}' if not cond and detail else ''))
    if not cond:
        fails.append(why)


node = shutil.which('node')
with tempfile.TemporaryDirectory() as only_node:
    os.symlink(node, os.path.join(only_node, 'node'))
    r = subprocess.run([node, os.path.join(ROOT, 'bin', 'axiomengine.js'), '--version'], capture_output=True, text=True,
                       env=dict(os.environ, PATH=only_node, AXIOMENGINE_BASH=''), timeout=30)
    check('the installed command prints the package version, with no bash on PATH',
          r.returncode == 0 and r.stdout == VERSION + '\n', f'rc={r.returncode} out={r.stdout!r} err={r.stderr[-200:]!r}')

r = subprocess.run(['bash', os.path.join(ROOT, 'bin', 'axiomengine'), '--version'], capture_output=True, text=True, timeout=30)
check('bin/axiomengine prints the same version', r.returncode == 0 and r.stdout == VERSION + '\n', f'rc={r.returncode} out={r.stdout!r}')

r = subprocess.run(['bash', os.path.join(ROOT, 'bin', 'axiomengine'), '--version', 'v9'], capture_output=True, text=True, timeout=30)
check('--version with a value is not taken for the version query', r.returncode != 0 and VERSION not in r.stdout,
      f'rc={r.returncode} out={r.stdout!r}')

print()
print(f"{len(checked) - len(fails)} of {len(checked)} check(s) held" if not fails else f"{len(fails)} FAILED: " + '; '.join(fails))
sys.exit(1 if fails else 0)
