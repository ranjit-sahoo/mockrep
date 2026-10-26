"""Regenerate app/static/coding-problems.json from app/coding.py.
The static pack lets the coding practice list and problem statements work offline
(served by the service worker). Evaluation and hints stay online-only.
Run after changing coding.py PROBLEMS/STARTERS; tests/test_coding_pack.py checks freshness."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import coding  # noqa: E402

pack = {"offline_note": "Offline copy: practice and statements work; AI review and hints need internet.",
        "problems": [coding.get(pid) for pid, *_ in coding.PROBLEMS]}
out = os.path.join(os.path.dirname(__file__), "..", "app", "static", "coding-problems.json")
with open(out, "w") as f:
    json.dump(pack, f, indent=1)
print("wrote", out, len(pack["problems"]), "problems", os.path.getsize(out), "bytes")
