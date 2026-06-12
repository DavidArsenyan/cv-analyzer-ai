import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "CV Analyzer AI",
    short_name: "CV Analyzer",
    description: "AI-assisted resume analysis, ATS scoring, and career document generation.",
    start_url: "/",
    display: "standalone",
    background_color: "#f8fbfa",
    theme_color: "#0d7a5f",
    icons: [
      {
        src: "/icon",
        sizes: "64x64",
        type: "image/png",
      },
      {
        src: "/apple-icon",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  };
}
