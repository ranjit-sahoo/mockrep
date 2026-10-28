"""Practice Sessions: the committed pack must be fresh, complete and safe to show."""
import json
import os
import re
import sys

from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_practice_pack as bp  # noqa: E402
from app.main import app  # noqa: E402

PACK_PATH = os.path.join(ROOT, "app", "static", "practice-pack.json")


def _pack():
    with open(PACK_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_pack_is_in_sync_with_builder():
    built = json.loads(json.dumps(bp.build(), ensure_ascii=False, sort_keys=True))
    assert built == _pack(), "run: python scripts/build_practice_pack.py"


def test_every_role_has_enough_questions_with_answers():
    p = _pack()
    assert len(p["roles"]) >= 33
    group_ids = {g["id"] for g in p["groups"]}
    ids = set()
    for r in p["roles"]:
        assert r["id"] not in ids
        ids.add(r["id"])
        assert r["group"] in group_ids and r["blurb"] and r["keys"]
        assert len(r["qs"]) >= 10, r["name"]
        assert len(set(r["qs"])) == len(r["qs"])
        for qid in r["qs"]:
            q = p["qs"][qid]
            assert q["q"].strip().endswith(("?", ".", ")")), q["q"]
            assert len(q["a"]) >= 25 or q["q"] == "Do you have any questions for us?", q
            assert q["t"] in ("technical", "behavioral", "scenario")
            assert q["l"] in ("easy", "medium", "hard")


def test_requested_roles_exist():
    names = {r["name"] for r in _pack()["roles"]}
    for need in ("Data Entry / Back Office", "Java Developer", "Data Scientist", "Business Analyst", "Hotel & Hospitality"):
        assert need in names
    hotel = next(r for r in _pack()["roles"] if r["name"] == "Hotel & Hospitality")
    assert "receptionist" in hotel["keys"]


def test_no_dashes_or_markup_in_content():
    raw = open(PACK_PATH, encoding="utf-8").read()
    assert "\u2014" not in raw
    for q in _pack()["qs"].values():
        assert not re.search(r"</?(script|iframe|style|img|a|b|i|p|div|span|svg|object)\b", q["a"] + q.get("w", "") + q.get("h", ""), re.I), q


def test_pack_served_and_cached_by_service_worker():
    c = TestClient(app)
    r = c.get("/static/practice-pack.json")
    assert r.status_code == 200 and r.json()["roles"]
    assert c.get("/static/sessions.js").status_code == 200
    sw = c.get("/sw.js").text
    assert "/static/practice-pack.json" in sw and "/static/sessions.js" in sw
    html = c.get("/").text
    assert 'data-v="sessions"' in html and "/static/sessions.js" in html


def test_report_kind_accepted():
    c = TestClient(app, headers={"origin": "http://testserver"})
    r = c.post("/api/content-report", json={"kind": "practice-session", "reason": "typo", "excerpt": "Tell me about yourself."})
    assert r.status_code == 200 and r.json()["ok"]
