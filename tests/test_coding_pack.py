"""The static offline coding pack must stay in sync with coding.py."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import coding  # noqa: E402

PACK = os.path.join(os.path.dirname(__file__), "..", "app", "static", "coding-problems.json")


def test_pack_matches_source():
    with open(PACK) as f:
        pack = json.load(f)
    by_id = {p["id"]: p for p in pack["problems"]}
    assert len(by_id) == len(coding.PROBLEMS)
    for pid, *_ in coding.PROBLEMS:
        assert by_id[pid] == coding.get(pid), pid
