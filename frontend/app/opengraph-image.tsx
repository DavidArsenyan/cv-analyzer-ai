import { ImageResponse } from "next/og";

export const size = {
  width: 1200,
  height: 630,
};

export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "72px",
          background: "linear-gradient(135deg, #f8fbfa 0%, #dff5ee 100%)",
          color: "#0f172a",
          fontFamily: "Arial",
        }}
      >
        <div style={{ fontSize: 34, fontWeight: 700, color: "#0d7a5f", marginBottom: 24 }}>
          CV Analyzer AI
        </div>
        <div style={{ fontSize: 72, fontWeight: 800, lineHeight: 1.05, maxWidth: 920 }}>
          Resume Checker and ATS Score
        </div>
        <div style={{ fontSize: 30, color: "#475569", marginTop: 28, maxWidth: 920 }}>
          AI-assisted job match, skill gaps, resume feedback, and career documents.
        </div>
      </div>
    ),
    size,
  );
}
