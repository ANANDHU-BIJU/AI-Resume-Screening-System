"""
matcher.py

Semantic similarity scoring between a resume and a job description.

FIX: this file previously also had skill_match() and final_score(), which
duplicated logic that already lives in jd_resume_matcher.py (the version
actually used by app.py). Keeping both around meant a change to scoring
logic had to be made in two places, and it was easy to accidentally edit
the copy that wasn't wired into the app. That duplicate code has been
removed — jd_resume_matcher.py is now the single source of truth for
scoring, and this file only does semantic similarity.

FIX: the SentenceTransformer model is now loaded lazily on first use
instead of eagerly at import time. This means importing matcher.py (e.g.
indirectly through jd_resume_matcher.py at app startup) no longer forces
the ~90MB model to load before it's actually needed, which slightly speeds
up app startup / the splash screen.
"""

from sklearn.metrics.pairwise import cosine_similarity

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def semantic_score(resume_text, jd_text):
    model = _get_model()
    emb1 = model.encode([resume_text])
    emb2 = model.encode([jd_text])
    score = cosine_similarity(emb1, emb2)[0][0]
    return round(float(score) * 100, 2)
