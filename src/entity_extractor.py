"""
entity_extractor.py

Extracts candidate biodata (name, email, phone, LinkedIn, GitHub) from raw
resume text. This module was referenced by resume_parser.py but was
missing from the codebase — parse_resume() would raise ImportError without
it, which is why app.py's try/except silently fell back to demo data.

Uses spaCy's pretrained NER model for name detection, and regex for the
more structured fields (email, phone, URLs), which are far more reliable
than NER for those.
"""

import re
import spacy

nlp = spacy.load("en_core_web_sm")

EMAIL_PATTERN = re.compile(r"[\w\.\-+]+@[\w\-]+\.[\w\.\-]+")

PHONE_CANDIDATE_PATTERN = re.compile(r"[\+\(]?[\d][\d\s\-\(\)]{8,18}\d")

LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/[A-Za-z0-9\-_/%]+", re.IGNORECASE
)

GITHUB_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/%]+", re.IGNORECASE
)


def _extract_email(text):
    match = EMAIL_PATTERN.search(text)
    return match.group(0).strip() if match else ""


def _extract_phone(text):
    # Search only in the first ~1000 chars — phone numbers live near the
    # top of a resume (header/contact block). Searching the whole document
    # risks false positives from dates, IDs, or year ranges further down.
    #
    # FIX: the original approach tried to match country-code / area-code /
    # main-number as separate regex groups, which is fragile — on a real
    # number like "+91 98765 43210" the greedy area-code group ate too
    # many digits and the match silently dropped the last digit. Instead,
    # grab any digit/space/dash/paren run of plausible length, then
    # validate by counting the actual digits (10-15, matching the same
    # rule resume_evaluator.py / resume_validator.py use downstream).
    header = text[:1000]
    for match in PHONE_CANDIDATE_PATTERN.finditer(header):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 15:
            return candidate
    return ""


def _extract_linkedin(text):
    match = LINKEDIN_PATTERN.search(text)
    if not match:
        return ""
    url = match.group(0)
    if not url.lower().startswith("http"):
        url = "https://" + url
    return url


def _extract_github(text):
    match = GITHUB_PATTERN.search(text)
    if not match:
        return ""
    url = match.group(0)
    if not url.lower().startswith("http"):
        url = "https://" + url
    return url


def _extract_name(text):
    """
    Heuristic: the candidate's name is almost always the first PERSON
    entity spaCy finds near the top of the document (resume headers put
    the name first, before any referenced people in work history, etc.).
    """
    # Only scan the header region for speed and to avoid picking up a
    # referenced person's name later in the document (e.g. "Reporting to
    # John Smith").
    header = text[:500]
    doc = nlp(header)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Guard against spaCy occasionally tagging a single stray word
            if len(name.split()) >= 2:
                return name

    # Fallback: first non-empty line, if it looks name-like (short, no
    # digits/@ symbols, mostly alphabetic — resumes conventionally open
    # with the candidate's name on its own line).
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if len(candidate) <= 40 and not any(ch.isdigit() for ch in candidate) \
                and "@" not in candidate:
            return candidate
        break

    return ""


def extract_entities(text):
    """
    Main entry point. Returns a dict with name, email, phone, linkedin,
    github extracted from raw resume text.
    """
    return {
        "name": _extract_name(text),
        "email": _extract_email(text),
        "phone": _extract_phone(text),
        "linkedin": _extract_linkedin(text),
        "github": _extract_github(text),
    }
