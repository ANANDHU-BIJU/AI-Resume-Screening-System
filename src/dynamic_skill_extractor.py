import spacy
import os
import re

nlp = spacy.load("en_core_web_sm")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SKILLS_DB_PATH = os.path.join(DATA_DIR, "skills_db.txt")


def extract_skills_from_text(text: str) -> list:
    """
    Extract candidate skill phrases from raw JD text using spaCy.
    Looks for noun chunks and proper nouns, filters out junk.
    """
    doc = nlp(text)
    candidates = set()

    # Noun chunks (e.g. "machine learning", "data analysis")
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip()
        if 2 <= len(phrase) <= 40 and not phrase.lower() in STOPWORD_PHRASES:
            candidates.add(phrase)

    # Proper nouns / tech-like tokens (e.g. "Python", "AWS", "React")
    for token in doc:
        if token.pos_ in ("PROPN",) or (token.text.isupper() and len(token.text) > 1):
            candidates.add(token.text.strip())

    # Clean up: remove punctuation-heavy or numeric-only entries
    cleaned = []
    for c in candidates:
        c = re.sub(r"[^\w\s\.\+\#]", "", c).strip()
        if c and not c.isdigit() and len(c) > 1:
            cleaned.append(c)

    return sorted(set(cleaned), key=str.lower)


STOPWORD_PHRASES = {
    "the company", "the role", "the team", "the candidate",
    "this position", "our team", "you", "we", "they", "it"
}


def save_skills_to_db(skills: list, path: str = None):
    """Append newly found skills to skills_db.txt, avoiding duplicates."""
    if path is None:
        path = SKILLS_DB_PATH

    existing = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = {line.strip() for line in f if line.strip()}

    combined = existing.union(skills)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for skill in sorted(combined, key=str.lower):
            f.write(skill + "\n")

    return sorted(combined, key=str.lower)


def extract_and_update_jd_skills(jd_text: str) -> list:
    """
    Main entry point: extract skills from JD text and merge into skills_db.txt.
    Returns the list of skills found in THIS specific JD (not the full merged db).
    """
    found_skills = extract_skills_from_text(jd_text)
    save_skills_to_db(found_skills)
    return found_skills