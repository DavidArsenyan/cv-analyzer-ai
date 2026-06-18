import Link from "next/link";
import type { ReactNode } from "react";

type SeoPageProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function SeoPage({ eyebrow, title, description, children }: SeoPageProps) {
  return (
    <main className="seo-shell">
      <nav className="seo-nav" aria-label="Site navigation">
        <Link href="/" className="seo-brand">
          <span className="seo-logo">CV</span>
          <span>CV Analyzer AI</span>
        </Link>
        <div className="seo-nav-links">
          <Link href="/free-resume-analyzer">Resume Analyzer</Link>
          <Link href="/ats-resume-checker">ATS Checker</Link>
          <Link href="/contact">Contact</Link>
        </div>
      </nav>

      <article className="seo-article">
        <header className="seo-hero">
          <p>{eyebrow}</p>
          <h1>{title}</h1>
          <span>{description}</span>
          <Link href="/" className="seo-cta">
            Try CV Analyzer AI
          </Link>
        </header>
        <div className="seo-content">{children}</div>
      </article>
    </main>
  );
}

