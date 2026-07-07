import re
from src.matcher import semantic_score


def skills_found_in_resume(jd_skills, resume_text):
    matched = []
    missing = []

    for skill in jd_skills:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, resume_text, re.IGNORECASE):
            matched.append(skill)
        else:
            missing.append(skill)

    skill_score = (len(matched) / len(jd_skills) * 100) if jd_skills else 0

    return {
        "matched": matched,
        "missing": missing,
        "skill_score": round(float(skill_score), 2)
    }


def evaluate_candidate(jd_text, jd_skills, resume_text):
    skill_result = skills_found_in_resume(jd_skills, resume_text)

    try:
        sem_score = semantic_score(resume_text, jd_text)
    except Exception:
        sem_score = 0

    final = round(float(0.7 * skill_result["skill_score"] + 0.3 * sem_score), 2)

    return {
        "score": final,
        "skill_score": skill_result["skill_score"],
        "semantic_score": sem_score,
        "matched": skill_result["matched"],
        "missing": skill_result["missing"],
    }