#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// The installed `axiomengine` command. It only finds a bash and hands everything to
// bin/axiomengine, which is the CLI.
//
// WHY A NODE LAUNCHER (#1229). npm writes the command's wrappers itself from the `bin` entry: a
// symlink on POSIX, and on Windows an axiomengine.cmd and an axiomengine.ps1 that run whatever the
// script's shebang names. For bin/axiomengine that is `bash`, so both wrappers ran a bare `bash.exe`
// from PATH, which on Windows is either missing or WSL's (see plugins/axiomengine/mcp/find-bash.js).
// A Node shebang makes npm's wrappers run node, which is always there, and the choice of bash is
// made by find-bash.js instead of by PATH. npx goes through the same wrappers, so this is also how
// `npx -y @axiomengine/code-graph mcp` starts on Windows.
//
// node resolves this file through the .bin symlink before setting __dirname, so bin/axiomengine is
// found beside it and its own root walk (#886) starts inside the package, as before.
//
// Python is chosen here too (#1331): the query verbs call `python3`, which a python.org install on Windows does
// not provide. find-python.js hands bash a python3 that runs whichever interpreter answered. A build needs no
// Python, so none found is not an error here; a verb that needs it says so from scripts/axiomengine.
// ─────────────────────────────────────────────────────────────────────────────
'use strict';
const { spawnSync } = require('child_process');
const path = require('path');
const { findBash } = require('../plugins/axiomengine/mcp/find-bash.js');
const { findPython, withPython } = require('../plugins/axiomengine/mcp/find-python.js');

function fail(msg) {
  process.stderr.write(`❌ ${msg}\n`);
  process.exit(127);
}

// `axiomengine --version` is answered here, before bash is looked for: it is what a user runs to check an install,
// including one whose bash cannot be found. bin/axiomengine answers it the same way when run from a checkout.
const args = process.argv.slice(2);
if (args.length === 1 && args[0] === '--version') {
  process.stdout.write(`${require('../package.json').version}\n`);
  process.exit(0);
}

const { bash, error } = findBash();
if (error) fail(error);
const py = findPython();
// AXIOMENGINE_BASH too, for the builds Python starts: a bare `bash` from Python on Windows is WSL's or nothing.
const env = { ...(py.exe ? withPython(process.env, py) : process.env), AXIOMENGINE_BASH: bash };
const r = spawnSync(bash, [path.join(__dirname, 'axiomengine'), ...args], { stdio: 'inherit', env });
if (r.error) fail(`could not start bash: ${r.error.message}`);
// Die of the same signal the CLI died of, so a caller sees what really happened.
if (r.signal) process.kill(process.pid, r.signal);
process.exit(r.status ?? 1);
