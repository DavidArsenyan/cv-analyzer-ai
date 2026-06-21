import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: {
    absolute: "Free AI ATS Resume Checker | Optimize for ATS Systems",
  },
  description: "Check if your resume is ATS-friendly. Scan your CV for missing keywords, format issues, and optimize it to pass automated recruiter filters instantly.",
  alternates: { canonical: "/ats-resume-checker" },
};

export default function AtsResumeCheckerPage() {
  return (
    <SeoPage
      eyebrow="ATS Resume Checker"
      title="Check whether your resume is ready for ATS screening"
      description="Get an ATS-style score and see which role requirements are clearly supported by your resume."
    >
      <section>
        <h2>What is an ATS resume check?</h2>
        <p>
          Applicant tracking systems help employers filter and organize applications. A strong resume should be easy to
          parse, clearly structured, and aligned with the role you are applying for.
        </p>
      </section>
      <section>
        <h2>What CV Analyzer AI looks for</h2>
        <ul>
          <li>Clear resume sections and readable formatting.</li>
          <li>Relevant skills that appear explicitly in the resume text.</li>
          <li>Missing skills or domain requirements for the target role.</li>
          <li>Weak areas such as vague bullets, low evidence, or missing metrics.</li>
        </ul>
      </section>
      <section>
        <h2>ATS score is guidance, not a guarantee</h2>
        <p>
          The score is a practical estimate to help you improve your resume. Hiring decisions still depend on the
          employer, role, market, and quality of your experience.
        </p>
      </section>
    </SeoPage>
  );
}
