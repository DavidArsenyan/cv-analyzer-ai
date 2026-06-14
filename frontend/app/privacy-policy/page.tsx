import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Privacy Policy for CV Analyzer AI, including resume uploads, account data, analytics, and third-party AI providers.",
  alternates: { canonical: "/privacy-policy" },
};

export default function PrivacyPolicyPage() {
  return (
    <SeoPage
      eyebrow="Privacy Policy"
      title="Privacy Policy"
      description="How CV Analyzer AI handles uploaded resumes, account data, analytics, and service providers."
    >
      <section>
        <h2>Information we process</h2>
        <p>
          CV Analyzer AI may process your email address, uploaded resume content, job title or job description text,
          generated analysis results, and basic technical data needed to run the service.
        </p>
      </section>
      <section>
        <h2>Resume analysis</h2>
        <p>
          Resume files are parsed so the application can generate ATS feedback, job match scores, missing skills, and
          document suggestions. If you use a cloud AI model, relevant text may be sent to the selected AI provider for
          processing.
        </p>
      </section>
      <section>
        <h2>Accounts and history</h2>
        <p>
          If you create an account, CV Analyzer AI stores your email address and analysis history so you can return to
          previous results. Guest analysis may be rate-limited and may not be saved to your account.
        </p>
      </section>
      <section>
        <h2>Analytics</h2>
        <p>
          We may use Google Analytics to understand aggregate website usage, such as page views, traffic sources, device
          type, and general location. Analytics data helps improve the product and user experience.
        </p>
      </section>
      <section>
        <h2>Contact</h2>
        <p>
          For privacy questions or deletion requests, contact us through the contact page.
        </p>
      </section>
    </SeoPage>
  );
}

