"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";

type SkillGap = { skill: string; reason: string };

type AnalysisResult = {
  analysis_mode: string;
  fallback_notice: string | null;
  ats_score: number;
  job_match_score: number | null;
  detected_skills: string[];
  missing_skills: SkillGap[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  improved_summary: string;
};

type GeneratedContent = {
  coverLetter?: string;
  interviewQuestions?: string[];
  rewrittenSection?: {
    section_type: string;
    rewritten_section: string;
    improvement_notes: string[];
  };
};

type HistoryItem = {
  id: number;
  filename: string;
  target_role: string | null;
  analysis_mode: string;
  ats_score: number;
  job_match_score: number | null;
  created_at: string;
  detected_skills: string[];
};

type AuthUser = { id: number; email: string; is_email_verified: boolean };
type ActiveTab = "analysis" | "tools" | "documents" | "history";
type AuthMode = "login" | "register" | "verify" | "forgot" | "reset";

declare global {
  interface Window {
    gtag?: (command: "event", eventName: string, params?: Record<string, string | number | boolean>) => void;
  }
}

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
const enableLocalNlp = process.env.NEXT_PUBLIC_ENABLE_LOCAL_NLP === "true";
const maxResumeBytes = 5 * 1024 * 1024;
const allowedResumeExtensions = [".pdf", ".docx", ".txt"];
const analysisProgressSteps = [
  "Extracting resume text",
  "Analyzing skills and job fit",
  "Generating feedback",
];

const Icons = {
  upload: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  ),
  file: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  ),
  spark: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  ),
  chart: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  ),
  tool: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  ),
  doc: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  ),
  history: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="12 8 12 12 14 14" />
      <path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5" />
    </svg>
  ),
  check: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  copy: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  ),
  skills: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2" />
      <line x1="9" y1="9" x2="9.01" y2="9" />
      <line x1="15" y1="9" x2="15.01" y2="9" />
    </svg>
  ),
  missing: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
  strong: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 12 2 2 4-4" />
      <path d="M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7z" />
    </svg>
  ),
  recs: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  ),
  summary: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  download: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  ),
  mail: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  ),
  questions: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  rewrite: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  loader: (
    <svg className="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
      <line x1="2" y1="12" x2="6" y2="12" />
      <line x1="18" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    </svg>
  ),
  sun: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="4" />
      <line x1="12" y1="20" x2="12" y2="22" />
      <line x1="4.93" y1="4.93" x2="6.34" y2="6.34" />
      <line x1="17.66" y1="17.66" x2="19.07" y2="19.07" />
      <line x1="2" y1="12" x2="4" y2="12" />
      <line x1="20" y1="12" x2="22" y2="12" />
      <line x1="6.34" y1="17.66" x2="4.93" y2="19.07" />
      <line x1="19.07" y1="4.93" x2="17.66" y2="6.34" />
    </svg>
  ),
  moon: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.8A8.7 8.7 0 1 1 11.2 3 6.8 6.8 0 0 0 21 12.8z" />
    </svg>
  ),
};

export default function Home() {
  const [resume, setResume] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [analysisMode, setAnalysisMode] = useState("groq");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysisProgressStep, setAnalysisProgressStep] = useState(0);
  const [generationLoading, setGenerationLoading] = useState<"cover" | "questions" | "rewrite" | null>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [rewriteSection, setRewriteSection] = useState("summary");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authExpanded, setAuthExpanded] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [verificationEmail, setVerificationEmail] = useState("");
  const [token, setToken] = useState("");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("analysis");
  const [dragOver, setDragOver] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const savedToken = window.localStorage.getItem("cv_analyzer_token");
    const savedUser = window.localStorage.getItem("cv_analyzer_user");
    const savedAnalysisMode = window.localStorage.getItem("cv_analyzer_analysis_mode");
    const savedActiveTab = window.localStorage.getItem("cv_analyzer_active_tab") as ActiveTab | null;
    const savedTheme = window.localStorage.getItem("cv_analyzer_theme");

    if (savedAnalysisMode) setAnalysisMode(savedAnalysisMode);
    if (savedTheme === "light" || savedTheme === "dark") {
      setTheme(savedTheme);
    } else if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
      setTheme("dark");
    }
    window.localStorage.removeItem("cv_analyzer_last_result");
    window.localStorage.removeItem("cv_analyzer_generated_content");
    window.localStorage.removeItem("cv_analyzer_job_description");
    if (savedActiveTab && ["analysis", "tools", "documents", "history"].includes(savedActiveTab)) {
      setActiveTab(savedActiveTab);
    }

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      void loadHistory(savedToken);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("cv_analyzer_analysis_mode", analysisMode);
  }, [analysisMode]);

  useEffect(() => {
    window.localStorage.setItem("cv_analyzer_active_tab", activeTab);
  }, [activeTab]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("cv_analyzer_theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!loading) {
      setAnalysisProgressStep(0);
      return;
    }

    setAnalysisProgressStep(0);
    const timer = window.setInterval(() => {
      setAnalysisProgressStep((current) => Math.min(current + 1, analysisProgressSteps.length - 1));
    }, 4200);

    return () => window.clearInterval(timer);
  }, [loading]);

  async function loadHistory(activeToken = token) {
    if (!activeToken) {
      setHistory([]);
      return;
    }
    try {
      const res = await fetch(`${apiUrl}/api/analyses?limit=6`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      if (res.ok) setHistory(await res.json());
    } catch {
      setHistory([]);
    }
  }

  async function readApiError(response: Response, fallback: string) {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const payload = await response.json();
      return payload.detail ?? fallback;
    }

    const text = await response.text();
    if (contentType.includes("text/html") || text.trim().startsWith("<!DOCTYPE") || text.includes("<html")) {
      if (response.status === 502 || response.status === 503 || response.status === 504) {
        return "AI analysis service is temporarily unavailable. Please try again in a moment.";
      }
      return fallback;
    }

    return text || fallback;
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (authMode === "verify") {
      await verifyEmailCode();
      return;
    }
    if (authMode === "forgot") {
      await requestPasswordReset();
      return;
    }
    if (authMode === "reset") {
      await resetPassword();
      return;
    }

    const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
    const options = authMode === "login"
      ? { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams({ username: email, password }) }
      : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) };
    try {
      const res = await fetch(`${apiUrl}${endpoint}`, options);
      if (!res.ok) {
        throw new Error(await readApiError(res, "Authentication failed."));
      }
      const payload = await res.json();
      if (authMode === "register") {
        setVerificationEmail(payload.email ?? email);
        setAuthMode("verify");
        setVerificationCode("");
        setPassword("");
        return;
      }
      setToken(payload.access_token);
      setUser(payload.user);
      setPassword("");
      setVerificationCode("");
      setVerificationEmail("");
      setAuthMode("login");
      window.localStorage.setItem("cv_analyzer_token", payload.access_token);
      window.localStorage.setItem("cv_analyzer_user", JSON.stringify(payload.user));
      await loadHistory(payload.access_token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Authentication failed.");
    }
  }

  async function verifyEmailCode() {
    const activeEmail = verificationEmail || email;
    try {
      const res = await fetch(`${apiUrl}/api/auth/verify-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: activeEmail, code: verificationCode }),
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Email verification failed."));
      }
      const payload = await res.json();
      setToken(payload.access_token);
      setUser(payload.user);
      setVerificationCode("");
      setVerificationEmail("");
      setEmail("");
      window.localStorage.setItem("cv_analyzer_token", payload.access_token);
      window.localStorage.setItem("cv_analyzer_user", JSON.stringify(payload.user));
      await loadHistory(payload.access_token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Email verification failed.");
    }
  }

  async function resendVerificationCode() {
    setError("");
    const activeEmail = verificationEmail || email;
    if (!activeEmail) {
      setError("Enter your email address first.");
      return;
    }
    try {
      const res = await fetch(`${apiUrl}/api/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: activeEmail }),
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Could not resend verification code."));
      }
      setVerificationEmail(activeEmail);
      setAuthMode("verify");
      setVerificationCode("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not resend verification code.");
    }
  }

  async function requestPasswordReset() {
    const activeEmail = email.trim();
    if (!activeEmail) {
      setError("Enter your email address first.");
      return;
    }
    try {
      const res = await fetch(`${apiUrl}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: activeEmail }),
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Could not send password reset code."));
      }
      setVerificationEmail(activeEmail);
      setVerificationCode("");
      setPassword("");
      setAuthMode("reset");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not send password reset code.");
    }
  }

  async function resetPassword() {
    const activeEmail = verificationEmail || email;
    try {
      const res = await fetch(`${apiUrl}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: activeEmail, code: verificationCode, password }),
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Password reset failed."));
      }
      const payload = await res.json();
      setToken(payload.access_token);
      setUser(payload.user);
      setVerificationCode("");
      setVerificationEmail("");
      setEmail("");
      setPassword("");
      setAuthMode("login");
      window.localStorage.setItem("cv_analyzer_token", payload.access_token);
      window.localStorage.setItem("cv_analyzer_user", JSON.stringify(payload.user));
      await loadHistory(payload.access_token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Password reset failed.");
    }
  }

  function handleLogout() {
    setToken("");
    setUser(null);
    setHistory([]);
    setResult(null);
    setGeneratedContent({});
    setAuthMode("login");
    setAuthExpanded(false);
    setPassword("");
    setVerificationCode("");
    setVerificationEmail("");
    setError("");
    window.localStorage.removeItem("cv_analyzer_token");
    window.localStorage.removeItem("cv_analyzer_user");
    clearWorkspaceState();
  }

  function clearWorkspaceState() {
    setResume(null);
    setResult(null);
    setGeneratedContent({});
    setActiveTab("analysis");
    setJobDescription("");
    window.localStorage.removeItem("cv_analyzer_last_result");
    window.localStorage.removeItem("cv_analyzer_generated_content");
    window.localStorage.removeItem("cv_analyzer_job_description");
    window.localStorage.setItem("cv_analyzer_active_tab", "analysis");
  }

  function selectResumeFile(file: File | null) {
    if (!file) {
      setResume(null);
      return;
    }

    const normalizedName = file.name.toLowerCase();
    const isAllowedType = allowedResumeExtensions.some((extension) => normalizedName.endsWith(extension));
    if (!isAllowedType) {
      setError("Unsupported file type. Upload PDF, DOCX, or TXT.");
      setResume(null);
      return;
    }

    if (file.size > maxResumeBytes) {
      setError("File is too large. Maximum size is 5 MB.");
      setResume(null);
      return;
    }

    setError("");
    setResume(file);
    trackResumeFileSelected(file);
  }

  function trackResumeFileSelected(file: File) {
    if (typeof window === "undefined" || !window.gtag) return;
    const extension = file.name.toLowerCase().split(".").pop() ?? "unknown";
    const sizeMb = file.size / (1024 * 1024);
    const sizeBucket = sizeMb < 1 ? "under_1mb" : sizeMb < 3 ? "1_3mb" : "3_5mb";

    window.gtag("event", "resume_file_selected", {
      file_extension: extension,
      file_size_bucket: sizeBucket,
      user_status: user ? "registered" : "guest",
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setGeneratedContent({});
    if (!resume) {
      setError("Upload a resume file first.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", resume);
    formData.append("analysis_mode", analysisMode);
    if (jobDescription.trim()) formData.append("job_description", jobDescription);

    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/analyze`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: formData,
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Analysis failed."));
      }
      setResult(await res.json());
      setActiveTab("analysis");
      if (token) await loadHistory(token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate(type: "cover" | "questions" | "rewrite") {
    setError("");
    if (!resume) {
      setError("Upload a resume file first.");
      return;
    }
    if (!token) {
      setError("Log in before using AI tools.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", resume);
    formData.append("analysis_mode", analysisMode);
    if (jobDescription.trim()) formData.append("job_description", jobDescription);
    if (type === "rewrite") formData.append("section_type", rewriteSection);

    const endpointMap = {
      cover: "/api/generate/cover-letter",
      questions: "/api/generate/interview-questions",
      rewrite: "/api/generate/rewrite-section",
    };

    setGenerationLoading(type);
    try {
      const res = await fetch(`${apiUrl}${endpointMap[type]}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Generation failed."));
      }
      const payload = await res.json();
      setGeneratedContent((cur) => ({
        ...cur,
        coverLetter: payload.cover_letter ?? cur.coverLetter,
        interviewQuestions: payload.questions ?? cur.interviewQuestions,
        rewrittenSection: payload.rewritten_section ? payload : cur.rewrittenSection,
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed.");
    } finally {
      setGenerationLoading(null);
    }
  }

  async function handleExportPdf() {
    setError("");
    if (!result) {
      setError("Run an analysis before exporting.");
      return;
    }
    if (!token) {
      setError("Log in before exporting.");
      return;
    }

    setExportLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/export/report`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis: result,
          cover_letter: generatedContent.coverLetter,
          rewritten_section: generatedContent.rewrittenSection?.rewritten_section,
        }),
      });
      if (!res.ok) {
        throw new Error(await readApiError(res, "Export failed."));
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "cv-analysis-report.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed.");
    } finally {
      setExportLoading(false);
    }
  }

  const tabs: Array<{ id: ActiveTab; label: string; icon: ReactNode; disabled?: boolean }> = [
    { id: "analysis", label: "Analysis", icon: Icons.chart, disabled: !result },
    { id: "tools", label: "AI Tools", icon: Icons.tool, disabled: !result },
    { id: "documents", label: "Documents", icon: Icons.doc, disabled: !result },
    { id: "history", label: "History", icon: Icons.history },
  ];
  const authFormVisible = authExpanded || authMode === "verify" || authMode === "forgot" || authMode === "reset";

  return (
    <main className="shell">
      <header className="topbar">
        <button className="brand brand-button" type="button" onClick={clearWorkspaceState} aria-label="Reset workspace">
          <div className="logo-icon">CV</div>
          <div className="brand-text">
            <span className="brand-sub">AI Career Assistant</span>
            <span className="brand-name">CV Analyzer</span>
          </div>
        </button>

        <div className="topbar-right">
          <button
            className="theme-toggle"
            type="button"
            onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <span className="theme-toggle-icon">{theme === "dark" ? Icons.sun : Icons.moon}</span>
            <span>{theme === "dark" ? "Light" : "Dark"}</span>
          </button>
          {user ? (
            <>
              <div className="avatar">{user.email.slice(0, 2).toUpperCase()}</div>
              <span className="topbar-email">{user.email}</span>
              <button className="btn-outline topbar-logout" type="button" onClick={handleLogout}>
                Sign out
              </button>
            </>
          ) : (
            <div className="status-badge">
              <span className="status-dot" />
              Guest session
            </div>
          )}
        </div>
      </header>

      <section className="workspace">
        <div className="panel input-panel">
          <div className="panel-header">
            <p className="panel-eyebrow">Resume Workspace</p>
            <h1 className="panel-title">Analyze and improve</h1>
          </div>

          {!user && (
            <div className={`auth-callout${authFormVisible ? " expanded" : ""}`}>
              <div className="auth-callout-summary">
                <div>
                  <p className="auth-callout-label">Unlock all AI tools</p>
                  <span>Optional. Try the analyzer as a guest first.</span>
                </div>
                <button
                  type="button"
                  className="auth-toggle-btn"
                  onClick={() => {
                    setAuthMode("login");
                    setAuthExpanded(!authFormVisible);
                  }}
                >
                  {authFormVisible ? "Hide" : "Login / Register"}
                </button>
              </div>
              {authFormVisible ? (
              <form className="auth-form-inner" onSubmit={handleAuth}>
                {authMode === "login" || authMode === "register" ? (
                  <div className="auth-tabs">
                    <button type="button" className={authMode === "login" ? "active" : ""} onClick={() => setAuthMode("login")}>Login</button>
                    <button type="button" className={authMode === "register" ? "active" : ""} onClick={() => setAuthMode("register")}>Register</button>
                  </div>
                ) : null}
                {authMode === "verify" ? (
                  <>
                    <input
                      type="email"
                      value={verificationEmail || email}
                      onChange={(e) => {
                        setVerificationEmail(e.target.value);
                        setEmail(e.target.value);
                      }}
                      placeholder="Email address"
                      required
                    />
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder="6-digit code"
                      required
                    />
                    <button type="submit">Verify email</button>
                    <button type="button" className="auth-link-btn" onClick={resendVerificationCode}>
                      Resend code
                    </button>
                    <button type="button" className="auth-link-btn" onClick={() => setAuthMode("login")}>
                      Back to login
                    </button>
                  </>
                ) : authMode === "forgot" ? (
                  <>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address" required />
                    <button type="submit">Send reset code</button>
                    <button type="button" className="auth-link-btn" onClick={() => setAuthMode("login")}>
                      Back to login
                    </button>
                  </>
                ) : authMode === "reset" ? (
                  <>
                    <input
                      type="email"
                      value={verificationEmail || email}
                      onChange={(e) => {
                        setVerificationEmail(e.target.value);
                        setEmail(e.target.value);
                      }}
                      placeholder="Email address"
                      required
                    />
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      placeholder="6-digit reset code"
                      required
                    />
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="New password" minLength={8} required />
                    <button type="submit">Reset password</button>
                    <button type="button" className="auth-link-btn" onClick={requestPasswordReset}>
                      Resend reset code
                    </button>
                    <button type="button" className="auth-link-btn" onClick={() => setAuthMode("login")}>
                      Back to login
                    </button>
                  </>
                ) : (
                  <>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address" required />
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" minLength={8} required />
                    <button type="submit">{authMode === "login" ? "Sign in" : "Create account"}</button>
                    {authMode === "login" ? (
                      <button type="button" className="auth-link-btn" onClick={() => setAuthMode("forgot")}>
                        Forgot password?
                      </button>
                    ) : null}
                  </>
                )}
              </form>
              ) : null}
            </div>
          )}

          <div className="panel-body">
            <form onSubmit={handleSubmit} className="form">
              {!user ? (
                <div className="guest-start-note">
                  <strong>No registration required</strong>
                  <span>Run 2 free guest analyses today. Sign in only if you want saved history and access to extra tools.</span>
                </div>
              ) : null}
              <div className="field">
                <span className="field-label">Resume file</span>
                {resume ? (
                  <div className="file-selected">
                    <div className="file-selected-name">
                      <span className="file-icon">{Icons.file}</span>
                      <span>{resume.name}</span>
                    </div>
                    <button type="button" className="clear-btn" onClick={() => setResume(null)}>Clear</button>
                  </div>
                ) : (
                  <div
                    className={`upload-zone${dragOver ? " drag-over" : ""}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={(e) => {
                      e.preventDefault();
                      setDragOver(false);
                      const f = e.dataTransfer.files?.[0];
                      selectResumeFile(f ?? null);
                    }}
                  >
                    <input id="resume-file" type="file" accept=".pdf,.docx,.txt" onChange={(e) => selectResumeFile(e.target.files?.[0] ?? null)} />
                    <label htmlFor="resume-file" className="upload-label">
                      <span className="upload-icon">{Icons.upload}</span>
                      <strong>Drop file or click to browse</strong>
                      <span>PDF, DOCX, or TXT. Up to 5 MB</span>
                    </label>
                  </div>
                )}
              </div>

              <div className="field">
                <span className="field-label">Analysis model</span>
                <select value={analysisMode} onChange={(e) => setAnalysisMode(e.target.value)}>
                  <option value="groq">Groq Llama</option>
                  <option value="openai">OpenAI GPT</option>
                  {enableLocalNlp ? <option value="nlp_local">Local Intelligence</option> : null}
                </select>
              </div>

              <div className="field">
                <span className="field-label">
                  Job title or description
                  <span className="field-optional">optional</span>
                </span>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  maxLength={4000}
                  rows={5}
                  placeholder="Paste a job title or full vacancy text for a personalized job-fit score."
                />
                <span className={`char-counter${jobDescription.length > 4000 ? " over" : ""}`}>
                  {jobDescription.length} / 4000
                </span>
                <span className="field-note">
                  Free resume match score tool with no signup. Analyze your alignment with the job description instantly as a guest.
                </span>
              </div>

              <button type="submit" disabled={loading} className="analyze-btn">
                {loading ? Icons.loader : Icons.spark}
                {loading ? "Analyzing..." : "Analyze CV"}
              </button>
              <p className="analysis-speed-note">
                {Icons.spark}
                Results usually appear in about 5-15 seconds.
              </p>
              {loading ? (
                <div className="analysis-progress" aria-live="polite">
                  <div className="analysis-progress-track">
                    <span style={{ width: `${((analysisProgressStep + 1) / analysisProgressSteps.length) * 100}%` }} />
                  </div>
                  <div className="analysis-progress-steps">
                    {analysisProgressSteps.map((step, index) => (
                      <span
                        key={step}
                        className={index < analysisProgressStep ? "done" : index === analysisProgressStep ? "active" : ""}
                      >
                        {step}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {error ? <p className="error">{error}</p> : null}
            </form>
          </div>
        </div>

        <div className="right-col">
          <div className="panel tabs-bar">
            <nav className="tabs-nav" aria-label="Dashboard views">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`tab-btn${activeTab === tab.id ? " active" : ""}`}
                  disabled={tab.disabled}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span className="tab-icon">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="dashboard-content">
            {result ? (
              <Dashboard
                activeTab={activeTab}
                result={result}
                generatedContent={generatedContent}
                history={history}
                generationLoading={generationLoading}
                rewriteSection={rewriteSection}
                exportLoading={exportLoading}
                onRewriteSectionChange={setRewriteSection}
                onGenerate={handleGenerate}
                onExportPdf={handleExportPdf}
              />
            ) : activeTab === "history" ? (
              <HistoryPanel history={history} />
            ) : (
              <EmptyState />
            )}
          </div>
        </div>
      </section>
      <footer className="site-footer">
        <div className="footer-links" aria-label="Helpful pages">
          <a href="/free-resume-analyzer">Free Resume Analyzer</a>
          <a href="/ats-resume-checker">ATS Resume Checker</a>
          <a href="/resume-job-match-checker">Resume Job Match Checker</a>
          <a href="/privacy-policy">Privacy Policy</a>
          <a href="/terms">Terms</a>
          <a href="/contact">Contact</a>
        </div>
      </footer>
    </main>
  );
}

function EmptyState() {
  const steps = [
    {
      title: "Upload your resume",
      desc: "PDF, DOCX, or TXT",
    },
    {
      title: "Paste the target job description",
      desc: "A full vacancy gives the clearest match score",
    },
    {
      title: "Get your AI job-fit match score in 5-15 seconds",
      desc: "ATS score - skill gaps - cover letter - PDF export",
    },
  ];
  const skills = ["Customer service", "Banking", "Excel", "Communication"];
  const gaps = ["Risk reporting", "CRM tools", "Sales targets"];

  return (
    <>
    <div className="panel empty-state">
      <div className="empty-preview-grid">
        <div className="empty-guide-card">
          <span className="empty-eyebrow">How it works</span>
          <h2>Land more interviews</h2>
          <p>Get your ATS score, job-fit feedback, missing skills, and rewrite suggestions before you apply.</p>
          <div className="empty-instructions">
            {steps.map((step, index) => (
              <div className="empty-instruction" key={step.title}>
                <span className="empty-instruction-num">{index + 1}</span>
                <div>
                  <strong>{step.title}</strong>
                  <p>{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="empty-report-card">
          <span className="empty-eyebrow">Resume report preview</span>
          <div className="mock-report" aria-label="Example resume analysis report">
            <div className="mock-report-top">
              <div>
                <span className="mock-label">ATS Score</span>
                <strong>87%</strong>
              </div>
              <div>
                <span className="mock-label">Job Match</span>
                <strong>74%</strong>
              </div>
            </div>

            <div className="mock-progress" aria-hidden="true">
              <span style={{ width: "87%" }} />
            </div>

            <div className="mock-section">
              <div className="mock-section-title">
                {Icons.skills}
                Detected skills
              </div>
              <div className="mock-chips">
                {skills.map((skill) => <span key={skill}>{skill}</span>)}
              </div>
            </div>

            <div className="mock-section">
              <div className="mock-section-title">
                {Icons.missing}
                Missing skills to add
              </div>
              <div className="mock-gaps">
                {gaps.map((gap) => (
                  <div key={gap}>
                    <span />
                    {gap}
                  </div>
                ))}
              </div>
            </div>

            <div className="mock-summary">
              <strong>Improved summary</strong>
              <p>Clearer role-focused summary with stronger keywords and measurable impact.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div className="panel empty-benefits">
      <div>
        <strong>Know what recruiters and ATS systems may miss.</strong>
        <span>Use the report to improve keywords, role fit, summary clarity, and application documents.</span>
      </div>
      <div className="empty-benefit-tags">
        {["ATS Score", "Job-fit match", "Skill gaps", "PDF export"].map((f) => (
          <span key={f}>{f}</span>
        ))}
        <span>Private by design</span>
        <span>No data sold</span>
        <span>PDF, DOCX, TXT supported</span>
      </div>
    </div>
    <div className="panel empty-faq-panel" aria-label="Resume analyzer details">
      <div>
        <strong>Is my resume data safe?</strong>
        <span>Uploaded files are not kept after parsing.</span>
      </div>
      <div>
        <strong>Which file formats work?</strong>
        <span>PDF, DOCX, TXT</span>
      </div>
      <div>
        <strong>How long does it take?</strong>
        <span>About 5-15 seconds</span>
      </div>
      <div>
        <strong>Do I need a job description?</strong>
        <span>
          No, a job title is enough. Want to see how well your CV aligns with a specific role? Use our dedicated{" "}
          <a href="/resume-job-match-checker">AI Resume Job Match Checker</a> to get a detailed compatibility score.
        </span>
      </div>
      <div>
        <strong>Can I use it for non-tech jobs?</strong>
        <span>Yes, it works across industries.</span>
      </div>
      <div>
        <strong>Do I need an account?</strong>
        <span>No, guests can run a limited analysis.</span>
      </div>
      <div>
        <strong>Can I export the report?</strong>
        <span>Yes, registered users can export PDF.</span>
      </div>
      <div>
        <strong>Does it guarantee interviews?</strong>
        <span>No, it gives improvement guidance.</span>
      </div>
      <div>
        <strong>Can I analyze DOCX resumes?</strong>
        <span>Yes, DOCX is supported.</span>
      </div>
    </div>
    </>
  );
}

function Dashboard({
  activeTab,
  result,
  generatedContent,
  history,
  generationLoading,
  rewriteSection,
  exportLoading,
  onRewriteSectionChange,
  onGenerate,
  onExportPdf,
}: {
  activeTab: ActiveTab;
  result: AnalysisResult;
  generatedContent: GeneratedContent;
  history: HistoryItem[];
  generationLoading: "cover" | "questions" | "rewrite" | null;
  rewriteSection: string;
  exportLoading: boolean;
  onRewriteSectionChange: (s: string) => void;
  onGenerate: (t: "cover" | "questions" | "rewrite") => void;
  onExportPdf: () => void;
}) {
  if (activeTab === "history") return (
    <>
      <AdSlot placement="history" />
      <HistoryPanel history={history} />
    </>
  );

  if (activeTab === "tools") return (
    <>
      <AdSlot placement="tools" />
      <ToolPanel
        generationLoading={generationLoading}
        rewriteSection={rewriteSection}
        exportLoading={exportLoading}
        onRewriteSectionChange={onRewriteSectionChange}
        onGenerate={onGenerate}
        onExportPdf={onExportPdf}
      />
      <GeneratedDocuments generatedContent={generatedContent} />
    </>
  );

  if (activeTab === "documents") return (
    <>
      <AdSlot placement="documents" />
      <section className="panel section-panel">
        <h2 className="section-title">
          <span className="section-title-icon">{Icons.download}</span>
          Export
        </h2>
        <div className="tool-actions">
          <button type="button" onClick={onExportPdf} disabled={exportLoading}>
            {exportLoading ? Icons.loader : Icons.download}
            {exportLoading ? "Exporting..." : "Export PDF Report"}
          </button>
        </div>
      </section>
      <GeneratedDocuments generatedContent={generatedContent} />
    </>
  );

  return (
    <>
      <div className="score-grid">
        <ScoreCard label="ATS Score" value={result.ats_score} />
        <ScoreCard label="Job Match" value={result.job_match_score} fallback="N/A" />
        <ScoreCard label="Relevant Skills" value={result.detected_skills.length} suffix="" max={20} />
      </div>

      <div className="panel mode-panel">
        <span className="mode-label">Analysis model</span>
        <span className="mode-value">
          {Icons.spark}
          {formatAnalysisMode(result.analysis_mode)}
        </span>
      </div>

      {result.fallback_notice ? (
        <div className="fallback-banner">
          <span className="fallback-banner-icon">{Icons.missing}</span>
          <span>{result.fallback_notice}</span>
        </div>
      ) : null}

      <section className="panel section-panel">
        <h2 className="section-title">
          <span className="section-title-icon">{Icons.skills}</span>
          Job-Relevant Skills
        </h2>
        <div className="chips">{result.detected_skills.map((s) => <span key={s}>{s}</span>)}</div>
      </section>

      <section className="panel section-panel">
        <h2 className="section-title">
          <span className="section-title-icon">{Icons.missing}</span>
          Missing Skills
        </h2>
        <ul className="analysis-list analysis-list-missing">
          {result.missing_skills.length
            ? result.missing_skills.map((g) => <li key={g.skill}><strong>{g.skill}</strong> - {g.reason}</li>)
            : <li>No role-specific skill gaps detected.</li>}
        </ul>
      </section>

      <section className="panel section-panel two-columns">
        <div>
          <h2 className="section-title">
            <span className="section-title-icon">{Icons.strong}</span>
            Strengths
          </h2>
          <ul className="analysis-list analysis-list-strengths strengths-list">{result.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div>
          <h2 className="section-title">
            <span className="section-title-icon section-title-icon-danger">{Icons.missing}</span>
            Weaknesses
          </h2>
          <ul className="analysis-list analysis-list-weaknesses weaknesses-list">{result.weaknesses.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </section>

      <section className="panel section-panel">
        <h2 className="section-title">
          <span className="section-title-icon">{Icons.recs}</span>
          Recommendations
        </h2>
        <ul className="analysis-list analysis-list-recommendations">{result.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
      </section>

      <section className="panel section-panel">
        <h2 className="section-title">
          <span className="section-title-icon">{Icons.summary}</span>
          Improved Summary
        </h2>
        <p className="summary">{result.improved_summary}</p>
      </section>
      <EarlyAccessPanel />
    </>
  );
}

function EarlyAccessPanel() {
  const [leadEmail, setLeadEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleEarlyAccessSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = leadEmail.trim();
    if (!email) return;
    const subject = encodeURIComponent("AI Resume Builder early access");
    const body = encodeURIComponent(`Please add me to early access for AI Resume Builder.\n\nEmail: ${email}`);
    window.location.href = `mailto:support@cvanalyzerai.com?subject=${subject}&body=${body}`;
    setSubmitted(true);
  }

  return (
    <section className="panel section-panel early-access-panel">
      <div>
        <h2 className="section-title">
          <span className="section-title-icon">{Icons.spark}</span>
          AI Resume Builder early access
        </h2>
        <p>
          Want to fix these mistakes in 1 click? We are launching our AI Resume Builder this month. Drop your email to
          get early access + 50% discount.
        </p>
      </div>
      <form className="early-access-form" onSubmit={handleEarlyAccessSubmit}>
        <input
          type="email"
          value={leadEmail}
          onChange={(event) => setLeadEmail(event.target.value)}
          placeholder="Email address"
          aria-label="Email address for AI Resume Builder early access"
          required
        />
        <button type="submit">{submitted ? "Email opened" : "Get early access"}</button>
      </form>
    </section>
  );
}

function AdSlot({ placement }: { placement: "tools" | "documents" | "history" }) {
  const adClient = process.env.NEXT_PUBLIC_ADSENSE_CLIENT;
  const adSlots = {
    tools: process.env.NEXT_PUBLIC_ADSENSE_SLOT_TOOLS,
    documents: process.env.NEXT_PUBLIC_ADSENSE_SLOT_DOCUMENTS,
    history: process.env.NEXT_PUBLIC_ADSENSE_SLOT_HISTORY,
  };
  const adSlot = adSlots[placement];

  useEffect(() => {
    if (!adClient || !adSlot) return;
    const adWindow = window as Window & { adsbygoogle?: unknown[] };
    adWindow.adsbygoogle = adWindow.adsbygoogle || [];
    adWindow.adsbygoogle.push({});
  }, [adClient, adSlot]);

  if (!adClient || !adSlot) {
    return null;
  }

  return (
    <aside className="ad-slot" aria-label="Advertisement" data-placement={placement}>
      <ins
        className="adsbygoogle"
        data-ad-client={adClient}
        data-ad-slot={adSlot}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </aside>
  );
}

function ToolPanel({ generationLoading, rewriteSection, exportLoading, onRewriteSectionChange, onGenerate, onExportPdf }: {
  generationLoading: "cover" | "questions" | "rewrite" | null;
  rewriteSection: string;
  exportLoading: boolean;
  onRewriteSectionChange: (s: string) => void;
  onGenerate: (t: "cover" | "questions" | "rewrite") => void;
  onExportPdf: () => void;
}) {
  return (
    <section className="panel section-panel">
      <h2 className="section-title">
        <span className="section-title-icon">{Icons.tool}</span>
        AI Tools
      </h2>
      <div className="tool-actions">
        <button type="button" onClick={() => onGenerate("cover")} disabled={generationLoading !== null}>
          {generationLoading === "cover" ? Icons.loader : Icons.mail}
          {generationLoading === "cover" ? "Generating..." : "Cover Letter"}
        </button>
        <button type="button" onClick={() => onGenerate("questions")} disabled={generationLoading !== null}>
          {generationLoading === "questions" ? Icons.loader : Icons.questions}
          {generationLoading === "questions" ? "Generating..." : "Interview Questions"}
        </button>
        <button type="button" onClick={onExportPdf} disabled={exportLoading} className="btn-outline">
          {exportLoading ? Icons.loader : Icons.download}
          {exportLoading ? "Exporting..." : "Export PDF"}
        </button>
      </div>
      <div className="rewrite-row">
        <select value={rewriteSection} onChange={(e) => onRewriteSectionChange(e.target.value)}>
          <option value="summary">Summary section</option>
          <option value="experience">Experience section</option>
          <option value="skills">Skills section</option>
        </select>
        <button type="button" onClick={() => onGenerate("rewrite")} disabled={generationLoading !== null}>
          {generationLoading === "rewrite" ? Icons.loader : Icons.rewrite}
          {generationLoading === "rewrite" ? "Rewriting..." : "Rewrite Section"}
        </button>
      </div>
    </section>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className={`copy-btn${copied ? " copied" : ""}`}
      onClick={() => {
        void navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
    >
      {copied ? Icons.check : Icons.copy}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function GeneratedDocuments({ generatedContent }: { generatedContent: GeneratedContent }) {
  const has = generatedContent.coverLetter || generatedContent.interviewQuestions || generatedContent.rewrittenSection;
  if (!has) return (
    <section className="panel section-panel">
      <p className="muted">No generated documents yet. Use the tools above to create content.</p>
    </section>
  );

  return (
    <>
      {generatedContent.coverLetter && (
        <section className="panel section-panel">
          <h2 className="section-title">
            <span className="section-title-icon">{Icons.mail}</span>
            Cover Letter Draft
          </h2>
          <CopyButton text={generatedContent.coverLetter} />
          <pre className="generated-text">{generatedContent.coverLetter}</pre>
        </section>
      )}
      {generatedContent.interviewQuestions && (
        <section className="panel section-panel">
          <h2 className="section-title">
            <span className="section-title-icon">{Icons.questions}</span>
            Mock Interview Questions
          </h2>
          <ol>{generatedContent.interviewQuestions.map((q) => <li key={q}>{q}</li>)}</ol>
        </section>
      )}
      {generatedContent.rewrittenSection && (
        <section className="panel section-panel">
          <h2 className="section-title">
            <span className="section-title-icon">{Icons.rewrite}</span>
            Rewritten {titleCase(generatedContent.rewrittenSection.section_type)}
          </h2>
          <CopyButton text={generatedContent.rewrittenSection.rewritten_section} />
          <pre className="generated-text">{generatedContent.rewrittenSection.rewritten_section}</pre>
          <ul className="notes-list">{generatedContent.rewrittenSection.improvement_notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </section>
      )}
    </>
  );
}

function HistoryPanel({ history }: { history: HistoryItem[] }) {
  return (
    <section className="panel section-panel">
      <h2 className="section-title">
        <span className="section-title-icon">{Icons.history}</span>
        Recent Analyses
      </h2>
      {history.length ? (
        <div className="history-list">
          {history.map((item) => (
            <div className="history-item" key={item.id}>
              <div className="history-item-main">
                <strong>{item.target_role ? `${item.target_role} - ${item.filename}` : item.filename}</strong>
                <span>{formatAnalysisMode(item.analysis_mode)} - {new Date(item.created_at).toLocaleString()}</span>
              </div>
              <div className="history-score">
                <strong>{item.ats_score}%</strong>
                <span>{item.job_match_score === null ? "No JD" : `${item.job_match_score}% match`}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">No saved analyses yet. Run your first analysis to see history here.</p>
      )}
    </section>
  );
}

function ScoreCard({ label, value, fallback, suffix = "%", max = 100 }: {
  label: string;
  value: number | null;
  fallback?: string;
  suffix?: string;
  max?: number;
}) {
  const progress = value === null ? 0 : Math.min(100, Math.round((value / max) * 100));
  const colorClass = value === null ? "score-na" : value >= 70 ? "score-high" : value >= 40 ? "score-mid" : "score-low";
  const r = 22;
  const circ = 2 * Math.PI * r;
  const offset = circ - (progress / 100) * circ;

  const displayValue = value === null ? fallback : `${value}${suffix}`;

  return (
    <section className={`panel score-card ${colorClass}`} aria-label={`${label}: ${displayValue}`}>
      <p className="score-card-label">{label}</p>
      <div className="score-card-ring-wrap">
        <svg className="score-ring" width="56" height="56" viewBox="0 0 56 56" aria-hidden="true">
          <circle className="track" cx="28" cy="28" r={r} />
          <circle
            className="fill"
            cx="28"
            cy="28"
            r={r}
            strokeDasharray={circ}
            strokeDashoffset={offset}
            transform="rotate(-90 28 28)"
          />
        </svg>
        <span className="score-value">{displayValue}</span>
      </div>
    </section>
  );
}

function titleCase(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatAnalysisMode(mode: string) {
  const labels: Record<string, string> = {
    openai: "OpenAI GPT",
    llm: "OpenAI GPT",
    groq: "Groq Llama",
    nlp_local: "Local Intelligence",
  };
  return labels[mode] ?? mode;
}
