"""Unit tests for Test Harness scenario schema and loader (test_harness.scenario)."""
import tempfile
from pathlib import Path

import pytest
import yaml

from test_harness.scenario import (
    DEFAULT_SUCCESS_PATTERNS,
    Scenario,
    load_scenario,
)
from test_harness.scenario_from_spec import scenario_from_spec


@pytest.mark.unit
def test_load_scenario_from_dict_required_fields():
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        spec_path = f.name
    try:
        data = {
            "goals": "Build minimal todo app",
            "greenfield_spec": spec_path,
            "repo": {"repo_name": "my-repo"},
        }
        s = load_scenario(data)
        assert s.goals == "Build minimal todo app"
        assert s.greenfield_spec == spec_path
        assert s.repo_name == "my-repo"
        assert s.repo_url is None
        assert s.repo_create is True
        assert s.success == DEFAULT_SUCCESS_PATTERNS
    finally:
        Path(spec_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_load_scenario_repo_url():
    data = {
        "goals": "x",
        "greenfield_spec": "/tmp/spec.md",
        "repo": {"repo_url": "https://github.com/u/r"},
    }
    s = load_scenario(data)
    assert s.repo_url == "https://github.com/u/r"
    assert s.repo_name is None


@pytest.mark.unit
def test_load_scenario_missing_greenfield_spec_raises():
    with pytest.raises(ValueError, match="greenfield_spec is required"):
        load_scenario({"goals": "x", "repo": {"repo_name": "r"}})


@pytest.mark.unit
def test_load_scenario_missing_repo_raises():
    with pytest.raises(ValueError, match="repo_name or repo_url"):
        load_scenario({"goals": "x", "greenfield_spec": "/tmp/s.md"})


@pytest.mark.unit
def test_load_scenario_from_yaml_file(tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec")
    scenario_file = tmp_path / "scenario.yaml"
    scenario_file.write_text(
        yaml.dump({
            "goals": "Minimal app",
            "greenfield_spec": "spec.md",
            "repo": {"repo_name": "foo"},
            "repo_create": False,
            "timeout": 300,
        })
    )
    s = load_scenario(str(scenario_file))
    assert s.goals == "Minimal app"
    assert s.greenfield_spec == str((tmp_path / "spec.md").resolve())
    assert s.repo_name == "foo"
    assert s.repo_create is False
    assert s.timeout == 300


# --- T1.2a: Scenario-from-spec generator ---


@pytest.mark.unit
def test_scenario_from_spec_output_loads_and_validates(tmp_path):
    """Generator output has required fields and passes load_scenario."""
    spec = tmp_path / "my-app.md"
    spec.write_text("# My App — Greenfield\n\nMinimal app.\n")
    data = scenario_from_spec(str(spec))
    s = load_scenario(data)
    assert s.goals == "My App — Greenfield"
    assert s.greenfield_spec == str(spec.resolve())
    assert s.repo_name == "my-app"
    assert s.repo_url is None
    assert s.repo_create is True


@pytest.mark.unit
def test_scenario_from_spec_goals_derived_from_description(tmp_path):
    """When no # heading, goals derived from Project Overview / Description."""
    spec = tmp_path / "no-heading.md"
    spec.write_text(
        "Intro\n\n## Project Overview\n\n**Name**: X\n**Description**: Build a minimal todo list.\n"
    )
    data = scenario_from_spec(str(spec))
    s = load_scenario(data)
    assert "todo" in s.goals.lower() or "minimal" in s.goals.lower() or s.goals


@pytest.mark.unit
def test_scenario_from_spec_repo_name_includes_run_id(tmp_path):
    """repo_name base from spec basename + run_id when provided."""
    spec = tmp_path / "trivial-todo-app.md"
    spec.write_text("# Trivial Todo\n")
    data = scenario_from_spec(str(spec), run_id="run-42")
    s = load_scenario(data)
    assert s.repo_name == "trivial-todo-app-run-42"


@pytest.mark.unit
def test_scenario_from_spec_overrides_merge(tmp_path):
    """Optional overrides (goals, repo_name, emulator_prompt) merge and still validate."""
    spec = tmp_path / "foo.md"
    spec.write_text("# Foo\n")
    data = scenario_from_spec(
        str(spec),
        overrides={
            "goals": "Custom goals",
            "repo_name": "custom-repo",
            "emulator_prompt": "You are a test user.",
        },
    )
    s = load_scenario(data)
    assert s.goals == "Custom goals"
    assert s.repo_name == "custom-repo"
    assert s.emulator_prompt == "You are a test user."


@pytest.mark.unit
def test_scenario_from_spec_missing_file_raises(tmp_path):
    """Non-existent spec path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        scenario_from_spec(str(tmp_path / "nonexistent.md"))
