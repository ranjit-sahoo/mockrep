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
    (re.compile(r"\bemployers cannot\b", re.I), "not all employers will"),
    (re.compile(r"\bcannot (?:consider|interview|hire|advance)\b", re.I), "may not always consider"),
    (re.compile(r"\bwill not (?:advance|consider|interview|hire)\b", re.I), "may not advance"),
    (re.compile(r"\bmandatory\b", re.I), "often requested"),
    (re.compile(r"\bmust[- ]have\b", re.I), "typically expected"),
    (re.compile(r"\bmeets? (?:the )?minimum (?:education )?requirement", re.I), "is typically part of what is asked for"),
    # Unsupported causal certainty about recruiter behavior.
    (re.compile(r"\bforces? (?:them|employers|recruiters|hiring managers) to assume\b", re.I), "may lead them to assume"),
    (re.compile(r"\bauto-?reject\w*\b", re.I), "rejection"),
    (re.compile(r"\b(?:often |always )?leads? to rejection\b", re.I), "can hurt the application"),
    (re.compile(r"\bguarantee[sd]?\b", re.I), "may improve the odds of"),
    (re.compile(r"=\s*lower ranking", re.I), "which can lower ranking"),
    (re.compile(r"\bwill be (?:rejected|filtered out|screened out)\b", re.I), "may be filtered out"),
    (re.compile(r"\bwill not (?:pass|get|clear)\b", re.I), "may not pass"),
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
# exact number does not appear anywhere in the candidate's own resume or the
# job description, the model invented it; replace the number (and only the
# number) with a conditional placeholder, keeping the sentence structure.
_METRIC = re.compile(
    r"(?P<num>\d+(?:\.\d+)?\+?)(?P<unit>\s*(?:%|percent)\s*(?:CSAT|FCR|QA|AHT|SLA|accuracy|save rate|retention|pass rate|first-call-resolution)[\w-]*"
    r"|\s*(?:CSAT|FCR|QA|AHT|SLA|WPM|NPS)"
    r"|\s*(?:new hires|calls/day|calls per day|patients|beds|students|joiners)\b)",
    re.I)
_PLACEHOLDER = "[add your number - only if you know it]"


_WINDOW = 60


def _attributed(num: str, unit: str, source: str) -> bool:
    """True only if the resume itself pairs this number with this metric.

    The JD is not evidence of candidate achievement, and an unrelated number
    elsewhere in the resume is not either: require the number within _WINDOW
    chars of one of the metric's keywords in the source text.
    """
    keywords = [w for w in re.findall(r"[a-z][a-z-]{2,}", unit.lower())
                if w not in ("percent", "per", "rate", "new")]
    synonyms = {"hires": ("joiners",), "joiners": ("hires",)}
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
        if _attributed(num.rstrip("+"), m.group("unit"), source):
            return m.group(0)
        fixes.append("invented-metric:" + m.group(0)[:40])
        return _PLACEHOLDER + m.group("unit")

    return _METRIC.sub(_sub, text)


def sanitize_with_source(value, source: str, fixes: list | None = None):
    """sanitize() plus invented-metric scrubbing against the source documents."""
    if fixes is None:
        fixes = []
    if isinstance(value, str):
        out, f = _scrub(value)
        fixes.extend(f)
        out = _scrub_invented_metrics(out, source, fixes)
        return out
    if isinstance(value, list):
        return [sanitize_with_source(v, source, fixes) for v in value]
    if isinstance(value, dict):
        return {k: sanitize_with_source(v, source, fixes) for k, v in value.items()}
    return value
