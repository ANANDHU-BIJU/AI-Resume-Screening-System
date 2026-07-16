"""
resume_parser.py

Combines all resume parsing modules and returns a structured
dictionary that can be directly used by the matching engine.
"""

import os
import re

from src.pdf_parser import extract_text
from src.preprocess import clean_text
from src.entity_extractor import extract_entities
from src.jd_parser import extract_skills  # was src.skill_extractor (removed — see below)
from src.resume_evaluator import evaluate_resume


# ---------------------------------------------------
# Generic Section Extractor
# ---------------------------------------------------

SECTION_HEADINGS = [
    "education",
    "academic qualification",
    "academic qualifications",
    "experience",
    "work experience",
    "professional experience",
    "internships",
    "projects",
    "academic projects",
    "personal projects",
    "technical skills",
    "skills",
    "certifications",
    "certificates",
    "courses",
    "achievements",
    "publications",
    "activities",
    "languages",
    "summary",
    "objective",
]


def extract_section(text, section_names):
    """
    Extract a section from resume text.

    Args:
        text (str)
        section_names (list)

    Returns:
        list
    """

    lines = text.splitlines()

    section = []

    capture = False

    for line in lines:

        current = line.strip()

        if not current:
            continue

        lower = current.lower()

        if lower in [x.lower() for x in section_names]:
            capture = True
            continue

        if capture:

            if lower in SECTION_HEADINGS:
                break

            section.append(current)

    return section


# ---------------------------------------------------
# Education
# ---------------------------------------------------

def extract_education(text):

    return extract_section(
        text,
        [
            "Education",
            "Academic Qualification",
            "Academic Qualifications"
        ]
    )


# ---------------------------------------------------
# Experience
# ---------------------------------------------------

def extract_experience(text):

    details = extract_section(
        text,
        [
            "Experience",
            "Work Experience",
            "Professional Experience",
            "Internships"
        ]
    )

    duration = re.findall(
        r'(\d+(?:\.\d+)?)\s*(?:year|years|month|months)',
        text,
        flags=re.IGNORECASE
    )

    return {
        "details": details,
        "duration": duration
    }


# ---------------------------------------------------
# Projects
# ---------------------------------------------------

def extract_projects(text):

    return extract_section(
        text,
        [
            "Projects",
            "Academic Projects",
            "Personal Projects"
        ]
    )


# ---------------------------------------------------
# Certifications
# ---------------------------------------------------

def extract_certifications(text):

    return extract_section(
        text,
        [
            "Certifications",
            "Certificates",
            "Courses"
        ]
    )


# ---------------------------------------------------
# Resume Score
# ---------------------------------------------------
#
# FIX: this module previously had its own calculate_resume_score(), a
# simple presence-check scorer, while resume_evaluator.py had a second,
# more detailed scorer under the SAME function name (weighing skill count,
# strong-skill keywords, certifications, projects, experience). Two
# functions with the same name computing different numbers meant "resume
# score" could mean different things depending on which code path ran —
# a real risk of confusing HR-facing output. resume_evaluator.evaluate_resume()
# is now the single source of truth; it also folds in biodata format
# validation (name/email/phone/LinkedIn/GitHub checks) in the same call.


# ---------------------------------------------------
# Main Resume Parser
# ---------------------------------------------------

def parse_resume(pdf_path):
    """
    Parse a resume PDF.

    Parameters
    ----------
    pdf_path : str
        Path to uploaded PDF.

    Returns
    -------
    dict
        Structured resume data.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"Resume file not found: {pdf_path}"
        )

    # Extract text
    raw_text = extract_text(pdf_path)

    if not raw_text.strip():
        raise ValueError(
            "Unable to extract text from the uploaded PDF."
        )

    # Clean text
    cleaned_text = clean_text(raw_text)

    # Extract candidate details
    entities = extract_entities(raw_text)

    # Extract skills
    # FIX: was extract_skills(cleaned_text). clean_text() strips punctuation,
    # which silently broke matching for symbol-bearing skills like "c++"
    # and "c#" (they became "c" before the skill list was checked). Skills
    # are matched against the raw text via regex, using jd_parser's
    # skills_db.txt-backed extractor — the same list app.py's live scoring
    # path already uses (skill_extractor.py's separate, smaller hardcoded
    # list has been removed to avoid two skill lists drifting apart).
    skills = extract_skills(raw_text)

    # Extract resume sections
    education = extract_education(raw_text)

    experience = extract_experience(raw_text)

    projects = extract_projects(raw_text)

    certifications = extract_certifications(raw_text)

    # Build final dictionary
    resume = {

        "name": entities.get("name", ""),

        "email": entities.get("email", ""),

        "phone": entities.get("phone", ""),

        "linkedin": entities.get("linkedin", ""),

        "github": entities.get("github", ""),

        "skills": skills,

        "education": education,

        "experience": experience,

        "projects": projects,

        "certifications": certifications,

        "raw_text": raw_text,

        "cleaned_text": cleaned_text

    }

    evaluation = evaluate_resume(resume)
    resume["resume_score"] = evaluation["resume_score"]
    resume["format_valid"] = evaluation["format_valid"]
    resume["format_issues"] = evaluation["format_issues"]

    return resume
