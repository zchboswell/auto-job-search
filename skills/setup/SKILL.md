---
name: setup
description: Set up the job search pipeline for a new user. Use this skill when someone first opens the project, says they want to get started, uploads a resume, or asks to configure their job search. Also use when they want to reconfigure or update their profile, scoring weights, or target roles.
---

# Job Search Setup

Walk the user through configuring their job search pipeline. This replaces the CLI setup wizard with a conversational flow.

## Prerequisites

The user needs:
- A resume/CV (uploaded or already in `resources/`)
- A few minutes to answer questions about what they're looking for

## Step 1: Parse the Resume

If the user uploaded a resume, read it. Extract:
- Full name, email, phone, location
- Key skills and tools
- Quantified achievements (anything with numbers, metrics, or concrete impact)
- Current/most recent title and company
- Education and credentials

If the resume is .docx, use python-docx or pandoc. If .pdf, try pdftotext or pymupdf. Copy the file to `resources/`.

Summarize what you found and confirm with the user before proceeding.

## Step 2: Gather Preferences

Use AskUserQuestion to collect the remaining information. Group related questions together (max 4 per round). The key things to learn:

**Round 1: Target & Compensation**
- What kinds of roles are you targeting? (Get 2-3 search queries for LinkedIn)
- What's your current total compensation? (base, bonus %, equity)
- What's the minimum compensation you'd accept?

**Round 2: Location & Seniority**
- Where are you based? Are you open to relocation?
- What level are you targeting? (IC, manager, director, etc.)

**Round 3: Priorities**
- Of these factors, which matter most to you: technical fit, compensation, location, company stability, career growth? (This calibrates scoring weights.)

## Step 3: Build the Evidence Bank

From the resume achievements you extracted, organize them into 3-6 themes with keywords. For example:
- If someone built ML models → theme: "Machine Learning", keywords: ["machine learning", "ML", "deep learning", "neural network"]
- If someone led a team → theme: "Leadership", keywords: ["cross-functional", "leadership", "managed"]

Present the themes to the user and ask if they want to add, edit, or remove any.

## Step 4: Generate config.yaml

Read `config.example.yaml` as a template. Fill in all sections with the gathered information:

- `profile`: name, credentials, email, phone, location, current_comp, resume_path
- `target`: search_queries, positive_keywords, negative_keywords
- `location`: home_region, scoring regions
- `scoring.dimensions`: adjust weights based on the user's stated priorities
- `evidence_bank`: the themed achievements with keywords
- `cover_letter`: sign-off preference, font

Write the completed config to `config.yaml` in the project root.

## Step 5: Confirm & Next Steps

Tell the user:
1. Their config is saved and they can edit `config.yaml` anytime
2. To start scanning, they can set up a scheduled task (offer to do it now)
3. They need to be logged into LinkedIn in Chrome for scans to work

If they want to set up the schedule now, create a scheduled task using `skills/daily-scan/SKILL.md` as the prompt. Suggest weekday mornings.

## Scoring Weight Calibration

When the user says what matters most, map to weights roughly like this:

| Priority | technical | domain | seniority | location | compensation | company_health | trajectory |
|----------|-----------|--------|-----------|----------|--------------|----------------|------------|
| Balanced (default) | 0.25 | 0.20 | 0.10 | 0.10 | 0.15 | 0.12 | 0.08 |
| Comp-focused | 0.20 | 0.15 | 0.10 | 0.10 | 0.25 | 0.12 | 0.08 |
| Location-locked | 0.22 | 0.18 | 0.10 | 0.20 | 0.12 | 0.10 | 0.08 |
| Growth-focused | 0.20 | 0.18 | 0.10 | 0.08 | 0.12 | 0.12 | 0.20 |
| Stability-focused | 0.22 | 0.18 | 0.10 | 0.10 | 0.12 | 0.20 | 0.08 |

These are starting points. The user can always fine-tune in config.yaml.

## Location Scoring

Based on the user's home region, set up the location scoring map:
- Their city and nearby areas → "home_region" (score 10)
- Neighboring commutable areas → "commutable" (score 6)
- Major industry hubs for their field → "major_hub" (score 4)

Ask which hubs are relevant to their industry.
