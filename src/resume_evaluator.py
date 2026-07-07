"""
resume_evaluator.py

Post-processing layer for resume analysis.

Input: parsed resume dictionary from resume_parser.py
Output:
- resume_score (skill-based)
- format validation (biodata correctness)
"""

import re


# =========================================================
# BIODATA VALIDATION (NO SCORING IMPACT)
# =========================================================

def validate_biodata(resume):
    """
    Validates format correctness of personal details.
    Does NOT affect resume score.
    """

    issues = []

    name = resume.get("name", "")
    email = resume.get("email", "")
    phone = resume.get("phone", "")
    linkedin = resume.get("linkedin", "")
    github = resume.get("github", "")

    # ---------------- NAME ----------------
    if not name or len(name.strip()) < 2:
        issues.append("Invalid or missing name")

    # ---------------- EMAIL ----------------
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not email:
        issues.append("Missing email")
    elif not re.match(email_pattern, email):
        issues.append("Invalid email format")

    # ---------------- PHONE ----------------
    phone_pattern = r'^\+?\d{10,15}$'
    if not phone:
        issues.append("Missing phone number")
    elif not re.match(phone_pattern, phone.replace(" ", "")):
        issues.append("Invalid phone format")

    # ---------------- LINKEDIN ----------------
    if linkedin and "linkedin.com" not in linkedin:
        issues.append("Invalid LinkedIn URL")

    # ---------------- GITHUB ----------------
    if github and "github.com" not in github:
        issues.append("Invalid GitHub URL")

    return {
        "format_valid": len(issues) == 0,
        "format_issues": issues
    }


# =========================================================
# SKILL-BASED RESUME SCORING ENGINE
# =========================================================

def calculate_resume_score(resume):
    """
    Computes resume quality score based ONLY on:
    skills, certifications, projects, experience.
    """

    score = 0

    # ---------------- SKILLS ----------------
    skills = resume.get("skills", [])

    if skills:
        score += 20

        skill_count = len(skills)

        if skill_count >= 15:
            score += 40
        elif skill_count >= 10:
            score += 30
        elif skill_count >= 5:
            score += 20
        elif skill_count >= 1:
            score += 10

        skill_text = " ".join(skills).lower()

        strong_skills = [
            "python", "java", "c++", "sql",
            "machine learning", "deep learning",
            "ai", "nlp", "tensorflow", "pytorch",
            "aws", "azure", "docker", "kubernetes"
        ]

        for sk in strong_skills:
            if sk in skill_text:
                score += 2


    # ---------------- CERTIFICATIONS ----------------
    certs = resume.get("certifications", [])

    if certs:
        score += 10

        cert_count = len(certs)

        if cert_count >= 5:
            score += 20
        elif cert_count >= 3:
            score += 15
        elif cert_count >= 1:
            score += 10

        cert_text = " ".join(certs).lower()

        high_value_certs = [
            "aws", "azure", "gcp",
            "machine learning", "data science",
            "devops", "docker", "kubernetes",
            "google cloud"
        ]

        for c in high_value_certs:
            if c in cert_text:
                score += 3


    # ---------------- PROJECTS ----------------
    projects = resume.get("projects", [])

    if projects:
        score += 10

        project_count = len(projects)

        if project_count >= 3:
            score += 15
        elif project_count == 2:
            score += 10
        elif project_count == 1:
            score += 5

        project_text = " ".join(projects).lower()

        project_keywords = [
            "machine learning", "ai", "automation",
            "web", "api", "flask", "django",
            "nlp", "iot", "computer vision"
        ]

        for p in project_keywords:
            if p in project_text:
                score += 2


    # ---------------- EXPERIENCE ----------------
    experience = resume.get("experience", {}).get("details", [])

    if experience:
        score += 10

        exp_text = " ".join(experience).lower()

        if "intern" in exp_text:
            score += 5
        if "developer" in exp_text:
            score += 5
        if "engineer" in exp_text:
            score += 5


    return min(score, 100)


# =========================================================
# MAIN EVALUATION FUNCTION (ENTRY POINT)
# =========================================================

def evaluate_resume(resume):
    """
    Final evaluation function.

    Returns:
    - resume_score (0–100)
    - format_valid (True/False)
    - format_issues (list of issues)
    """

    score = calculate_resume_score(resume)
    validation = validate_biodata(resume)

    return {
        "resume_score": score,
        "format_valid": validation["format_valid"],
        "format_issues": validation["format_issues"]
    }