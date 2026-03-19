---
name: daily-linkedin
description: Look for new applicable job listings on LinkedIn
---

Check LinkedIn for new listings that fit my profile. Use Chrome.

Read `config.yaml` for search queries, target keywords, location preferences, and scoring rubric.
Read my resume at the path specified in `config.yaml` (profile.resume_path) if you haven't already.

## How the Scan Works

1. **Search LinkedIn** using each query from `config.yaml > target > search_queries`.
   Apply time filter and location filter from `config.yaml > linkedin`.
   Sort by most recent.

2. **Collect listings** from search results. For each listing, extract:
   - LinkedIn job ID (from the URL)
   - Title, company, location, salary (if shown)
   - Full URL

3. **Filter out noise** using `config.yaml > target > negative_keywords` (e.g., intern, postdoc, contract).

4. **Run through the database**:
   Write collected listings to a temporary JSON file and run:
   ```
   python scripts/jobs_db.py new /path/to/today.json
   ```
   This returns only genuinely new listings and updates the database.

5. **Score new listings** using the fit scoring system:
   ```
   python scripts/jobs_db.py fscore <job_id> <score_per_dimension...>
   ```
   Dimensions and rubrics are in `config.yaml > scoring > dimensions`. Run `python scripts/fit_score.py rubric` for the full reference. Score each dimension 0-10 based on the JD content.

6. **Auto-generate cover letters** for listings that score above the threshold (`config.yaml > scoring > cover_letter_threshold`, default 85):
   - Capture the full JD text from LinkedIn while browsing.
   - Run `python scripts/cover_letter.py <job_id>` to identify which achievements are relevant.
   - Write the letter following the voice principles in `skills/cover-letter/SKILL.md`.
   - Generate a .docx (see the docx skill for formatting). Set `NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules`.
   - Save as `cover-letter-<company>-YYYY-MM-DD.docx` in `outputs/cover-letters/`.

7. **Run trends**: `python scripts/jobs_db.py trends`

8. **Save observations**: `python scripts/jobs_db.py observe "Your observation here"`

## Project Structure

```
job-search/
├── config.yaml             # Your personalized configuration
├── resources/              # CV and static reference materials
├── scripts/                # Pipeline scripts
│   ├── config_loader.py    # Central config reader
│   ├── jobs_db.py          # Job tracking database
│   ├── fit_score.py        # Configurable fit scoring
│   ├── cover_letter.py     # Cover letter outline generator
│   └── setup.py            # Setup wizard
├── data/                   # Database (jobs.json)
├── outputs/
│   ├── reports/            # Daily scan reports
│   ├── cover-letters/      # Generated cover letters
│   └── interview-prep/     # Per-company interview prep folders
└── skills/                 # Skill definitions
    ├── daily-scan/         # This file
    ├── cover-letter/       # Cover letter voice & style guide
    └── interview-prep/     # Interview prep report template
```

## Output

Generate a concise markdown report. Save it to `outputs/reports/linkedin-report-YYYY-MM-DD.md`.

Always include the LinkedIn listing URL for every listing in the report.
