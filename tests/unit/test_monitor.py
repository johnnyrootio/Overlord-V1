"""Unit tests: status snapshot and gather_status (stub)."""
import pytest

from overlord.monitor import StatusSnapshot, gather_status, _parse_check_worker_status_output


@pytest.mark.unit
def test_gather_status_returns_snapshot():
    """gather_status returns a StatusSnapshot (stub when multiclaude not available)."""
    snap = gather_status("proj", "/tmp/state", repo_name=None)
    assert isinstance(snap, StatusSnapshot)
    assert snap.workers == []
    assert snap.health in ("stub", "ok", "daemon_down")


@pytest.mark.unit
def test_status_snapshot_has_expected_fields():
    """StatusSnapshot has workers, issues_in_progress, liveness, health."""
    snap = StatusSnapshot(workers=["w1"], issues_in_progress=["#1"], liveness="ok", health="ok")
    assert snap.workers == ["w1"]
    assert snap.issues_in_progress == ["#1"]
    assert snap.liveness == "ok"
    assert snap.health == "ok"


@pytest.mark.unit
def test_status_snapshot_has_extended_fields():
    """StatusSnapshot has active_workers, processes_summary, resource_usage, repo_changes."""
    snap = StatusSnapshot(
        active_workers=["w1"],
        processes_summary="2 Claude process(es)",
        resource_usage={"cpu_pct": 5.0, "mem_pct": 10.0, "disk_mb": 100},
        repo_changes=["src/math.py"],
    )
    assert snap.active_workers == ["w1"]
    assert snap.processes_summary == "2 Claude process(es)"
    assert snap.resource_usage == {"cpu_pct": 5.0, "mem_pct": 10.0, "disk_mb": 100}
    assert snap.repo_changes == ["src/math.py"]


@pytest.mark.unit
def test_parse_check_worker_status_output():
    """_parse_check_worker_status_output parses script key=value and LIVENESS line."""
    out = """WORKERS=w1,w2
ACTIVE_WORKERS=w1
PROCESS_COUNT=2
CPU_PCT=12.5
MEM_PCT=3.2
DISK_MB=50
REPO_CHANGES=src/math.py,tests/test_math.py
LIVENESS: 1 active of 2 workers; 2 Claude process(es); CPU 12.5% MEM 3.2%; disk 50MB
"""
    parsed = _parse_check_worker_status_output(out)
    assert parsed["active_workers"] == ["w1"]
    assert parsed["processes_summary"] == "2 Claude process(es)"
    assert parsed["resource_usage"] == {"cpu_pct": 12.5, "mem_pct": 3.2, "disk_mb": 50}
    assert parsed["repo_changes"] == ["src/math.py", "tests/test_math.py"]
    assert "LIVENESS:" in parsed["liveness"]
