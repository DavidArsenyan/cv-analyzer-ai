import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: "Resume Job Match Checker",
  description: "Compare your resume with a job title or job description and find missing skills, strengths, and job-fit gaps.",
  alternates: { canonical: "/resume-job-match-checker" },
};

export default function ResumeJobMatchCheckerPage() {
  return (
    <SeoPage
      eyebrow="Resume Job Match Checker"
      title="Compare your resume with a job title or job description"
      description="Use job-fit scoring to understand how closely your resume matches a target role."
    >
      <section>
        <h2>Job title or full job description</h2>
        <p>
          You can paste a full vacancy description or enter only a job title. CV Analyzer AI uses the available context
          to estimate role-relevant skills and gaps.
        </p>
      </section>
      <section>
        <h2>What the match score means</h2>
        <p>
          The job match score reflects how much evidence your resume provides for the target role. It considers detected
          skills, missing requirements, role fit, and the clarity of your experience.
        </p>
      </section>
      <section>
        <h2>Best use cases</h2>
        <ul>
          <li>Checking whether your resume fits a specific vacancy.</li>
          <li>Finding missing skills before applying.</li>
          <li>Adapting one resume for different roles or industries.</li>
        </ul>
      </section>
    </SeoPage>
  );
}

