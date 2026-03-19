#!/usr/bin/env python3
"""
JSON-based job-tracking database for the LinkedIn search pipeline.

Stores listings, detects new vs. reposted jobs, tracks pipeline status,
manages fit scores, and surfaces trends. All configuration is read from
config.yaml via config_loader.

Data lives in data/jobs.json (relative to project root).

Usage:
    python jobs_db.py add      <json_file>   # Bulk-add listings; print new vs updated counts
    python jobs_db.py new      <json_file>   # Add listings; print only genuinely new ones
    python jobs_db.py trends                 # Print trend summary and observations
    python jobs_db.py dump                   # Dump all rows as JSON
    python jobs_db.py observe  <text...>     # Save a manual observation
    python jobs_db.py status   <job_id> <s>  # Set status (new/applied/screen/interview/offer/rejected/ghosted/skipped/expired)
    python jobs_db.py fscore   <job_id> <scores...>  # Set fit scores (one int per dimension, 0-10)
    python jobs_db.py pipeline               # Print application pipeline summary
    python jobs_db.py event    <job_id> <type> [note...]  # Log a pipeline event
"""

import json, sys, os
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config, get_dimensions, get_tiers, db_path, ensure_dirs
from fit_score import composite_score, tier_from_score, format_scorecard


def load_db() -> dict:
    """Load or initialize the database."""
    p = db_path()
    if p.exists():
        return json.loads(p.read_text())
    return {"listings": {}, "observations": []}


def save_db(db: dict):
    ensure_dirs()
    db_path().write_text(json.dumps(db, indent=2))


def upsert_listing(db: dict, row: dict) -> str:
    """Insert or update a listing. Returns 'new' or 'seen_before'."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    jid = str(row["linkedin_job_id"])

    if jid in db["listings"]:
        db["listings"][jid]["last_seen"] = today
        db["listings"][jid]["times_seen"] = db["listings"][jid].get("times_seen", 1) + 1
        return "seen_before"
    else:
        db["listings"][jid] = {
            "linkedin_job_id": jid,
            "title": row.get("title", ""),
            "company": row.get("company", ""),
            "location": row.get("location", ""),
            "salary_min": row.get("salary_min"),
            "salary_max": row.get("salary_max"),
            "url": row.get("url", ""),
            "fit_tier": row.get("fit_tier", ""),
            "fit_scores": row.get("fit_scores"),
            "fit_composite": row.get("fit_composite"),
            "first_seen": today,
            "last_seen": today,
            "times_seen": 1,
            "status": "new",
            "notes": row.get("notes", ""),
            "events": [],
        }
        return "new"


def add_observation(db: dict, note: str):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    db["observations"].append({"date": today, "note": note})


def get_trends(db: dict) -> list[str]:
    """Generate automatic trend observations."""
    trends = []
    listings = list(db["listings"].values())

    trends.append(f"Total unique listings tracked: {len(listings)}")

    co_counts = Counter(l["company"] for l in listings)
    top = co_counts.most_common(5)
    if top:
        parts = [f"{co} ({n})" for co, n in top]
        trends.append(f"Top hiring companies: {', '.join(parts)}")

    with_sal = [l for l in listings if l.get("salary_min") is not None]
    if with_sal:
        lo = min(l["salary_min"] for l in with_sal)
        hi = max(l["salary_max"] for l in with_sal if l.get("salary_max") is not None)
        avg_lo = sum(l["salary_min"] for l in with_sal) / len(with_sal)
        avg_hi_list = [l["salary_max"] for l in with_sal if l.get("salary_max") is not None]
        avg_hi = sum(avg_hi_list) / len(avg_hi_list) if avg_hi_list else avg_lo
        trends.append(
            f"Salary range: ${lo:,.0f}–${hi:,.0f} "
            f"(avg band ${avg_lo:,.0f}–${avg_hi:,.0f})"
        )

    tier_counts = Counter(l.get("fit_tier", "unset") for l in listings)
    trends.append(f"Fit tiers: {dict(tier_counts)}")

    status_counts = Counter(l.get("status", "new") for l in listings)
    trends.append(f"Statuses: {dict(status_counts)}")

    reposts = [l for l in listings if l.get("times_seen", 1) >= 3]
    reposts.sort(key=lambda l: l["times_seen"], reverse=True)
    if reposts:
        parts = [f"{r['title']} @ {r['company']} (seen {r['times_seen']}x)" for r in reposts]
        trends.append(f"Frequently reposted (possible hard-to-fill): {'; '.join(parts)}")

    week_counts = Counter()
    for l in listings:
        fs = l.get("first_seen", "")
        if fs:
            try:
                d = datetime.strptime(fs, "%Y-%m-%d")
                week_counts[d.strftime("%Y-W%V")] += 1
            except ValueError:
                pass
    if len(week_counts) > 1:
        trends.append("Listings by week first seen:")
        for wk in sorted(week_counts):
            trends.append(f"  {wk}: {week_counts[wk]} new")

    obs = db.get("observations", [])
    if obs:
        trends.append("--- Recent observations ---")
        for o in obs[-10:]:
            trends.append(f"  [{o['date']}] {o['note']}")

    return trends


# ── CLI ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: jobs_db.py <add|new|trends|dump|observe|status|fscore|pipeline|event> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    db = load_db()
    config = load_config()
    dimensions = get_dimensions(config)
    tiers = get_tiers(config)
    dim_keys = list(dimensions.keys())

    if cmd == "add":
        data = json.loads(Path(sys.argv[2]).read_text())
        new_count = 0
        for row in data:
            result = upsert_listing(db, row)
            if result == "new":
                new_count += 1
        save_db(db)
        print(json.dumps({"added_new": new_count, "updated": len(data) - new_count}))

    elif cmd == "new":
        data = json.loads(Path(sys.argv[2]).read_text())
        new_ids = []
        for row in data:
            result = upsert_listing(db, row)
            if result == "new":
                new_ids.append(str(row["linkedin_job_id"]))
        save_db(db)
        new_listings = [r for r in data if str(r["linkedin_job_id"]) in new_ids]
        print(json.dumps(new_listings, indent=2))

    elif cmd == "trends":
        for line in get_trends(db):
            print(line)

    elif cmd == "dump":
        print(json.dumps(list(db["listings"].values()), indent=2))

    elif cmd == "observe":
        note = " ".join(sys.argv[2:])
        add_observation(db, note)
        save_db(db)
        print("Observation saved.")

    elif cmd == "status":
        jid = sys.argv[2]
        new_status = sys.argv[3]
        if jid in db["listings"]:
            db["listings"][jid]["status"] = new_status
            save_db(db)
            print(f"Updated {jid} → {new_status}")
        else:
            print(f"Job ID {jid} not found.")
            sys.exit(1)

    elif cmd == "fscore":
        jid = sys.argv[2]
        score_values = sys.argv[3:3 + len(dim_keys)]
        if len(score_values) != len(dim_keys):
            print(f"Expected {len(dim_keys)} scores for dimensions: {', '.join(dim_keys)}")
            print(f"Got {len(score_values)} values.")
            sys.exit(1)
        scores = {k: int(v) for k, v in zip(dim_keys, score_values)}
        if jid in db["listings"]:
            db["listings"][jid]["fit_scores"] = scores
            comp = composite_score(scores, dimensions)
            db["listings"][jid]["fit_composite"] = comp
            db["listings"][jid]["fit_tier"] = tier_from_score(comp, tiers)
            save_db(db)
            title = f"{db['listings'][jid]['title']} @ {db['listings'][jid]['company']}"
            print(format_scorecard(scores, title, dimensions, tiers))
        else:
            print(f"Job ID {jid} not found.")
            sys.exit(1)

    elif cmd == "event":
        jid = sys.argv[2]
        event_type = sys.argv[3]
        note = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if jid in db["listings"]:
            if "events" not in db["listings"][jid]:
                db["listings"][jid]["events"] = []
            db["listings"][jid]["events"].append({
                "date": today,
                "type": event_type,
                "note": note,
            })
            save_db(db)
            print(f"Logged {event_type} for {db['listings'][jid]['title']} @ {db['listings'][jid]['company']}")
        else:
            print(f"Job ID {jid} not found.")
            sys.exit(1)

    elif cmd == "pipeline":
        active = [l for l in db["listings"].values() if l.get("status") != "new"]
        if not active:
            print("No active pipeline entries yet.")
        else:
            for l in sorted(active, key=lambda x: x.get("events", [{}])[-1].get("date", "") if x.get("events") else "", reverse=True):
                comp = l.get("fit_composite", "—")
                print(f"\n  {l['title']} @ {l['company']}")
                print(f"  Status: {l['status'].upper()}  |  Fit: {comp}  |  {l['url']}")
                events = l.get("events", [])
                if events:
                    for e in events:
                        print(f"    [{e['date']}] {e['type']}: {e.get('note', '')}")
                else:
                    print(f"    (no events logged)")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
