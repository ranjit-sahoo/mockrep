"""Render eMudhra CA-compromise advisory (Oct 2026): keep CA bundles patched."""


def test_certifi_pinned_to_patched_version():
    reqs = open("requirements.txt").read()
    assert "certifi>=2026.10.19" in reqs


def test_dockerfile_updates_system_ca_store():
    d = open("Dockerfile").read()
    assert "ca-certificates" in d


def test_dockerfile_bootstraps_fixed_pip_with_official_hash():
    d = open("Dockerfile").read()
    assert "pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70" in d
