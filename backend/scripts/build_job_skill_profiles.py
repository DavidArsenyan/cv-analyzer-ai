from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from app.services.analysis import SKILL_KEYWORDS
except ImportError:
    SKILL_KEYWORDS = {}


DATASET_URL = "hf://datasets/batuhanmtl/job-skill-set/data/train-00000-of-00001.parquet"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "app" / "data" / "job_skill_profiles.generated.json"


ROLE_COLUMN_CANDIDATES = (
    "job_title",
    "title",
    "role",
    "position",
    "job",
    "Job Title",
    "jobTitle",
)
SKILL_COLUMN_CANDIDATES = (
    "job_skill_set",
    "skills",
    "skill",
    "required_skills",
    "job_skills",
    "Skill",
    "Skills",
)
DESCRIPTION_COLUMN_CANDIDATES = (
    "description",
    "job_description",
    "Job Description",
    "responsibilities",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compact role->skills profiles from a parquet, CSV, or ZIP CSV dataset.")
    parser.add_argument("--source", default=DATASET_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-role-count", type=int, default=1)
    parser.add_argument("--max-skills-per-role", type=int, default=16)
    parser.add_argument("--max-roles", type=int, default=2500)
    args = parser.parse_args()

    df = _read_source(args.source)
    role_column = _find_column(df.columns, ROLE_COLUMN_CANDIDATES)
    skill_column = _find_column(df.columns, SKILL_COLUMN_CANDIDATES)
    description_column = _find_column(df.columns, DESCRIPTION_COLUMN_CANDIDATES)

    if not role_column:
        raise SystemExit(f"Could not find role/title column. Available columns: {list(df.columns)}")
    if not skill_column and not description_column:
        raise SystemExit(f"Could not find skills or description column. Available columns: {list(df.columns)}")

    role_skill_counts: dict[str, Counter[str]] = defaultdict(Counter)
    role_counts: Counter[str] = Counter()

    for row_dict in df.to_dict("records"):
        role = _normalize_text(row_dict.get(role_column))
        if not role:
            continue

        skills = []
        if skill_column:
            skills.extend(_parse_skills(row_dict.get(skill_column)))
        if description_column:
            skills.extend(_extract_known_skills_from_text(row_dict.get(description_column)))

        if not skills:
            continue

        role_counts[role] += 1
        role_skill_counts[role].update(skills)

    profiles = {}
    for role, count in role_counts.most_common(args.max_roles):
        if count < args.min_role_count:
            continue
        skills = [
            skill
            for skill, _ in role_skill_counts[role].most_common(args.max_skills_per_role)
        ]
        if skills:
            profiles[role] = skills

    payload = {
        "source": args.source,
        "role_column": role_column,
        "skill_column": skill_column,
        "description_column": description_column,
        "profiles": profiles,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Wrote {len(profiles)} role profiles to {args.output}")


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    exact = {column: column for column in columns}
    lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in exact:
            return exact[candidate]
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _read_source(source: str) -> pd.DataFrame:
    source_path = Path(source)
    suffix = source_path.suffix.lower()
    if suffix in {".csv", ".zip"}:
        return pd.read_csv(source)
    return pd.read_parquet(source)


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).lower()).strip()


def _parse_skills(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [_normalize_skill(item) for item in value if _normalize_skill(item)]

    text = _normalize_text(value)
    if not text:
        return []

    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text.replace("'", '"'))
            if isinstance(parsed, list):
                return [_normalize_skill(item) for item in parsed if _normalize_skill(item)]
        except json.JSONDecodeError:
            pass

    return [_normalize_skill(part) for part in re.split(r"[,;|/]\s*", text) if _normalize_skill(part)]


def _extract_known_skills_from_text(value: object) -> list[str]:
    text = _normalize_text(value)
    if not text:
        return []

    known_skills = set(SKILL_KEYWORDS) or {
        "python",
        "sql",
        "excel",
        "communication",
        "leadership",
        "project management",
    }
    return _merge_unique(
        [skill for skill in known_skills if _contains_keyword(text, skill)],
        _extract_declared_skills_from_text(text),
    )


def _extract_declared_skills_from_text(text: str) -> list[str]:
    skills: list[str] = []
    patterns = (
        r"skills\s+required\s*:?\s*(.+)",
        r"required\s+skills\s*:?\s*(.+)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            line = match.group(1).splitlines()[0]
            line = re.split(r"\b(?:job code|experience range|educational qualifications|responsibilities)\b", line, flags=re.IGNORECASE)[0]
            skills.extend(_parse_skills(line))
    return _merge_unique(skills, [])


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged = []
    seen = set()
    for item in [*primary, *secondary]:
        if item and item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


def _normalize_skill(value: object) -> str:
    skill = _normalize_text(value)
    skill = re.sub(r"^[\"'`]+|[\"'`]+$", "", skill)
    skill = re.sub(r"\s+", " ", skill).strip(" .")
    blocked_terms = {
        "age",
        "color",
        "gender",
        "gender identity",
        "national origin",
        "religion",
        "sex",
        "sexual orientation",
        "disability",
    }
    blocked_phrases = (
        "such as ",
        " must ",
        " or disability",
        " expectation ",
        " equal ",
        "paid ",
        "401k",
        "holiday",
        "benefit",
        "knowledge of ",
    )
    if skill in blocked_terms or any(phrase in f" {skill} " for phrase in blocked_phrases):
        return ""
    if len(skill) < 2 or len(skill) > 60:
        return ""
    if len(skill.split()) > 5:
        return ""
    return skill


def _contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", text) is not None


if __name__ == "__main__":
    main()
