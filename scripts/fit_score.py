#!/usr/bin/env python3
"""
Configurable job-fit scoring system.

Produces a 0-100 composite score across user-defined dimensions (each 0-10).
Dimensions, weights, rubrics, and tier thresholds are all read from config.yaml.

Usage:
    python fit_score.py rubric           # Show the full scoring rubric
    python fit_score.py score            # Score a listing interactively
    python fit_score.py batch <file>     # Batch-score from a JSON file
"""

import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config, get_dimensions, get_tiers, get_profile


def composite_score(scores: dict[str, int], dimensions: dict = None) -> float:
    """Compute weighted composite score (0-100) from dimension scores (each 0-10)."""
    if dimensions is None:
        dimensions = get_dimensions()
    total = 0.0
    for key, dim in dimensions.items():
        s = scores.get(key, 0)
        total += dim.get("weight", 0) * s
    return round(total * 10, 1)


def tier_from_score(score: float, tiers: dict = None) -> str:
    """Map composite score to a human-readable tier label."""
    if tiers is None:
        tiers = get_tiers()
    if score >= tiers.get("top", 80):
        return "top"
    elif score >= tiers.get("strong", 60):
        return "strong"
    elif score >= tiers.get("worth_a_look", 40):
        return "worth_a_look"
    elif score >= tiers.get("stretch", 25):
        return "stretch"
    else:
        return "skip"


def format_scorecard(scores: dict[str, int], title: str = "",
                     dimensions: dict = None, tiers: dict = None) -> str:
    """Pretty-print a scorecard."""
    if dimensions is None:
        dimensions = get_dimensions()
    if tiers is None:
        tiers = get_tiers()
    comp = composite_score(scores, dimensions)
    tier = tier_from_score(comp, tiers)
    lines = []
    if title:
        lines.append(f"  {title}")
        lines.append(f"  {'─' * len(title)}")
    for key, dim in dimensions.items():
        s = scores.get(key, 0)
        bar = "█" * s + "░" * (10 - s)
        label = dim.get("label", key)
        weight = dim.get("weight", 0)
        lines.append(f"  {label:<22} {bar} {s}/10  (×{weight:.0%})")
    lines.append(f"  {'─' * 50}")
    lines.append(f"  Composite: {comp:.0f}/100 → {tier.upper()}")
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────

def print_rubric():
    """Print the full scoring rubric for reference."""
    config = load_config()
    dimensions = get_dimensions(config)
    profile = get_profile(config)
    tiers = get_tiers(config)

    name = profile.get("name", "User")
    comp = profile.get("current_comp", {})
    location = profile.get("location", "Not set")

    print("=" * 60)
    print(f"  FIT SCORE RUBRIC — {name}")
    if comp:
        base = comp.get("base_salary", "?")
        total = comp.get("total_comp_estimate", "?")
        print(f"  Current comp: ~${base:,} base (≈${total:,} total)")
    print(f"  Location: {location}")
    print("=" * 60)
    for key, dim in dimensions.items():
        label = dim.get("label", key)
        desc = dim.get("description", "")
        weight = dim.get("weight", 0)
        print(f"\n  {label} (weight: {weight:.0%})")
        print(f"  {desc}")
        print(f"  {'─' * 50}")
        rubric = dim.get("rubric", {})
        for score_val in sorted(rubric.keys(), reverse=True):
            print(f"    {score_val:>2}: {rubric[score_val]}")

    thresholds = []
    for tier_name in ["top", "strong", "worth_a_look", "stretch"]:
        if tier_name in tiers:
            thresholds.append(f"≥{tiers[tier_name]} {tier_name.upper().replace('_', ' ')}")
    thresholds.append(f"<{tiers.get('stretch', 25)} SKIP")
    print(f"\n  Tier thresholds: {' | '.join(thresholds)}")
    print()


def interactive_score():
    """Walk through scoring a single listing."""
    config = load_config()
    dimensions = get_dimensions(config)
    tiers = get_tiers(config)

    title = input("Job title & company: ")
    scores = {}
    for key, dim in dimensions.items():
        label = dim.get("label", key)
        desc = dim.get("description", "")
        print(f"\n  {label} — {desc}")
        rubric = dim.get("rubric", {})
        for sv in sorted(rubric.keys(), reverse=True):
            print(f"    {sv:>2}: {rubric[sv]}")
        while True:
            try:
                val = int(input(f"  Score (0–10): "))
                if 0 <= val <= 10:
                    scores[key] = val
                    break
            except ValueError:
                pass
            print("  Enter an integer 0–10.")
    print()
    print(format_scorecard(scores, title, dimensions, tiers))
    return scores


def batch_score(path: str):
    """Score listings from a JSON file. Each entry needs a 'scores' dict."""
    config = load_config()
    dimensions = get_dimensions(config)
    tiers = get_tiers(config)
    data = json.loads(Path(path).read_text())
    for entry in data:
        scores = entry.get("scores", {})
        title = f"{entry.get('title', '?')} @ {entry.get('company', '?')}"
        print(format_scorecard(scores, title, dimensions, tiers))
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: fit_score.py <rubric|score|batch> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "rubric":
        print_rubric()
    elif cmd == "score":
        interactive_score()
    elif cmd == "batch":
        batch_score(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
