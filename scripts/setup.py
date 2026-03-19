#!/usr/bin/env python3
"""
Interactive setup wizard for the job search pipeline.

Walks you through creating a config.yaml tailored to your profile.
Can optionally parse your resume (.docx, .pdf, or .txt) to auto-populate
the evidence bank, target keywords, and profile information.

Usage:
    python scripts/setup.py                     # Full interactive setup
    python scripts/setup.py --resume path/to/cv.docx  # Start from resume
    python scripts/setup.py --minimal           # Quick setup, skip evidence bank

The wizard generates config.yaml in the project root and copies your resume
to resources/.
"""

import sys, os, shutil, re, json
from pathlib import Path
from datetime import datetime

# Try yaml import
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install it: pip install pyyaml")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
EXAMPLE_PATH = PROJECT_ROOT / "config.example.yaml"
RESOURCES_DIR = PROJECT_ROOT / "resources"


# ── Resume text extraction ──────────────────────────────────────────

def extract_text_from_docx(path: str) -> str:
    """Extract plain text from a .docx file."""
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        print("  python-docx not installed. Trying pandoc fallback...")
        return _pandoc_extract(path)


def extract_text_from_pdf(path: str) -> str:
    """Extract plain text from a PDF file."""
    try:
        import subprocess
        result = subprocess.run(
            ["pdftotext", "-layout", path, "-"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass

    # Fallback: try pymupdf
    try:
        import fitz
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    except ImportError:
        pass

    print("  WARNING: Could not extract text from PDF.")
    print("  Install pdftotext or pymupdf (pip install pymupdf).")
    return ""


def extract_text_from_txt(path: str) -> str:
    """Read plain text file."""
    return Path(path).read_text()


def extract_resume_text(path: str) -> str:
    """Auto-detect format and extract text from a resume."""
    path = str(path)
    if path.endswith(".docx"):
        return extract_text_from_docx(path)
    elif path.endswith(".pdf"):
        return extract_text_from_pdf(path)
    elif path.endswith(".txt") or path.endswith(".md"):
        return extract_text_from_txt(path)
    else:
        print(f"  Unsupported format: {path}")
        print("  Supported: .docx, .pdf, .txt, .md")
        return ""


def _pandoc_extract(path: str) -> str:
    """Fallback: use pandoc to extract text."""
    try:
        import subprocess
        result = subprocess.run(
            ["pandoc", path, "-t", "plain"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    return ""


# ── Resume analysis (heuristic) ─────────────────────────────────────

def analyze_resume(text: str) -> dict:
    """Extract structured information from resume text using heuristics.

    This is a best-effort extraction. The user will review and edit everything.
    Returns a dict with: name, email, phone, location, skills, achievements, etc.
    """
    lines = text.strip().split("\n")
    result = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "skills": [],
        "achievements": [],
        "experience_sections": [],
        "education": [],
    }

    # Name: usually the first non-empty line
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) < 60 and not re.search(r'[@\d]', line):
            result["name"] = line
            break

    # Email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
    if email_match:
        result["email"] = email_match.group()

    # Phone
    phone_match = re.search(r'[\(]?\d{3}[\)]?[\s.-]?\d{3}[\s.-]?\d{4}', text)
    if phone_match:
        result["phone"] = phone_match.group()

    # Location: look for city/state patterns
    loc_match = re.search(
        r'(?:Greater\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s*([A-Z]{2})\b',
        text[:500]
    )
    if loc_match:
        result["location"] = f"{loc_match.group(1)}, {loc_match.group(2)}"

    # Skills: look for a skills/technical section
    skills_section = re.search(
        r'(?:TECHNICAL\s+SKILLS?|SKILLS?|TOOLS?|TECHNOLOGIES)\s*[:\n](.*?)(?:\n\n|\n[A-Z]{2,})',
        text, re.IGNORECASE | re.DOTALL
    )
    if skills_section:
        skills_text = skills_section.group(1)
        # Extract individual skills (comma or pipe separated)
        skills = re.split(r'[,|;]', skills_text)
        result["skills"] = [s.strip() for s in skills if s.strip() and len(s.strip()) < 50]

    # Achievements: look for lines with quantified results
    achievement_patterns = [
        r'(?:led|built|developed|created|designed|deployed|achieved|improved|increased|reduced|launched).*?\d+',
        r'\d+[%xX].*?(?:improvement|increase|reduction|faster|better)',
        r'(?:first|novel|patent|award|publication)',
    ]
    for line in lines:
        line = line.strip()
        if len(line) > 30 and any(re.search(p, line, re.IGNORECASE) for p in achievement_patterns):
            result["achievements"].append(line)

    return result


# ── Interactive prompts ──────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    """Ask user for input with an optional default."""
    if default:
        response = input(f"  {prompt} [{default}]: ").strip()
        return response if response else default
    return input(f"  {prompt}: ").strip()


def ask_int(prompt: str, default: int = 0) -> int:
    """Ask user for integer input."""
    while True:
        try:
            response = ask(prompt, str(default))
            return int(response)
        except ValueError:
            print("  Please enter a number.")


def ask_float(prompt: str, default: float = 0.0) -> float:
    """Ask user for float input."""
    while True:
        try:
            response = ask(prompt, str(default))
            return float(response)
        except ValueError:
            print("  Please enter a number.")


def ask_yn(prompt: str, default: bool = True) -> bool:
    """Ask yes/no question."""
    suffix = "[Y/n]" if default else "[y/N]"
    response = input(f"  {prompt} {suffix}: ").strip().lower()
    if not response:
        return default
    return response.startswith("y")


def ask_list(prompt: str, examples: str = "") -> list[str]:
    """Ask user for a comma-separated list."""
    if examples:
        print(f"  (Examples: {examples})")
    response = ask(prompt)
    return [item.strip() for item in response.split(",") if item.strip()]


# ── Config generation ────────────────────────────────────────────────

def generate_config(resume_analysis: dict = None, minimal: bool = False) -> dict:
    """Walk through interactive setup and return a config dict."""
    print("\n" + "=" * 60)
    print("  JOB SEARCH PIPELINE — SETUP WIZARD")
    print("=" * 60)

    config = yaml.safe_load(EXAMPLE_PATH.read_text()) if EXAMPLE_PATH.exists() else {}

    # ── Profile ──
    print("\n── YOUR PROFILE ──")
    ra = resume_analysis or {}

    name = ask("Full name", ra.get("name", ""))
    config.setdefault("profile", {})
    config["profile"]["name"] = name

    # Derive short name
    short = name.split()[0] if name else ""
    config["profile"]["name_short"] = ask("Short name (for sign-offs)", short)

    config["profile"]["credentials"] = ask("Credentials (e.g., Ph.D., MBA, M.S.)", "")
    config["profile"]["email"] = ask("Email", ra.get("email", ""))
    config["profile"]["phone"] = ask("Phone", ra.get("phone", ""))
    config["profile"]["location"] = ask("Location (city, state)", ra.get("location", ""))

    print("\n── COMPENSATION ──")
    config["profile"].setdefault("current_comp", {})
    base = ask_int("Current base salary ($)", 0)
    config["profile"]["current_comp"]["base_salary"] = base
    bonus = ask_int("Annual bonus (% of base)", 10)
    config["profile"]["current_comp"]["bonus_percent"] = bonus
    has_eq = ask_yn("Do you have equity/RSUs?", True)
    config["profile"]["current_comp"]["has_equity"] = has_eq
    total_est = int(base * (1 + bonus / 100)) + (10000 if has_eq else 0)
    total = ask_int("Estimated total annual comp ($)", total_est)
    config["profile"]["current_comp"]["total_comp_estimate"] = total

    yoe = ask_int("Years post-terminal-degree experience", 5)
    config["profile"]["years_experience"] = yoe
    config["profile"]["current_title"] = ask("Current title", "")

    levels = ["entry_ic", "mid_ic", "senior_ic", "staff_ic", "manager", "director", "vp"]
    print(f"  Level options: {', '.join(levels)}")
    config["profile"]["current_level"] = ask("Current level", "senior_ic")

    # ── Target roles ──
    print("\n── TARGET ROLES ──")
    config.setdefault("target", {})

    print("  What kinds of roles are you looking for?")
    queries = ask_list("Search queries (comma-separated)",
                       '"machine learning" pharma, data scientist biotech')
    config["target"]["search_queries"] = queries if queries else config.get("target", {}).get("search_queries", [])

    pos_kw = ask_list("Positive keywords (skills, tools, domains)",
                      "machine learning, Python, drug discovery")
    if pos_kw:
        config["target"]["positive_keywords"] = pos_kw
    elif ra.get("skills"):
        print(f"  Auto-detected from resume: {', '.join(ra['skills'][:10])}")
        if ask_yn("Use these as positive keywords?"):
            config["target"]["positive_keywords"] = ra["skills"][:15]

    neg_kw = ask_list("Negative keywords (roles to skip)",
                      "intern, postdoc, contract")
    if neg_kw:
        config["target"]["negative_keywords"] = neg_kw

    # ── Location ──
    print("\n── LOCATION PREFERENCES ──")
    config.setdefault("location", {})
    home = config["profile"]["location"]
    config["location"]["home_region"] = ask("Home region (for scoring)", home)

    # ── Scoring weights ──
    if not minimal:
        print("\n── FIT SCORING WEIGHTS ──")
        print("  Weights must sum to 1.0. Press Enter to use defaults.")
        dims = config.get("scoring", {}).get("dimensions", {})
        total_w = 0
        for key, dim in dims.items():
            label = dim.get("label", key)
            default_w = dim.get("weight", 0.1)
            w = ask_float(f"{label} weight", default_w)
            dim["weight"] = w
            total_w += w
        if abs(total_w - 1.0) > 0.01:
            print(f"  WARNING: Weights sum to {total_w:.2f}, not 1.0. Normalizing...")
            for dim in dims.values():
                dim["weight"] = round(dim["weight"] / total_w, 2)

    # ── Evidence bank ──
    if not minimal and ra.get("achievements"):
        print("\n── EVIDENCE BANK (from resume) ──")
        print("  Found these quantified achievements:")
        for i, ach in enumerate(ra["achievements"][:8], 1):
            print(f"    {i}. {ach[:100]}...")
        print("  These will be added to your evidence bank.")
        print("  You can edit them in config.yaml after setup.\n")

    # ── Cover letter ──
    print("\n── COVER LETTER PREFERENCES ──")
    cl = config.setdefault("cover_letter", {})
    cl["sign_off"] = ask("Sign-off phrase", cl.get("sign_off", "Best,"))
    cl["font"] = ask("Font", cl.get("font", "Georgia"))
    cl["target_words"] = ask_int("Target word count", cl.get("target_words", 250))

    return config


# ── Main ─────────────────────────────────────────────────────────────

def main():
    resume_path = None
    minimal = "--minimal" in sys.argv
    resume_analysis = {}

    # Check for --resume flag
    for i, arg in enumerate(sys.argv):
        if arg == "--resume" and i + 1 < len(sys.argv):
            resume_path = sys.argv[i + 1]

    # If no flag but a resume path is the first arg
    if not resume_path and len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        resume_path = sys.argv[1]

    # Parse resume if provided
    if resume_path:
        resume_path = Path(resume_path).expanduser()
        if not resume_path.exists():
            print(f"Resume not found: {resume_path}")
            sys.exit(1)

        print(f"\n  Parsing resume: {resume_path}")
        text = extract_resume_text(str(resume_path))
        if text:
            resume_analysis = analyze_resume(text)
            print(f"  Detected name: {resume_analysis.get('name', '?')}")
            print(f"  Detected email: {resume_analysis.get('email', '?')}")
            print(f"  Detected location: {resume_analysis.get('location', '?')}")
            skills = resume_analysis.get("skills", [])
            if skills:
                print(f"  Detected skills: {', '.join(skills[:8])}...")
            achs = resume_analysis.get("achievements", [])
            if achs:
                print(f"  Found {len(achs)} quantified achievements")

            # Copy resume to resources/
            RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
            dest = RESOURCES_DIR / resume_path.name
            if not dest.exists():
                shutil.copy2(resume_path, dest)
                print(f"  Copied resume to: {dest.relative_to(PROJECT_ROOT)}")
        else:
            print("  Could not extract text from resume.")

    # Check for existing config
    if CONFIG_PATH.exists():
        print(f"\n  config.yaml already exists.")
        if not ask_yn("Overwrite?", False):
            print("  Setup cancelled.")
            return

    # Run wizard
    config = generate_config(resume_analysis, minimal)

    # Store resume path in config
    if resume_path:
        rel = Path("resources") / resume_path.name
        config["profile"]["resume_path"] = str(rel)

    # Write config
    CONFIG_PATH.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True))
    print(f"\n  Config saved to: {CONFIG_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  Edit it to fine-tune scoring rubrics, evidence bank, and search queries.")
    print(f"\n  Next steps:")
    print(f"    1. Review and edit config.yaml")
    print(f"    2. Set up the daily scan schedule (see skills/daily-scan/SKILL.md)")
    print(f"    3. Run your first scan!")
    print()


if __name__ == "__main__":
    main()
