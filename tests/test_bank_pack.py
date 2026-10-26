"""The static offline question-bank pack must stay in sync with bank.py."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import bank  # noqa: E402

PACK = os.path.join(os.path.dirname(__file__), "..", "app", "static", "bank-common.json")


def test_pack_matches_source():
    with open(PACK) as f:
        pack = json.load(f)
    assert pack["roles"] == bank.roles()
    assert pack["general"] == bank._fmt(bank.GENERAL)
    assert set(pack["by_role"]) == set(bank.roles())
    for role in bank.roles():
        assert pack["by_role"][role] == bank._fmt(list(bank._B[role])), role
    assert pack["offline_note"]
