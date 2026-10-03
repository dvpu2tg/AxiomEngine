#!/usr/bin/env python3
"""tests/mixed_separators.py — the verb dispatcher finds its own folder when $0 mixes '/' and '\\'.

On Windows the MCP server starts the dispatcher as os.path.join(AXIOMENGINE_PLUGIN_ROOT, 'skills', 'axiomengine',
'scripts', 'axiomengine'), and bin/axiomengine exports that root from bash with forward slashes, so bash sees
C:/.../plugins/axiomengine\\skills\\axiomengine\\scripts\\axiomengine. Splitting it on '/' alone gave .../plugins, and every
MCP tool call ran a helper that is not there ("can't open file ...\\plugins\\ax_grep.py").

Off Windows a backslash is an ordinary file-name character, so the same $0 is built for real: a directory whose
plugins/axiomengine links to the plugin, and beside it a link literally named axiomengine\\skills\\axiomengine\\scripts\\axiomengine
pointing at the dispatcher. `help impact` reads the verb's script from the dispatcher's folder, so it answers only
when that folder is the scripts folder. The plain path is the control.

    python3 tests/mixed_separators.py
"""
import os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, 'plugins', 'axiomengine')
SCRIPTS = os.path.join(PLUGIN, 'skills', 'axiomengine', 'scripts')
MIXED = 'axiomengine\\skills\\axiomengine\\scripts\\axiomengine'


def main():
    fails = []
    def check(ok, why, detail=''):
        print(('ok   ' if ok else 'FAIL ') + why + ('' if ok else '\n     ' + detail.strip().replace('\n', '\n     ')))
        if not ok: fails.append(why)

    bash = os.environ.get('AXIOMENGINE_BASH') or 'bash'
    def helps(dispatcher):
        r = subprocess.run([bash, dispatcher, 'help', 'impact'], capture_output=True, text=True)
        return r.returncode == 0 and 'impact' in r.stdout and 'no such verb' not in r.stderr, r.stdout[-300:] + r.stderr[-300:]

    ok, out = helps(os.path.join(SCRIPTS, 'axiomengine'))
    check(ok, 'control: the dispatcher run by its own path finds its verbs', out)

    with tempfile.TemporaryDirectory(prefix='axiomengine-mixed-sep-') as t:
        if os.name == 'nt':
            dispatcher = PLUGIN.replace('\\', '/') + '\\' + MIXED.split('\\', 1)[1]
        else:
            os.makedirs(os.path.join(t, 'plugins'))
            os.symlink(PLUGIN, os.path.join(t, 'plugins', 'axiomengine'))
            os.symlink(os.path.join(SCRIPTS, 'axiomengine'), os.path.join(t, 'plugins', MIXED))
            dispatcher = os.path.join(t, 'plugins', MIXED)
        ok, out = helps(dispatcher)
        check(ok, 'a $0 that mixes / and \\ (how the MCP server starts it on Windows) finds the verbs', out)

    print(f"\n{'FAIL' if fails else 'ok'}: {len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
