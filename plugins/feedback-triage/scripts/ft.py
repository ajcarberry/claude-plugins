#!/usr/bin/env python3
"""ft — the feedback-triage queue CLI.

Every queue mutation goes through this script, so the ledger, schema, state
machine, report lint, and report rendering stay deterministic.
Skills decide *what* to write; this script decides *whether it is valid*.
Stdlib only. Output is JSON on stdout unless noted; errors go to stderr with
exit 1 (bad input) or 2 (blocked by a rule).

Run `ft.py help` for the command list.
"""
import contextlib
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_VERSION = 1

TYPES = ("bug", "feature")
TIERS = ("low", "medium", "high")
OPEN_STATUSES = ("new", "investigating", "investigated", "needs-reinvestigation",
                 "blocked", "reported")
CLOSED_STATUSES = ("resolved", "duplicate", "invalid")
STATUSES = OPEN_STATUSES + CLOSED_STATUSES
TRANSITIONS = {
    "new": {"investigating", "duplicate", "invalid", "resolved"},
    "investigating": {"investigated", "blocked", "new", "needs-reinvestigation"},
    "investigated": {"reported", "needs-reinvestigation", "resolved", "duplicate", "invalid"},
    "needs-reinvestigation": {"investigating", "resolved", "duplicate", "invalid"},
    "blocked": {"investigating", "new", "needs-reinvestigation", "resolved", "duplicate", "invalid"},
    "reported": {"reported", "needs-reinvestigation", "resolved", "duplicate", "invalid"},
    "resolved": {"needs-reinvestigation"},
    "duplicate": set(),
    "invalid": {"needs-reinvestigation"},
}
REPRO = ("reproduced", "not-reproduced", "partial", "not-attempted", "n/a")
RELATIONS = ("original", "duplicate", "mention")
REPORTABLE = ("investigated", "reported")
CLAIM_TTL_HOURS = 6

PR_VERDICTS = ("fixes", "partial", "wrong", "unverified")

DEFAULT_CONFIG = {
    "state": {"dir": ".feedback-triage", "persist": "branch",
              "branch": "feedback-triage/state", "remote": "origin"},
    "sources": {"github": [], "slack": []},
    "intake": {"lookback_days": 14, "overlap_hours": 24},
    "investigate": {"max_parallel": 4, "max_per_run": 8, "base_branch": "main",
                    "branch_prefix": "triage/", "open_prs": True, "draft_prs": True, "setup": ""},
    "report": {"tracker": ""},
    "recheck": {"max_per_run": 20, "min_age_hours": 12},
}


# ---------------------------------------------------------------- utilities

class Blocked(Exception):
    """A rule refused the operation (exit 2)."""


class BadInput(Exception):
    """Malformed input (exit 1)."""


def now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt=None):
    return (dt or now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def project_root():
    env = os.environ.get("FT_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return os.path.abspath(env)
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, check=True).stdout.strip()
        if out:
            return out
    except (OSError, subprocess.CalledProcessError):
        pass
    return os.getcwd()


def config_path(root=None):
    return os.path.join(root or project_root(), ".claude", "feedback-triage.json")


def load_config(root=None):
    path = config_path(root)
    if os.path.exists(path):
        with open(path) as f:
            return deep_merge(DEFAULT_CONFIG, json.load(f))
    return json.loads(json.dumps(DEFAULT_CONFIG))


def state_dir(root=None, cfg=None):
    root = root or project_root()
    cfg = cfg or load_config(root)
    d = cfg["state"]["dir"]
    return d if os.path.isabs(d) else os.path.join(root, d)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def load_input(arg):
    """--json takes a file path, '-' for stdin, or an inline JSON string."""
    if arg is None:
        raise BadInput("missing --json")
    if arg == "-":
        text = sys.stdin.read()
    elif os.path.exists(arg):
        with open(arg) as f:
            text = f.read()
    else:
        text = arg
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise BadInput(f"invalid JSON: {e}")


def emit(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# ------------------------------------------------------------ ref handling

GH_URL = re.compile(r"https?://(?:www\.)?github\.com/([\w.-]+)/([\w.-]+)/(?:issues|pull|discussions)/(\d+)", re.I)
GH_SHORT = re.compile(r"^([\w.-]+)/([\w.-]+)#(\d+(?:~\d+)?)$")
SLACK_URL = re.compile(r"https?://[\w.-]+\.slack\.com/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", re.I)
SLACK_REF = re.compile(r"^slack:([A-Z0-9]+)/(\d{10}\.\d{6}(?:~\d+)?)$", re.I)


def normalize_ref(value):
    """Canonical source ref, or None. github:owner/repo#N, slack:CHANNEL/TS."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip()
    m = GH_URL.search(v)
    if m:
        return f"github:{m.group(1).lower()}/{m.group(2).lower()}#{m.group(3)}"
    if v.lower().startswith("github:"):
        v = v[7:]
    m = GH_SHORT.match(v)
    if m:
        return f"github:{m.group(1).lower()}/{m.group(2).lower()}#{m.group(3)}"
    m = SLACK_URL.search(value)
    if m:
        return f"slack:{m.group(1).upper()}/{m.group(2)}.{m.group(3)}"
    m = SLACK_REF.match(v)
    if m:
        return f"slack:{m.group(1).upper()}/{m.group(2)}"
    if re.match(r"^[a-z][\w-]*:\S+$", v):
        return v
    return None


def extract_refs(text):
    """All recognisable refs (GitHub/Slack URLs) inside free text."""
    found = []
    for m in GH_URL.finditer(text or ""):
        found.append(normalize_ref(m.group(0)))
    for m in SLACK_URL.finditer(text or ""):
        found.append(normalize_ref(m.group(0)))
    return [r for r in dict.fromkeys(found) if r]


# ------------------------------------------------------------------- store

class Store:
    def __init__(self, root=None):
        self.root = root or project_root()
        self.cfg = load_config(self.root)
        self.dir = state_dir(self.root, self.cfg)
        self.queue_dir = os.path.join(self.dir, "queue")
        self.index_path = os.path.join(self.dir, "index.json")
        self.log_path = os.path.join(self.dir, "log.jsonl")

    # locking: one writer at a time (intake, recheck, investigate may overlap)
    @contextlib.contextmanager
    def lock(self):
        os.makedirs(self.dir, exist_ok=True)
        with open(os.path.join(self.dir, ".lock"), "w") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    def require(self):
        if not os.path.exists(self.index_path):
            raise BadInput(f"queue not initialised at {self.dir} — run: ft.py init")

    def index(self):
        return read_json(self.index_path, {"schema": SCHEMA_VERSION, "next_id": 1,
                                           "refs": {}, "ignored": {}, "watermarks": {}})

    def save_index(self, idx):
        write_json(self.index_path, idx)

    def ticket_path(self, tid):
        return os.path.join(self.queue_dir, f"{tid}.json")

    def get(self, tid):
        tid = canonical_id(tid)
        t = read_json(self.ticket_path(tid))
        if t is None:
            raise BadInput(f"no such ticket: {tid}")
        return t

    def put(self, t):
        t["updated_at"] = iso()
        validate_ticket(t)
        write_json(self.ticket_path(t["id"]), t)

    def all(self):
        if not os.path.isdir(self.queue_dir):
            return []
        out = []
        for name in sorted(os.listdir(self.queue_dir)):
            if re.match(r"^FT-\d{4,}\.json$", name):
                out.append(read_json(os.path.join(self.queue_dir, name)))
        return out

    def log(self, event, **detail):
        os.makedirs(self.dir, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps({"at": iso(), "event": event, **detail}, ensure_ascii=False) + "\n")


def canonical_id(tid):
    m = re.match(r"^(?:FT-)?(\d+)$", str(tid).strip(), re.I)
    if not m:
        raise BadInput(f"bad ticket id: {tid}")
    return f"FT-{int(m.group(1)):04d}"


def history(t, event, actor="ft", **detail):
    t.setdefault("history", []).append({"at": iso(), "actor": actor, "event": event, **detail})


def transition(t, new_status, actor, reason=None):
    old = t["status"]
    if new_status == old and new_status != "reported":
        return
    if new_status not in TRANSITIONS.get(old, set()):
        raise Blocked(f"{t['id']}: illegal transition {old} → {new_status}")
    t["status"] = new_status
    history(t, "status", actor, **{"from": old, "to": new_status, **({"reason": reason} if reason else {})})


# ---------------------------------------------------------------- validate

def _need(cond, msg, errs):
    if not cond:
        errs.append(msg)


def validate_source(s, errs, where="source"):
    _need(isinstance(s, dict), f"{where}: must be an object", errs)
    if not isinstance(s, dict):
        return
    _need(normalize_ref(s.get("ref")) == s.get("ref"), f"{where}: ref not canonical: {s.get('ref')}", errs)
    _need(s.get("relation") in RELATIONS, f"{where}: relation must be one of {RELATIONS}", errs)
    _need(bool(s.get("url")) or s.get("ref", "").startswith("slack:"), f"{where}: url required", errs)
    _need(len(s.get("excerpt") or "") <= 400, f"{where}: excerpt > 400 chars", errs)


def validate_ticket(t):
    errs = []
    _need(re.match(r"^FT-\d{4,}$", t.get("id", "")), "id malformed", errs)
    _need(t.get("type") in TYPES, f"type must be one of {TYPES}", errs)
    _need(t.get("status") in STATUSES, f"status must be one of {STATUSES}", errs)
    title = t.get("title") or ""
    _need(0 < len(title) <= 90, "title required, ≤ 90 chars", errs)
    _need(0 < len(t.get("summary") or "") <= 600, "summary required, ≤ 600 chars", errs)
    srcs = t.get("sources") or []
    _need(len(srcs) >= 1, "at least one source required", errs)
    for i, s in enumerate(srcs):
        validate_source(s, errs, f"sources[{i}]")
    _need(sum(1 for s in srcs if s.get("relation") == "original") == 1,
          "exactly one source must have relation 'original'", errs)
    c = t.get("complexity")
    if c is not None:
        _need(c.get("tier") in TIERS, f"complexity.tier must be one of {TIERS}", errs)
        _need(bool(c.get("rationale")), "complexity.rationale required", errs)
    inv = t.get("investigation") or {}
    if inv.get("repro") is not None:
        _need(inv["repro"] in REPRO, f"investigation.repro must be one of {REPRO}", errs)
    if t.get("status") == "duplicate":
        _need(bool(t.get("duplicate_of")), "duplicate tickets need duplicate_of", errs)
    if t.get("status") in ("investigated", "reported"):
        _need(c is not None, "investigated tickets need complexity", errs)
        _need(bool(inv.get("file")), "investigated tickets need investigation.file", errs)
        if c and c.get("tier") == "low" and inv.get("review") == "approved":
            _need(bool(inv.get("branch")), "low tier with approved review needs investigation.branch", errs)
    if errs:
        raise BadInput(f"{t.get('id', '?')} invalid: " + "; ".join(errs))


# --------------------------------------------------------------- reporters

def reporters(t):
    names = set()
    anon = 0
    for s in t.get("sources", []):
        a = (s.get("author") or "").strip().lower()
        if a:
            names.add(a)
        else:
            anon += 1
        for p in s.get("plus_ones") or []:
            if p and p.strip():
                names.add(p.strip().lower())
    return len(names) + anon


# ------------------------------------------------------------- report lint

BANNED = {
    "utilize": "use", "utilise": "use", "leverage": "use", "facilitate": "help",
    "basically": None, "simply": None, "just": None, "very": None, "really": None,
    "actually": None, "obviously": None, "clearly": None, "seamless": None,
    "seamlessly": None, "robust": "strong", "synergy": None, "paradigm": None,
    "holistic": None, "impactful": None, "in order to": "to", "please note": None,
    "it should be noted": None, "going forward": None, "at this point in time": "now",
    "a number of": "some", "etc": None,
}
HEDGES = ("might possibly", "could potentially", "it seems like", "sort of", "kind of")
PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?(?:\w+ed|broken|written|taken|"
                     r"given|shown|seen|known|chosen|hidden|driven|frozen|forgotten|done|made|sent|"
                     r"built|found|kept|left|lost|held|told|caught|paid)\b", re.I)
INTERNAL_ID = re.compile(r"\bFT-\d{2,}\b", re.I)  # queue ids are ours; they never reach a report
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]|:[a-z0-9_+-]+:")
MARKUP = re.compile(r"\*\*|__|^#|<[^>]+\|[^>]+>|\[[^\]]+\]\([^)]+\)", re.M)

LIMITS = {  # field: (max words per sentence, max sentences, max total words)
    "headline": (12, 1, 12),
    "what": (20, 2, 40),
    "finding": (20, 1, 20),
    "fix": (25, 3, 60),
    "handoff": (25, 1, 25),
}


def sentences(text):
    text = re.sub(r"`[^`]*`", "CODE", text)  # code spans count as one word
    text = re.sub(r"\b(e\.g|i\.e|etc|vs)\.", r"\1", text, flags=re.I)
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text):
    return re.findall(r"[\w'’/.-]+", re.sub(r"`[^`]*`", "CODE", text))


def lint_text(field, text):
    """Return (errors, warnings) for one prose field."""
    errs, warns = [], []
    if not text or not text.strip():
        return [f"{field}: empty"], []
    max_s_words, max_sents, max_words = LIMITS[field]
    sents = sentences(text)
    if len(sents) > max_sents:
        errs.append(f"{field}: {len(sents)} sentences (max {max_sents})")
    for s in sents:
        n = len(words(s))
        if n > max_s_words:
            errs.append(f"{field}: sentence has {n} words (max {max_s_words}): \"{s[:60]}…\"")
    total = len(words(text))
    if total > max_words:
        errs.append(f"{field}: {total} words (max {max_words})")
    low = " " + re.sub(r"[^\w\s']", " ", text.lower()) + " "
    for term, alt in BANNED.items():
        if f" {term} " in low:
            errs.append(f"{field}: avoid \"{term}\"" + (f" — use \"{alt}\"" if alt else " — delete it"))
    for h in HEDGES:
        if h in low:
            errs.append(f"{field}: hedge \"{h}\" — state the confidence instead")
    if INTERNAL_ID.search(text):
        errs.append(f"{field}: internal ticket id \"{INTERNAL_ID.search(text).group(0)}\" — refer to the issue or describe it instead")
    if EMOJI.search(text):
        errs.append(f"{field}: no emoji in prose — the template adds them")
    if MARKUP.search(text):
        errs.append(f"{field}: no markdown/links in prose — the template formats; links go in sources")
    if field == "headline" and text.rstrip().endswith((".", "!", "?")):
        errs.append("headline: no end punctuation")
    if field != "headline" and not text.rstrip().endswith((".", "?", "`", ")")):
        warns.append(f"{field}: end with a full stop")
    if PASSIVE.search(text):
        warns.append(f"{field}: passive voice? \"{PASSIVE.search(text).group(0)}\" — prefer active")
    return errs, warns


def lint_report(report, fix_ready, pr_numbers=None):
    """fix_ready: the report carries a high-confidence fix (verified PR or our reviewed change)."""
    errs, warns = [], []
    if not isinstance(report, dict):
        return ["report must be an object"], []
    for f in ("headline", "what"):
        e, w = lint_text(f, report.get(f) or "")
        errs += e
        warns += w
    findings = report.get("findings") or []
    if not 1 <= len(findings) <= 4:
        errs.append(f"findings: {len(findings)} items (need 1–4)")
    for i, item in enumerate(findings):
        e, w = lint_text("finding", item or "")
        errs += [x.replace("finding:", f"findings[{i}]:") for x in e]
        warns += [x.replace("finding:", f"findings[{i}]:") for x in w]
    fix = report.get("fix")
    if fix_ready and not fix:
        errs.append("fix: required — this report carries a ready fix; say what it changes and what to check")
    if fix and not fix_ready:
        errs.append("fix: only for a high-confidence fix (verified PR or reviewed change); put research in findings")
    if fix:
        e, w = lint_text("fix", fix)
        errs += e
        warns += w
        named = set(re.findall(r"\bPR #?(\d+)", fix))
        if pr_numbers is not None and named - pr_numbers:
            errs.append(f"fix names PR #{', #'.join(sorted(named))} but the report links "
                        f"PR #{', #'.join(sorted(pr_numbers)) or 'none'} — they must agree")
    extra = set(report) - {"headline", "what", "findings", "fix"}
    if extra:
        errs.append(f"unknown report fields: {sorted(extra)}")
    return errs, warns


# --------------------------------------------------------------- rendering

def load_theme(root):
    theme = read_json(os.path.join(PLUGIN_ROOT, "templates", "report", "theme.json"))
    over = read_json(os.path.join(root, ".claude", "feedback-triage", "theme.json"))
    return deep_merge(theme, over or {})


def load_template(root, name):
    for base in (os.path.join(root, ".claude", "feedback-triage", "report"),
                 os.path.join(PLUGIN_ROOT, "templates", "report")):
        p = os.path.join(base, name)
        if os.path.exists(p):
            with open(p) as f:
                return f.read()
    raise BadInput(f"template not found: {name}")


def fill(template, values):
    """{{key}} substitution. A line whose placeholders are all empty is dropped.
    A line containing {{key[]}} repeats once per list item. Lines between
    {{#key}} and {{/key}} are kept only when key is non-empty (whole sections)."""
    out, skip = [], []
    for line in template.splitlines():
        stripped = line.strip()
        if stripped.startswith("{{!"):
            continue  # template comment
        m = re.fullmatch(r"\{\{([#/])(\w+)\}\}", stripped)
        if m:
            if m.group(1) == "#":
                skip.append(not values.get(m.group(2)))
            elif skip:
                skip.pop()
            continue
        if any(skip):
            continue
        keys = re.findall(r"\{\{(\w+)(\[\])?\}\}", line)
        if not keys:
            out.append(line)
            continue
        list_keys = [k for k, is_list in keys if is_list]
        if list_keys:
            for item in values.get(list_keys[0]) or []:
                out.append(re.sub(r"\{\{\w+\[\]\}\}", lambda _m, v=item: v, fill_scalars(line, values)))
            continue
        if all(not values.get(k) for k, _ in keys):
            continue
        out.append(fill_scalars(line, values))
    text = "\n".join(line.rstrip() for line in out).strip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", text)


def fill_scalars(line, values):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(values.get(m.group(1)) or ""), line)


def source_line(s, theme):
    ref = s["ref"]
    if ref.startswith("github:"):
        label = f"{theme['source']['github']} {ref.split(':', 1)[1]}"
    elif ref.startswith("slack:"):
        ch = s.get("channel_name") or ref.split(":")[1].split("/")[0]
        label = f"{theme['source']['slack']} #{ch.lstrip('#')}"
    else:
        label = f"{theme['source']['other']} {ref.split(':')[0]}"
    who = f" ({s['author']})" if s.get("author") else ""
    return f"{label}{who}: {s['url']}" if s.get("url") else f"{label}{who}"


def fix_kind(t):
    """'existing' (a linked upstream PR we tested fixes it), 'ours' (our reviewed PR),
    'branch' (our reviewed change, no PR opened), or None (a researched report)."""
    inv = t.get("investigation") or {}
    if (inv.get("existing_pr") or {}).get("verdict") == "fixes":
        return "existing"
    if (t.get("complexity") or {}).get("tier") == "low" and inv.get("review") == "approved":
        return "ours" if inv.get("pr_url") else "branch"
    return None


def fix_pr_numbers(t):
    inv = t.get("investigation") or {}
    kind = fix_kind(t)
    url = inv.get("pr_url") if kind == "ours" else (inv.get("existing_pr") or {}).get("url") if kind == "existing" else None
    return {m.group(1) for m in [re.search(r"/pull/(\d+)", url or "")] if m}


def ticket_values(t, theme):
    tier = t["complexity"]["tier"]
    inv = t.get("investigation") or {}
    rep = t["report"]
    kind = fix_kind(t)
    ext = inv.get("existing_pr") or {}
    if kind == "existing":
        status, link = theme["status"]["fix_existing"], ext["url"]
    elif kind == "ours":
        status, link = theme["status"]["fix_ours"], inv["pr_url"]
    elif kind == "branch":
        # branches made before ids were dropped from names (ft/FT-0001-…) are not printed
        status = theme["status"]["fix_branch_unnamed"] if INTERNAL_ID.search(inv["branch"]) else \
            theme["status"]["fix_branch"].replace("{branch}", inv["branch"])
        link = ""
    else:
        status, link = theme["status"][tier], ""
    sources = [source_line(s, theme) for s in t["sources"]]
    seen = {link}
    for s in t["sources"]:
        for p in s.get("linked_prs") or []:
            if p.get("url") and p["url"] not in seen:
                seen.add(p["url"])
                sources.append(f"{theme['source']['pr']} ({p.get('state') or 'linked'}): {p['url']}")
    n = reporters(t)
    repro = theme["repro"].get(inv.get("repro") or "", "") if t["type"] == "bug" else ""
    return {
        "headline": rep["headline"],
        "intro": theme["intro"]["fix" if kind else "report"],
        "type_label": theme["type"][t["type"]],
        "status": status,
        "repro_part": f" · **Reproduced:** {repro}" if repro else "",
        "reporters": f"{n} {'person' if n == 1 else 'people'}",
        "what": rep["what"],
        "findings": rep["findings"],
        "fix": rep.get("fix") or "",
        "fix_link": f"{theme['labels']['review']} {link}" if link and rep.get("fix") else "",
        # steps the project's rules leave to a person (sign-off, PR description): only for our own change
        "handoff": (f"**{theme['labels']['handoff']}** " + " ".join(h.rstrip('.') + "." for h in inv["handoff"]))
                   if kind in ("ours", "branch") and inv.get("handoff") and rep.get("fix") else "",
        "sources": sources,
    }


def report_hash(t):
    inv = t.get("investigation") or {}
    rep = {k: v for k, v in (t.get("report") or {}).items() if not k.startswith("_")}
    basis = {"report": rep, "fix": fix_kind(t), "reporters": reporters(t),
             "tier": (t.get("complexity") or {}).get("tier"), "pr": inv.get("pr_url"), "handoff": inv.get("handoff"),
             "existing_pr": (inv.get("existing_pr") or {}).get("verdict"),
             "status": "closed" if t["status"] in CLOSED_STATUSES else "open"}
    return hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- commands

def cmd_init(args, st):
    with st.lock():
        os.makedirs(st.queue_dir, exist_ok=True)
        for sub in ("investigations", "runs", "reports/outbox", "reports/sent"):
            os.makedirs(os.path.join(st.dir, sub), exist_ok=True)
        created = not os.path.exists(st.index_path)
        if created:
            st.save_index(st.index())
        cfg_created = False
        if not os.path.exists(config_path(st.root)) and "--no-config" not in args:
            write_json(config_path(st.root), DEFAULT_CONFIG)
            cfg_created = True
    emit({"state_dir": st.dir, "index_created": created,
          "config": config_path(st.root), "config_created": cfg_created})


def cmd_paths(args, st):
    emit({"project": st.root, "config": config_path(st.root), "state_dir": st.dir,
          "queue": st.queue_dir, "index": st.index_path,
          "investigations": os.path.join(st.dir, "investigations"),
          "runs": os.path.join(st.dir, "runs"),
          "outbox": os.path.join(st.dir, "reports", "outbox"),
          "plugin_root": PLUGIN_ROOT})


def cmd_config(args, st):
    emit(st.cfg)


def build_source(raw, relation):
    ref = normalize_ref(raw.get("ref") or raw.get("url"))
    if not ref:
        raise BadInput(f"source has no recognisable ref/url: {raw}")
    src = {
        "ref": ref,
        "kind": raw.get("kind") or ref.split(":")[0],
        "url": raw.get("url") or "",
        "author": raw.get("author") or "",
        "raised_at": raw.get("raised_at") or "",
        "excerpt": (raw.get("excerpt") or "")[:400],
        "relation": relation,
        "added_at": iso(),
    }
    for k in ("channel_name", "plus_ones", "state", "linked_prs"):
        if raw.get(k):
            src[k] = raw[k]
    errs = []
    validate_source(src, errs)
    if errs:
        raise BadInput("; ".join(errs))
    return src


def resolve_target(st, tid):
    """Follow duplicate_of to the surviving ticket."""
    seen = set()
    t = st.get(tid)
    while t["status"] == "duplicate" and t.get("duplicate_of") and t["id"] not in seen:
        seen.add(t["id"])
        t = st.get(t["duplicate_of"])
    return t


def attach_source(st, idx, tid, raw, relation, actor, note=None):
    t = resolve_target(st, tid)
    tid = t["id"]
    src = build_source(raw, relation)
    if src["ref"] in idx["refs"]:
        return idx["refs"][src["ref"]], False
    t["sources"].append(src)
    idx["refs"][src["ref"]] = tid
    history(t, "source-added", actor, ref=src["ref"], relation=relation, **({"note": note} if note else {}))
    if t["status"] in ("resolved", "invalid", "blocked"):
        transition(t, "needs-reinvestigation", actor, f"new report {src['ref']} after {t['status']}")
    st.put(t)
    return tid, True


def resolve_dup_target(idx, value):
    """duplicate_of may be a ticket id or the original's source URL/ref — never a predicted id."""
    if re.match(r"^(?:FT-)?\d+$", str(value).strip(), re.I):
        return canonical_id(value)
    ref = normalize_ref(value)
    if not ref or ref not in idx["refs"]:
        raise BadInput(f"duplicate_of {value!r} is not a tracked ticket or source — upsert the original first")
    return idx["refs"][ref]


def refresh_existing(st, idx, ref, src_raw):
    """Re-reading a tracked source merges new +1s, state, and linked PRs."""
    t = resolve_target(st, idx["refs"][ref])
    for s_ in t["sources"]:
        if s_["ref"] != ref:
            continue
        changed = False
        new_po = sorted(set(s_.get("plus_ones") or []) | set(src_raw.get("plus_ones") or []))
        if new_po != sorted(s_.get("plus_ones") or []):
            s_["plus_ones"] = new_po
            changed = True
        for k in ("state", "linked_prs"):
            if src_raw.get(k) and src_raw[k] != s_.get(k):
                s_[k] = src_raw[k]
                changed = True
        if changed and t["status"] in ("resolved", "invalid") and (src_raw.get("state") or "").lower() == "open":
            transition(t, "needs-reinvestigation", "intake", f"{ref} reopened upstream")
        if changed:
            history(t, "source-refreshed", "intake", ref=ref)
            st.put(t)
        return t["id"], changed
    return t["id"], False


def cmd_upsert(args, st):
    """Intake one candidate. Idempotent by source ref."""
    st.require()
    cand = load_input(opt(args, "--json"))
    dry = "--dry-run" in args
    actor = opt(args, "--actor") or "intake"
    src_raw = cand.get("source") or {}
    ref = normalize_ref(src_raw.get("ref") or src_raw.get("url"))
    if not ref:
        raise BadInput("candidate.source needs a ref or url")
    with st.lock():
        idx = st.index()
        if ref in idx["refs"]:
            tid, changed = (idx["refs"][ref], False) if dry else refresh_existing(st, idx, ref, src_raw)
            emit({"action": "exists", "id": tid, "ref": ref, "refreshed": changed})
            return
        if ref in idx["ignored"]:
            closed_reason = re.match(r"^(?:\w+:\s*)?closed", idx["ignored"][ref]["reason"].lower())
            # reopened upstream, or re-read and now judged feedback (a question that turned out a bug)
            reopened = (src_raw.get("state") or "").lower() == "open" if closed_reason else cand.get("type") in TYPES
            if not reopened:
                emit({"action": "ignored", "ref": ref, "reason": idx["ignored"][ref]["reason"]})
                return
            if not dry:
                idx["ignored"].pop(ref)  # reopened upstream: it is feedback again
        # cross-links are evidence, not a verdict: the orchestrator decides
        linked = [r for r in dict.fromkeys([normalize_ref(x) for x in cand.get("links") or []]
                  + extract_refs(src_raw.get("excerpt") or "")) if r and r in idx["refs"] and r != ref]
        dup = cand.get("duplicate_of")
        if dup:
            target = resolve_dup_target(idx, dup)
            if dry:
                emit({"action": "would-link", "id": resolve_target(st, target)["id"], "ref": ref})
                return
            tid, _ = attach_source(st, idx, target, src_raw, "duplicate", actor,
                                   note=cand.get("duplicate_reason"))
            st.save_index(idx)
            st.log("linked", id=tid, ref=ref)
            emit({"action": "linked", "id": tid, "ref": ref})
            return
        if linked and not cand.get("distinct"):
            ids = sorted({resolve_target(st, idx["refs"][r])["id"] for r in linked})
            if dry:
                emit({"action": "links-tracked", "ids": ids, "ref": ref,
                      "next": "same issue → duplicate_of; different issue → distinct: true"})
                return
            raise Blocked(f"{ref} links tracked {', '.join(ids)} — set duplicate_of (same issue) "
                          "or distinct: true (different issue)")
        if cand.get("type") not in TYPES:
            raise BadInput(f"candidate.type must be one of {TYPES}")
        tid = f"FT-{idx['next_id']:04d}"
        t = {
            "id": tid, "schema": SCHEMA_VERSION, "type": cand["type"],
            "title": (cand.get("title") or "").strip(),
            "summary": (cand.get("summary") or "").strip(),
            "status": "new", "created_at": iso(), "updated_at": iso(),
            "sources": [build_source(src_raw, "original")],
            "labels": cand.get("labels") or [],
            "component": cand.get("component") or "",
            "severity": cand.get("severity") or "",
            "environment": cand.get("environment") or {},
            "complexity": None,
            "investigation": {}, "verification": {}, "report": None, "reported": {},
            "history": [],
        }
        history(t, "created", actor, ref=ref)
        validate_ticket(t)
        if dry:
            emit({"action": "would-create", "ticket": t})
            return
        write_json(st.ticket_path(tid), t)
        idx["refs"][ref] = tid
        idx["next_id"] += 1
        st.save_index(idx)
        st.log("created", id=tid, ref=ref)
        emit({"action": "created", "id": tid, "ref": ref})


def cmd_link(args, st):
    st.require()
    tid = canonical_id(args[0])
    raw = load_input(opt(args, "--json"))
    relation = opt(args, "--relation") or "duplicate"
    if relation not in RELATIONS[1:]:
        raise BadInput("--relation must be duplicate or mention")
    with st.lock():
        idx = st.index()
        got, added = attach_source(st, idx, tid, raw, relation, opt(args, "--actor") or "intake",
                                   note=opt(args, "--note"))
        st.save_index(idx)
    emit({"action": "linked" if added else "exists", "id": got})


def cmd_move_source(args, st):
    """move-source REF --to ID --reason T: re-home a source that was linked to the wrong ticket."""
    st.require()
    ref = normalize_ref(args[0] if args else None)
    to_id, reason = opt(args, "--to"), opt(args, "--reason")
    if not ref or not to_id or not reason:
        raise BadInput("move-source REF --to ID --reason TEXT")
    with st.lock():
        idx = st.index()
        if ref not in idx["refs"]:
            raise BadInput(f"{ref} is not tracked")
        src_t = resolve_target(st, idx["refs"][ref])
        dst_t = resolve_target(st, to_id)
        if src_t["id"] == dst_t["id"]:
            raise BadInput(f"{ref} is already on {dst_t['id']}")
        moving = next(x for x in src_t["sources"] if x["ref"] == ref)
        if moving["relation"] == "original":
            raise Blocked(f"{ref} is {src_t['id']}'s original report — merge the tickets instead")
        src_t["sources"] = [x for x in src_t["sources"] if x["ref"] != ref]
        dst_t["sources"].append(dict(moving, relation="duplicate"))
        idx["refs"][ref] = dst_t["id"]
        if dst_t["status"] in ("resolved", "invalid", "blocked"):
            transition(dst_t, "needs-reinvestigation", "intake", f"moved-in report {ref}")
        for t, ev in ((src_t, "source-removed"), (dst_t, "source-added")):
            history(t, ev, "intake", ref=ref, reason=reason)
            st.put(t)
        st.save_index(idx)
        st.log("moved", ref=ref, frm=src_t["id"], to=dst_t["id"])
    emit({"action": "moved", "ref": ref, "from": src_t["id"], "to": dst_t["id"]})


def cmd_ignore(args, st):
    st.require()
    ref = normalize_ref(opt(args, "--ref"))
    reason = opt(args, "--reason")
    if not ref or not reason:
        raise BadInput("ignore needs --ref and --reason")
    with st.lock():
        idx = st.index()
        if ref in idx["refs"]:
            emit({"action": "exists", "id": idx["refs"][ref]})
            return
        idx["ignored"][ref] = {"reason": reason, "at": iso()}
        st.save_index(idx)
    emit({"action": "ignored", "ref": ref})


def cmd_merge(args, st):
    """merge DUP INTO --reason: semantic duplicates discovered after both were tracked."""
    st.require()
    dup_id, into_id = canonical_id(args[0]), canonical_id(args[1])
    reason = opt(args, "--reason")
    if not reason:
        raise BadInput("merge needs --reason")
    if dup_id == into_id:
        raise BadInput("cannot merge a ticket into itself")
    with st.lock():
        idx = st.index()
        dup, into = st.get(dup_id), st.get(into_id)
        if dup["status"] in ("duplicate", "invalid"):
            raise Blocked(f"{dup_id} is already {dup['status']} — nothing to merge")
        if into["status"] in CLOSED_STATUSES:
            raise Blocked(f"{into_id} is {into['status']} — merge into an open ticket")
        for s in dup["sources"]:
            moved = dict(s, relation="duplicate" if s["relation"] == "original" else s["relation"])
            into["sources"].append(moved)
            idx["refs"][s["ref"]] = into_id
        history(into, "merged-in", "merge", source=dup_id, reason=reason)
        transition(dup, "duplicate", "merge", reason)
        dup["duplicate_of"] = into_id
        for other in st.all():
            if other.get("duplicate_of") == dup_id:
                other["duplicate_of"] = into_id
                st.put(other)
        st.put(into)
        st.put(dup)
        st.save_index(idx)
        st.log("merged", id=dup_id, into=into_id)
    emit({"action": "merged", "id": dup_id, "into": into_id})


STOP = set("a an the and or but if of to in on at for with by from is are was were be been "
           "it its this that these those i we you they he she my our your their when then "
           "not no can cant cannot do does did dont doesnt have has had will would should "
           "could there here what which who how why all any some more most very just".split())


def tokens(text):
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if w not in STOP and len(w) > 2}


def cmd_search(args, st):
    st.require()
    q = tokens(" ".join(a for a in args if not a.startswith("--")))
    include_closed = "--all" in args
    hits = []
    for t in st.all():
        if t["status"] in CLOSED_STATUSES and not include_closed:
            continue
        orig = next((s.get("excerpt", "") for s in t["sources"] if s["relation"] == "original"), "")
        doc = tokens(" ".join((t["title"], t["summary"], t.get("component", ""), orig)))
        if not q or not doc:
            continue
        score = len(q & doc) / len(q)  # share of the query this ticket covers
        if score >= 0.25:
            hits.append({"id": t["id"], "score": round(score, 3), "type": t["type"],
                         "status": t["status"], "title": t["title"]})
    hits.sort(key=lambda h: -h["score"])
    emit(hits[:int(opt(args, "--limit") or 5)])


def cmd_get(args, st):
    st.require()
    emit(st.get(args[0]))


def cmd_list(args, st):
    st.require()
    statuses = set((opt(args, "--status") or "").split(",")) - {""}
    typ = opt(args, "--type")
    fmt = opt(args, "--format") or "table"
    rows = [t for t in st.all() if (not statuses or t["status"] in statuses)
            and (not typ or t["type"] == typ)]
    if fmt == "json":
        emit(rows)
    elif fmt == "ids":
        print("\n".join(t["id"] for t in rows))
    elif fmt == "brief":
        for t in rows:
            print(f"{t['id']} {t['type'][0]} {t['title']}")
    else:
        for t in rows:
            tier = (t.get("complexity") or {}).get("tier", "-")
            print(f"{t['id']}  {t['status']:<22} {t['type']:<8} tier={tier:<6} "
                  f"raised={reporters(t)}  {t['title']}")


def cmd_stats(args, st):
    st.require()
    tickets = st.all()
    idx = st.index()
    by = lambda key: {k: sum(1 for t in tickets if key(t) == k)
                      for k in sorted({key(t) for t in tickets}, key=str)}
    emit({"total": len(tickets), "by_status": by(lambda t: t["status"]),
          "by_type": by(lambda t: t["type"]),
          "by_tier": by(lambda t: (t.get("complexity") or {}).get("tier") or "-"),
          "tracked_refs": len(idx["refs"]), "ignored_refs": len(idx["ignored"]),
          "watermarks": idx["watermarks"],
          "multi_raised": [t["id"] for t in tickets if len(t["sources"]) > 1]})


def cmd_watermark(args, st):
    st.require()
    sub, source = args[0], args[1]
    with st.lock():
        idx = st.index()
        if sub == "get":
            emit({"source": source, "value": idx["watermarks"].get(source)})
        elif sub == "set":
            old = idx["watermarks"].get(source)
            new = args[2]
            if old and new < old:
                raise Blocked(f"watermark for {source} would move backwards ({old} → {new})")
            idx["watermarks"][source] = new
            st.save_index(idx)
            st.log("watermark", source=source, value=new)
            emit({"source": source, "value": new, "previous": old})
        else:
            raise BadInput("watermark get|set SOURCE [VALUE]")


def related(st, t, limit=3):
    """Open tickets about the same thing — investigators keep recommendations consistent.
    Words shared by more than a quarter of open tickets ("error", "fails") don't count."""
    open_t = [o for o in st.all() if o["status"] not in CLOSED_STATUSES]
    docs = {o["id"]: tokens(" ".join((o["title"], o["summary"], o.get("component", "")))) for o in open_t}
    df = {}
    for d in docs.values():
        for w in d:
            df[w] = df.get(w, 0) + 1
    common = {w for w, n in df.items() if n > max(2, len(docs) // 4)}
    q = tokens(t["title"] + " " + t.get("component", "")) - common
    out = []
    for oid, d in docs.items():
        if oid == t["id"] or not q:
            continue
        shared = q & (d - common)
        if len(shared) >= 2 or (len(shared) == 1 and len(q) <= 2):
            out.append((len(shared) / len(q), oid))
    return [i for _, i in sorted(out, reverse=True)[:limit]]


def cmd_related(args, st):
    """related ID: open tickets on the same topic (as stored at claim, else computed)."""
    st.require()
    t = st.get(args[0])
    rel = t["investigation"].get("related")
    if rel is None:
        rel = related(st, t)
    emit([{"id": r, "title": st.get(r)["title"],
           "fix": (st.get(r).get("report") or {}).get("fix"),
           "findings": (st.get(r).get("report") or {}).get("findings")} for r in rel])


def cmd_claim(args, st):
    """Atomically take tickets for investigation (new / needs-reinvestigation / expired claims)."""
    st.require()
    limit = int(opt(args, "--limit") or st.cfg["investigate"]["max_per_run"])
    only = [canonical_id(x) for x in (opt(args, "--ids") or "").split(",") if x]
    actor = opt(args, "--actor") or "investigate"
    claimed = []
    with st.lock():
        cutoff = now() - timedelta(hours=CLAIM_TTL_HOURS)
        pool = []
        for t in st.all():
            if only and t["id"] not in only:
                continue
            expired = t["status"] == "investigating" and (parse_iso(t["investigation"].get("claimed_at")) or now()) < cutoff
            if t["status"] in ("new", "needs-reinvestigation") or expired or (only and t["status"] == "blocked"):
                pool.append(t)
        pool.sort(key=lambda t: (t["status"] != "needs-reinvestigation", -reporters(t), t["created_at"]))
        for t in pool[:limit]:
            rel = related(st, t)
            t["investigation"]["related"] = rel
            if t["status"] != "investigating":
                transition(t, "investigating", actor)
            t["investigation"]["claimed_at"] = iso()
            st.put(t)
            claimed.append({"id": t["id"], "type": t["type"], "title": t["title"],
                            "failures": int(t["investigation"].get("attempts") or 0), "related": rel})
    emit({"claimed": claimed, "remaining": max(0, len(pool) - len(claimed))})


def cmd_release(args, st):
    st.require()
    tid = canonical_id(args[0])
    reason = opt(args, "--reason") or "released"
    with st.lock():
        t = st.get(tid)
        # failures of the ticket only: --infra (disk full, run killed, network) counts nothing
        attempts = int(t["investigation"].get("attempts") or 0) + (0 if "--infra" in args else 1)
        t["investigation"]["attempts"] = attempts
        target = "blocked" if attempts >= 2 or "--blocked" in args else "new"
        transition(t, target, "investigate", reason)
        t["investigation"].pop("claimed_at", None)
        t["investigation"]["blocked_reason"] = reason if target == "blocked" else None
        st.put(t)
    emit({"id": tid, "status": target})


INVESTIGATION_KEYS = {"id", "status", "type", "complexity", "repro",
                      "investigation_file", "branch", "worktree", "commit", "summary_correction",
                      "concerns", "options_count", "root_cause", "existing_pr",
                      "fixed_on_base", "handoff"}


def cmd_investigated(args, st):
    """Apply an investigator's structured result."""
    st.require()
    res = load_input(opt(args, "--json"))
    extra = set(res) - INVESTIGATION_KEYS
    if extra:
        raise BadInput(f"unknown result keys: {sorted(extra)}")
    tid = canonical_id(res.get("id") or args[0])
    with st.lock():
        t = st.get(tid)
        if t["status"] != "investigating":
            raise Blocked(f"{tid} is {t['status']}, not investigating — claim it first")
        if res.get("status") == "BLOCKED":
            raise BadInput("BLOCKED results go through: ft.py release ID --reason ...")
        fixed = res.get("fixed_on_base")
        if fixed:  # {"commit": sha, "evidence": "..."} — the problem no longer exists on the base branch
            if not isinstance(fixed, dict) or not fixed.get("commit") or not fixed.get("evidence"):
                raise BadInput("fixed_on_base needs commit and evidence")
            inv = t["investigation"]
            inv.update({"file": res.get("investigation_file"), "completed_at": iso(), "attempts": 0})
            inv.pop("claimed_at", None)
            t["verification"] = dict(t.get("verification") or {}, fixed_by=fixed["commit"],
                                     notes=fixed["evidence"], last_checked_at=iso(), verdict="resolved")
            transition(t, "new", "investigate", "already fixed on base")
            transition(t, "resolved", "investigate", f"fixed on base by {fixed['commit']}")
            st.put(t)
            st.log("investigated", id=tid, fixed_on_base=fixed["commit"])
            emit({"id": tid, "status": "resolved", "fixed_by": fixed["commit"], "next": "none"})
            return
        c = res.get("complexity") or {}
        if c.get("tier") not in TIERS or not c.get("rationale"):
            raise BadInput("complexity needs tier (low|medium|high) and rationale")
        if res.get("type") and res["type"] != t["type"]:
            if res["type"] not in TYPES:
                raise BadInput("type must be bug or feature")
            history(t, "type-corrected", "investigate", **{"from": t["type"], "to": res["type"]})
            t["type"] = res["type"]
        f = res.get("investigation_file")
        if not f or not os.path.exists(os.path.join(st.root, f) if not os.path.isabs(f) else f):
            raise BadInput(f"investigation_file missing or not found: {f}")
        if t["type"] == "bug" and res.get("repro") not in REPRO:
            raise BadInput(f"bugs need repro: one of {REPRO}")
        ext = res.get("existing_pr")
        if ext and (not isinstance(ext, dict) or ext.get("verdict") not in PR_VERDICTS or not ext.get("url")):
            raise BadInput(f"existing_pr needs url and verdict (one of {PR_VERDICTS})")
        if ext:
            linked = {normalize_ref(p.get("url")) for s_ in t["sources"] for p in s_.get("linked_prs") or []}
            ext["linked"] = normalize_ref(ext["url"]) in linked
            if not ext["linked"] and not ext.get("unlinked_reason"):
                raise BadInput(f"{ext['url']} is not linked from this ticket's sources "
                               f"({sorted(x for x in linked if x) or 'none'}) — use a linked PR, or give unlinked_reason")
        defer = bool(ext) and ext["verdict"] == "fixes"  # only a verified fix waives our own tested change
        if ext and ext["verdict"] == "fixes" and res.get("branch"):
            raise BadInput(f"{ext['url']} already fixes this — review it instead of building a duplicate branch")
        prior = t["investigation"].get("prior_attempt")
        if prior and c["tier"] == "low":
            raise BadInput(f"a low-tier attempt ({prior}) failed review twice — classify medium and keep it as an option")
        if res.get("branch"):
            taken = [x["id"] for x in st.all() if x["id"] != tid and res["branch"].casefold() in
                     {(x.get("investigation") or {}).get(k, "").casefold() for k in ("branch", "prior_attempt")
                      if (x.get("investigation") or {}).get(k)}]
            if taken:
                raise Blocked(f"branch {res['branch']} is already recorded on {', '.join(taken)} — use the worktree's own branch")
        if c["tier"] == "low" and not res.get("branch") and not defer:
            raise BadInput("low tier needs the branch holding the change (or an existing_pr that covers it)")
        if c["tier"] == "medium" and int(res.get("options_count") or 0) < 2:
            raise BadInput("medium tier needs ≥ 2 implementation options in the investigation file")
        t["complexity"] = {"tier": c["tier"], "rationale": c["rationale"]}
        inv = t["investigation"]
        inv.update({"file": os.path.relpath(f, st.root) if os.path.isabs(f) else f,
                    "repro": res.get("repro") or "n/a", "completed_at": iso(),
                    "root_cause": res.get("root_cause") or inv.get("root_cause"),
                    "concerns": res.get("concerns") or None})
        inv.pop("claimed_at", None)
        inv["existing_pr"] = ext or None
        inv["attempts"] = 0  # failures reset after a success
        if not (c["tier"] == "low" and res.get("branch")):
            for k in ("branch", "worktree", "commit", "review", "review_notes", "pr_url", "handoff"):
                inv.pop(k, None)  # a re-investigation that built nothing carries no stale PR/branch
        if c["tier"] == "low" and res.get("branch"):
            handoff = res.get("handoff") or []
            if not isinstance(handoff, list) or len(handoff) > 3 or not all(isinstance(h, str) for h in handoff):
                raise BadInput("handoff is a list of ≤ 3 short steps")
            bad = [e for h in handoff for e in lint_text("handoff", h)[0]]  # same prose rules as the report
            if bad:
                raise BadInput("; ".join(bad))
            inv.update({"branch": res["branch"], "worktree": res.get("worktree"),
                        "commit": res.get("commit"), "review": "pending", "handoff": handoff or None})
        if res.get("summary_correction"):
            history(t, "summary-corrected", "investigate", old=t["summary"])
            t["summary"] = res["summary_correction"]
        if t.get("report"):
            t["report"]["_stale"] = True  # reinvestigated: old prose may be wrong now
        transition(t, "investigated", "investigate")
        st.put(t)
        st.log("investigated", id=tid, tier=c["tier"])
    emit({"id": tid, "tier": c["tier"],
          "next": "review" if inv.get("review") == "pending" else "report"})


def cmd_review(args, st):
    """review ID --verdict approved|changes --notes '...' [--commit SHA]: the independent check on a low-tier change."""
    st.require()
    tid = canonical_id(args[0])
    verdict = opt(args, "--verdict")
    notes = opt(args, "--notes") or ""
    if verdict not in ("approved", "changes"):
        raise BadInput("--verdict approved|changes")
    with st.lock():
        t = st.get(tid)
        if (t.get("complexity") or {}).get("tier") != "low":
            raise Blocked(f"{tid} is not low tier — nothing to review")
        inv = t["investigation"]
        inv["review"] = verdict
        inv["review_notes"] = notes
        if verdict == "approved":
            commit = opt(args, "--commit")
            if not commit or not re.fullmatch(r"[0-9a-f]{7,40}", commit):
                raise BadInput("an approval needs --commit <sha of the reviewed head>")
            inv["reviewed_commit"] = inv["commit"] = commit  # a revise moves the branch head
        else:
            inv.pop("reviewed_commit", None)
        # every round's notes stay in history; review_notes holds the latest
        history(t, "review", "reviewer", verdict=verdict, notes=notes, commit=opt(args, "--commit"))
        if verdict == "changes" and "--downgrade" in args:
            inv["review"] = "rejected"
            inv["prior_attempt"] = inv.get("branch")
            t["complexity"] = {"tier": "medium", "rationale": f"low attempt rejected twice in review: {notes}"}
            history(t, "tier-downgraded", "reviewer", to="medium", notes=notes)
            transition(t, "needs-reinvestigation", "reviewer", f"low attempt rejected twice: {notes}")
        st.put(t)
    emit({"id": tid, "review": t["investigation"]["review"], "tier": t["complexity"]["tier"]})


def cmd_pr(args, st):
    st.require()
    tid = canonical_id(args[0])
    url = opt(args, "--url")
    if not url:
        raise BadInput("pr needs --url")
    with st.lock():
        t = st.get(tid)
        if t["investigation"].get("review") != "approved":
            raise Blocked(f"{tid}: review not approved — no change request")
        t["investigation"]["pr_url"] = url
        history(t, "pr-opened", "investigate", url=url)
        st.put(t)
    emit({"id": tid, "pr_url": url})


def branch_head(st, branch):
    remote = st.cfg["state"]["remote"]
    for ref in (f"refs/heads/{branch}", f"refs/remotes/{remote}/{branch}"):
        try:
            out = subprocess.run(["git", "-C", st.root, "rev-parse", "--verify", "-q", ref],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            out = ""
        if out:
            return out
    return ""


def remote_head(st, branch):
    remote = st.cfg["state"]["remote"]
    try:
        out = subprocess.run(["git", "-C", st.root, "ls-remote", remote, f"refs/heads/{branch}"],
                             capture_output=True, text=True, timeout=8).stdout.split()
    except (OSError, subprocess.SubprocessError):
        out = []
    return out[0] if out else ""


def cmd_gate_pr(args, st):
    """gate-pr --branch B [--commit SHA | --remote]: exit 0 only if exactly that reviewed commit may ship."""
    branch = re.sub(r"^(?:refs/heads/|\+)", "", opt(args, "--branch") or "", flags=re.I)
    prefix = st.cfg["investigate"]["branch_prefix"]
    if not branch.casefold().startswith(prefix.casefold()) or not os.path.exists(st.index_path):
        return  # not a feedback-triage branch — not our business
    owners = [x for x in st.all() if branch.casefold() in
              {(x.get("investigation") or {}).get(k, "").casefold() for k in ("branch", "prior_attempt") if
               (x.get("investigation") or {}).get(k)}]
    if len(owners) != 1:
        raise Blocked(f"{branch} is a triage branch " + ("no ticket has finished with" if not owners else
                      f"claimed by {len(owners)} tickets") + " — only one reviewed low-complexity change "
                      "becomes a change request")
    t = owners[0]
    inv = t["investigation"]
    if inv.get("branch", "").casefold() != branch.casefold():
        raise Blocked(f"{branch} is {t['id']}'s rejected prior attempt — it never becomes a change request")
    if t["status"] not in REPORTABLE:
        raise Blocked(f"{t['id']} is {t['status']} — only an active, investigated ticket's change becomes a PR")
    tier = (t.get("complexity") or {}).get("tier")
    if tier != "low":
        raise Blocked(f"{t['id']} is {tier or 'unclassified'} complexity — only low-complexity tickets get a change request")
    if inv.get("review") != "approved":
        raise Blocked(f"{t['id']}: the change has not passed the independent change-reviewer (review={inv.get('review')}). "
                      "Run the change-reviewer, record it with ft.py review, then open the PR")
    reviewed = inv.get("reviewed_commit")
    if not reviewed:
        raise Blocked(f"{t['id']}: no reviewed commit recorded — record the approval with ft.py review --commit")
    if opt(args, "--commit"):
        sending, where = opt(args, "--commit"), "being pushed"  # the exact commit the push sends
    elif "--remote" in args:
        sending, where = remote_head(st, branch), "on the remote"  # what a PR would be built from
    else:
        sending, where = branch_head(st, branch), "local"
    if not sending or not (sending.startswith(reviewed) or reviewed.startswith(sending)) or len(sending) < 7:
        raise Blocked(f"{branch}: the commit {where} ({(sending or 'unknown')[:12]}) is not the commit the reviewer "
                      f"approved ({reviewed[:12]}) — review that commit, record it with ft.py review --commit")


def cmd_report_set(args, st):
    st.require()
    tid = canonical_id(args[0])
    report = load_input(opt(args, "--json"))
    with st.lock():
        t = st.get(tid)
        if t["status"] not in REPORTABLE:
            raise Blocked(f"{tid} is {t['status']} — only investigated/reported tickets get a report")
        errs, warns = lint_report(report, bool(fix_kind(t)), fix_pr_numbers(t))
        if errs:
            emit({"id": tid, "ok": False, "errors": errs, "warnings": warns})
            sys.exit(2)
        t["report"] = {k: report[k] for k in ("headline", "what", "findings", "fix") if report.get(k)}
        history(t, "report-written", opt(args, "--actor") or "report")
        st.put(t)
    emit({"id": tid, "ok": True, "warnings": warns})


def cmd_lint(args, st):
    report = load_input(opt(args, "--json"))
    errs, warns = lint_report(report, "--fix-ready" in args)
    emit({"ok": not errs, "errors": errs, "warnings": warns})
    if errs:
        sys.exit(2)


def due_reports(st, ignore_hash=False, only=None):
    out = []
    for t in st.all():
        if only and t["id"] not in only:
            continue
        if t["status"] not in REPORTABLE or not t.get("report") or t["report"].get("_stale"):
            continue
        inv = t.get("investigation") or {}
        if inv.get("review") in ("pending", "changes"):
            continue  # wait for the reviewer verdict / the revision
        if not ignore_hash and (t.get("reported") or {}).get("hash") == report_hash(t):
            continue
        out.append(t)
    out.sort(key=lambda t: (fix_kind(t) is None, -reporters(t), t["created_at"]))  # ready fixes first
    return out


def cmd_due(args, st):
    st.require()
    kind = args[0] if args else "report"
    if kind == "report":
        emit([{"id": t["id"], "fix": fix_kind(t), "title": t["title"]} for t in due_reports(st)])
    elif kind == "report-writing":
        emit([{"id": t["id"], "fix_ready": bool(fix_kind(t))} for t in st.all() if t["status"] in REPORTABLE and
              (not t.get("report") or t["report"].get("_stale"))
              and t["investigation"].get("review") not in ("pending", "changes")])
    elif kind == "review":
        emit([t["id"] for t in st.all() if t["status"] == "investigated"
              and t["investigation"].get("review") in ("pending", "changes")])
    elif kind == "recheck":
        hours = float(opt(args, "--min-age-hours") or st.cfg["recheck"]["min_age_hours"])
        limit = int(opt(args, "--limit") or st.cfg["recheck"]["max_per_run"])
        cutoff = now() - timedelta(hours=hours)
        pool = [t for t in st.all() if t["status"] not in ("duplicate", "invalid", "investigating")
                and not (t["status"] == "resolved" and int((t.get("verification") or {}).get("quiet_resolved") or 0) >= 2)
                and (parse_iso((t.get("verification") or {}).get("last_checked_at")) or datetime.min.replace(tzinfo=timezone.utc)) < cutoff]
        pool.sort(key=lambda t: ((t.get("verification") or {}).get("last_checked_at") or "", t["id"]))
        emit([{"id": t["id"], "status": t["status"], "title": t["title"]} for t in pool[:limit]])
    else:
        raise BadInput("due report|report-writing|review|recheck")


def cmd_render(args, st):
    st.require()
    ids = [canonical_id(x) for x in (opt(args, "--ids") or "").split(",") if x]
    tickets = due_reports(st, ignore_hash=bool(ids), only=ids) if ids else due_reports(st)
    theme = load_theme(st.root)
    closed_ids = [t["id"] for t in st.all() if t["status"] == "resolved"
                  and (t.get("reported") or {}).get("at") and not t["reported"].get("closed_announced")]
    if not tickets and not closed_ids:
        emit({"run": None, "files": [], "note": "nothing due"})
        return
    run = now().strftime("%Y%m%dT%H%M%SZ")
    n = 1
    while any(os.path.exists(os.path.join(st.dir, "reports", box, run)) for box in ("outbox", "sent")):
        n += 1
        run = now().strftime("%Y%m%dT%H%M%SZ") + f"-{n}"
    tpl = load_template(st.root, "report.md")
    rendered, held = [], []
    for t in tickets:
        text = fill(tpl, ticket_values(t, theme))
        leak = INTERNAL_ID.search(text)
        if leak:  # deterministic guard: internal ids never reach a report; hold this one, render the rest
            held.append({"id": t["id"], "title": t["title"], "reason": f"would show internal id {leak.group(0)}"})
            continue
        rendered.append((t, text))
    if not rendered and not closed_ids:
        emit({"run": None, "files": [], "held": held, "note": "nothing renderable"})
        return
    outdir = os.path.join(st.dir, "reports", "outbox", run)
    os.makedirs(outdir, exist_ok=True)
    files, texts = [], []
    for n, (t, text) in enumerate(rendered, 1):
        slug = re.sub(r"[^a-z0-9]+", "-", t["report"]["headline"].lower()).strip("-")[:50]
        path = os.path.join(outdir, f"{n:02d}-{slug}.md")
        with open(path, "w") as f:
            f.write(text)
        texts.append(text.strip())
        files.append({"file": os.path.relpath(path, st.root), "kind": "ticket", "id": t["id"],
                      "fix": fix_kind(t), "hash": report_hash(t)})
    if closed_ids:  # closures are announced in the run summary, not in a report
        files.append({"file": "-", "kind": "closed", "closed": closed_ids})
    with open(os.path.join(outdir, "all-reports.md"), "w") as fh:
        fh.write("\n\n---\n\n".join(texts) + "\n")
    write_json(os.path.join(outdir, "manifest.json"), {"run": run, "files": files})
    # older unposted runs are superseded by a full render (a re-print with --ids keeps them)
    for old in ([] if ids else os.listdir(os.path.join(st.dir, "reports", "outbox"))):
        if old != run:
            os.makedirs(os.path.join(st.dir, "reports", "superseded"), exist_ok=True)
            os.replace(os.path.join(st.dir, "reports", "outbox", old),
                       os.path.join(st.dir, "reports", "superseded", old))
    every = st.all()
    emit({"run": run, "dir": os.path.relpath(outdir, st.root), "held": held,
          "all": os.path.relpath(os.path.join(outdir, "all-reports.md"), st.root),
          "files": [f for f in files if f["kind"] == "ticket"],
          "closed": [{"title": st.get(c)["title"], "fixed_by": (st.get(c).get("verification") or {}).get("fixed_by")}
                     for c in closed_ids],
          "backlog": {"not_investigated": sum(1 for t in every if t["status"] in ("new", "needs-reinvestigation", "investigating")),
                      "blocked": [t["title"] for t in every if t["status"] == "blocked"]}})


def cmd_sent(args, st):
    """sent RUN [--file F | --all] [--permalink URL]: record posted outbox messages."""
    st.require()
    run = args[0] if args else ""
    outdir = os.path.join(st.dir, "reports", "outbox", run)
    if not os.path.exists(outdir) and os.path.exists(os.path.join(st.dir, "reports", "superseded", run)):
        outdir = os.path.join(st.dir, "reports", "superseded", run)  # pasted before a newer render
    manifest = read_json(os.path.join(outdir, "manifest.json"))
    if not manifest:
        raise BadInput(f"no outbox run {run}")
    rel = opt(args, "--file")
    entries = manifest["files"] if "--all" in args else \
        [f for f in manifest["files"] if rel and (f["file"] == rel or os.path.basename(f["file"]) == rel)]
    if not entries:
        raise BadInput(f"{rel} not in run {run} (or pass --all)")
    with st.lock():
        for entry in entries:
            if entry.get("sent_at"):
                continue
            if entry["kind"] == "ticket":
                t = st.get(entry["id"])
                if t["status"] in REPORTABLE:  # changed since render: record it, keep its status
                    transition(t, "reported", "report")
                t["reported"] = {"at": iso(), "hash": entry["hash"], "permalink": opt(args, "--permalink"),
                                 "count": int((t.get("reported") or {}).get("count") or 0) + 1}
                st.put(t)
            else:
                for cid in entry.get("closed") or []:
                    t = st.get(cid)
                    t["reported"]["closed_announced"] = iso()
                    st.put(t)
            entry["sent_at"] = iso()
            write_json(os.path.join(outdir, "manifest.json"), manifest)
        if all(f.get("sent_at") for f in manifest["files"]):
            os.replace(outdir, os.path.join(st.dir, "reports", "sent", run))
        st.log("sent", run=run, count=len(entries))
    emit({"run": run, "recorded": [e.get("id") or "closures" for e in entries]})


RECHECK_PATCH_KEYS = {"title", "summary", "type", "severity", "environment", "labels", "component", "plus_ones"}
VERDICTS = ("confirmed", "corrected", "resolved", "needs-reinvestigation", "invalid")


def cmd_recheck_apply(args, st):
    """Apply a verifier verdict to an EXISTING ticket. Never creates tickets or sources."""
    st.require()
    res = load_input(opt(args, "--json"))
    tid = canonical_id(res.get("id") or (args[0] if args else ""))
    verdict = res.get("verdict")
    if verdict not in VERDICTS:
        raise BadInput(f"verdict must be one of {VERDICTS}")
    patch = res.get("patch") or {}
    bad = set(patch) - RECHECK_PATCH_KEYS
    if bad:
        raise Blocked(f"recheck may not change {sorted(bad)} — allowed: {sorted(RECHECK_PATCH_KEYS)}")
    if verdict == "corrected" and not patch:
        raise BadInput("corrected verdict needs a patch")
    if not res.get("evidence"):
        raise BadInput("every verdict needs evidence (list of what was checked, with refs)")
    with st.lock():
        t = st.get(tid)
        if t["status"] in ("duplicate", "invalid"):
            raise Blocked(f"{tid} is {t['status']} — not rechecked")
        changed = {}
        if "type" in patch and patch["type"] not in TYPES:
            raise BadInput("type must be bug or feature")
        for ref_, names in (patch.pop("plus_ones", None) or {}).items():
            for s_ in t["sources"]:
                if s_["ref"] == normalize_ref(ref_):
                    merged = sorted(set(s_.get("plus_ones") or []) | set(names))
                    if merged != sorted(s_.get("plus_ones") or []):
                        changed[f"plus_ones:{s_['ref']}"] = {"from": s_.get("plus_ones"), "to": merged}
                        s_["plus_ones"] = merged
        for k, v in patch.items():
            if t.get(k) != v:
                changed[k] = {"from": t.get(k), "to": v}
                t[k] = v
        upstream = res.get("upstream") or {}
        for s in t["sources"]:
            st_ = (upstream.get("states") or {}).get(s["ref"])
            if st_:
                s["state"] = st_
        quiet = int((t.get("verification") or {}).get("quiet_resolved") or 0)
        quiet = quiet + 1 if t["status"] == "resolved" and verdict in ("confirmed", "resolved") else 0
        t["verification"] = {"last_checked_at": iso(), "verdict": verdict, "quiet_resolved": quiet,
                             "notes": res.get("notes") or "", "evidence": res["evidence"][:8],
                             "fixed_by": upstream.get("fixed_by"),
                             "checks": int((t.get("verification") or {}).get("checks") or 0) + 1}
        if verdict == "resolved":
            transition(t, "resolved", "recheck", res.get("notes"))
        elif verdict == "needs-reinvestigation" and t["status"] not in ("new", "needs-reinvestigation"):
            transition(t, "needs-reinvestigation", "recheck", res.get("notes"))
        elif verdict == "invalid":
            transition(t, "invalid", "recheck", res.get("notes"))
        if changed and t.get("report"):
            t["report"]["_stale"] = True
        history(t, "rechecked", "recheck", verdict=verdict, changed=sorted(changed))
        st.put(t)
        st.log("rechecked", id=tid, verdict=verdict)
    emit({"id": tid, "verdict": verdict, "status": t["status"], "changed": changed})


def cmd_validate(args, st):
    """Whole-queue integrity: schema, ledger ⇄ tickets, no ref tracked twice."""
    st.require()
    idx = st.index()
    problems = []
    seen = {}
    ids = set()
    for t in st.all():
        ids.add(t["id"])
        try:
            validate_ticket(t)
        except BadInput as e:
            problems.append(str(e))
        for s in t.get("sources", []):
            if t["status"] == "duplicate":
                continue  # provenance copy; the surviving ticket holds the ref
            if s["ref"] in seen:
                problems.append(f"{s['ref']} tracked by both {seen[s['ref']]} and {t['id']}")
            seen[s["ref"]] = t["id"]
            if idx["refs"].get(s["ref"]) != t["id"]:
                problems.append(f"ledger maps {s['ref']} to {idx['refs'].get(s['ref'])}, ticket {t['id']} holds it")
        if t["status"] == "duplicate" and t.get("duplicate_of") not in ids | {x for x in idx["refs"].values()}:
            problems.append(f"{t['id']} duplicate_of {t.get('duplicate_of')} does not exist")
    for ref, tid in idx["refs"].items():
        if tid not in ids:
            problems.append(f"ledger ref {ref} points at missing {tid}")
        if ref in idx["ignored"]:
            problems.append(f"{ref} is both tracked and ignored")
    max_id = max([int(i[3:]) for i in ids] or [0])
    if idx["next_id"] <= max_id:
        problems.append(f"next_id {idx['next_id']} ≤ highest id {max_id}")
    emit({"ok": not problems, "tickets": len(ids), "refs": len(idx["refs"]), "problems": problems})
    if problems:
        sys.exit(2)


def cmd_log(args, st):
    st.log(args[0], **{k[2:]: v for k, v in zip(args[1::2], args[2::2]) if k.startswith("--")})
    emit({"logged": args[0]})


def cmd_help(args, st):
    print(__doc__)
    for name, fn in sorted(COMMANDS.items()):
        print(f"  {name:<15} {(fn.__doc__ or '').strip().splitlines()[0] if fn.__doc__ else ''}")


def opt(args, name):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return None


COMMANDS = {
    "init": cmd_init, "paths": cmd_paths, "config": cmd_config,
    "upsert": cmd_upsert, "link": cmd_link, "ignore": cmd_ignore, "merge": cmd_merge,
    "move-source": cmd_move_source, "related": cmd_related,
    "search": cmd_search, "get": cmd_get, "list": cmd_list, "stats": cmd_stats,
    "watermark": cmd_watermark, "claim": cmd_claim, "release": cmd_release,
    "investigated": cmd_investigated, "review": cmd_review, "pr": cmd_pr, "gate-pr": cmd_gate_pr,
    "report-set": cmd_report_set, "lint": cmd_lint, "due": cmd_due, "render": cmd_render,
    "sent": cmd_sent, "recheck-apply": cmd_recheck_apply, "validate": cmd_validate,
    "log": cmd_log, "help": cmd_help,
}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        cmd_help([], None)
        return 1
    if "--help" in argv or "-h" in argv:
        cmd_help([], None)  # never act on a help request
        return 0
    try:
        COMMANDS[argv[0]](argv[1:], Store())
        return 0
    except Blocked as e:
        print(f"ft: blocked: {e}", file=sys.stderr)
        return 2
    except (BadInput, KeyError, IndexError, ValueError, TypeError, re.error, StopIteration) as e:
        print(f"ft: error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
