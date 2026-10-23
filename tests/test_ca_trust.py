"""Render eMudhra CA-compromise advisory (Oct 2026): keep CA bundles patched."""


def test_certifi_pinned_to_patched_version():
    reqs = open("requirements.txt").read()
    assert "certifi>=2026.10.19" in reqs


def test_dockerfile_updates_system_ca_store():
    d = open("Dockerfile").read()
    assert "ca-certificates" in d
