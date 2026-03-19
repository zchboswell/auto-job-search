---
name: interview-prep
description: Generate a focused interview prep report. Use this skill whenever the user mentions an interview, preparing for a conversation with a company, or asks for company research, role analysis, or comp benchmarking in a job search context.
---

# Interview Prep Report

This skill produces a focused, one-page interview prep document. The report should be something you can skim an hour before a call and come away knowing: what this company does and where they stand, what the role needs and how your background maps to it, what fair comp looks like, and who you're talking to.

## What You Need

At minimum:
- **Company name**
- **Role title** and **job description** (pasted text or a link)

Optionally:
- **Interviewer name(s)** and/or titles
- **Any other context** (stage of interview, concerns, etc.)

## Research Phase

Before writing anything, gather information. Use web search liberally.

### Company Research
- What they do: core technology, products, key programs
- Stage and traction: milestones, recent press, publications
- Funding: last round, total raised, investors, runway signals
- Partnerships and collaborations
- Leadership: CEO, relevant department heads
- Culture signals: Glassdoor, recent news

### Role Research
From the JD, extract:
- The actual core need (not the wish list, the *need*)
- Required vs. nice-to-have qualifications
- Reporting structure, team size, scope

### Interviewer Research (if names provided)
- LinkedIn background, tenure, previous companies
- Publications or conference talks
- Likely interview angle

### Compensation Research
- Market data for this role title, level, and geography
- Glassdoor, Levels.fyi, H1B data, industry-specific sources
- Consider company stage (startup equity vs. big company cash comp)
- Read `config.yaml > profile > current_comp` for the user's baseline

## The Report

Generate a .docx file. Tone: direct and useful, like a briefing from a sharp colleague.

### Structure

**1. Company Snapshot** — What they do, where they are, key news. End with anything to watch out for (red flags or strong signals).

**2. Role Analysis** — What this role actually is, then a frank assessment of fit. Where is the match strong? Where are the gaps? Don't sugarcoat, but don't undersell either.

**3. Compensation Benchmark** — Proposed base range, bonus, equity expectations. Flag if the posted comp is below market for this user's level. Provide a clear total comp summary.

**4. Interviewer Brief** (only if names provided) — Short bios, likely angles, any connections to flag.

### Formatting
- Clean, professional. Use the docx skill for implementation.
- Save as `<company>-interview-prep-YYYY-MM-DD.docx` in `outputs/interview-prep/<company>-<date>/`
