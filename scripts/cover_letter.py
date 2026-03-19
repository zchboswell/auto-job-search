#!/usr/bin/env python3
"""
Cover letter outline generator for high-scoring job listings.

Auto-triggered during daily scans when a listing's composite score exceeds
the threshold defined in config.yaml (default: 85).

This script handles the *analytical* part: matching JD keywords to the user's
evidence bank to identify which achievements are relevant. The actual cover
letter *writing* is done by the AI agent using the cover-letter skill, which
controls voice, tone, and structure.

Usage:
    python cover_letter.py <job_id>            # Print outline + matched themes
    python cover_letter.py <job_id> --dry-run  # Same as above, explicit dry-run
    python cover_letter.py <job_id> --force    # Override threshold check

Configuration: config.yaml (evidence_bank, cover_letter, scoring sections)
"""

import json, sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import (
    load_config, get_evidence_bank, get_keyword_map,
    get_cover_letter_config, get_scoring, db_path
)

TRIGGER_THRESHOLD = None  # Loaded from config


def get_threshold(config: dict = None) -> int:
    scoring = get_scoring(config)
    return scoring.get("cover_letter_threshold", 85)


def match_evidence_to_jd(jd_text: str, config: dict = None, max_themes: int = 4) -> list[str]:
    """Return ordered list of evidence theme keys that best match the JD text."""
    keyword_map = get_keyword_map(config)
    theme_hits: dict[str, int] = {}
    jd_lower = jd_text.lower()
    for keyword, theme in keyword_map.items():
        if keyword.lower() in jd_lower:
            theme_hits[theme] = theme_hits.get(theme, 0) + 1

    ranked = sorted(theme_hits.keys(), key=lambda t: theme_hits[t], reverse=True)
    return ranked[:max_themes]


def build_outline(listing: dict, jd_text: str, config: dict = None) -> dict:
    """Build a structured cover letter outline from listing + JD text."""
    evidence_bank = get_evidence_bank(config)
    themes = match_evidence_to_jd(jd_text, config)

    # Always include leadership/cross-functional if present and not already matched
    leadership_keys = [k for k in evidence_bank if "leadership" in k.lower() or "cross" in k.lower()]
    for lk in leadership_keys:
        if lk not in themes and len(themes) < 5:
            themes.append(lk)

    outline = {
        "company": listing.get("company", ""),
        "title": listing.get("title", ""),
        "date": datetime.now().strftime("%B %d, %Y"),
        "themes": themes,
        "evidence_blocks": [],
    }

    for theme_key in themes:
        if theme_key in evidence_bank:
            block = evidence_bank[theme_key]
            outline["evidence_blocks"].append({
                "theme": block.get("label", theme_key),
                "achievements": block.get("achievements", []),
            })

    return outline


def print_outline(outline: dict):
    """Print the letter outline for review."""
    print(f"\n  COVER LETTER OUTLINE")
    print(f"  {outline['title']} @ {outline['company']}")
    print(f"  Date: {outline['date']}")
    print(f"  ─────────────────────────────────────────")
    print(f"  Matched themes ({len(outline['themes'])}):")
    for i, block in enumerate(outline['evidence_blocks'], 1):
        print(f"    {i}. {block['theme']}")
        for ach in block['achievements']:
            claim = ach.get("claim", "")
            print(f"       → {claim}")
    print()


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    config = load_config()
    threshold = get_threshold(config)

    if len(sys.argv) < 2:
        print(f"Usage: cover_letter.py <job_id> [--dry-run] [--force]")
        print(f"  Auto-trigger threshold: composite ≥ {threshold}")
        sys.exit(1)

    jid = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    # Load listing from DB
    p = db_path()
    if not p.exists():
        print("No jobs database found. Run a scan first.")
        sys.exit(1)

    db = json.loads(p.read_text())
    if jid not in db["listings"]:
        print(f"Job ID {jid} not found in database.")
        sys.exit(1)

    listing = db["listings"][jid]
    comp = listing.get("fit_composite", 0)

    print(f"  Listing: {listing['title']} @ {listing['company']}")
    print(f"  Composite score: {comp}")

    if comp < threshold and not force:
        print(f"  Below auto-trigger threshold ({threshold}). Use --force to override.")
        sys.exit(0)

    # Use listing notes as JD text proxy
    jd_text = listing.get("notes", "") + " " + listing.get("title", "")

    outline = build_outline(listing, jd_text, config)
    print_outline(outline)

    if dry_run:
        print("  (Dry run — no document generated)")
        return

    print("  Outline ready. The AI agent uses this to write the cover letter")
    print("  following the voice principles in skills/cover-letter/SKILL.md.")


if __name__ == "__main__":
    main()
