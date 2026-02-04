"""
Per-run capture and run summary for the Test Harness.

Run dir: overlord_output, emulator_log, run_manifest.json, run_summary.json, artifacts/.
See roadmap/features/autonomous-test-bench.md §4.1 and §4.2.
"""
import json
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RunManifest:
    """Run manifest written to run_dir (run_manifest.json)."""

    run_id: str
    repo: str
    repo_created: bool
    timestamp: str  # ISO or human-readable


@dataclass
class RunSummary:
    """Machine-readable run summary for comparison (run_summary.json)."""

    run_id: str
    repo: str
    duration_sec: float
    exit_code: Optional[int] = None
    phase_reached: Optional[int] = None
    completion_signals_seen: List[str] = field(default_factory=list)
    artifacts_copied: List[str] = field(default_factory=list)


class RunCapture:
    """
    Collects Overlord output and emulator log for one run; finalize() writes run dir
    (overlord_output, emulator_log, run_manifest, run_summary, artifacts copy).
    """

    def __init__(
        self,
        run_dir: Path,
        run_id: str,
        repo_identifier: str,
        repo_created: bool,
        success_patterns: Optional[List[str]] = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.repo_identifier = repo_identifier
        self.repo_created = repo_created
        self.success_patterns = success_patterns or []
        self._overlord_output: List[str] = []
        self._emulator_log: List[Dict[str, Any]] = []
        self._start_time = time.time()

    def append_overlord_output(self, text: str) -> None:
        self._overlord_output.append(text)

    def log_emulator_turn(self, recent_output: str, reply: str) -> None:
        self._emulator_log.append({
            "recent_output_preview": recent_output[-2000:] if len(recent_output) > 2000 else recent_output,
            "reply": reply,
        })

    def finalize(
        self,
        overlord_state_dir: Optional[str] = None,
        exit_code: Optional[int] = None,
    ) -> RunSummary:
        """
        Write run dir files and copy artifacts. Returns RunSummary.
        """
        self.run_dir.mkdir(parents=True, exist_ok=True)
        full_output = "".join(self._overlord_output)
        (self.run_dir / "overlord_output.txt").write_text(full_output, encoding="utf-8")
        (self.run_dir / "emulator_log.jsonl").write_text(
            "\n".join(json.dumps(e) for e in self._emulator_log),
            encoding="utf-8",
        )
        duration_sec = time.time() - self._start_time
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._start_time))
        manifest = RunManifest(
            run_id=self.run_id,
            repo=self.repo_identifier,
            repo_created=self.repo_created,
            timestamp=timestamp,
        )
        (self.run_dir / "run_manifest.json").write_text(
            json.dumps(asdict(manifest), indent=2),
            encoding="utf-8",
        )
        completion_seen = [
            p for p in self.success_patterns
            if p in full_output
        ]
        artifacts_copied: List[str] = []
        if overlord_state_dir:
            state_path = Path(overlord_state_dir)
            projects_dir = state_path / "projects"
            dest_artifacts = self.run_dir / "artifacts"
            if projects_dir.is_dir():
                for proj in projects_dir.iterdir():
                    if proj.is_dir():
                        src_art = proj / "artifacts"
                        if src_art.is_dir():
                            dest_proj = dest_artifacts / proj.name
                            dest_proj.mkdir(parents=True, exist_ok=True)
                            for f in src_art.iterdir():
                                if f.is_file():
                                    shutil.copy2(f, dest_proj / f.name)
                                    artifacts_copied.append(f"{proj.name}/{f.name}")
        phase_reached = _infer_phase_from_artifacts(self.run_dir)
        summary = RunSummary(
            run_id=self.run_id,
            repo=self.repo_identifier,
            duration_sec=duration_sec,
            exit_code=exit_code,
            phase_reached=phase_reached,
            completion_signals_seen=completion_seen,
            artifacts_copied=artifacts_copied,
        )
        (self.run_dir / "run_summary.json").write_text(
            json.dumps(asdict(summary), indent=2),
            encoding="utf-8",
        )
        return summary


def _infer_phase_from_artifacts(run_dir: Path) -> Optional[int]:
    """Infer highest phase (0-4) from copied artifacts under run_dir/artifacts."""
    artifacts = run_dir / "artifacts"
    if not artifacts.is_dir():
        return None
    phase = 0
    for proj in artifacts.iterdir():
        if not proj.is_dir():
            continue
        for f in proj.iterdir():
            if not f.is_file():
                continue
            name = f.name
            if "workgraph" in name or "plan" in name:
                phase = max(phase, 2)
            if "phase_4" in name or "phase_3" in name:
                phase = max(phase, 4)
            if "phase_2" in name:
                phase = max(phase, 2)
            if "bootstrap" in name or "phase_0" in name or "phase_1" in name:
                phase = max(phase, 1)
    return phase if phase > 0 else None
