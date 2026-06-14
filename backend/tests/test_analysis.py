from __future__ import annotations

import unittest

from app.schemas import ResumeAnalysisResponse, SkillGap
import app.services.analysis as analysis_service
from app.services.analysis import _post_process_llm_result, analyze_resume


class LocalAnalysisTests(unittest.TestCase):
    def test_data_analyst_role_filters_relevant_skills(self) -> None:
        resume = (
            "Built Python, SQL, and Docker dashboards with pandas. "
            "Improved reporting accuracy by 20% using dashboard development."
        )

        result = analyze_resume(resume, "data analyst", "local")

        self.assertIn("sql", result.detected_skills)
        self.assertIn("dashboard development", result.detected_skills)
        self.assertNotIn("docker", result.detected_skills)
        self.assertIn("statistics", [gap.skill for gap in result.missing_skills])

    def test_data_analysis_short_role_expands_to_analytics_profile(self) -> None:
        resume = (
            "Built Python and SQL reporting workflows with pandas. "
            "Created dashboards and improved data analysis quality by 20%."
        )

        result = analyze_resume(resume, "Data Analysis", "local")

        self.assertIn("python", result.detected_skills)
        self.assertIn("sql", result.detected_skills)
        self.assertIn("pandas", result.detected_skills)
        self.assertIn("data analysis", result.detected_skills)
        self.assertGreater(len(result.detected_skills), 1)

    def test_short_marketing_title_expands_to_role_profile(self) -> None:
        resume = (
            "Managed SEO, Google Analytics, content marketing, and email marketing campaigns. "
            "Improved qualified leads by 28%."
        )

        result = analyze_resume(resume, "Marketing", "local")

        self.assertIn("seo", result.detected_skills)
        self.assertIn("google analytics", result.detected_skills)
        self.assertIn("content marketing", result.detected_skills)
        self.assertGreater(len(result.missing_skills), 1)

    def test_short_translator_title_expands_to_role_profile(self) -> None:
        resume = (
            "Translated product documentation, localized website copy, and proofread technical content. "
            "Used memoQ and Smartcat for terminology consistency."
        )

        result = analyze_resume(resume, "Translator", "local")

        self.assertIn("translation", result.detected_skills)
        self.assertIn("localization", result.detected_skills)
        self.assertIn("proofreading", result.detected_skills)
        self.assertIn("cat tools", result.detected_skills)

    def test_banking_title_reports_multiple_missing_skills_for_sparse_resume(self) -> None:
        resume = "Worked with clients and prepared daily office documents."

        result = analyze_resume(resume, "banking", "local")
        missing = [gap.skill for gap in result.missing_skills]

        self.assertGreaterEqual(len(missing), 5)
        self.assertIn("banking", missing)
        self.assertIn("financial services", missing)
        self.assertIn("compliance", missing)
        self.assertIn("risk management", missing)

    def test_devops_role_profile_has_stable_missing_skills(self) -> None:
        resume = "Built Docker services and automated deployment scripts. Improved release speed by 30%."

        result = analyze_resume(resume, "devops engineer", "local")

        self.assertEqual(result.detected_skills, ["docker"])
        self.assertIn("kubernetes", [gap.skill for gap in result.missing_skills])
        self.assertIn("terraform", [gap.skill for gap in result.missing_skills])

    def test_frontend_developer_title_uses_frontend_profile(self) -> None:
        resume = "Built React interfaces with TypeScript, HTML, CSS, and Git."

        result = analyze_resume(resume, "frontend developer", "local")

        self.assertIn("react", result.detected_skills)
        self.assertIn("typescript", result.detected_skills)
        self.assertIn("html", result.detected_skills)
        self.assertNotIn("node.js", [gap.skill for gap in result.missing_skills])

    def test_hr_summary_uses_hr_language(self) -> None:
        resume = "Managed HR recruitment, talent acquisition, employee relations, and communication."

        result = analyze_resume(resume, "HR manager", "local")

        self.assertIn("HR professional", result.improved_summary)
        self.assertIn("supporting hiring", result.improved_summary)
        self.assertNotIn("improving workflows", result.improved_summary)

    def test_russian_resume_keywords_are_detected(self) -> None:
        resume = "Опыт: подбор персонала, рекрутинг, управление персоналом, коммуникация."

        result = analyze_resume(resume, "human resources", "local")

        self.assertIn("human resources", result.detected_skills)
        self.assertIn("recruitment", result.detected_skills)


class LLMPostProcessingTests(unittest.TestCase):
    def test_llm_unavailable_returns_local_result_with_notice(self) -> None:
        original = analysis_service._try_analyze_resume_with_llm
        analysis_service._try_analyze_resume_with_llm = lambda *args, **kwargs: None
        try:
            result = analyze_resume(
                "Built Docker services and automated deployment scripts. Improved release speed by 30%.",
                None,
                "groq",
            )
        finally:
            analysis_service._try_analyze_resume_with_llm = original

        self.assertEqual(result.analysis_mode, "local")
        self.assertIsNotNone(result.fallback_notice)
        self.assertIn("Groq Llama", result.fallback_notice or "")

    def test_post_processing_removes_invented_detected_skills(self) -> None:
        raw_result = ResumeAnalysisResponse(
            analysis_mode="groq",
            ats_score=82,
            job_match_score=95,
            detected_skills=["python", "deep learning", "aws"],
            missing_skills=[SkillGap(skill="terraform", reason="Required")],
            strengths=["Strong technical background."],
            weaknesses=["Missing cloud infrastructure evidence."],
            recommendations=["Add infrastructure projects."],
            improved_summary="Improved summary.",
        )

        result = _post_process_llm_result(
            result=raw_result,
            resume_text="Python SQL Docker project improved latency by 25%.",
            job_description="devops engineer",
            provider="groq",
        )

        self.assertEqual(result.detected_skills, ["docker"])
        self.assertNotIn("deep learning", result.detected_skills)
        self.assertNotIn("aws", result.detected_skills)
        self.assertLess(result.job_match_score or 100, 95)

    def test_post_processing_sets_no_job_match_without_job_description(self) -> None:
        raw_result = ResumeAnalysisResponse(
            analysis_mode="openai",
            ats_score=70,
            job_match_score=88,
            detected_skills=["python"],
            missing_skills=[SkillGap(skill="kubernetes", reason="Required")],
            strengths=["Uses Python."],
            weaknesses=["No deployment evidence."],
            recommendations=["Add metrics."],
            improved_summary="Improved summary.",
        )

        result = _post_process_llm_result(
            result=raw_result,
            resume_text="Python project improved reporting by 20%.",
            job_description=None,
            provider="openai",
        )

        self.assertEqual(result.detected_skills, ["python"])
        self.assertEqual(result.missing_skills, [])
        self.assertIsNone(result.job_match_score)


if __name__ == "__main__":
    unittest.main()
