"""Regression: recruiter candidate rows must be scoped so generic .cand cards
(question bank, prep, coding, history) cannot break candidate collection."""


def test_candidate_queries_scoped_to_cands_container():
    src = open("app/static/app.js").read()
    assert "querySelectorAll('#cands .candRow')" in src
    assert "document.querySelectorAll('.cand')" not in src
    assert "d.className='cand candRow'" in src
