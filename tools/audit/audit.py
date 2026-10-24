"""Opt-in audit of Supervisor for Claude pack runs, read from local Claude Code transcripts.

Run as `python3 -I tools/audit/audit.py [--root DIR ...] [--since YYYY-MM-DD] > tools/audit/out/run.md`.
Standard library only; Python 3.9 compatible. Prints markdown tables to stdout and writes no files.

Metrics: critic round-1 PASS by lead, round-1 empty and NIT-only-or-empty findings-table rates
by lead, scope-critic dispatches per critic round, lead-tree tokens per run (lead / workers /
reviewers), files read by two or more workers of one run, quick-tier ESCALATE rate, main-thread
final context, and corpus counts.

Privacy: transcripts are only regex-matched, never printed. The whole report is built first and
refused (exit status 2, no offending text shown) if a line looks like a home-directory path or
contains a working directory seen in the transcripts.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re
import statistics
import sys

DEFAULT_ROOTS = ["~/.config/claude-supervisor/projects", "~/.claude/projects"]
SHARED_STORE = "~/.claude/projects"  # shared with plain Claude Code: only pack-using sessions count
LEADS = ["researcher", "planner", "executor", "writer"]
QUICK = {"scout", "clerk", "git-ops", "curator", "quick-edit"}
PACK = set(LEADS) | QUICK | {"critic", "scope-critic", "researcher-worker", "planner-worker",
                             "executor-worker", "writer-worker"}
DISPATCH = ("Agent", "Task")
PATH_LEAK = re.compile(r"[/-](Users|home)[/-]")
FRACTION = re.compile(r"(\.\d+)")


def parse_time(s):
    """Epoch seconds for an ISO timestamp, or None. Python 3.9 rejects fractions that are not 3 or 6 digits."""
    if not isinstance(s, str):
        return None
    s = s.replace("Z", "+00:00")
    for text in (s, FRACTION.sub(lambda m: (m.group(1) + "000000")[:7], s, count=1)):
        try:
            d = datetime.datetime.fromisoformat(text)
        except ValueError:
            continue
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        return d.timestamp()
    return None


def load_transcript(path):
    """Parse one JSONL transcript into tool calls, usage per message id, handback text and times."""
    usage = {}  # message id -> usage; a message split over several lines is counted once
    tools = []  # (message id, tool name, input, tool_use id) in file order
    handback = last_text = ""
    cwds = set()  # every working directory the transcript records
    first = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            t = parse_time(d.get("timestamp"))
            if t is not None and (first is None or t < first):
                first = t
            if isinstance(d.get("cwd"), str) and len(d["cwd"]) > 1:
                cwds.add(d["cwd"])
            m = d.get("message")
            if d.get("type") != "assistant" or not isinstance(m, dict):
                continue
            mid = m.get("id") or d.get("uuid")
            if isinstance(m.get("usage"), dict):
                usage[mid] = m["usage"]
            content = m.get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    tools.append((mid, b.get("name"), inp, b.get("id")))
                    if b.get("name") == "SubagentHandback":
                        handback = str(inp.get("message", ""))
                elif b.get("type") == "text" and str(b.get("text", "")).strip():
                    last_text = b["text"]
    return {"usage": usage, "tools": tools, "handback": handback, "last_text": last_text,
            "cwds": cwds, "first": first}


def usage_total(p):
    """All tokens (input, output, cache read, cache creation) of one transcript."""
    return sum(int(u.get(k) or 0) for u in p["usage"].values()
               for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                         "cache_creation_input_tokens"))


def context_sizes(p):
    """Prompt size (input plus cache tokens) of each assistant message, in order."""
    return [sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens",
                                             "cache_creation_input_tokens"))
            for u in p["usage"].values()]


def load_sessions(roots, since):
    """Load every session under the roots; the shared store keeps only sessions that dispatched a pack agent."""
    shared = os.path.realpath(os.path.expanduser(SHARED_STORE))
    sessions = []
    for root in roots:
        root = os.path.expanduser(root)
        is_shared = os.path.realpath(root) == shared
        for main_file in sorted(glob.glob(os.path.join(root, "*", "*.jsonl"))):
            main = load_transcript(main_file)
            if since is not None and (main["first"] is None or main["first"] < since):
                continue
            if is_shared and not any(
                    name in DISPATCH and inp.get("subagent_type") in PACK
                    for _, name, inp, _ in main["tools"]):
                continue
            sid = os.path.basename(main_file)[:-len(".jsonl")]
            subs = {}
            sub_dir = os.path.join(os.path.dirname(main_file), sid, "subagents")
            for sub_file in sorted(glob.glob(os.path.join(sub_dir, "*.jsonl"))):
                try:
                    with open(sub_file[:-len(".jsonl")] + ".meta.json", encoding="utf-8") as fh:
                        meta = json.load(fh)
                except (OSError, ValueError):
                    meta = {}
                sub = load_transcript(sub_file)
                sub["meta"] = meta if isinstance(meta, dict) else {}
                subs[os.path.basename(sub_file)[len("agent-"):-len(".jsonl")]] = sub
            sessions.append({"sid": sid[:8], "main": main, "subs": subs})
    return sessions


def word(w, text):
    return len(re.findall(r"\b" + w + r"\b", text))


VERDICT_LINE = re.compile(r"(?im)^.*(verdict|^\W*(PASS|REVISE)\b).*$")


def verdict(text):
    """PASS, REVISE, ambiguous or none. With both words present, REVISE wins only on a verdict-like line."""
    p, r = word("PASS", text) > 0, word("REVISE", text) > 0
    if p and r:
        lines = [m.group(0) for m in VERDICT_LINE.finditer(text)]
        return "REVISE" if any(re.search(r"\bREVISE\b", x) for x in lines) else "ambiguous"
    return "PASS" if p else "REVISE" if r else "none"


ABOVE_NIT = ("BLOCKING", "MUST", "SHOULD")


def findings_rows(text, levels=ABOVE_NIT + ("NIT",)):
    """Number of findings-table rows: table lines with a cell that is exactly one of `levels`.

    Heuristic for the round-1 rates: the critic report format puts a severity word in its own
    cell on every finding row, so a handback with none has an empty findings table, and one with
    no BLOCKING/MUST/SHOULD cell is NIT-only or empty (scope-critic may be skipped).
    """
    n = 0
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            cells = [c.strip().strip("*`").upper() for c in line.strip().strip("|").split("|")]
            if any(c in levels for c in cells):
                n += 1
    return n


def lead_runs(session):
    """One record per lead transcript of the session, with its reviewers, tokens and worker reads."""
    subs = session["subs"]
    owner = {}  # tool_use id -> ("main", None) or ("sub", agent id)
    for t in session["main"]["tools"]:
        owner[t[3]] = ("main", None)
    for aid, p in subs.items():
        for t in p["tools"]:
            owner[t[3]] = ("sub", aid)
    kids = collections.defaultdict(list)
    for aid, p in subs.items():
        o = owner.get(p["meta"].get("toolUseId"))
        kids[o[1] if o and o[0] == "sub" else None].append(aid)

    runs = []
    for aid, p in subs.items():
        lead = p["meta"].get("agentType")
        if lead not in LEADS:
            continue
        # Round numbering: index of the critic-dispatching assistant message within the lead run.
        rounds = []
        for mid, name, inp, _ in p["tools"]:
            if name in DISPATCH and inp.get("subagent_type") == "critic" and mid not in rounds:
                rounds.append(mid)
        msg_of = {t[3]: t[0] for t in p["tools"]}
        scope = sum(1 for _, name, inp, _ in p["tools"]
                    if name in DISPATCH and inp.get("subagent_type") == "scope-critic")
        critics, tok = [], {"lead": usage_total(p), "workers": 0, "reviewers": 0}
        reads = collections.defaultdict(set)  # file -> workers that read it
        for k in kids[aid]:
            kp, kt = subs[k], subs[k]["meta"].get("agentType", "")
            if kt in ("critic", "scope-critic"):
                tok["reviewers"] += usage_total(kp)
            else:
                tok["workers"] += usage_total(kp)
            if kt == "critic":
                mid = msg_of.get(kp["meta"].get("toolUseId"))
                rn = rounds.index(mid) + 1 if mid in rounds else 0
                critics.append({"round": rn, "verdict": verdict(kp["handback"]),
                                "rows": findings_rows(kp["handback"]),
                                "above_nit": findings_rows(kp["handback"], ABOVE_NIT)})
            if kt.endswith("-worker"):
                for _, name, inp, _ in kp["tools"]:
                    if name == "Read":
                        reads[inp.get("file_path", "")].add(k)
        runs.append({
            "lead": lead, "critics": critics, "rounds": len(rounds),
            "scope": scope,
            "skipped": len(re.findall(r"scope-critic skipped", p["handback"])),
            "tok": tok,
            "dup_files": sum(1 for ks in reads.values() if len(ks) > 1),
            "dup_excess": sum(len(ks) - 1 for ks in reads.values()),
        })
    return runs


def quick_runs(session):
    """(agent type, escalated) for each quick-tier transcript; ESCALATE is a word in the handback."""
    return [(p["meta"].get("agentType"),
             bool(re.search(r"\bESCALATE\b", p["handback"] or p["last_text"])))
            for p in session["subs"].values() if p["meta"].get("agentType") in QUICK]


def ratio(a, b):
    return "%d/%d (%d%%)" % (a, b, round(100.0 * a / b)) if b else "0/0"


def fmt(n):
    return "%.1fM" % (n / 1e6) if n >= 1e6 else "%dk" % round(n / 1e3) if n >= 1e3 else str(int(n))


def table(out, header, rows):
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * len(header))
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    out.append("")


def by_lead(runs):
    return [(lead, [r for r in runs if r["lead"] == lead]) for lead in LEADS
            if any(r["lead"] == lead for r in runs)]


def build_report(sessions):
    """The full report as a list of lines."""
    runs = [r for s in sessions for r in lead_runs(s)]
    quick = [q for s in sessions for q in quick_runs(s)]
    out = ["# Pack audit", ""]

    n_subs = sum(len(s["subs"]) for s in sessions)
    starts = [s["main"]["first"] for s in sessions if s["main"]["first"] is not None]
    span = "%s to %s" % tuple(datetime.datetime.fromtimestamp(x, datetime.timezone.utc).strftime("%Y-%m-%d")
                              for x in (min(starts), max(starts))) if starts else "n/a"
    out += ["## Corpus", ""]
    table(out, ["sessions", "subagent transcripts", "lead runs", "critic handbacks", "quick-tier runs",
                "session start range (UTC)"],
          [[len(sessions), n_subs, len(runs), sum(len(r["critics"]) for r in runs), len(quick), span]])

    out += ["## Critic round-1 PASS by lead", ""]
    rows = []
    for lead, L in by_lead(runs):
        r1 = [c for r in L for c in r["critics"] if c["round"] == 1]
        rows.append([lead, len(L), ratio(sum(c["verdict"] == "PASS" for c in r1), len(r1))])
    table(out, ["lead", "runs", "round-1 PASS"], rows)

    out += ["## Round-1 findings tables by lead", ""]
    out.append("Empty: no table row has a BLOCKING, MUST, SHOULD or NIT cell. NIT-only or empty: no "
               "BLOCKING, MUST or SHOULD cell (scope-critic skip-eligible within the size bound).")
    out.append("")
    rows = []
    for lead, L in by_lead(runs):
        r1 = [c for r in L for c in r["critics"] if c["round"] == 1]
        rows.append([lead, len(r1), ratio(sum(c["rows"] == 0 for c in r1), len(r1)),
                     ratio(sum(c["above_nit"] == 0 for c in r1), len(r1))])
    table(out, ["lead", "round-1 critic handbacks", "empty", "NIT-only or empty"], rows)

    out += ["## Scope-critic dispatches per critic round", ""]
    rows = []
    for lead, L in by_lead(runs):
        rounds, scope = sum(r["rounds"] for r in L), sum(r["scope"] for r in L)
        rows.append([lead, rounds, scope, "%.2f" % (scope / rounds) if rounds else "n/a",
                     sum(r["skipped"] for r in L)])
    table(out, ["lead", "critic rounds", "scope-critic dispatches", "per critic round",
                "'scope-critic skipped' mentions"], rows)

    out += ["## Lead-tree tokens per run (all tokens incl. cache)", ""]
    out.append("Workers are every non-reviewer child; reviewers are critic and scope-critic.")
    out.append("")
    rows = []
    for lead, L in by_lead(runs):
        cells = [lead, len(L)]
        for part in ("lead", "workers", "reviewers"):
            xs = [r["tok"][part] for r in L]
            cells.append("%s total, %s median" % (fmt(sum(xs)), fmt(statistics.median(xs))))
        cells.append(fmt(sum(sum(r["tok"].values()) for r in L)))
        rows.append(cells)
    table(out, ["lead", "runs", "lead", "workers", "reviewers", "tree total"], rows)

    out += ["## Files read by two or more workers of one run", ""]
    rows = []
    for lead, L in by_lead(runs):
        rows.append([lead, len(L), sum(1 for r in L if r["dup_files"]), sum(r["dup_files"] for r in L),
                     sum(r["dup_excess"] for r in L)])
    table(out, ["lead", "runs", "runs affected", "files", "excess reads"], rows)

    out += ["## Quick-tier ESCALATE rate", ""]
    rows = []
    for t in sorted(QUICK):
        q = [e for ty, e in quick if ty == t]
        if q:
            rows.append([t, ratio(sum(q), len(q))])
    rows.append(["all", ratio(sum(e for _, e in quick), len(quick))])
    table(out, ["agent", "ESCALATE"], rows)

    out += ["## Main-thread final context (tokens)", ""]
    finals = []
    for s in sessions:
        ctx = context_sizes(s["main"])
        if ctx:
            finals.append((ctx[-1], s["sid"]))
    if finals:
        biggest = max(finals)
        table(out, ["sessions", "median", "max", "max session"],
              [[len(finals), fmt(statistics.median(c for c, _ in finals)), fmt(biggest[0]), biggest[1]]])
    else:
        table(out, ["sessions", "median", "max", "max session"], [[0, "n/a", "n/a", "n/a"]])
    return out


def scrub(lines, sessions):
    """Return the number of lines that look like they carry a path or a working directory."""
    cwds = set()
    for s in sessions:
        for p in [s["main"]] + list(s["subs"].values()):
            cwds |= p["cwds"]
    return sum(1 for line in lines if PATH_LEAK.search(line) or any(c in line for c in cwds))


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="audit.py",
        description="Print pack-usage metrics from local Claude Code transcripts as markdown tables. "
                    "Output holds counts, medians, rates and 8-character session prefixes only.",
        epilog="Redirect stdout to tools/audit/out/run.md; nothing is written by the script itself.")
    p.add_argument("--root", action="append", metavar="DIR",
                   help="projects directory to read (repeatable; default: %s)" % " and ".join(DEFAULT_ROOTS))
    p.add_argument("--since", metavar="YYYY-MM-DD", help="only sessions starting on or after this date (UTC)")
    args = p.parse_args(argv)
    args.since_ts = None
    if args.since:
        try:
            d = datetime.datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            p.error("--since must be YYYY-MM-DD")
        args.since_ts = d.replace(tzinfo=datetime.timezone.utc).timestamp()
    return args


def main(argv=None):
    args = parse_args(argv)
    sessions = load_sessions(args.root or DEFAULT_ROOTS, args.since_ts)
    lines = build_report(sessions)
    if scrub(lines, sessions):
        print("audit.py: refusing to print: the report contains a path-like line; nothing was printed",
              file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
