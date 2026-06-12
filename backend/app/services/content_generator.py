from __future__ import annotations

import re
from typing import Optional

from app.services.analysis import SKILL_KEYWORDS, analyze_resume
from app.services.llm_provider import LLMUnavailableError, generate_json, generate_text


def generate_cover_letter(
    resume_text: str,
    job_description: Optional[str] = None,
    company_name: Optional[str] = None,
    role_title: Optional[str] = None,
    analysis_mode: str = "openai",
) -> str:
    if not _use_local_generation(analysis_mode):
        llm_result = _try_generate_cover_letter_with_llm(
            resume_text=resume_text,
            job_description=job_description,
            company_name=company_name,
            role_title=role_title,
        )
        if llm_result:
            return llm_result

    local_analysis = analyze_resume(resume_text, job_description, "nlp_local")
    detected_skills = local_analysis.detected_skills or _detect_skills(resume_text)
    role = role_title.strip() if role_title else _role_title_from_job(job_description)
    company = company_name.strip() if company_name else "your team"
    skill_sentence = _skill_sentence(detected_skills)
    job_focus = _job_focus(job_description)

    return (
        f"Dear Hiring Team,\n\n"
        f"I am excited to apply for the {role} at {company}. My background combines {skill_sentence}, "
        "with a practical focus on reliable execution, clear communication, and measurable outcomes.\n\n"
        f"In recent work, I have applied these strengths to solve practical problems and improve workflows. "
        f"{job_focus} I would bring a hands-on, outcome-focused approach to the role and continue building "
        "evidence around the most important requirements.\n\n"
        "Thank you for your time and consideration. I would welcome the opportunity to discuss how my skills "
        "can support your data initiatives.\n\n"
        "Sincerely,\n"
        "Candidate"
    )


def generate_interview_questions(
    resume_text: str,
    job_description: Optional[str] = None,
    analysis_mode: str = "openai",
) -> list[str]:
    if not _use_local_generation(analysis_mode):
        llm_result = _try_generate_questions_with_llm(
            resume_text=resume_text,
            job_description=job_description,
        )
        if llm_result:
            return llm_result

    local_analysis = analyze_resume(resume_text, job_description, "nlp_local")
    detected_skills = local_analysis.detected_skills or _detect_skills(resume_text)
    required_skills = [gap.skill for gap in local_analysis.missing_skills]
    focus_skills = required_skills or detected_skills[:5]

    questions = [
        "Walk me through one relevant project or work example from problem definition to final result.",
        "Which part of your experience best matches this role, and what evidence supports it?",
        "Describe a time you improved a process, result, or workflow. What changed?",
        "How do you communicate technical or detailed work to a non-technical stakeholder?",
        "What metrics would you use to prove that your work was successful?",
    ]

    for skill in focus_skills[:5]:
        questions.append(f"How have you used {skill} in a real project, and what was the outcome?")

    if required_skills:
        missing = [skill for skill in required_skills if skill not in detected_skills]
        for skill in missing[:3]:
            questions.append(f"The role mentions {skill}. How would you close that skill gap quickly?")

    return questions[:10]


def rewrite_resume_section(
    resume_text: str,
    section_type: str,
    job_description: Optional[str] = None,
    analysis_mode: str = "openai",
) -> dict[str, object]:
    normalized_section = section_type.lower().strip()
    if normalized_section not in {"summary", "experience", "skills"}:
        normalized_section = "summary"

    if not _use_local_generation(analysis_mode):
        llm_result = _try_rewrite_section_with_llm(
            resume_text=resume_text,
            section_type=normalized_section,
            job_description=job_description,
        )
        if llm_result:
            return llm_result

    return _fallback_rewrite_section(
        resume_text=resume_text,
        section_type=normalized_section,
        job_description=job_description,
    )


def _try_generate_cover_letter_with_llm(
    resume_text: str,
    job_description: Optional[str],
    company_name: Optional[str],
    role_title: Optional[str],
) -> Optional[str]:
    prompt = (
        "Write a concise, professional cover letter draft.\n\n"
        f"Role title: {role_title or 'Not provided'}\n"
        f"Company name: {company_name or 'Not provided'}\n\n"
        f"Resume text:\n{_trim_text(resume_text)}\n\n"
        f"Job description:\n{_trim_text(job_description or 'Not provided')}"
    )
    system_prompt = (
        "You are an expert career coach for data science candidates. "
        "Write truthful, specific, ATS-friendly content. Do not invent employers, degrees, or metrics. "
        "Keep the letter under 280 words."
    )

    try:
        return generate_text(prompt=prompt, system_prompt=system_prompt, max_output_tokens=650)
    except LLMUnavailableError:
        return None


def _try_generate_questions_with_llm(
    resume_text: str,
    job_description: Optional[str],
) -> Optional[list[str]]:
    prompt = (
        "Create 10 mock interview questions for this candidate. "
        "Return one question per line, without numbering.\n\n"
        f"Resume text:\n{_trim_text(resume_text)}\n\n"
        f"Job description:\n{_trim_text(job_description or 'Not provided')}"
    )
    system_prompt = (
        "You are a data science interview coach. Focus on practical projects, statistics, ML, SQL, "
        "communication, deployment, and role-specific gaps. Questions must be concise."
    )

    try:
        output = generate_text(prompt=prompt, system_prompt=system_prompt, max_output_tokens=700)
    except LLMUnavailableError:
        return None

    questions = [
        re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
        for line in output.splitlines()
    ]
    questions = [question for question in questions if question.endswith("?")]
    return questions[:10] or None


def _try_rewrite_section_with_llm(
    resume_text: str,
    section_type: str,
    job_description: Optional[str],
) -> Optional[dict[str, object]]:
    prompt = (
        f"Rewrite the candidate's resume {section_type} section for a data science or analytics role. "
        "Return only JSON with this shape: "
        '{"section_type":"summary|experience|skills","rewritten_section":"text","improvement_notes":["note"]}.\n\n'
        "Rules: preserve truth, do not invent employers/degrees/metrics, make the result ATS-friendly, "
        "and tailor to the job description when provided.\n\n"
        f"Resume text:\n{_trim_text(resume_text)}\n\n"
        f"Job description:\n{_trim_text(job_description or 'Not provided')}"
    )
    system_prompt = (
        "You are an expert resume editor for data science candidates. "
        "Return valid JSON only. Keep rewritten content concise, specific, and truthful."
    )

    try:
        payload = generate_json(prompt=prompt, system_prompt=system_prompt, max_output_tokens=900)
    except LLMUnavailableError:
        return None

    rewritten_section = str(payload.get("rewritten_section", "")).strip()
    notes = payload.get("improvement_notes", [])
    if not rewritten_section or not isinstance(notes, list):
        return None

    return {
        "section_type": section_type,
        "rewritten_section": rewritten_section,
        "improvement_notes": [str(note) for note in notes[:5]],
    }


def _fallback_rewrite_section(
    resume_text: str,
    section_type: str,
    job_description: Optional[str],
) -> dict[str, object]:
    local_analysis = analyze_resume(resume_text, job_description, "nlp_local")
    detected_skills = local_analysis.detected_skills or _detect_skills(resume_text)
    skill_sentence = _skill_sentence(detected_skills)
    job_focus = _job_focus(job_description)

    if section_type == "experience":
        focus_skills = ", ".join(detected_skills[:3]) if detected_skills else "role-relevant tools and processes"
        rewritten = (
            f"- Delivered role-relevant work using {focus_skills}, with clear ownership from problem definition to outcome.\n"
            "- Improved workflows or results by connecting daily execution to measurable business impact.\n"
            "- Communicated progress, tradeoffs, and results clearly to stakeholders and documented repeatable processes."
        )
    elif section_type == "skills":
        skills = detected_skills or ["communication", "problem solving", "process improvement"]
        rewritten = _format_skills_section(skills)
    else:
        rewritten = (
            f"Professional with hands-on experience in {skill_sentence}. "
            f"Skilled at solving practical problems, communicating clearly, and improving outcomes. {job_focus}"
        )

    return {
        "section_type": section_type,
        "rewritten_section": rewritten,
        "improvement_notes": [
            "Uses verified role-relevant skills found in the resume.",
            "Organizes skills for faster recruiter and ATS scanning.",
            "Add tools, metrics, and project context only where they are truthful.",
        ],
    }


def _detect_skills(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    detected = []
    for skill, keywords in SKILL_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            detected.append(skill)
    return detected


def _format_skills_section(skills: list[str]) -> str:
    data_tools = {
        "sql",
        "excel",
        "power bi",
        "tableau",
        "dashboard development",
        "data analysis",
        "data visualization",
        "statistics",
        "python",
        "pandas",
        "numpy",
    }
    technical_tools = {
        "docker",
        "kubernetes",
        "terraform",
        "aws",
        "azure",
        "gcp",
        "linux",
        "git",
        "ci/cd",
        "github actions",
        "fastapi",
        "postgresql",
    }

    data = [skill for skill in skills if skill in data_tools]
    technical = [skill for skill in skills if skill in technical_tools and skill not in data]
    other = [skill for skill in skills if skill not in data and skill not in technical]

    lines = []
    if data:
        lines.append(f"Data & Reporting: {', '.join(data)}")
    if technical:
        lines.append(f"Technical Tools: {', '.join(technical)}")
    if other:
        lines.append(f"Business & Professional Skills: {', '.join(other)}")

    return "\n".join(lines) if lines else "Role-Relevant Skills: " + ", ".join(skills)


def _use_local_generation(analysis_mode: str) -> bool:
    return analysis_mode.lower().strip() in {"nlp_local", "local"}


def _role_title_from_job(job_description: Optional[str]) -> str:
    if not job_description:
        return "target role"

    normalized = re.sub(r"\s+", " ", job_description).strip()
    if 2 <= len(normalized.split()) <= 6 and len(normalized) <= 80:
        return normalized

    return "target role"


def _skill_sentence(skills: list[str]) -> str:
    if not skills:
        return "data analysis, structured problem solving, and communication"

    if len(skills) == 1:
        return skills[0]

    return f"{', '.join(skills[:3])}, and {skills[min(len(skills), 4) - 1]}"


def _job_focus(job_description: Optional[str]) -> str:
    if not job_description:
        return "The role aligns with my interest in practical data products and measurable improvements."

    detected = _detect_skills(job_description)
    if detected:
        return f"The job description's focus on {', '.join(detected[:4])} strongly matches my target direction."

    return "The role's responsibilities align with my interest in practical data products and measurable improvements."


def _trim_text(text: str, limit: int = 7000) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit]}..."
