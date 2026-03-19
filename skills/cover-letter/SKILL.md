---
name: cover-letter
description: Generate targeted cover letters for job applications. Use this skill whenever generating, drafting, or revising a cover letter or cover page for a job listing, whether triggered automatically by a high fit score or requested manually. Also use when the user asks to refine cover letter tone, voice, or content.
---

# Cover Letter Generator

This skill produces cover letters tailored to specific job listings. Letters are short, specific, and written in the voice of a professional who is genuinely engaged with the company's work.

## Voice Principles

The single most important thing: the letter must not read like an AI wrote it.

What makes something sound AI-generated isn't any one word or phrase. It's a feeling of assembly. When a letter reads like blocks of evidence snapped together with connective tissue, the reader can feel the seams. A real person writing a cover letter doesn't organize their thoughts by mapping CV bullets to JD requirements. They write about what caught their eye, mention the relevant parts of their background in the natural flow of explaining why they're interested, and stop.

**Show, don't tell.** Never announce a quality. Don't write "I have both X and Y expertise." Instead, describe the work in a way that makes the reader realize this on their own.

**Specificity about their work.** The opening should reference something concrete about the company's work. Not "I admire your innovative approach" but the actual project, the actual product, the actual milestone.

**One voice throughout.** The whole letter should feel like it was written in one sitting by one person. No sudden tonal shifts between paragraphs.

## Formatting Rules

Read the user's preferences from `config.yaml > cover_letter`:
- `sign_off`: How to close the letter (e.g., "Best," or "Cheers,")
- `font`: Document font
- `font_size_body` / `font_size_name`: Type sizes
- `target_words`: Approximate body text length (default ~250 words)
- `anti_patterns`: Phrases and patterns to avoid

Additional rules:
- No em dashes. Use commas, periods, or parentheses instead.
- Length: roughly 200-250 words of body text. Three to four paragraphs. One page.
- Header: name, location, phone, email. A thin rule. Date. "Hiring Team" and company name.

## Structure

This isn't a rigid template. The paragraphs should flow naturally. But the general shape is:

**Opening (2-3 sentences).** What caught your attention about their work. Be specific. Transition naturally into wanting to be part of it.

**Your background (longest paragraph, still concise).** Relevant work told as a narrative. This is where range shows up implicitly. End with something that reveals how you think.

**Brief philosophy or approach (1-2 sentences).** What drives your work, in a sentence. Not a list of tools.

**Close (1 sentence).** Express interest in learning more.

## Anti-Patterns to Avoid

- "The hard part of X isn't Y, it's Z." Dead giveaway.
- "What sets me apart is..." or "My unique combination of..."
- Opening with a grand statement about the field.
- Regurgitating the resume.
- Listing achievements separated by semicolons or em dashes.
- Being explicit about your own identity: "I'm a big believer in..."

## Technical Implementation

1. Use `cover_letter.py` to match JD keywords to evidence themes from `config.yaml > evidence_bank`. This identifies *what* to mention; the voice principles determine *how*.
2. Generate the .docx with docx-js (Node.js). Set `NODE_PATH=/usr/local/lib/node_modules_global/lib/node_modules`.
3. Read the user's profile from `config.yaml > profile` for name, contact info, credentials.
4. Save as `cover-letter-<company>-YYYY-MM-DD.docx` in `outputs/cover-letters/`.
5. Validate with `python scripts/office/validate.py <output.docx>` (if available via docx skill).
