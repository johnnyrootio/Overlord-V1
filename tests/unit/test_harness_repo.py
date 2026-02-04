"""Unit tests for Test Harness repo resolution (repo_url path, no gh)."""
import pytest

from test_harness.scenario import Scenario
from test_harness.repo import ResolvedRepo, resolve_repo, _url_to_identifier


def _scenario(repo_name=None, repo_url=None, repo_create=True):
    return Scenario(
        goals="x",
        greenfield_spec="/tmp/spec.md",
        repo_name=repo_name,
        repo_url=repo_url,
        repo_create=repo_create,
    )


@pytest.mark.unit
def test_resolve_repo_with_repo_url():
    """When scenario has repo_url, resolve_repo returns it without calling gh."""
    s = _scenario(repo_url="https://github.com/owner/repo-name")
    r = resolve_repo(s, run_id="run-1")
    assert isinstance(r, ResolvedRepo)
    assert r.repo_created is False
    assert r.identifier == "owner/repo-name"
    assert "owner" in r.repo_url and "repo-name" in r.repo_url


@pytest.mark.unit
def test_url_to_identifier():
    assert _url_to_identifier("https://github.com/foo/bar") == "foo/bar"
    assert _url_to_identifier("https://github.com/foo/bar.git") == "foo/bar"
    assert _url_to_identifier("https://github.com/u/r/") == "u/r"
