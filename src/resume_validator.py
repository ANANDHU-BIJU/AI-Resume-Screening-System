import re

try:
    from spellchecker import SpellChecker
    spell = SpellChecker()
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False


def check_spelling(text, max_words_to_check=500):
    """
    Basic spelling check on resume text. Skips common technical terms,
    numbers, and proper nouns to avoid false positives.
    """
    if not SPELLCHECK_AVAILABLE:
        return {"checked": False, "misspelled": [], "error_count": 0}

    words = re.findall(r"[a-zA-Z]+", text.lower())[:max_words_to_check]
    words = [w for w in words if len(w) > 3]  # skip tiny words/abbreviations

    misspelled = spell.unknown(words)
    # Filter out likely tech terms / proper nouns (capitalized in original text)
    misspelled = [w for w in misspelled if len(w) > 3]

    return {
        "checked": True,
        "misspelled": sorted(misspelled)[:20],  # cap list length
        "error_count": len(misspelled)
    }


def validate_required_sections(resume_text):
    """
    Checks whether key resume sections are present at all.
    """
    text_lower = resume_text.lower()
    required_sections = {
        "education": ["education", "academic"],
        "experience": ["experience", "internship", "work history"],
        "skills": ["skills", "technical skills"],
        "contact": ["@"],  # at least an email present somewhere
    }

    missing = []
    for section, keywords in required_sections.items():
        if not any(kw in text_lower for kw in keywords):
            missing.append(section)

    return missing


def validate_resume(resume_text, entities):
    """
    Full validation: biodata format + missing sections + spelling.
    Returns a verdict: 'Accepted', 'Flagged', or 'Rejected'.
    """
    issues = []

    # --- Biodata checks ---
    name = entities.get("name", "")
    email = entities.get("email", "")
    phone = entities.get("phone", "")

    if not name or len(name.strip()) < 2:
        issues.append("Missing or invalid name")

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not email:
        issues.append("Missing email")
    elif not re.match(email_pattern, email):
        issues.append("Invalid email format")

    phone_pattern = r'^\+?\d{10,15}$'
    if not phone:
        issues.append("Missing phone number")
    elif not re.match(phone_pattern, phone.replace(" ", "").replace("-", "")):
        issues.append("Invalid phone format")

    # --- Missing sections ---
    missing_sections = validate_required_sections(resume_text)
    if missing_sections:
        issues.append(f"Missing sections: {', '.join(missing_sections)}")

    # --- Spelling ---
    spelling = check_spelling(resume_text)
    if spelling["checked"] and spelling["error_count"] > 15:
        issues.append(f"High number of spelling errors ({spelling['error_count']} found)")

    # --- Verdict ---
    critical_issues = [i for i in issues if "Missing email" in i or "Missing or invalid name" in i]

    if critical_issues:
        verdict = "Rejected"
    elif issues:
        verdict = "Flagged"
    else:
        verdict = "Accepted"

    return {
        "verdict": verdict,
        "issues": issues,
        "spelling_errors": spelling.get("misspelled", []),
        "spelling_error_count": spelling.get("error_count", 0),
    }
