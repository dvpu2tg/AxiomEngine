#!/usr/bin/env python3
"""gen_blind_brief.py <tasks.json> <graph-repo> <task-id>... — the DEPLOYABLE brief: issue text in, chains out,
no fix-file knowledge anywhere. Mechanical recipe, identical for every task:
  1. seeds   = identifiers the issue text contains that the graph declares, rarest first (max 4)
  2. expand  = per seed: `impact <seed>` page 1 (callers/contract) + `path <seed> '*' --depth 3` page 1 (downstream)
  3. select  = include each answer's first page verbatim, capped at ~5000 tokens total
Scoring (printed, not injected): whether any gold basename appears in the brief and at which line — the
discovery metric. The brief file itself never sees the gold list."""
import json, os, re, subprocess, sys, sqlite3

AX = os.path.expanduser('~/Documents/AxiomEngine/wt-bench19/plugins/axiomengine/skills/axiomengine/scripts/axiomengine')
ENV = dict(os.environ, AXIOMENGINE_NO_REFRESH='1',
           AXIOM_PARSER=os.path.expanduser('~/Documents/AxiomEngine/wt-bench19/parser/dist/index.js'))
ENV.pop('AXIOMENGINE_ENGINE', None)

def run(repo, *args, timeout=150):
    try:
        p = subprocess.run(['bash', AX, *args, repo], capture_output=True, text=True, env=ENV, timeout=timeout)
        return p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return ''

def seeds_of(repo, issue):
    con = sqlite3.connect(f"file:{os.path.join(repo, '.axiomengine', 'out', 'graph.sqlite')}?mode=ro", uri=True)
    cand = set(re.findall(r'`([A-Za-z_][\w.]*)`', issue)) | set(re.findall(r'\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b', issue)) \
           | set(re.findall(r'\b([a-z]+[A-Z]\w+)\b', issue))
    title = issue.split('\n', 1)[0]
    rows = []
    for c in cand:
        n = con.execute("SELECT count(*) FROM symbols WHERE name = ?", (c.split('.')[-1],)).fetchone()[0]
        if 0 < n <= 40: rows.append((c not in title, n, c))
    con.close()
    return [c for _t, _n, c in sorted(rows)[:4]]

def main():
    tasks_file, repo, *ids = sys.argv[1:]
    tasks = {t['id']: t for t in json.load(open(tasks_file))}
    for tid in ids:
        t = tasks[tid]
        issue = '# ' + t['title'] + '\n\n' + t['body']
        seeds = seeds_of(repo, issue)
        parts = ['## Call-graph analysis (generated from the issue text alone; every row is a repo file:line)']
        for s in seeds:
            imp = run(repo, 'impact', s)
            if imp: parts += ['', f'### impact {s} — callers, contract, tests', imp.strip()[:3500]]
            dn = run(repo, 'path', s, '*', '--depth', '3')
            if dn: parts += ['', f"### path {s} '*' --depth 3 — what runs under it", dn.strip()[:3500]]
        brief = '\n'.join(parts)[:20000]
        out = f'blind-briefs/{tid}.md'
        os.makedirs('blind-briefs', exist_ok=True)
        open(out, 'w').write(brief)
        # discovery scoring, outside the brief
        golds = [g.rsplit('/', 1)[-1].replace('.java', '') for g in t['gold_files']]
        hits = []
        for g in golds:
            for i, line in enumerate(brief.splitlines(), 1):
                if g in line: hits.append(f'{g}@line{i}'); break
        print(f"{tid}: seeds={seeds} | brief {len(brief)}B | GOLD-IN-BRIEF: {hits or 'NO'}", flush=True)

if __name__ == '__main__':
    main()
