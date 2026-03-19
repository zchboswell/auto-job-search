# Job Search Autopilot

**Your AI-powered job search assistant.** Drop in your resume, tell it what you're looking for, and let it scan LinkedIn daily, score listings against your priorities, and draft cover letters for the best matches.

Built for [Claude Cowork](https://claude.ai) and [Claude Code](https://docs.claude.com/en/docs/claude-code). No coding experience required.

---

## What It Does

- Scans LinkedIn for new listings matching your target roles
- Tracks every listing in a database so you never see the same one twice
- Scores each listing against your personal priorities (technical fit, salary, location, career trajectory, etc.)
- Auto-generates tailored cover letters for top-scoring matches
- Spots trends in hiring activity over time
- Prepares interview briefing docs when you get a callback

You configure it once, and it runs on autopilot. Every day you get a clean report of what's new and what's worth your time.

---

## Getting Started

### What You'll Need

- **Claude Cowork** (desktop app) or **Claude Code** (terminal)
- **Chrome** with the [Claude in Chrome extension](https://chromewebstore.google.com/detail/claude-in-chrome) installed (for LinkedIn browsing)
- A resume in `.docx`, `.pdf`, or `.txt` format
- A LinkedIn account (logged in via Chrome)

### Step 1: Get the Project

Download or clone this project to your computer:

```
git clone https://github.com/YOUR_USERNAME/job-search-autopilot.git
```

Or just download the ZIP and unzip it somewhere convenient.

### Step 2: Set Up Your Profile

Open the project folder in Cowork (or `cd` into it in Claude Code). Upload your resume and say something like:

> "I want to set up my job search. Here's my resume."

Claude will read the setup skill and walk you through it conversationally:

1. **Parse your resume** — extracts name, contact info, skills, and key achievements
2. **Ask a few questions** — target roles, salary expectations, location, what matters most to you
3. **Build your evidence bank** — organizes your achievements into themes for cover letter generation
4. **Generate `config.yaml`** — your personalized config that all scripts read from

The whole thing takes about 5 minutes. After it's done, you can always edit `config.yaml` directly to fine-tune anything.

**Prefer the terminal?** There's also a CLI wizard:

```bash
pip install pyyaml python-docx
python scripts/setup.py --resume /path/to/your/resume.docx
```

### Step 3: Set Up the Daily Scan

**In Cowork:** Create a scheduled task that runs the daily scan. You can say:

> "Schedule a daily LinkedIn scan using the skill in skills/daily-scan/SKILL.md. Run it every weekday morning at 9am."

**In Claude Code:** You can run scans manually by telling Claude to follow the instructions in `skills/daily-scan/SKILL.md`, or set up a scheduled task the same way.

Both approaches use the Claude in Chrome extension to browse LinkedIn on your behalf.

### Step 4: Sit Back

Each scan produces a markdown report in `outputs/reports/` with:
- New listings found and their fit scores
- Links to every listing on LinkedIn
- Cover letters for top matches (saved to `outputs/cover-letters/`)
- Trend observations over time

---

## How Scoring Works

Every listing gets scored across 7 dimensions, each rated 0-10:

| Dimension | What It Measures | Default Weight |
|-----------|------------------|----------------|
| **Technical Match** | Does the role use your skills? | 25% |
| **Domain Context** | Is it in your target industry? | 20% |
| **Compensation** | Does it meet or beat your current pay? | 15% |
| **Company Health** | Is the company well-funded and growing? | 12% |
| **Seniority Fit** | Does the level match your experience? | 10% |
| **Location** | Is it near home, remote, or requires relocation? | 10% |
| **Career Trajectory** | Does it advance your long-term goals? | 8% |

These combine into a composite score (0-100) that determines the tier:

| Score | Tier | What It Means |
|-------|------|---------------|
| 80+ | **TOP** | Strong match. Worth serious consideration. |
| 60-79 | **STRONG** | Good fit with some trade-offs. |
| 40-59 | **WORTH A LOOK** | Partial fit. Review if the market is slow. |
| 25-39 | **STRETCH** | Long shot, but might surprise you. |
| <25 | **SKIP** | Not a match right now. |

**You control the weights.** If location matters more to you than salary, bump up the location weight and lower compensation. If you're early career and prioritize growth, increase the trajectory weight. Edit these in `config.yaml > scoring > dimensions`.

---

## Project Structure

```
job-search/
├── config.yaml                 # Your personalized settings (created by setup wizard)
├── config.example.yaml         # Reference template with all options documented
├── resources/                  # Your resume lives here
├── scripts/
│   ├── setup.py                # Setup wizard
│   ├── config_loader.py        # Config reader (used by all scripts)
│   ├── jobs_db.py              # Job tracking database
│   ├── fit_score.py            # Scoring engine
│   └── cover_letter.py         # Cover letter outline generator
├── data/
│   └── jobs.json               # Your job database (auto-created)
├── outputs/
│   ├── reports/                # Daily scan reports
│   ├── cover-letters/          # Generated cover letters
│   └── interview-prep/         # Interview prep docs
├── skills/
│   ├── setup/SKILL.md          # Interactive setup wizard (conversational)
│   ├── daily-scan/SKILL.md     # Instructions for the daily LinkedIn scan
│   ├── cover-letter/SKILL.md   # Cover letter voice and style guide
│   └── interview-prep/SKILL.md # Interview prep report template
└── examples/                   # Sample configs and reports
```

---

## Using With Cowork vs. Claude Code

This project works with both. Here's what's different:

| Feature | Cowork | Claude Code |
|---------|--------|-------------|
| **Setup** | Open folder, chat with Claude | `cd` into folder, chat with Claude |
| **Chrome browsing** | Built-in via Claude in Chrome MCP | Add Chrome MCP to `.claude/settings.json` |
| **Scheduled scans** | Use Cowork's scheduled tasks | Use Claude Code's scheduled tasks or cron |
| **File output** | Files appear in your selected folder | Files appear in the project directory |

### Chrome Extension Setup for Claude Code

If you're using Claude Code, you'll need to connect the Chrome extension as an MCP server. Add this to your Claude Code MCP config:

```json
{
  "mcpServers": {
    "claude-in-chrome": {
      "type": "sse",
      "url": "http://localhost:PORT/sse"
    }
  }
}
```

The Chrome extension documentation has the exact port and connection details. The extension must be running in Chrome for LinkedIn browsing to work.

---

## Common Tasks

### "I got an interview!"

Tell Claude:

> "I have an interview at [Company Name] for [Role Title]. Here's the JD: [paste or link]. The interviewer is [Name]."

Claude will use the interview-prep skill to generate a briefing doc with company research, role analysis, comp benchmarks, and interviewer background.

### "Score this listing for me"

> "Score this listing: [paste JD or LinkedIn URL]"

Claude will evaluate it against your scoring rubric and add it to your database.

### "Generate a cover letter for this role"

> "Write a cover letter for [Company] [Role]. Here's the JD: [paste]"

Claude will match your achievements to the JD and write a targeted letter following your voice preferences.

### "What does my pipeline look like?"

```bash
python scripts/jobs_db.py pipeline
```

Shows all listings you've moved beyond "new" status, with event history.

### "Show me trends"

```bash
python scripts/jobs_db.py trends
```

Prints hiring trends, salary ranges, reposting patterns, and your observations over time.

---

## Customization

### Scoring Rubric

The scoring rubric in `config.yaml` includes anchor descriptions for each score level (0, 2, 4, 6, 8, 10) in each dimension. These guide the AI when scoring listings. Edit them to match your field.

For example, if you're in software engineering, the "Technical Match: 10" description might be "Role requires my exact tech stack (React, TypeScript, Node.js) and domain (fintech)."

### Evidence Bank

The evidence bank (`config.yaml > evidence_bank`) maps your key achievements to themes, with keywords that match them to job descriptions. The setup wizard populates this from your resume, but you should review and refine it. Better evidence = better cover letters.

### Cover Letter Voice

Edit `skills/cover-letter/SKILL.md` to match your personal writing style. The defaults produce a concise, professional letter, but you might want something warmer, more technical, or more casual.

---

## Dependencies

Required:
- Python 3.9+
- `pyyaml` (pip install pyyaml)

Recommended:
- `python-docx` (pip install python-docx) — for resume parsing
- `Node.js` with `docx` package (npm install -g docx) — for generating .docx cover letters

---

## Troubleshooting

**"LinkedIn isn't loading"** — Make sure you're logged into LinkedIn in Chrome and the Claude in Chrome extension is active.

**"No new listings found"** — Try broadening your search queries in `config.yaml > target > search_queries`. LinkedIn's search can be finicky with exact-match quotes.

**"Scores seem off"** — Run `python scripts/fit_score.py rubric` to review your scoring rubric. The anchor descriptions guide the AI's ratings; if they don't match your expectations, edit them.

**"Cover letters sound generic"** — Improve your evidence bank in `config.yaml`. The more specific and quantified your achievements, the better the letters.

---

## Contributing

PRs welcome. If you've adapted this for a different field or platform (Indeed, Glassdoor, etc.), we'd love to see it.

---

## License

MIT
