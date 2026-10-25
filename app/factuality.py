"""Deterministic factuality backstop for AI-generated resume feedback.

The LLM prompts already ban invented credentials, blanket licensing/legal
"hiring rules" and unsupported causal certainty. This module is the
deterministic second line of defense: it walks the parsed JSON output and
rewrites any surviving banned constructions into hedged, verify-first
phrasing, while leaving real resume facts, numbers and conditional
placeholders untouched.
"""
import re

# (pattern, replacement). Applied in order to every string value in the
# parsed model output. Replacements keep the surrounding facts intact and
# only soften the unsupported claim.
_RULES = [
    # Blanket legal/licensing assertions stated as fact.
    (re.compile(r"\blegally (?:require[sd]?|mandate[sd]?)\b", re.I), "commonly ask for"),
    (re.compile(r"\bemployers cannot\b", re.I), "employers may not always"),
    (re.compile(r"\bcannot (?:consider|interview|hire|advance)\b", re.I), "may not always consider"),
    (re.compile(r"\bwill not (?:advance|consider|interview|hire)\b", re.I), "may not advance"),
    (re.compile(r"\bmandatory\b", re.I), "often requested"),
    (re.compile(r"\bmust[- ]have\b", re.I), "typically expected"),
    (re.compile(r"\bmeets? (?:the )?minimum (?:education )?requirement", re.I), "is typically part of what is asked for"),
    # Unsupported causal certainty about recruiter behavior.
    (re.compile(r"\bforces? (?:them|employers|recruiters|hiring managers) to assume\b", re.I), "may lead them to assume"),
    (re.compile(r"\bwill auto-?reject\w*\b", re.I), "may deprioritize"),
    (re.compile(r"\bauto-?reject\w*\b", re.I), "rejection"),
    (re.compile(r"\b(?:often |always )?leads? to rejection\b", re.I), "can hurt the application"),
    (re.compile(r"\bguarantee[sd]?\b", re.I), "may improve the odds of"),
    (re.compile(r"=\s*lower ranking", re.I), "which can lower ranking"),
    (re.compile(r"\bwill be (?:rejected|filtered out|screened out)\b", re.I), "may be filtered out"),
    (re.compile(r"\bwill not (?:pass|get|clear)\b", re.I), "may not pass"),
    # Unsupported ranking certainty about screening.
    (re.compile(r"\bthe first screen-out factor\b", re.I), "a common early screening question"),
    (re.compile(r"\bthe (?:number one|#1|top) (?:screen-out|dealbreaker|deal-breaker)\b", re.I), "a common screening concern"),
    (re.compile(r"\bleads? to (?:immediate |automatic )?screen-?out\b", re.I), "can hurt the application"),
    (re.compile(r"\b(?:universally|always) require[sd]?\b", re.I), "commonly ask for"),
    (re.compile(r"\bimmediate screen-?out\b", re.I), "being set aside"),
]

# Sentences containing a banned phrase that survived replacement (paraphrases
# we have no targeted rule for) get flagged so callers can log/monitor.
_WATCH = re.compile(
    r"\b(legally required|cannot be hired|cannot be interviewed|never hired|"
    r"always rejected|guaranteed (?:interview|job|hire))\b", re.I)


def _scrub(text: str) -> tuple[str, list[str]]:
    fixes = []
    out = text
    for rx, rep in _RULES:
        new = rx.sub(rep, out)
        if new != out:
            fixes.append(rx.pattern)
            out = new
    if _WATCH.search(out):
        fixes.append("WATCH:" + _WATCH.search(out).group(0))
    return out, fixes


def sanitize(value, fixes: list | None = None):
    """Recursively scrub every string in a parsed-JSON structure.

    Returns the sanitized structure. If ``fixes`` (a list) is given, the
    patterns that fired are appended for logging. Structure, keys, numbers,
    and factual content (real resume facts, bracketed placeholders) are
    preserved; only banned claim phrasing is rewritten.
    """
    if fixes is None:
        fixes = []
    if isinstance(value, str):
        out, f = _scrub(value)
        fixes.extend(f)
        return out
    if isinstance(value, list):
        return [sanitize(v, fixes) for v in value]
    if isinstance(value, dict):
        return {k: sanitize(v, fixes) for k, v in value.items()}
    return value


# Metric-claim detector: a concrete number tied to a performance metric. If the
# resume itself does not pair that number with that metric, the model invented
# it (or lifted it from the JD); replace the number (and only the number) with
# a conditional placeholder, keeping the sentence structure.
_KW = (r"(?:CSAT|FCR|QA|AHT|SLA|NPS|accuracy|retention|save rate|pass rate"
       r"|first[- ]call[- ]resolution|handle time|ramp-up time"
       r"|escalation rate|callback compliance)")
_NUM = r"\d+(?:[.:]\d+)?\+?"
_METRIC_PATTERNS = [
    # number glued to its unit keyword: "92% CSAT", "6.5 AHT", "5 new hires"
    re.compile(
        rf"(?P<num>{_NUM})(?P<unit>\s*(?:%|percent)\s*{_KW}[\w-]*"
        rf"|\s*(?:CSAT|FCR|QA|AHT|SLA|WPM|NPS)\b"
        rf"|\s*(?:new hires|calls/day|calls per day|patients|beds|students|joiners)\b)",
        re.I),
    # number, keyword within a few words: "88%+ on weekly QA audits",
    # "6:30 avg handle time", "6.5-minute AHT"
    re.compile(
        rf"(?P<num>{_NUM})(?P<unit>\s*(?:[%+.]\+?)?(?:[-\s]*[A-Za-z]+){{0,4}}[-\s]*{_KW}\b[\w-]*)",
        re.I),
    # keyword first, number after: "first-call resolution of 85%",
    # "ramp-up time by 20%", "QA scores of 85%"
    re.compile(
        rf"(?P<kw>{_KW})\b(?P<unit>(?:\s+[A-Za-z-]+){{0,4}}\s*)(?P<num>{_NUM})(?P<tail>\s*(?:%|percent\b))",
        re.I),
]
_PLACEHOLDER = "[add your number - only if you know it]"


_WINDOW = 60


def _attributed(num: str, unit: str, source: str) -> bool:
    """True only if the resume itself pairs this number with this metric.

    The JD is not evidence of candidate achievement, and an unrelated number
    elsewhere in the resume is not either: require the number within _WINDOW
    chars of one of the metric's keywords in the source text.
    """
    keywords = [w for w in re.findall(r"[a-z][a-z-]{2,}", unit.lower())
                if w not in ("percent", "per", "rate", "new", "avg",
                             "average", "minute", "minutes")]
    synonyms = {"hires": ("joiners",), "joiners": ("hires",),
                "handle": ("aht",), "resolution": ("fcr",),
                "first-call": ("fcr",)}
    keywords = keywords + [s for k in keywords for s in synonyms.get(k, ())]
    if not keywords:
        return False
    src = source.lower()
    num_rx = re.compile(r"(?<![0-9.])" + re.escape(num) + r"\+?(?![0-9.])")
    for kw in keywords:
        for km in re.finditer(re.escape(kw), src):
            lo, hi = max(0, km.start() - _WINDOW), km.end() + _WINDOW
            if num_rx.search(src, lo, hi):
                return True
    return False


def _scrub_invented_metrics(text: str, source: str, fixes: list) -> str:
    def _sub(m: re.Match) -> str:
        num = m.group("num")
        unit = (m.groupdict().get("kw") or "") + m.group("unit") + (m.groupdict().get("tail") or "")
        if _attributed(num.rstrip("+"), unit, source):
            return m.group(0)
        fixes.append("invented-metric:" + m.group(0)[:40])
        if m.groupdict().get("kw"):
            return m.group("kw") + m.group("unit") + _PLACEHOLDER + m.group("tail")
        return _PLACEHOLDER + m.group("unit")

    for pattern in _METRIC_PATTERNS:
        text = pattern.sub(_sub, text)
    return text


# General fallback: ANY concrete number in the output must be attributable to
# the source (the resume; plus the JD when the string frames the number as the
# job's requirement/target). A number is attributed when it appears in the
# source within 60 chars of a content word that also neighbors it in the
# output. This catches invented specifics in copy-ready text regardless of
# which metric vocabulary they use ("Cared for 2 critically ill patients",
# "100% medication-safety compliance", "1:2 ratio").
_NUMBER = re.compile(r"(?<![0-9.A-Za-z])(?P<num>\d+(?:[.:]\d+)?)(?![0-9.A-Za-z])")
_REQ_CUE = re.compile(
    r"\b(?:target|requirement|required|requires|threshold|job description|JD|"
    r"asks? for|must maintain|the role expects|the posting)\b", re.I)
_STOP = set("""the and for with your you only true add know per than over under around about
from this that each every any all not are was were have has had will would can could should
may might must our their its his her who what when where how why into onto upon within
without between across after before during while through both such same more most less
least much many few several other another also just even still yet already very too
include including includes included write example known number shift shifts day days
year years month months hour hours minute minutes""".split())


_SYNONYMS = {"hires": ("joiners",), "joiners": ("hires",),
             "handle": ("aht",), "resolution": ("fcr",), "first-call": ("fcr",)}


def _number_attributed(num: str, text: str, pos: int, source: str) -> bool:
    lo = max(0, pos - 40)
    ctx = [w for w in re.findall(r"[a-z][a-z-]{2,}", text[lo:pos + len(num) + 40].lower())
           if w not in _STOP]
    ctx = ctx + [syn for w in ctx for syn in _SYNONYMS.get(w, ())]
    src = source.lower()
    num_rx = re.compile(r"(?<![0-9.])" + re.escape(num) + r"\+?(?![0-9.])")
    for nm in num_rx.finditer(src):
        window = src[max(0, nm.start() - 60):nm.end() + 60]
        if any(w in window for w in ctx):
            return True
    return False


def _scrub_unattributed_numbers(text: str, resume: str, requirement_source: str | None,
                                attr_source: str, fixes: list) -> str:
    source = attr_source

    def repl(m: re.Match) -> str:
        if m.start() > 0 and text[m.start() - 1] in "vV":
            return m.group(0)  # version numbers (ITIL v4)
        if _number_attributed(m.group("num"), text, m.start(), source):
            return m.group(0)
        fixes.append("unattributed-number:" + m.group(0)[:40])
        return _PLACEHOLDER

    return _NUMBER.sub(repl, text)


# Credential / legal-status assertions that must never be presented as
# copy-ready fact unless the resume itself evidences the topic. When the
# resume does not, the assertion is rewritten as explicitly conditional.
_STATUS_TOPICS = [
    (re.compile(r"\bNCLEX[- ]RN passed\b|\bpassed (?:the )?NCLEX\b", re.I), ("nclex",)),
    (re.compile(r"\b(?:RN |state |nursing )?license application submitted\b", re.I), ("license", "licensure", "licensed")),
    (re.compile(r"\bactive (?:RN |state |unrestricted |registered nurse )?license\b", re.I), ("license", "licensure", "licensed")),
    (re.compile(r"\bauthorized to work\b", re.I), ("authorized to work", "work authorization", "green card", "ead", "citizen", "permanent resident")),
    (re.compile(r"\bOPT (?:valid|active|until|through|expires)\b", re.I), ("opt",)),
    (re.compile(r"\bH-?1B\b", re.I), ("h-1b", "h1b")),
    (re.compile(r"\b(ACLS|BLS|CCRN|NIHSS|PALS|TNCC)\s*\(\s*exp", re.I), ()),
]

# Past-tense achievement/activity verbs. In a copy-ready rewrite clause such a
# verb asserts the candidate actually did the thing; if the resume shows no
# evidence of it, the whole clause is made explicitly conditional instead of
# standing as an invented fact.
_ACTIVITY = re.compile(
    r"\b(achieved|built|cut|delivered|designed|earned|improved|increased|launched|"
    r"led|managed|mentored|precepted|reduced|saved|trained|won)\b", re.I)
_ACTIVITY_STEMS = {
    "achieved": ("achiev",), "built": ("built", "build"), "cut": ("cut",),
    "delivered": ("deliver",), "designed": ("design",), "earned": ("earn",),
    "improved": ("improv",), "increased": ("increas",), "launched": ("launch",),
    "led": ("led", "lead", "leading"), "managed": ("manag",),
    "mentored": ("mentor", "train"), "precepted": ("precept", "train", "mentor"),
    "reduced": ("reduc",), "saved": ("sav",), "trained": ("train", "mentor"),
    "won": ("won", "win"),
}
_CONDITIONAL_PREFIX = "If this reflects your real experience: "


def _conditionalize_unsupported(text: str, resume: str, key: str | None, fixes: list) -> str:
    src = resume.lower()
    for rx, evidence in _STATUS_TOPICS:
        m = rx.search(text)
        if not m:
            continue
        topics = evidence or (m.group(1).lower(),) if m.lastindex else evidence
        if any(t in src for t in topics):
            continue
        fixes.append("unsupported-status:" + m.group(0)[:40])
        text = rx.sub(lambda mm: mm.group(0) + " (include only if true for you)", text)
    if "[" in text or key in ("after", "strengths"):
        for m in _ACTIVITY.finditer(text):
            stems = _ACTIVITY_STEMS.get(m.group(1).lower(), ())
            if stems and not any(st in src for st in stems):
                fixes.append("unsupported-activity:" + m.group(0)[:40])
                if not text.startswith(_CONDITIONAL_PREFIX):
                    text = _CONDITIONAL_PREFIX + text
                break
    return text


def sanitize_with_source(value, source: str, fixes: list | None = None,
                         requirement_source: str | None = None,
                         requirement_keys=(), _key: str | None = None):
    """sanitize() plus source attribution scrubbing.

    ``source`` is the candidate's resume: the only evidence allowed for
    candidate-claim text. Keys named in ``requirement_keys`` (e.g. a match
    report's missing_keywords / gap fields) quote the job's requirements, so
    numbers there may be attributed to ``requirement_source`` (the JD) and are
    preserved as requirements, never treated as candidate achievements.
    """
    if fixes is None:
        fixes = []
    if isinstance(value, str):
        out, f = _scrub(value)
        fixes.extend(f)
        attr_source = source
        if requirement_source and (_key in requirement_keys or _REQ_CUE.search(out)):
            attr_source = source + "\n" + requirement_source
        out = _scrub_invented_metrics(out, attr_source, fixes)
        out = _scrub_unattributed_numbers(out, source, requirement_source, attr_source, fixes)
        out = _conditionalize_unsupported(out, source, _key, fixes)
        return out
    if isinstance(value, list):
        return [sanitize_with_source(v, source, fixes, requirement_source,
                                     requirement_keys, _key) for v in value]
    if isinstance(value, dict):
        return {k: sanitize_with_source(v, source, fixes, requirement_source,
                                        requirement_keys, k) for k, v in value.items()}
    return value
