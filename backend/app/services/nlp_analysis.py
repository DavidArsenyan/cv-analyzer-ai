from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv


load_dotenv()

NLP_MODEL_NAME = os.getenv("NLP_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")


class NLPUnavailableError(RuntimeError):
    pass


def semantic_similarity(left: str, right: str) -> float:
    if not left.strip() or not right.strip():
        return 0.0

    try:
        model = _model()
        embeddings = model.encode([left, right], normalize_embeddings=True)
    except Exception as exc:
        raise NLPUnavailableError(str(exc)) from exc

    return float(embeddings[0] @ embeddings[1])


def semantic_score(left: str, right: str) -> int:
    similarity = semantic_similarity(left, right)
    # Map cosine similarity from a useful resume/JD range into 0-100.
    normalized = (similarity + 0.1) / 0.9
    return max(0, min(100, round(normalized * 100)))


def semantic_skill_gaps(
    resume_text: str,
    job_description: str,
    required_skills: list[str],
    detected_skills: list[str],
) -> list[str]:
    if not required_skills:
        return []

    gaps = []
    for skill in required_skills:
        if skill in detected_skills:
            continue

        try:
            resume_similarity = semantic_similarity(skill, resume_text)
            job_similarity = semantic_similarity(skill, job_description)
        except NLPUnavailableError:
            return []

        if job_similarity >= 0.25 and resume_similarity < 0.18:
            gaps.append(skill)

    return gaps


def nlp_available() -> bool:
    try:
        _model()
    except Exception:
        return False
    return True


@lru_cache(maxsize=1)
def _model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise NLPUnavailableError("sentence-transformers is not installed.") from exc

    return SentenceTransformer(NLP_MODEL_NAME)
