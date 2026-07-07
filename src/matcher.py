from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")


def skill_match(resume_skills, jd_skills):
    matched = list(set(resume_skills) & set(jd_skills))
    missing = list(set(jd_skills) - set(resume_skills))
    score = len(matched) / len(jd_skills) * 100 if jd_skills else 0

    return {
        "score": round(float(score), 2),
        "matched": matched,
        "missing": missing
    }


def semantic_score(resume_text, jd_text):
    emb1 = model.encode([resume_text])
    emb2 = model.encode([jd_text])
    score = cosine_similarity(emb1, emb2)[0][0]
    return round(float(score) * 100, 2)


def final_score(skill_score, semantic_score):
    return round(float(0.7 * skill_score + 0.3 * semantic_score), 2)