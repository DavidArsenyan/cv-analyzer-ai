import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const routes = [
    { path: "", priority: 1 },
    { path: "/free-resume-analyzer", priority: 0.9 },
    { path: "/ats-resume-checker", priority: 0.9 },
    { path: "/resume-job-match-checker", priority: 0.9 },
    { path: "/privacy-policy", priority: 0.5 },
    { path: "/terms", priority: 0.5 },
    { path: "/contact", priority: 0.5 },
  ];

  return routes.map((route) => ({
    url: `${siteUrl}${route.path}`,
    lastModified: now,
    changeFrequency: "weekly",
    priority: route.priority,
  }));
}
