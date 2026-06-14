import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: "Free Resume Analyzer",
  description: "Analyze your resume for ATS readiness, missing skills, strengths, weaknesses, and job-fit feedback with CV Analyzer AI.",
  alternates: { canonical: "/free-resume-analyzer" },
};

export default function FreeResumeAnalyzerPage() {
  return (
    <SeoPage
      eyebrow="Free Resume Analyzer"
      title="Free AI resume analyzer for practical resume feedback"
      description="Upload a resume, add a job title or job description, and get clear feedback before you apply."
    >
      <section>
        <h2>What the resume analyzer checks</h2>
        <p>
          CV Analyzer AI reviews resume structure, ATS readability, detected skills, missing role-specific skills,
          strengths, weaknesses, and improvement recommendations. It works with PDF, DOCX, and TXT resumes.
        </p>
      </section>
      <section>
        <h2>Use it for different roles</h2>
        <p>
          The analyzer is built for more than software roles. You can test resumes for banking, finance, marketing,
          HR, sales, translation, design, data, engineering, and other professional fields.
        </p>
      </section>
      <section>
        <h2>How to get better results</h2>
        <ul>
          <li>Add the exact job title or paste the full job description.</li>
          <li>Use a resume with clear work history, skills, education, and achievements.</li>
          <li>Add measurable outcomes where possible, such as revenue, time saved, accuracy, or volume.</li>
        </ul>
      </section>
    </SeoPage>
  );
}

