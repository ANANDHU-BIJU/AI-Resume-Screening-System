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

try:
    from src.skill_extractor import SKILLS as _SKILL_TOKENS
except Exception:
    _SKILL_TOKENS = set()

try:
    from src.jd_parser import load_skill_set
    _SKILL_PHRASES = {s.lower() for s in load_skill_set()}
except Exception:
    _SKILL_PHRASES = set()

nlp = spacy.load("en_core_web_sm")

EMAIL_PATTERN = re.compile(r"[\w\.\-+]+@[\w\-]+\.[\w\.\-]+")

PHONE_CANDIDATE_PATTERN = re.compile(r"[\+\(]?[\d][\d\s\-\.\(\)]{7,18}\d")

LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/[A-Za-z0-9\-_/%]+", re.IGNORECASE
)

GITHUB_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_/%]+", re.IGNORECASE
)


def _extract_email(text):
    match = EMAIL_PATTERN.search(text)
    return match.group(0).strip() if match else ""


def _search_phone(segment):
    for match in PHONE_CANDIDATE_PATTERN.finditer(segment):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        if 10 <= len(digits) <= 15:
            return candidate
    return ""


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
    #
    # FIX 2: if nothing turns up in the header, fall back to scanning the
    # full text. Some templates place the contact block lower on the page,
    # and pdf_parser.py now appends tel: hyperlink URIs after each page's
    # text — those can land past the 1000-char cutoff.
    found = _search_phone(text[:1000])
    if found:
        return found
    return _search_phone(text)


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


_NON_NAME_LINE = re.compile(
    r"^(curriculum vitae|resume|c\.?v\.?|profile|contact( info)?|address|"
    r"objective|summary|career objective|personal details)\s*:?$",
    re.IGNORECASE,
)


def _looks_like_name(candidate: str) -> bool:
    """Shape check used to sanity-filter both heuristic and NER name
    candidates — rejects section headers, contact lines, and junk."""
    candidate = candidate.strip()
    if not candidate or len(candidate) > 40:
        return False
    if any(ch.isdigit() for ch in candidate):
        return False
    if "@" in candidate or "http" in candidate.lower() or "www." in candidate.lower():
        return False
    if _NON_NAME_LINE.match(candidate):
        return False
    words = candidate.split()
    if not (1 <= len(words) <= 4):
        return False
    # Reject lines that are actually skills/tech terms picked up from a
    # sidebar or tools list near the top of the document (e.g. "Raspberry
    # Pi", "Machine Learning") — these pass every shape check above but
    # are never a person's name.
    if any(w.lower() in _SKILL_TOKENS for w in words):
        return False
    if candidate.lower() in _SKILL_PHRASES:
        return False
    # Mostly alphabetic (allow spaces, dots, hyphens, apostrophes for
    # names like "Jean-Luc" or "O'Brien" or middle initials).
    letters_only = re.sub(r"[.\-'\s]", "", candidate)
    return letters_only.isalpha()


def _extract_name(text):
    """
    Heuristic: the candidate's name is almost always the first line or the
    first PERSON entity spaCy finds near the top of the document (resume
    headers put the name first, before any referenced people in work
    history, etc.).

    FIX: the previous fallback loop only ever checked the FIRST non-empty
    line and `break`-ed immediately after, whether or not it matched — so
    a stray line above the real name (e.g. a "CURRICULUM VITAE" title, a
    job-title line, an icon glyph left over from PDF extraction) meant no
    name was ever found, or the wrong line got returned. This version
    checks several of the top lines, and also handles ALL-CAPS name
    headers ("JOHN DOE"), which spaCy's NER — trained mostly on title-case
    text — frequently fails to tag as PERSON at all.
    """
    header = text[:800]
    lines = [ln.strip() for ln in header.splitlines() if ln.strip()]

    heuristic_candidates = [ln for ln in lines[:8] if _looks_like_name(ln)]

    ner_candidates = []
    doc = nlp(header)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            ner_candidates.append(ent.text.strip())

    # Best: a spaCy PERSON entity that also passes the shape check and has
    # a first + last name — highest confidence.
    for cand in ner_candidates:
        if len(cand.split()) >= 2 and _looks_like_name(cand):
            return cand

    # Next: an early line that looks name-shaped, even if spaCy didn't tag
    # it (covers ALL-CAPS headers and other NER misses).
    if heuristic_candidates:
        return heuristic_candidates[0]

    # Fall back to any multi-word PERSON entity, even one that didn't pass
    # the shape check.
    for cand in ner_candidates:
        if len(cand.split()) >= 2:
            return cand

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
