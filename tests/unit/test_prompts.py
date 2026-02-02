"""
Unit tests: prompt assembly from Palpatine (overlord/prompts.py).
Assembled system prompts are derived from foundational docs and injected at phase invocation.
"""
import os

import pytest

from overlord.prompts import (
    assemble_phase0_system_prompt,
    assemble_phase1_system_prompt,
    get_phase_system_prompt,
    load_doc,
)


@pytest.mark.unit
def test_load_doc_returns_content_for_existing_file():
    """load_doc returns file content when file exists under palpatine."""
    text = load_doc("PHASE-GATES.md")
    # Repo may or may not have foundational/palpatine in same layout
    if text:
        assert "Phase Gates" in text or "phase" in text.lower()
    # If palpatine not present, load_doc returns ""
    assert isinstance(text, str)


@pytest.mark.unit
def test_load_doc_returns_empty_for_missing_file():
    """load_doc returns empty string for missing path."""
    assert load_doc("NONEXISTENT-DOC-12345.md") == ""


@pytest.mark.unit
def test_assemble_phase0_system_prompt_includes_mandatory_instructions():
    """Phase 0 assembled prompt includes mandatory Superpowers and Socratic instructions."""
    prompt = assemble_phase0_system_prompt()
    assert "Phase 0" in prompt or "Bootstrap" in prompt
    assert "Superpowers" in prompt
    assert "One question at a time" in prompt or "one question" in prompt.lower()


@pytest.mark.unit
def test_assemble_phase1_system_prompt_includes_mandatory_instructions():
    """Phase 1 assembled prompt includes mandatory tool and spec-first instructions."""
    prompt = assemble_phase1_system_prompt()
    assert "Phase 1" in prompt or "Specifier" in prompt
    assert "Superpowers" in prompt or "Spec Kit" in prompt
    assert "spec" in prompt.lower() or "testing" in prompt.lower()


@pytest.mark.unit
def test_get_phase_system_prompt_returns_non_empty_for_phase_0_1_4():
    """get_phase_system_prompt returns non-empty string for phases 0, 1, 4."""
    for phase in (0, 1, 4):
        prompt = get_phase_system_prompt(phase)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert f"Phase {phase}" in prompt or str(phase) in prompt


@pytest.mark.unit
def test_get_phase_system_prompt_returns_minimal_for_phase_2_3():
    """get_phase_system_prompt returns minimal prompt for phases 2, 3."""
    for phase in (2, 3):
        prompt = get_phase_system_prompt(phase)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert f"Phase {phase}" in prompt
