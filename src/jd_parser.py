import re
import os
import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


def load_skill_set(path=None):
    if path is None:
        path = os.path.join(DATA_DIR, "skills_db.txt")
    with open(path, "r", encoding="utf-8") as file:
        skills = [line.strip() for line in file if line.strip()]
    return skills


SKILL_SET = load_skill_set()


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


def extract_skills(text):
    skills = []
    for skill in SKILL_SET:
        if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE):
            skills.append(skill)
    return skills