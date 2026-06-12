from __future__ import annotations

import re
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from app.schemas import ResumeAnalysisResponse, SkillGap
from app.services.llm_provider import LLMUnavailableError, generate_json
from app.services.nlp_analysis import NLPUnavailableError, semantic_score, semantic_skill_gaps


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
GENERATED_JOB_SKILL_PROFILES_PATH = DATA_DIR / "job_skill_profiles.generated.json"
MAX_REQUIRED_SKILLS = 12
MAX_MISSING_SKILLS = 8


SKILL_KEYWORDS = {
    "python": ["python"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "sql": ["sql"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "sqlite": ["sqlite"],
    "machine learning": ["machine learning", "ml"],
    "classification": ["classification"],
    "regression": ["regression"],
    "nlp": ["nlp", "natural language processing"],
    "text mining": ["text mining"],
    "llm": ["llm", "large language model"],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "matplotlib": ["matplotlib"],
    "seaborn": ["seaborn"],
    "plotly": ["plotly"],
    "statistics": ["statistics", "statistical analysis"],
    "hypothesis testing": ["hypothesis testing", "hypothesis test"],
    "a/b testing": ["a/b testing", "ab testing", "a/b test"],
    "deep learning": ["deep learning"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow"],
    "keras": ["keras"],
    "neural networks": ["neural network", "neural networks"],
    "lstm": ["lstm"],
    "cnn": ["cnn", "convolutional neural network"],
    "rnn": ["rnn", "recurrent neural network"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "rest api": ["rest api", "restful api"],
    "etl": ["etl"],
    "data pipelines": ["data pipeline", "data pipelines"],
    "airflow": ["airflow"],
    "dbt": ["dbt"],
    "excel": ["excel"],
    "shap": ["shap"],
    "lightgbm": ["lightgbm", "light gbm"],
    "feature engineering": ["feature engineering"],
    "model deployment": ["model deployment", "deployed model", "deployed models"],
    "dashboard development": ["dashboard development", "dashboards", "dashboard"],
    "time series forecasting": ["time series forecasting", "time series"],
    "oop": ["oop", "object oriented programming", "object-oriented programming"],
    "client segmentation": ["client segmentation", "customer segmentation"],
    "explainability": ["explainability", "model explainability", "explainable ai"],
    "roc-auc": ["roc-auc", "roc auc", "auc"],
    "data analysis": ["data analysis", "data analytics"],
    "backend development": ["backend development"],
    "data visualization": ["data visualization"],
    "api": ["api", "apis"],
    "cloud": ["cloud"],
    "mlops": ["mlops", "ml ops", "machine learning operations"],
    "linux": ["linux"],
    "terraform": ["terraform"],
    "ci/cd": ["ci/cd", "cicd", "ci cd", "continuous integration", "continuous delivery"],
    "github actions": ["github actions"],
    "git": ["git", "github", "gitlab"],
    "devops": ["devops", "dev ops"],
    "human resources": ["human resources", "hr", "human resource", "кадры", "управление персоналом", "մարդկային ռեսուրսներ"],
    "recruitment": ["recruitment", "recruiting", "recruiter", "подбор персонала", "рекрутинг", "найм", "հավաքագրում"],
    "talent acquisition": ["talent acquisition"],
    "employee relations": ["employee relations"],
    "performance management": ["performance management"],
    "payroll processing": ["payroll processing", "payroll"],
    "labor law compliance": ["labor law compliance", "employment law", "legal compliance"],
    "communication": ["communication", "communication skills"],
    "interpersonal skills": ["interpersonal skills"],
    "conflict management": ["conflict management"],
    "training and development": ["training and development", "training & development"],
    "leadership": ["leadership"],
    "seo": ["seo", "search engine optimization", "поисковая оптимизация"],
    "marketing": ["marketing", "маркетинг", "մարքեթինգ"],
    "sem": ["sem", "search engine marketing"],
    "google ads": ["google ads", "google adwords"],
    "meta ads": ["meta ads", "facebook ads", "instagram ads"],
    "content marketing": ["content marketing"],
    "copywriting": ["copywriting", "copywriter"],
    "social media marketing": ["social media marketing", "social media"],
    "email marketing": ["email marketing"],
    "google analytics": ["google analytics", "ga4"],
    "crm": ["crm", "salesforce", "hubspot"],
    "sales": ["sales", "selling", "продажи", "վաճառք"],
    "lead generation": ["lead generation", "prospecting"],
    "account management": ["account management"],
    "customer service": ["customer service", "customer support"],
    "project management": ["project management", "управление проектами", "նախագծերի կառավարում"],
    "risk management": ["risk management"],
    "product management": ["product management"],
    "agile": ["agile", "scrum", "kanban"],
    "jira": ["jira"],
    "figma": ["figma"],
    "ui design": ["ui design", "user interface design"],
    "ux design": ["ux design", "user experience design"],
    "adobe photoshop": ["photoshop", "adobe photoshop"],
    "adobe illustrator": ["illustrator", "adobe illustrator"],
    "graphic design": ["graphic design"],
    "translation": ["translation", "translator", "translated", "перевод", "переводчик", "թարգմանություն", "թարգմանիչ"],
    "localization": ["localization", "localisation", "localized", "localised", "локализация", "տեղայնացում"],
    "interpreting": ["interpreting", "interpreter"],
    "proofreading": ["proofreading", "proofread"],
    "editing": ["editing", "editorial"],
    "cat tools": ["cat tools", "trados", "memoq", "smartcat"],
    "accounting": ["accounting", "бухгалтерия", "бухгалтерский учет", "հաշվապահություն"],
    "bookkeeping": ["bookkeeping", "ведение учета"],
    "financial analysis": ["financial analysis", "finance analysis"],
    "budgeting": ["budgeting", "budget planning"],
    "quickbooks": ["quickbooks"],
    "sap": ["sap"],
    "market research": ["market research"],
    "operations management": ["operations management", "operations"],
    "supply chain": ["supply chain", "logistics"],
    "quality assurance": ["quality assurance", "qa"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular", "angularjs"],
    "vue.js": ["vue.js", "vuejs", "vue"],
    "graphql": ["graphql", "graph ql"],
    "next.js": ["next.js", "nextjs"],
    "node.js": ["node.js", "nodejs"],
    "express.js": ["express.js", "expressjs", "express"],
    "java": ["java"],
    "spring": ["spring", "spring boot"],
    "c#": ["c#"],
    "php": ["php"],
    "laravel": ["laravel"],
    "wordpress": ["wordpress"],
    "django": ["django"],
    "flutter": ["flutter"],
    "dart": ["dart"],
    "swift": ["swift"],
    "ios development": ["ios", "ios development"],
    "android development": ["android", "android development"],
    "mongodb": ["mongodb", "mongo db"],
    "oracle": ["oracle"],
    "database administration": ["database administration", "database administrator", "dba"],
    "network administration": ["network administration", "network administrator"],
    "bash": ["bash", "shell scripting"],
    "ruby": ["ruby"],
    "puppet": ["puppet"],
    "chef": ["chef"],
    "windows server": ["windows server"],
    "html": ["html"],
    "css": ["css"],
}

ROLE_PROFILES = {
    "data analytics": [
        "python",
        "sql",
        "excel",
        "pandas",
        "data analysis",
        "data visualization",
        "statistics",
        "dashboard development",
        "tableau",
        "power bi",
    ],
    "data analysis": [
        "python",
        "sql",
        "excel",
        "pandas",
        "data analysis",
        "data visualization",
        "statistics",
        "dashboard development",
        "tableau",
        "power bi",
    ],
    "ml engineer": [
        "python",
        "machine learning",
        "scikit-learn",
        "feature engineering",
        "model deployment",
        "api",
        "docker",
        "cloud",
        "mlops",
        "sql",
    ],
    "machine learning": [
        "python",
        "machine learning",
        "scikit-learn",
        "feature engineering",
        "model deployment",
        "sql",
    ],
    "machine learning engineer": [
        "python",
        "machine learning",
        "scikit-learn",
        "feature engineering",
        "model deployment",
        "api",
        "docker",
        "cloud",
        "mlops",
        "sql",
    ],
    "data analyst": [
        "python",
        "sql",
        "excel",
        "pandas",
        "data analysis",
        "data visualization",
        "statistics",
        "dashboard development",
        "tableau",
        "power bi",
    ],
    "business analyst": [
        "sql",
        "excel",
        "data analysis",
        "data visualization",
        "statistics",
        "dashboard development",
        "power bi",
    ],
    "data scientist": [
        "python",
        "sql",
        "machine learning",
        "statistics",
        "data visualization",
        "feature engineering",
        "scikit-learn",
        "model deployment",
    ],
    "devops engineer": [
        "linux",
        "docker",
        "kubernetes",
        "cloud",
        "aws",
        "terraform",
        "ci/cd",
        "github actions",
        "git",
        "devops",
    ],
    "cloud engineer": [
        "linux",
        "cloud",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "terraform",
        "ci/cd",
    ],
    "hr": [
        "human resources",
        "recruitment",
        "talent acquisition",
        "employee relations",
        "performance management",
        "payroll processing",
        "labor law compliance",
        "communication",
        "interpersonal skills",
        "conflict management",
        "training and development",
    ],
    "human resources": [
        "human resources",
        "recruitment",
        "talent acquisition",
        "employee relations",
        "performance management",
        "payroll processing",
        "labor law compliance",
        "communication",
        "interpersonal skills",
        "conflict management",
        "training and development",
    ],
    "human resources manager": [
        "human resources",
        "recruitment",
        "employee relations",
        "performance management",
        "labor law compliance",
        "communication",
        "leadership",
        "training and development",
        "payroll processing",
    ],
    "digital marketing": [
        "seo",
        "sem",
        "google ads",
        "meta ads",
        "content marketing",
        "social media marketing",
        "email marketing",
        "google analytics",
        "copywriting",
    ],
    "marketing manager": [
        "marketing",
        "market research",
        "content marketing",
        "social media marketing",
        "google analytics",
        "leadership",
        "project management",
        "crm",
    ],
    "translator": [
        "translation",
        "localization",
        "proofreading",
        "editing",
        "cat tools",
        "communication",
    ],
    "interpreter": [
        "interpreting",
        "translation",
        "communication",
        "interpersonal skills",
    ],
    "accountant": [
        "accounting",
        "bookkeeping",
        "excel",
        "quickbooks",
        "sap",
        "financial analysis",
        "budgeting",
    ],
    "finance analyst": [
        "financial analysis",
        "excel",
        "sql",
        "budgeting",
        "data analysis",
        "power bi",
    ],
    "sales manager": [
        "sales",
        "lead generation",
        "account management",
        "crm",
        "communication",
        "leadership",
    ],
    "project manager": [
        "project management",
        "agile",
        "jira",
        "communication",
        "leadership",
        "risk management",
    ],
    "product manager": [
        "product management",
        "market research",
        "project management",
        "agile",
        "communication",
        "data analysis",
    ],
    "ui designer": [
        "ui design",
        "ux design",
        "figma",
        "graphic design",
        "adobe photoshop",
        "adobe illustrator",
    ],
    "software engineer": [
        "javascript",
        "typescript",
        "react",
        "node.js",
        "api",
        "git",
        "sql",
    ],
    "frontend developer": [
        "javascript",
        "typescript",
        "react",
        "html",
        "css",
        "git",
    ],
    "backend developer": [
        "python",
        "node.js",
        "sql",
        "api",
        "docker",
        "git",
    ],
    "fullstack developer": [
        "javascript",
        "react",
        "node.js",
        "sql",
        "api",
        "git",
    ],
    "full stack developer": [
        "javascript",
        "react",
        "node.js",
        "sql",
        "api",
        "git",
    ],
    "ios developer": [
        "swift",
        "ios development",
        "git",
    ],
    "android developer": [
        "android development",
        "java",
        "git",
    ],
}

ACTION_VERBS = {
    "built",
    "created",
    "designed",
    "implemented",
    "improved",
    "automated",
    "deployed",
    "analyzed",
    "optimized",
    "reduced",
    "increased",
}

SKILL_EQUIVALENTS = {
    "machine learning": {
        "classification",
        "regression",
        "scikit-learn",
        "lstm",
        "lightgbm",
        "feature engineering",
        "model deployment",
    },
    "model deployment": {"api", "fastapi", "flask", "docker", "cloud", "mlops"},
    "deep learning": {"lstm", "cnn", "rnn", "pytorch", "tensorflow", "keras", "neural networks"},
    "data visualization": {"tableau", "power bi", "matplotlib", "seaborn", "plotly", "dashboard development"},
    "api": {"fastapi", "flask", "rest api"},
    "cloud": {"aws", "azure", "gcp", "docker", "kubernetes"},
    "etl": {"data pipelines", "airflow", "dbt"},
    "devops": {"docker", "kubernetes", "linux", "terraform", "ci/cd", "github actions"},
    "ci/cd": {"github actions"},
}


def analyze_resume(
    resume_text: str,
    job_description: Optional[str] = None,
    analysis_mode: str = "openai",
) -> ResumeAnalysisResponse:
    normalized_mode = analysis_mode.lower().strip()

    if normalized_mode in {"openai", "groq"}:
        llm_result = _try_analyze_resume_with_llm(
            resume_text=resume_text,
            job_description=job_description,
            provider=normalized_mode,
        )
        if llm_result:
            llm_result.analysis_mode = normalized_mode
            return llm_result
        fallback_result = analyze_resume_locally(
            resume_text=resume_text,
            job_description=job_description,
            use_nlp=True,
        )
        fallback_result.fallback_notice = (
            f"{_provider_label(normalized_mode)} is unavailable, rate-limited, or returned an invalid response. "
            "Local Intelligence was used instead."
        )
        return fallback_result

    if normalized_mode == "local":
        return analyze_resume_locally(
            resume_text=resume_text,
            job_description=job_description,
            use_nlp=False,
        )

    return analyze_resume_locally(
        resume_text=resume_text,
        job_description=job_description,
        use_nlp=True,
    )


def _provider_label(provider: str) -> str:
    labels = {
        "openai": "OpenAI GPT",
        "groq": "Groq Llama",
    }
    return labels.get(provider, provider)


def analyze_resume_locally(
    resume_text: str,
    job_description: Optional[str] = None,
    use_nlp: bool = True,
) -> ResumeAnalysisResponse:
    normalized_resume = _normalize(resume_text)
    normalized_job = _normalize(job_description or "")

    all_detected_skills = _detect_skills(normalized_resume)
    required_skills = _infer_required_skills(normalized_job) if normalized_job else []
    relevant_detected_skills = _filter_relevant_detected_skills(
        detected_skills=all_detected_skills,
        required_skills=required_skills,
    )
    displayed_skills = relevant_detected_skills if normalized_job else all_detected_skills
    missing_skill_names = [
        skill for skill in required_skills if not _is_required_skill_satisfied(skill, all_detected_skills)
    ]

    resume_score = _score_resume_quality(normalized_resume, all_detected_skills)
    keyword_job_match_score = _score_job_match(all_detected_skills, required_skills) if required_skills else None
    semantic_job_text = _build_semantic_job_text(normalized_job, required_skills)
    semantic_job_score = _try_semantic_score(normalized_resume, semantic_job_text) if use_nlp and normalized_job else None
    job_match_score = _combine_job_scores(keyword_job_match_score, semantic_job_score)
    nlp_missing_skills = (
        _try_semantic_skill_gaps(normalized_resume, semantic_job_text, required_skills, all_detected_skills)
        if use_nlp and normalized_job
        else []
    )
    missing_skill_names = [
        skill
        for skill in _merge_unique(missing_skill_names, nlp_missing_skills)
        if not _is_required_skill_satisfied(skill, all_detected_skills)
    ][:MAX_MISSING_SKILLS]
    ats_score = _score_ats(
        resume_score=resume_score,
        job_match_score=job_match_score,
        semantic_job_score=semantic_job_score,
    )

    strengths = _build_strengths(normalized_resume, displayed_skills, required_skills)
    weaknesses = _build_weaknesses(normalized_resume, displayed_skills, missing_skill_names, required_skills)
    recommendations = _build_recommendations(missing_skill_names, normalized_resume, required_skills)

    return ResumeAnalysisResponse(
        analysis_mode="nlp_local" if semantic_job_score is not None else "local",
        ats_score=max(0, min(100, ats_score)),
        job_match_score=job_match_score,
        detected_skills=displayed_skills,
        missing_skills=[
            SkillGap(skill=skill, reason="Required or semantically important for the job, but weak or missing in the resume.")
            for skill in missing_skill_names
        ],
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        improved_summary=_build_improved_summary(displayed_skills, missing_skill_names, required_skills),
    )


def _try_analyze_resume_with_llm(
    resume_text: str,
    job_description: Optional[str],
    provider: str = "openai",
) -> Optional[ResumeAnalysisResponse]:
    prompt = (
        "Analyze this resume for the target job. Return only JSON.\n\n"
        "JSON shape:\n"
        "{\n"
        '  "ats_score": integer 0-100,\n'
        '  "job_match_score": integer 0-100 or null,\n'
        '  "detected_skills": ["skill explicitly present in the resume text"],\n'
        '  "missing_skills": [{"skill": "skill", "reason": "short reason"}],\n'
        '  "strengths": ["specific strength"],\n'
        '  "weaknesses": ["specific weakness"],\n'
        '  "recommendations": ["specific recommendation"],\n'
        '  "improved_summary": "2-3 sentence rewritten resume summary"\n'
        "}\n\n"
        f"Resume text:\n{_trim_text(resume_text)}\n\n"
        f"Job description:\n{_trim_text(job_description or 'Not provided')}"
    )
    # system_prompt = (
    #     "You are an expert ATS resume reviewer for data science roles. "
    #     "You must return valid JSON only. Be strict but fair. Do not invent experience, employers, "
    #     "degrees, certificates, metrics, or skills that are not present. "
    #     "For detected_skills, include only skills explicitly written in the resume text. "
    #     "Do not infer broad parent categories such as deep learning, cloud, or API unless the exact concept "
    #     "or a clearly named tool from that category appears in the resume. If a skill is required by the job "
    #     "but missing in the resume, put it in missing_skills, not detected_skills. If a job description is not provided, "
    #     "set job_match_score to null and infer general data-role fit from the resume."
    # )
    system_prompt = (
        "You are an expert ATS resume reviewer and career coach. "
        "Return valid JSON only. Be strict, but do not punish a resume for skills that are not clearly required. "
        "Do not invent experience, employers, degrees, certificates, metrics, or skills. "

        # Универсальность
        "Analyze the resume for ANY professional role — software engineering, marketing, "
        "finance, design, data science, management, sales, or any other field. "
        "Automatically detect the target role from resume content and job description. "

        # Scoring
        "ats_score: evaluate structure, clarity, action verbs, measurable outcomes, and ATS readability. "
        "job_match_score: consider required skills, equivalent tools, project evidence, seniority fit, and domain relevance. "
        "Do not use a raw keyword ratio as the only score. "

        # Skills
        "detected_skills: lowercase, specific tools and skills only, no duplicates. "
        "Relevant to the detected role — technical skills, soft skills, domain knowledge, tools. "
        "missing_skills: list only the most important gaps for the target role. "
        "Prioritize job description requirements if provided. "

        "If job description is not provided, set job_match_score to null."
    )
    try:
        payload = generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            max_output_tokens=1400,
            provider=provider,
        )
        result = ResumeAnalysisResponse.model_validate(payload)
        result.analysis_mode = provider
        return _post_process_llm_result(
            result=result,
            resume_text=resume_text,
            job_description=job_description,
            provider=provider,
        )
    except (LLMUnavailableError, ValidationError, ValueError):
        return None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _post_process_llm_result(
    result: ResumeAnalysisResponse,
    resume_text: str,
    job_description: Optional[str],
    provider: str,
) -> ResumeAnalysisResponse:
    normalized_resume = _normalize(resume_text)
    normalized_job = _normalize(job_description or "")
    job_is_short_title = _is_short_role_query(normalized_job)

    keyword_detected = _detect_skills(normalized_resume)
    llm_detected = [
        _normalize_skill_name(skill)
        for skill in result.detected_skills
        if _skill_has_text_evidence(skill, normalized_resume)
    ]
    all_verified_skills = _merge_unique(keyword_detected, llm_detected)

    known_required_skills = _infer_required_skills(normalized_job) if normalized_job else []
    llm_missing = [
        _normalize_skill_name(gap.skill)
        for gap in result.missing_skills
        if normalized_job and _normalize_skill_name(gap.skill)
    ]
    if job_is_short_title:
        required_skills = known_required_skills
    else:
        llm_missing_with_job_evidence = [
            skill for skill in llm_missing if _skill_has_text_evidence(skill, normalized_job)
        ]
        required_skills = _merge_unique(known_required_skills, llm_missing_with_job_evidence)

    if known_required_skills:
        displayed_skills = _filter_relevant_detected_skills(all_verified_skills, known_required_skills)
        missing_skill_names = [
            skill for skill in required_skills if not _is_required_skill_satisfied(skill, all_verified_skills)
        ][:MAX_MISSING_SKILLS]
        keyword_job_match_score = _score_job_match(all_verified_skills, known_required_skills)
        job_match_score = _blend_llm_and_keyword_job_score(
            llm_score=result.job_match_score,
            keyword_score=keyword_job_match_score,
        )
    else:
        displayed_skills = all_verified_skills
        missing_skill_names = [
            skill for skill in llm_missing if not _is_required_skill_satisfied(skill, all_verified_skills)
        ][:MAX_MISSING_SKILLS]
        job_match_score = _clamp_score(result.job_match_score) if normalized_job and result.job_match_score is not None else None

    result.analysis_mode = provider
    result.detected_skills = displayed_skills
    result.missing_skills = [
        SkillGap(skill=skill, reason="Required for the target role, but not clearly evidenced in the resume.")
        for skill in missing_skill_names
    ]
    result.job_match_score = job_match_score
    result.ats_score = _clamp_score(result.ats_score)

    if result.job_match_score is not None:
        result.job_match_score = _clamp_score(result.job_match_score)

    return result


def _normalize_skill_name(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.lower()).strip()


def _skill_has_text_evidence(skill: str, normalized_text: str) -> bool:
    normalized_skill = _normalize_skill_name(skill)
    if not normalized_skill:
        return False

    known_keywords = SKILL_KEYWORDS.get(normalized_skill)
    if known_keywords:
        return any(_contains_keyword(normalized_text, keyword) for keyword in known_keywords)

    return _contains_keyword(normalized_text, normalized_skill)


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _is_short_role_query(job_text: str) -> bool:
    if not job_text:
        return False

    tokens = re.findall(r"[a-z0-9+#]+", job_text)
    if len(tokens) > 8 or len(job_text) > 100:
        return False

    description_markers = {
        "responsibilities",
        "requirements",
        "qualifications",
        "benefits",
        "salary",
        "experience",
        "we",
        "looking",
        "candidate",
        "must",
        "should",
    }
    return not any(token in description_markers for token in tokens)


def _blend_llm_and_keyword_job_score(
    llm_score: Optional[int],
    keyword_score: int,
) -> int:
    if llm_score is None:
        return keyword_score

    clamped_llm_score = _clamp_score(llm_score)
    return round((keyword_score * 0.55) + (clamped_llm_score * 0.45))


def _detect_skills(text: str) -> list[str]:
    detected = []
    for skill, keywords in SKILL_KEYWORDS.items():
        if any(_contains_keyword(text, keyword) for keyword in keywords):
            detected.append(skill)
    return detected


def _infer_required_skills(job_text: str) -> list[str]:
    required = _detect_skills(job_text)
    matched_curated_profile = False
    for role_name, role_skills in ROLE_PROFILES.items():
        if _contains_keyword(job_text, role_name):
            required = _merge_unique(required, role_skills)
            matched_curated_profile = True

    if not matched_curated_profile:
        required = _merge_unique(required, _best_curated_role_skills(job_text))
        if _is_weak_required_skill_set(required):
            required = _merge_unique(required, _best_generated_role_skills(job_text))

    if _contains_keyword(job_text, "analyst") and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["data analyst"])
    if _contains_keyword(job_text, "engineer") and ("ml" in job_text.split() or _contains_keyword(job_text, "machine learning")):
        required = _merge_unique(required, ROLE_PROFILES["ml engineer"])
    if _contains_keyword(job_text, "marketing") and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["digital marketing"])
    if _contains_keyword(job_text, "translator") and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["translator"])
    if (_contains_keyword(job_text, "accounting") or _contains_keyword(job_text, "accountant")) and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["accountant"])
    if _contains_keyword(job_text, "sales") and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["sales manager"])
    if _contains_keyword(job_text, "designer") and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["ui designer"])
    if _contains_keyword(job_text, "project manager") and _is_weak_required_skill_set(required):
        required = _merge_unique(required, ROLE_PROFILES["project manager"])
    return required[:MAX_REQUIRED_SKILLS]


def _is_weak_required_skill_set(required: list[str]) -> bool:
    return len(required) <= 1


def _best_curated_role_skills(job_text: str) -> list[str]:
    best_score = 0.0
    best_skills: list[str] = []
    for role_name, role_skills in ROLE_PROFILES.items():
        score = _role_match_score(job_text, role_name)
        if score > best_score:
            best_score = score
            best_skills = role_skills

    return best_skills if best_score >= 0.70 else []


@lru_cache(maxsize=1)
def _load_generated_role_profiles() -> dict[str, list[str]]:
    if not GENERATED_JOB_SKILL_PROFILES_PATH.exists():
        return {}

    try:
        payload = json.loads(GENERATED_JOB_SKILL_PROFILES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    profiles = payload.get("profiles", payload)
    if not isinstance(profiles, dict):
        return {}

    normalized_profiles: dict[str, list[str]] = {}
    for role_name, skills in profiles.items():
        if not isinstance(role_name, str) or not isinstance(skills, list):
            continue
        normalized_skills = [
            _normalize_skill_name(str(skill))
            for skill in skills
            if isinstance(skill, str) and _normalize_skill_name(skill)
        ]
        if normalized_skills:
            normalized_profiles[_normalize(role_name)] = _merge_unique(normalized_skills, [])

    return normalized_profiles


def _best_generated_role_skills(job_text: str) -> list[str]:
    profiles = _load_generated_role_profiles()
    if not profiles:
        return []

    best_score = 0.0
    best_skills: list[str] = []
    for role_name, role_skills in profiles.items():
        score = _role_match_score(job_text, role_name)
        if score > best_score:
            best_score = score
            best_skills = role_skills

    return best_skills if best_score >= 0.55 else []


def _role_match_score(job_text: str, role_name: str) -> float:
    normalized_job = _normalize(job_text)
    normalized_role = _normalize(role_name)
    if not normalized_job or not normalized_role:
        return 0.0
    if normalized_job == normalized_role:
        return 1.0

    job_tokens = _role_tokens(normalized_job)
    role_tokens = _role_tokens(normalized_role)

    if _contains_keyword(normalized_role, normalized_job):
        return 0.62 if len(job_tokens) == 1 else 0.85
    if _contains_keyword(normalized_job, normalized_role):
        return 0.8

    if not job_tokens or not role_tokens:
        return 0.0

    overlap = len(job_tokens & role_tokens)
    precision = overlap / len(job_tokens)
    recall = overlap / len(role_tokens)
    return (precision * 0.75) + (recall * 0.25)


def _role_tokens(text: str) -> set[str]:
    stopwords = {
        "senior",
        "junior",
        "middle",
        "lead",
        "principal",
        "remote",
        "hybrid",
        "intern",
        "internship",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9+#]+", _normalize(text))
        if len(token) > 1 and token not in stopwords
    }


def _filter_relevant_detected_skills(detected_skills: list[str], required_skills: list[str]) -> list[str]:
    if not required_skills:
        return detected_skills

    relevant = []
    for detected_skill in detected_skills:
        if any(_detected_skill_supports_requirement(detected_skill, required_skill) for required_skill in required_skills):
            relevant.append(detected_skill)
    return relevant


def _detected_skill_supports_requirement(detected_skill: str, required_skill: str) -> bool:
    if detected_skill == required_skill:
        return True
    return detected_skill in SKILL_EQUIVALENTS.get(required_skill, set())


def _build_semantic_job_text(job_text: str, required_skills: list[str]) -> str:
    if not required_skills:
        return job_text
    return " ".join([job_text, "required skills:", ", ".join(required_skills)])


def _contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", text) is not None


def _score_resume_quality(text: str, detected_skills: list[str]) -> int:
    score = 35

    word_count = len(text.split())
    if word_count >= 250:
        score += 15
    elif word_count >= 120:
        score += 8

    score += min(len(detected_skills) * 5, 25)

    if re.search(r"\d+%|\$?\d+[kKmM]?|[0-9]+x", text):
        score += 10

    if any(verb in text for verb in ACTION_VERBS):
        score += 10

    if "project" in text or "experience" in text:
        score += 5

    return max(0, min(100, score))


def _score_job_match(detected_skills: list[str], required_skills: list[str]) -> int:
    if not required_skills:
        return 0

    matched = len([skill for skill in required_skills if _is_required_skill_satisfied(skill, detected_skills)])
    return round((matched / len(required_skills)) * 100)


def _is_required_skill_satisfied(required_skill: str, detected_skills: list[str]) -> bool:
    if required_skill in detected_skills:
        return True

    equivalents = SKILL_EQUIVALENTS.get(required_skill, set())
    return any(skill in detected_skills for skill in equivalents)


def _combine_job_scores(keyword_score: Optional[int], semantic_score_value: Optional[int]) -> Optional[int]:
    if keyword_score is None and semantic_score_value is None:
        return None
    if keyword_score is None:
        return semantic_score_value
    if semantic_score_value is None:
        return keyword_score
    return round((keyword_score * 0.45) + (semantic_score_value * 0.55))


def _score_ats(
    resume_score: int,
    job_match_score: Optional[int],
    semantic_job_score: Optional[int],
) -> int:
    if job_match_score is None:
        return max(0, min(100, resume_score))

    semantic_component = semantic_job_score if semantic_job_score is not None else job_match_score
    return max(
        0,
        min(
            100,
            round((resume_score * 0.45) + (job_match_score * 0.35) + (semantic_component * 0.20)),
        ),
    )


def _try_semantic_score(resume_text: str, job_description: str) -> Optional[int]:
    try:
        return semantic_score(resume_text, job_description)
    except NLPUnavailableError:
        return None


def _try_semantic_skill_gaps(
    resume_text: str,
    job_description: str,
    required_skills: list[str],
    detected_skills: list[str],
) -> list[str]:
    try:
        return semantic_skill_gaps(resume_text, job_description, required_skills, detected_skills)
    except NLPUnavailableError:
        return []


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged = []
    seen = set()
    for item in [*primary, *secondary]:
        if item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


def _build_strengths(text: str, detected_skills: list[str], required_skills: list[str]) -> list[str]:
    strengths = []

    if required_skills and detected_skills:
        strengths.append(f"Matches job-relevant skills: {', '.join(detected_skills[:6])}.")
    elif detected_skills:
        strengths.append(f"Shows technical coverage: {', '.join(detected_skills[:6])}.")
    if re.search(r"\d+%|\$?\d+[kKmM]?|[0-9]+x", text):
        strengths.append("Includes measurable impact, which helps ATS and recruiter review.")
    if any(verb in text for verb in ACTION_VERBS):
        strengths.append("Uses action-oriented language for experience descriptions.")

    return strengths or ["Resume has enough text to start analysis, but technical evidence is limited."]


def _build_weaknesses(
    text: str,
    detected_skills: list[str],
    missing_skills: list[str],
    required_skills: list[str],
) -> list[str]:
    weaknesses = []

    if required_skills and len(detected_skills) < max(2, len(required_skills) // 3):
        weaknesses.append("The resume has limited evidence for the selected role's core requirements.")
    elif not required_skills and len(detected_skills) < 4:
        weaknesses.append("Role-relevant skill coverage is thin for the target role.")
    if missing_skills:
        weaknesses.append("Several role-specific skills are missing or not clearly evidenced.")
    if not re.search(r"\d+%|\$?\d+[kKmM]?|[0-9]+x", text):
        weaknesses.append("Achievements need more numbers, metrics, or business impact.")
    if "project" not in text and "experience" not in text:
        weaknesses.append("The resume should make project or work experience sections clearer.")

    return weaknesses or ["No major structural weakness detected in the current MVP analysis."]


def _build_recommendations(missing_skills: list[str], text: str, required_skills: list[str]) -> list[str]:
    recommendations = [
        "Start bullets with action verbs and connect each bullet to a measurable outcome.",
        "Group skills by category so recruiters can scan role-relevant tools, domain knowledge, and strengths quickly.",
    ]

    if required_skills:
        recommendations.insert(
            0,
            f"Tailor the resume around these target requirements: {', '.join(required_skills[:6])}.",
        )

    if missing_skills:
        recommendations.insert(
            0,
            f"Add evidence for these role-specific skills if truthful: {', '.join(missing_skills[:6])}.",
        )

    if not re.search(r"\d+%|\$?\d+[kKmM]?|[0-9]+x", text):
        recommendations.append("Add metrics such as accuracy, time saved, revenue impact, or dataset size.")

    return recommendations


def _build_improved_summary(
    detected_skills: list[str],
    missing_skills: list[str],
    required_skills: list[str],
) -> str:
    all_skills = _merge_unique(detected_skills, required_skills)
    domain = _summary_domain(all_skills)
    skill_phrase = ", ".join(detected_skills[:4]) if detected_skills else domain["fallback_skill"]
    gap_phrase = ""
    if missing_skills:
        gap_phrase = f" Target roles requiring {', '.join(missing_skills[:3])} by adding truthful project evidence."
    elif required_skills:
        gap_phrase = f" Position the resume around {', '.join(required_skills[:3])} with clear project outcomes."

    return (
        f"{domain['title']} with hands-on experience in {skill_phrase}. "
        f"Skilled at {domain['impact']} and communicating results clearly.{gap_phrase}"
    )


def _summary_domain(skills: list[str]) -> dict[str, str]:
    skill_set = set(skills)
    if skill_set & {"human resources", "recruitment", "talent acquisition", "employee relations"}:
        return {
            "title": "HR professional",
            "fallback_skill": "recruitment, employee support, and stakeholder communication",
            "impact": "supporting hiring, employee communication, and people operations",
        }
    if skill_set & {"marketing", "seo", "sem", "content marketing", "social media marketing", "google analytics"}:
        return {
            "title": "Marketing professional",
            "fallback_skill": "campaign execution, audience research, and marketing analytics",
            "impact": "planning campaigns, tracking performance, and improving audience engagement",
        }
    if skill_set & {"sales", "lead generation", "account management", "crm"}:
        return {
            "title": "Sales professional",
            "fallback_skill": "lead generation, client communication, and CRM management",
            "impact": "building pipeline, managing customer relationships, and closing opportunities",
        }
    if skill_set & {"translation", "localization", "interpreting", "proofreading", "cat tools"}:
        return {
            "title": "Language professional",
            "fallback_skill": "translation, localization, and editorial review",
            "impact": "delivering accurate translations, adapting content, and maintaining terminology quality",
        }
    if skill_set & {"accounting", "bookkeeping", "financial analysis", "budgeting"}:
        return {
            "title": "Finance professional",
            "fallback_skill": "accounting, financial analysis, and reporting",
            "impact": "maintaining accurate records, analyzing financial data, and supporting budget decisions",
        }
    if skill_set & {"ui design", "ux design", "figma", "graphic design"}:
        return {
            "title": "Design professional",
            "fallback_skill": "user interface design, visual design, and prototyping",
            "impact": "creating clear user experiences, visual systems, and production-ready design assets",
        }
    if skill_set & {"python", "javascript", "typescript", "react", "node.js", "api", "docker"}:
        return {
            "title": "Software professional",
            "fallback_skill": "software development, debugging, and delivery",
            "impact": "building reliable features, solving technical problems, and shipping maintainable systems",
        }
    if skill_set & {"data analysis", "sql", "excel", "pandas", "statistics", "power bi", "tableau"}:
        return {
            "title": "Data professional",
            "fallback_skill": "data analysis, reporting, and decision support",
            "impact": "turning data into insights, building reports, and supporting business decisions",
        }
    return {
        "title": "Professional",
        "fallback_skill": "role-relevant problem solving",
        "impact": "solving practical problems, organizing work clearly, and delivering measurable outcomes",
    }


def _trim_text(text: str, limit: int = 9000) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit]}..."
