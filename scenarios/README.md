# Scenarios

YAML scenario files for scripted runs. See ROADMAP-V1.md C8–C10.

**Format:**
- `spec_path`: path to genesis spec (relative to CWD or absolute)
- `project_id`: optional; if omitted, derived from spec basename
- `gate_responses`: list of answers fed when Overlord blocks (one per gate)

**Run:** `overlord scenario <path> [--state-dir DIR]`

Example: `scenarios/example-gate1.yaml`
