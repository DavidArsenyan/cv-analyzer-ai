import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: "Terms of Use",
  description: "Terms of Use for CV Analyzer AI resume analysis, ATS scoring, and career document tools.",
  alternates: { canonical: "/terms" },
};

export default function TermsPage() {
  return (
    <SeoPage
      eyebrow="Terms"
      title="Terms of Use"
      description="Basic terms for using CV Analyzer AI and its resume analysis tools."
    >
      <section>
        <h2>Use of the service</h2>
        <p>
          CV Analyzer AI provides resume analysis, ATS-style scoring, job-fit feedback, and career document tools for
          informational purposes. You are responsible for reviewing and editing any generated content before using it.
        </p>
      </section>
      <section>
        <h2>No hiring guarantee</h2>
        <p>
          Scores and recommendations are guidance only. CV Analyzer AI does not guarantee interviews, job offers,
          employer decisions, or applicant tracking system outcomes.
        </p>
      </section>
      <section>
        <h2>User content</h2>
        <p>
          You should only upload resumes and job descriptions that you have the right to process. Do not upload content
          that is unlawful, harmful, or contains information you are not authorized to share.
        </p>
      </section>
      <section>
        <h2>Service availability</h2>
        <p>
          The service may change, slow down, or become temporarily unavailable due to maintenance, provider limits, or
          infrastructure issues.
        </p>
      </section>
    </SeoPage>
  );
}

