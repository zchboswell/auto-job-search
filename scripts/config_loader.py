#!/usr/bin/env python3
"""
Central config loader for the job search pipeline.

All scripts import from here. Reads config.yaml from the project root.
Falls back to config.example.yaml if config.yaml doesn't exist.
"""

import sys
from pathlib import Path

# Try to import yaml; if not available, provide a helpful error
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "config.example.yaml"


def load_config() -> dict:
    """Load the user's config.yaml, falling back to the example config."""
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text())
    elif EXAMPLE_CONFIG_PATH.exists():
        print("WARNING: No config.yaml found. Using config.example.yaml.")
        print("Run 'python scripts/setup.py' to create your config.")
        return yaml.safe_load(EXAMPLE_CONFIG_PATH.read_text())
    else:
        print("ERROR: No config.yaml or config.example.yaml found.")
        print("Run 'python scripts/setup.py' to get started.")
        sys.exit(1)


def get_profile(config: dict = None) -> dict:
    """Get the user profile section."""
    config = config or load_config()
    return config.get("profile", {})


def get_scoring(config: dict = None) -> dict:
    """Get the scoring configuration."""
    config = config or load_config()
    return config.get("scoring", {})


def get_dimensions(config: dict = None) -> dict:
    """Get scoring dimensions with weights and rubrics."""
    scoring = get_scoring(config)
    return scoring.get("dimensions", {})


def get_weights(config: dict = None) -> dict[str, float]:
    """Get dimension weights as a flat dict."""
    dims = get_dimensions(config)
    return {k: v.get("weight", 0) for k, v in dims.items()}


def get_tiers(config: dict = None) -> dict:
    """Get tier thresholds."""
    scoring = get_scoring(config)
    return scoring.get("tiers", {"top": 80, "strong": 60, "worth_a_look": 40, "stretch": 25})


def get_evidence_bank(config: dict = None) -> dict:
    """Get the evidence bank for cover letter generation."""
    config = config or load_config()
    return config.get("evidence_bank", {})


def get_keyword_map(config: dict = None) -> dict[str, str]:
    """Build a keyword -> theme mapping from the evidence bank."""
    bank = get_evidence_bank(config)
    mapping = {}
    for theme_key, theme_data in bank.items():
        for kw in theme_data.get("keywords", []):
            mapping[kw] = theme_key
    return mapping


def get_target(config: dict = None) -> dict:
    """Get target role preferences."""
    config = config or load_config()
    return config.get("target", {})


def get_location_config(config: dict = None) -> dict:
    """Get location preferences."""
    config = config or load_config()
    return config.get("location", {})


def get_linkedin_settings(config: dict = None) -> dict:
    """Get LinkedIn search settings."""
    config = config or load_config()
    return config.get("linkedin", {})


def get_cover_letter_config(config: dict = None) -> dict:
    """Get cover letter style preferences."""
    config = config or load_config()
    return config.get("cover_letter", {})


def get_report_settings(config: dict = None) -> dict:
    """Get report generation settings."""
    config = config or load_config()
    return config.get("reports", {})


# ── Convenience: project paths ──────────────────────────────

def data_dir() -> Path:
    return PROJECT_ROOT / "data"


def outputs_dir() -> Path:
    return PROJECT_ROOT / "outputs"


def resources_dir() -> Path:
    return PROJECT_ROOT / "resources"


def db_path() -> Path:
    return data_dir() / "jobs.json"


def ensure_dirs():
    """Create all required directories if they don't exist."""
    for d in [data_dir(), outputs_dir(), resources_dir(),
              outputs_dir() / "reports", outputs_dir() / "cover-letters",
              outputs_dir() / "interview-prep"]:
        d.mkdir(parents=True, exist_ok=True)
