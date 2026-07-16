import re
import os
import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SKILLS_DB_PATH = os.path.join(DATA_DIR, "skills_db.txt")


def load_skill_set(path=None):
    if path is None:
        path = SKILLS_DB_PATH
    with open(path, "r", encoding="utf-8") as file:
        skills = [line.strip() for line in file if line.strip()]
    return skills


def read_jd(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def read_jd_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_skills(text, skill_set=None):
    """
    Extract JD skills present in `text`.

    FIX: previously SKILL_SET was loaded once at module import time and
    cached in memory. If dynamic_skill_extractor.py appended new skills to
    skills_db.txt later in the same running session, those new skills were
    invisible until the app restarted. Now the skill set is re-read from
    disk on every call (skills_db.txt is small — a few hundred lines — so
    this costs a few milliseconds and is negligible next to the model
    inference already happening in the matching pipeline).

    You can still pass skill_set explicitly (e.g. a cached list) if you
    want to avoid the disk read in a hot loop.
    """
    if skill_set is None:
        skill_set = load_skill_set()

    skills = []
    for skill in skill_set:
        if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE):
            skills.append(skill)
    return skills
