import type { Metadata } from "next";
import { SeoPage } from "../seo-page";

export const metadata: Metadata = {
  title: "Contact",
  description: "Contact CV Analyzer AI for feedback, support, privacy questions, or product suggestions.",
  alternates: { canonical: "/contact" },
};

export default function ContactPage() {
  return (
    <SeoPage
      eyebrow="Contact"
      title="Contact CV Analyzer AI"
      description="Send feedback, support questions, privacy requests, or product suggestions."
    >
      <section>
        <h2>Support and feedback</h2>
        <p>
          CV Analyzer AI is actively improving. If you find a bug, have an idea, or want to report confusing analysis
          output, include the role you tested and a short description of what happened.
        </p>
      </section>
      <section>
        <h2>Email</h2>
        <p>
          Contact: <a href="mailto:support@cvanalyzerai.com">support@cvanalyzerai.com</a>
        </p>
      </section>
      <section>
        <h2>Follow the project</h2>
        <p>
          Founder:{" "}
          <a href="https://www.linkedin.com/in/david-arsenyan-b49158220" target="_blank" rel="noopener noreferrer">
            David Arsenyan
          </a>
        </p>
        <p>
          Build updates, product progress, and launch news:{" "}
          <a href="https://tiktok.com/@cvanalyzerai" target="_blank" rel="noopener noreferrer">
            TikTok
          </a>
        </p>
      </section>
      <section>
        <h2>Privacy requests</h2>
        <p>
          For account or data deletion requests, contact us from the email address associated with your account when
          possible.
        </p>
      </section>
    </SeoPage>
  );
}
