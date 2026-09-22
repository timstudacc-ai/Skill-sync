#!/usr/bin/env python3
"""nlmq - deterministic NotebookLM retrieval wrapper for the nlm CLI.

Contract (documented in SKILL.md):
  * stdout carries ONLY the payload (answer text / listing / suggested commands)
  * stderr carries provenance and diagnostics
  * exit codes: 0 ok | 1 usage/config | 2 nlm/auth/network |
                3 malformed-or-empty answer | 4 topic unresolved/ambiguous |
                5 profile not found

No notebook ID is ever cached or hardcoded. Resolution is live:
  alias name -> routing keyword -> exact title -> keyword token -> title substring
The only persisted routing state is the alias table owned by the CLI
(~/.notebooklm-mcp-cli/aliases.json) plus the keyword map next to this file
(scripts/routing.json).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_NLM = 2
EXIT_BADANSWER = 3
EXIT_AMBIGUOUS = 4
EXIT_PROFILE = 5

SKILL_DIR = Path(__file__).resolve().parent.parent
ROUTING_JSON = SKILL_DIR / "scripts" / "routing.json"
DEFAULT_QUERY_TIMEOUT = 180


def die(code, msg):
    print(f"[nlmq] error(rc={code}): {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(f"[nlmq] {msg}", file=sys.stderr)


def nlm():
    p = shutil.which("nlm")
    if not p:
        die(EXIT_NLM, "nlm binary not found on PATH (install notebooklm-mcp-cli)")
    return p


def storage_dir():
    env = os.environ.get("NOTEBOOKLM_MCP_CLI_PATH", "").strip()
    return Path(env) if env else Path.home() / ".notebooklm-mcp-cli"


def load_aliases():
    f = storage_dir() / "aliases.json"
    if not f.exists():
        return {}
    try:
        raw = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for name, entry in raw.items():
        out[name] = entry.get("value", "") if isinstance(entry, dict) else str(entry)
    return out


def load_routing():
    if not ROUTING_JSON.exists():
        die(EXIT_USAGE, f"routing map missing: {ROUTING_JSON}")
    try:
        return json.loads(ROUTING_JSON.read_text(encoding="utf-8"))
    except Exception as e:
        die(EXIT_USAGE, f"routing map unparsable: {e}")


def run(args, timeout):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        die(EXIT_NLM, f"binary not found: {args[0]}")
    except subprocess.TimeoutExpired:
        die(EXIT_NLM, f"timed out after {timeout}s: {' '.join(args[:4])} ...")


def nlm_json(args, timeout, profile=None, what=""):
    cmd = [nlm()] + list(args)
    if profile:
        cmd += ["--profile", profile]
    p = run(cmd, timeout)
    if p.returncode != 0:
        out = (p.stdout or "").strip()
        msg = out or (p.stderr or "").strip() or "unknown failure"
        try:
            j = json.loads(out)
            msg = j.get("error") or msg
        except Exception:
            pass
        if "Profile" in msg and "not found" in msg:
            die(EXIT_PROFILE, msg)
        die(EXIT_NLM, f"{what}: {msg}" if what else msg)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        die(EXIT_NLM, f"{what}: expected JSON, got: {p.stdout[:200]!r}")


def notebooks(profile=None):
    data = nlm_json(["notebook", "list", "--json"], 60, profile, "notebook list")
    if not isinstance(data, list):
        die(EXIT_NLM, "notebook list: unexpected payload")
    return data


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


class Ambiguous(Exception):
    def __init__(self, candidates):
        super().__init__("ambiguous")
        self.candidates = candidates


def find_by_id(nid, nbs):
    return next((n for n in nbs if n.get("id") == nid), None)


def report_ambiguous(topic, candidates):
    if candidates:
        listing = "\n  ".join(candidates)
        die(EXIT_AMBIGUOUS, f"topic '{topic}' matched several notebooks - ask the user which one:\n  {listing}")
    die(EXIT_AMBIGUOUS, f"topic '{topic}' matched no notebook. Run: nlmq --list")


def resolve(topic, nbs, aliases, routing):
    t = norm(topic)
    if not t:
        raise Ambiguous(["empty topic"])
    # 1. alias name, exact
    for name, val in aliases.items():
        if norm(name) == t:
            nb = find_by_id(val, nbs)
            if nb:
                return nb, f"alias '{name}'"
            die(EXIT_NLM, f"alias '{name}' -> {val} is not in the live notebook list (notebook probably re-created). Fix with: nlmq --sync-aliases")
    # 2. routing keyword, whole topic
    if t in routing:
        a = routing[t]
        val = aliases.get(a)
        if val:
            nb = find_by_id(val, nbs)
            if nb:
                return nb, f"keyword '{t}' -> alias '{a}'"
    # 3. exact title, case-insensitive
    for n in nbs:
        if norm(n.get("title", "")) == t:
            return n, "exact title"
    # 4. routing keywords as tokens
    toks = set(re.findall(r"[a-z0-9]+", t))
    hits = {routing[k] for k in routing if k in toks}
    if len(hits) == 1:
        a = hits.pop()
        val = aliases.get(a)
        if val:
            nb = find_by_id(val, nbs)
            if nb:
                return nb, f"keyword token -> alias '{a}'"
    if len(hits) > 1:
        raise Ambiguous([f"keyword '{k}' -> alias '{routing[k]}'" for k in sorted(routing) if k in toks])
    # 5. title substring
    subs = [n for n in nbs if t and t in norm(n.get("title", ""))]
    if len(subs) == 1:
        return subs[0], "unique title substring"
    if len(subs) > 1:
        raise Ambiguous([f"{n.get('title', '')} ({n.get('id', '')[:8]})" for n in subs])
    raise Ambiguous([])


def query_raw(nb_id, question, timeout, profile):
    cmd = [nlm(), "notebook", "query", nb_id, question, "--json",
           "--timeout", str(timeout), "--new-conversation"]
    if profile:
        cmd += ["--profile", profile]
    return run(cmd, timeout + 30)


def parse_answer(p):
    out = (p.stdout or "").strip()
    if p.returncode == 0:
        try:
            j = json.loads(out)
        except Exception:
            return None, f"query rc=0 but output is not JSON: {out[:200]!r}"
        ans = j.get("answer") if isinstance(j, dict) else None
        if isinstance(ans, str) and ans.strip():
            return ans, None
        return None, "query OK but 'answer' field missing or empty"
    # verified: with --json the CLI emits {"status": "error", ...} on STDOUT
    msg = out or (p.stderr or "").strip() or "unknown failure"
    try:
        j = json.loads(out)
        msg = j.get("error") or msg
    except Exception:
        pass
    return None, msg


def looks_notfound(msg):
    m = (msg or "").lower()
    return "not_found" in m or "not found" in m


def classify(msg):
    m = (msg or "").lower()
    if "profile" in m and "not found" in m:
        return EXIT_PROFILE
    if "answer" in m and ("missing" in m or "empty" in m):
        return EXIT_BADANSWER
    return EXIT_NLM


def do_query(topic, question, timeout, profile):
    aliases = load_aliases()
    routing = load_routing()
    nbs = notebooks(profile)
    try:
        nb, how = resolve(topic, nbs, aliases, routing)
    except Ambiguous as e:
        report_ambiguous(topic, e.candidates)
    info(f"resolved '{topic}' -> {how} :: '{nb.get('title', '')}' ({nb.get('id', '')}, sources={nb.get('source_count', '?')})")
    p = query_raw(nb["id"], question, timeout, profile)
    ans, msg = parse_answer(p)
    if ans is None and looks_notfound(msg):
        if find_by_id(nb["id"], notebooks(profile)) is None:
            die(EXIT_NLM, "resolved notebook no longer exists on the server (re-created?). Refresh routing with: nlmq --sync-aliases --apply")
        info("transient NOT_FOUND, notebook still present - retrying once")
        p = query_raw(nb["id"], question, timeout, profile)
        ans, msg = parse_answer(p)
    if ans is None:
        die(classify(msg), msg)
    print(ans)


def cmd_discover(topic, profile):
    nbs = notebooks(profile)
    try:
        nb, how = resolve(topic, nbs, load_aliases(), load_routing())
    except Ambiguous as e:
        report_ambiguous(topic, e.candidates)
    print(f"{nb['id']}  {nb.get('source_count', '?')}src  {nb.get('title', '')}  (via {how})")


def cmd_list(profile):
    nbs = notebooks(profile)
    aliases = load_aliases()
    by_id = {}
    for name, val in aliases.items():
        by_id.setdefault(val, []).append(name)
    w = min(max([len(n.get("title", "")) for n in nbs] or [5]), 58)
    print(f"{'ALIAS':<18} {'SRC':>4}  {'TITLE':<{w}}  ID")
    for n in sorted(nbs, key=lambda x: norm(x.get("title", ""))):
        al = ",".join(by_id.get(n.get("id"), [])) or "-"
        print(f"{al:<18.18} {n.get('source_count', '?'):>4}  {n.get('title', '')[:w]:<{w}}  {n.get('id', '')}")
    dangling = [(k, v) for k, v in aliases.items() if not find_by_id(v, nbs)]
    if dangling:
        print("")
        print("DANGLING ALIASES (target not in live list):")
        for k, v in dangling:
            print(f"  {k} -> {v}   # fix: nlm alias set {k} <new-uuid>")


def slugify(title):
    s = re.sub(r"\([^)]*\)", "", title or "")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:40].rstrip("-") or "notebook"


def cmd_sync(apply, profile):
    nbs = notebooks(profile)
    aliases = load_aliases()
    referenced = set(aliases.values())
    missing = [n for n in nbs if n.get("id") not in referenced]
    if not missing:
        info("all notebooks are aliased")
        return
    for n in missing:
        slug = slugify(n.get("title", ""))
        print(f"nlm alias set {slug} {n['id']} --type notebook")
        if apply:
            p = run([nlm(), "alias", "set", slug, n["id"], "--type", "notebook"], 60)
            if p.returncode == 0:
                info(f"applied {slug} -> {n['id'][:8]}")
            else:
                out = ((p.stdout or "") + (p.stderr or "")).strip()
                info(f"FAILED {slug}: {out[:120]}")
    if not apply:
        info("dry run - re-run with --apply to create these aliases")


def usage():
    print(__doc__.strip())
    print("")
    print("usage:")
    print('  nlmq <topic> "<question>" [--timeout S] [--profile P]    query a notebook')
    print("  nlmq --discover <topic>       show what a topic resolves to (no query)")
    print("  nlmq --list                   notebooks + alias coverage + dangling aliases")
    print("  nlmq --sync-aliases [--apply] suggest/apply aliases for unaliased notebooks")
    print("")
    print("stdout = payload, stderr = provenance.")
    print("exit: 0 ok | 1 usage/config | 2 nlm/auth/network | 3 bad answer | 4 unresolved topic | 5 profile")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        usage()
        return EXIT_OK
    mode = "query"
    apply = False
    profile = None
    timeout = DEFAULT_QUERY_TIMEOUT
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--list":
            mode = "list"
        elif a == "--discover":
            mode = "discover"
            i += 1
            if i >= len(argv):
                die(EXIT_USAGE, "--discover needs a topic argument")
            pos.append(argv[i])
        elif a == "--sync-aliases":
            mode = "sync"
        elif a == "--apply":
            apply = True
        elif a == "--profile":
            i += 1
            if i >= len(argv):
                die(EXIT_USAGE, "--profile needs a value")
            profile = argv[i]
        elif a == "--timeout":
            i += 1
            if i >= len(argv):
                die(EXIT_USAGE, "--timeout needs seconds")
            try:
                timeout = float(argv[i])
            except ValueError:
                die(EXIT_USAGE, f"bad --timeout value: {argv[i]}")
        elif a.startswith("-"):
            die(EXIT_USAGE, f"unknown option: {a}")
        else:
            pos.append(a)
        i += 1

    if mode == "list":
        cmd_list(profile)
    elif mode == "discover":
        if not pos:
            die(EXIT_USAGE, "--discover needs a topic")
        cmd_discover(" ".join(pos), profile)
    elif mode == "sync":
        cmd_sync(apply, profile)
    else:
        if not pos:
            die(EXIT_USAGE, 'usage: nlmq <topic> "<question>"  (see: nlmq --help)')
        do_query(pos[0], " ".join(pos[1:]), timeout, profile)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
