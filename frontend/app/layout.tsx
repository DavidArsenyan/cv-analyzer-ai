import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const gaMeasurementId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "CV Analyzer AI - Resume Checker and ATS Score",
    template: "%s | CV Analyzer AI",
  },
  description: "Analyze resumes for ATS score, job match, missing skills, strengths, and AI-generated career documents across industries.",
  keywords: [
    "CV analyzer",
    "resume checker",
    "ATS resume checker",
    "job match score",
    "resume analysis",
    "cover letter generator",
    "interview questions",
    "free resume analyzer",
    "ATS score checker",
    "resume feedback",
    "AI resume review",
    "resume optimizer",
    "CV checker",
    "job application tools",
  ],
  alternates: {
    canonical: siteUrl,
  },
  applicationName: "CV Analyzer AI",
  authors: [{ name: "CV Analyzer AI" }],
  creator: "CV Analyzer AI",
  publisher: "CV Analyzer AI",
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    title: "CV Analyzer AI - Resume Checker and ATS Score",
    description: "Upload a resume, compare it with a job description, find missing skills, and generate career documents.",
    url: siteUrl,
    siteName: "CV Analyzer AI",
    type: "website",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "CV Analyzer AI",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "CV Analyzer AI - Resume Checker and ATS Score",
    description: "AI-assisted resume analysis, ATS scoring, job-fit feedback, and career document generation.",
    images: ["/opengraph-image"],
  },
  icons: {
    icon: "/icon",
    apple: "/apple-icon",
  },
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" dir="ltr">
      <body>
        {process.env.NEXT_PUBLIC_ADSENSE_CLIENT ? (
          <Script
            id="adsense-loader"
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${process.env.NEXT_PUBLIC_ADSENSE_CLIENT}`}
            crossOrigin="anonymous"
            strategy="afterInteractive"
          />
        ) : null}
        {gaMeasurementId ? (
          <>
            <Script
              id="google-analytics-loader"
              src={`https://www.googletagmanager.com/gtag/js?id=${gaMeasurementId}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics-init" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${gaMeasurementId}');
              `}
            </Script>
          </>
        ) : null}
        {children}
      </body>
    </html>
  );
}
