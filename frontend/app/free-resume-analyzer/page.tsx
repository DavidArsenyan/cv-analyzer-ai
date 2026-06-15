import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: "Free Resume Analyzer",
  description: "Analyze your resume for ATS readiness, missing skills, strengths, weaknesses, and job-fit feedback with CV Analyzer AI.",
  alternates: { canonical: "/free-resume-analyzer" },
};

export default function FreeResumeAnalyzerPage() {
  const faqJsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "Is CV Analyzer AI free to use?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "CV Analyzer AI offers free resume analysis for guests with usage limits. Creating an account lets you save analysis history and use additional career document tools.",
        },
      },
      {
        "@type": "Question",
        name: "What file formats are supported?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "The resume analyzer supports PDF, DOCX, and TXT files up to the upload size limit shown in the app.",
        },
      },
      {
        "@type": "Question",
        name: "Can I use it without a full job description?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes. You can enter only a job title, such as banking, marketing manager, data analyst, translator, or frontend developer. A full job description usually gives more specific feedback.",
        },
      },
      {
        "@type": "Question",
        name: "Does the ATS score guarantee a job interview?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "No. The ATS score is practical guidance for improving clarity, structure, and role fit. It does not guarantee interviews, job offers, or employer decisions.",
        },
      },
    ],
  };
  const appJsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "CV Analyzer AI",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    url: "https://cvanalyzerai.com/free-resume-analyzer",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };

  return (
    <SeoPage
      eyebrow="Free Resume Analyzer"
      title="Free AI resume analyzer for practical resume feedback"
      description="Upload a resume, add a job title or job description, and get clear feedback before you apply."
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(appJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <section>
        <h2>What the resume analyzer checks</h2>
        <p>
          CV Analyzer AI reviews resume structure, ATS readability, detected skills, missing role-specific skills,
          strengths, weaknesses, and improvement recommendations. It works with PDF, DOCX, and TXT resumes.
        </p>
      </section>
      <section>
        <h2>How it works</h2>
        <ol>
          <li>Upload your resume as a PDF, DOCX, or TXT file.</li>
          <li>Add a job title or paste a full job description.</li>
          <li>Choose the analysis model and run the resume check.</li>
          <li>Review the ATS score, job match score, skill gaps, and recommendations.</li>
          <li>Use the AI tools to draft a cover letter, interview questions, or a rewritten resume section.</li>
        </ol>
      </section>
      <section>
        <h2>Use it for different roles</h2>
        <p>
          The analyzer is built for more than software roles. You can test resumes for banking, finance, marketing,
          HR, sales, translation, design, data, engineering, and other professional fields.
        </p>
      </section>
      <section>
        <h2>What makes the feedback useful</h2>
        <p>
          The tool separates skills that are explicitly present in your resume from skills that appear to be missing
          for the target role. That distinction matters because adding truthful evidence is usually better than simply
          stuffing keywords into a resume.
        </p>
        <p>
          If your resume is short or vague, the analyzer will usually recommend stronger work history, clearer skills,
          measurable achievements, and a more targeted professional summary.
        </p>
      </section>
      <section>
        <h2>How to get better results</h2>
        <ul>
          <li>Add the exact job title or paste the full job description.</li>
          <li>Use a resume with clear work history, skills, education, and achievements.</li>
          <li>Add measurable outcomes where possible, such as revenue, time saved, accuracy, or volume.</li>
          <li>Keep job-specific tools and domain knowledge in a dedicated skills section.</li>
          <li>Review all AI-generated text before using it in real applications.</li>
        </ul>
      </section>
      <section>
        <h2>Frequently asked questions</h2>
        <h3>Is CV Analyzer AI free?</h3>
        <p>
          Guests can run free resume analysis with usage limits. Registered users can save history and access additional
          document tools.
        </p>
        <h3>Do I need a job description?</h3>
        <p>
          No. A job title is enough for a general role-based check. A full job description gives more precise missing
          skill and job-fit feedback.
        </p>
        <h3>Can I analyze a non-IT resume?</h3>
        <p>
          Yes. CV Analyzer AI is designed for different industries, including banking, finance, HR, marketing, sales,
          translation, design, operations, and software roles.
        </p>
        <h3>Is the ATS score guaranteed?</h3>
        <p>
          No. It is an estimate for improving your resume. Employers, recruiters, and applicant tracking systems use
          different criteria.
        </p>
      </section>
    </SeoPage>
  );
}
