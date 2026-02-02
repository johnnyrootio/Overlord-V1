"""
Integration test: start with spec path then list (stub path; no persistence yet).
When persistence exists (C4), list will show the project.
"""
import os
import tempfile

import pytest
from click.testing import CliRunner

from overlord.cli import cli


@pytest.mark.integration
def test_start_then_list_exits_cleanly():
    """Start with a temp spec file then list; both exit 0 (stub: list shows no projects)."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(b"# Example spec\n")
        spec_path = f.name
    try:
        start_result = runner.invoke(cli, ["start", spec_path])
        assert start_result.exit_code == 0, start_result.output
        list_result = runner.invoke(cli, ["list"])
        assert list_result.exit_code == 0, list_result.output
    finally:
        os.unlink(spec_path)
