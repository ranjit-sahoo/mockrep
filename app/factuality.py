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
