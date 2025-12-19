import React, { useState, useEffect, Suspense, useRef } from "react";
import DOMPurify from "dompurify";
import {
  Upload,
  Sparkles,
  CheckCircle,
  Award,
  Briefcase,
  FileText,
  TrendingUp,
  Target,
  Loader2,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/components/ui/toast";
import { apiClient } from "@/utils/api";
import { track } from "@/utils/analytics";
import { useOutletContext } from "react-router-dom";
import type { OutletContextType } from "@/components/layout/RootLayout";

// Redefine interfaces if not easily imported, or move to types file later.
// Job interface matches MatchedResults internal type
export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  url: string;
}

interface MatchedJob {
  job: Job;
  match_score: number;
  match_reasons: string[];
}

type UploadStep = "upload" | "analyzing" | "profile" | "matching" | "results";

export default function Dashboard() {
  const { user } = useAuth();
  const { profile, setProfile } = useOutletContext<OutletContextType>();
  const toast = useToast();

  const [uploadStep, setUploadStep] = useState<UploadStep>("upload");
  // Profile state managed by OutletContext
  const [matchedJobs, setMatchedJobs] = useState<MatchedJob[]>([]);
  // const [_loading, setLoading] = useState(false) // Removed unused state

  const [error, setError] = useState<string>("");

  // Filtering state for matches
  const [minMatchScore, setMinMatchScore] = useState(0);
  const [useDemoJobs, setUseDemoJobs] = useState(false);
  const [location, setLocation] = useState("South Africa");
  const [manualTitle, setManualTitle] = useState("");
  const [manualDescription, setManualDescription] = useState("");

  // Applying state
  const [applying, setApplying] = useState(false);
  const [generatedFiles, setGeneratedFiles] = useState<{
    cv: string;
    cover_letter: string;
    interview_prep?: string;
  } | null>(null);
  const [generatedATS, setGeneratedATS] = useState<{
    score?: number;
    analysis?: string;
  } | null>(null);
  const [applyAttempts, setApplyAttempts] = useState(0);
  const [applyMaxAttempts, setApplyMaxAttempts] = useState(40);
  const [currentApplyJobId, setCurrentApplyJobId] = useState<string | null>(
    null
  );
  // Use ref for cancellation to avoid stale closure during async loop
  const applyCancelledRef = useRef(false);
  const [pendingJob, setPendingJob] = useState<Job | null>(null);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [applyTemplate, setApplyTemplate] = useState<
    "MODERN" | "PROFESSIONAL" | "ACADEMIC"
  >("MODERN");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState<{
    cv_html: string;
    cover_letter_html: string;
    ats?: { score?: number; analysis?: string };
  } | null>(null);
  const [cvHealth, setCvHealth] = useState<{
    filename?: string;
    uploadedAt?: string;
  } | null>(null);
  const cvFileInputRef = React.useRef<HTMLInputElement>(null);
  const [resumeAvailable, setResumeAvailable] = useState(false);
  const [lastMatches, setLastMatches] = useState<MatchedJob[]>([]);

  const API_ORIGIN = (
    import.meta.env.VITE_API_URL || "http://localhost:8000/api"
  ).replace(/\/api$/, "");
  const MatchedResults = React.lazy(
    () => import("@/components/MatchedResults")
  );

  useEffect(() => {
    if (user && matchedJobs.length === 0) {
      recoverMatches();
    }
  }, [user]);

  const recoverMatches = async () => {
    try {
      const response = await apiClient(
        `/matches/last?location=${encodeURIComponent(location)}`
      );
      const data = await response.json();
      if (
        data.success &&
        Array.isArray(data.matches) &&
        data.matches.length > 0
      ) {
        setMatchedJobs(data.matches);
        setUploadStep("results");
        // toast.show({ title: 'Resumed', description: 'Loaded your last matches', variant: 'success' })
      }
    } catch (e) {
      console.error("Recover matches failed", e);
    }
  };

  const handleCVUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      setError("File is too large. Max 10MB.");
      toast.show({
        title: "Upload failed",
        description: "File is too large. Max 10MB.",
        variant: "error",
      });
      return;
    }
    const allowed = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (file.type && !allowed.includes(file.type)) {
      setError("Invalid file type. Please upload PDF, DOC, or DOCX.");
      toast.show({
        title: "Upload failed",
        description: "Invalid file type. Use PDF, DOC, or DOCX.",
        variant: "error",
      });
      return;
    }

    setError("");
    setUploadStep("analyzing");
    // setLoading(true)

    try {
      const formData = new FormData();
      formData.append("cv", file);
      const response = await apiClient("/analyze-cv", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (data.success) {
        setProfile(data.profile);
        setUploadStep("profile");
        setTimeout(() => findMatches(), 1500);
      } else {
        setError(data.error || "Failed to analyze CV");
        setUploadStep("upload");
      }
    } catch (err) {
      setError("Error uploading CV. Please try again.");
      setUploadStep("upload");
    } finally {
      // setLoading(false)
    }
  };

  const findMatches = async () => {
    setUploadStep("matching");
    // setLoading(true)
    setError("");

    try {
      const response = await apiClient("/match-jobs", {
        method: "POST",
        body: JSON.stringify({
          location: location,
          max_results: 20,
          use_demo: useDemoJobs,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setMatchedJobs(data.matches || []);
        setUploadStep("results");
        track(
          "matches_search",
          {
            location,
            count: (data.matches || []).length,
            use_demo: useDemoJobs,
          },
          "app"
        );
      } else {
        setError(data.error || "Failed to find matches");
        setUploadStep("profile");
      }
    } catch (err) {
      setError("Error finding job matches. Please try again.");
      setUploadStep("profile");
    } finally {
      // setLoading(false)
    }
  };

  const handleApply = (job: Job) => {
    setPendingJob(job);
    setShowTemplateDialog(true);
  };

  const previewApply = async () => {
    if (!pendingJob) return;
    try {
      const resp = await apiClient("/apply-preview", {
        method: "POST",
        body: JSON.stringify({ job: pendingJob, template: applyTemplate }),
      });
      const data = await resp.json();
      if (data.success) {
        setPreviewContent({
          cv_html: data.cv_html,
          cover_letter_html: data.cover_letter_html,
          ats: data.ats,
        });
        setPreviewOpen(true);
      } else {
        const msg =
          data.error ||
          "Failed to generate preview. Ensure your CV is uploaded.";
        toast.show({
          title: "Preview failed",
          description: msg,
          variant: "error",
        });
      }
    } catch (e) {
      console.error("Preview failed", e);
      toast.show({
        title: "Preview failed",
        description: "An error occurred generating the preview.",
        variant: "error",
      });
    }
  };

  React.useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;

    (async () => {
      try {
        const resp = await apiClient("/profile/current", { method: "GET" });
        const data = await resp.json();
        if (data.success) {
          setCvHealth({
            filename: data.cv_filename,
            uploadedAt: data.uploaded_at,
          });
          const pResp = await apiClient("/profile/structured", {
            method: "GET",
          });
          const pData = await pResp.json();
          if (pData.success && pData.profile) {
            setProfile(pData.profile);
          }
          setUploadStep("profile");
          track("dashboard_autoload_profile", { hasCv: true }, "dashboard");
          const lastResp = await apiClient(
            `/matches/last?location=${encodeURIComponent(location)}`
          );
          const lastData = await lastResp.json();
          if (
            lastData.success &&
            Array.isArray(lastData.matches) &&
            lastData.matches.length > 0
          ) {
            setResumeAvailable(true);
            setLastMatches(lastData.matches);
            track(
              "resume_available",
              { count: lastData.matches.length },
              "app"
            );
          } else {
            toast.show({
              title: "Profile loaded",
              description: "Searching for matches…",
              variant: "default",
            });
            timeoutId = setTimeout(() => findMatches(), 1200);
          }
        }
      } catch (e) {
        // ignore
      }
    })();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  const resumeLastSession = () => {
    if (!resumeAvailable || lastMatches.length === 0) return;
    setMatchedJobs(lastMatches);
    setUploadStep("results");
    track("resume_last_session", { count: lastMatches.length }, "app");
  };

  const handleChangeCvClick = () => {
    track("cv_change_click", { fromIndicator: true }, "dashboard");
    cvFileInputRef.current?.click();
  };

  const formatRecency = (iso?: string) => {
    if (!iso) return { label: "Unknown", tone: "default" as const };
    const ts = Date.parse(iso);
    if (isNaN(ts)) return { label: iso, tone: "default" as const };
    const days = Math.floor((Date.now() - ts) / (1000 * 60 * 60 * 24));
    if (days <= 0) return { label: "Updated today", tone: "fresh" as const };
    if (days <= 7)
      return { label: `Updated ${days}d ago`, tone: "fresh" as const };
    if (days <= 30)
      return { label: `Updated ${days}d ago`, tone: "warn" as const };
    return { label: `Updated ${days}d ago`, tone: "stale" as const };
  };

  const confirmApply = async () => {
    if (!pendingJob) return;
    setShowTemplateDialog(false);
    setApplying(true);
    setError("");
    setApplying(true);
    setError("");
    applyCancelledRef.current = false;
    setGeneratedFiles(null);
    setGeneratedATS(null);

    try {
      const start = await apiClient("/apply-job", {
        method: "POST",
        body: JSON.stringify({ job: pendingJob, template: applyTemplate }),
      });
      const startData = await start.json();
      if (!startData.success || !startData.job_id) {
        setError(startData.error || "Failed to start application");
        setApplying(false);
        return;
      }
      const jobId = startData.job_id;
      setCurrentApplyJobId(jobId);

      let attempts = 0;
      const maxAttempts = 40;
      setApplyMaxAttempts(maxAttempts);
      const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

      while (attempts < maxAttempts) {
        if (applyCancelledRef.current) break;

        const statusResp = await apiClient(`/apply-status?job_id=${jobId}`, {
          method: "GET",
        });
        const statusData = await statusResp.json();

        if (statusData.status === "done" && statusData.files) {
          setGeneratedFiles({
            cv: statusData.files.cv,
            cover_letter: statusData.files.cover_letter,
            interview_prep: statusData.files.interview_prep,
          });
          if (statusData.ats) {
            setGeneratedATS({
              score: statusData.ats.score,
              analysis: statusData.ats.analysis,
            });
          }
          track(
            "apply_complete",
            {
              jobId,
              title: pendingJob.title,
              company: pendingJob.company,
              template: applyTemplate,
            },
            "app"
          );
          break;
        }
        if (statusData.status === "error") {
          setError(statusData.error || "Application failed");
          break;
        }
        if (statusData.status === "not_found") {
          attempts += 1;
          await delay(1000);
          continue;
        }
        attempts += 1;
        setApplyAttempts(attempts);
        const backoff = Math.min(1000 * Math.pow(1.3, attempts), 5000);
        await delay(backoff);
      }
    } catch (error) {
      console.error("Error applying to job:", error);
      setError("Error submitting application. Please try again.");
    } finally {
      setApplying(false);
      setCurrentApplyJobId(null);
    }
  };

  const handleCancelApply = async () => {
    try {
      applyCancelledRef.current = true;
      if (currentApplyJobId) {
        await apiClient(`/apply-cancel?job_id=${currentApplyJobId}`, {
          method: "POST",
        });
      }
      toast.show({
        title: "Cancelled",
        description: "Application process cancelled",
        variant: "error",
      });
    } catch (e) {
      console.error("Cancel apply failed", e);
    }
  };

  const filteredMatchedJobs = matchedJobs.filter(
    (match) => match.match_score >= minMatchScore
  );

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-muted-foreground">
            Manage your job search and applications
          </p>
        </div>
        {uploadStep === "results" && (
          <Button
            onClick={() => setUploadStep("upload")}
            variant="outline"
            className="border-white/10 hover:bg-white/5"
          >
            <Upload className="mr-2 h-4 w-4" /> Upload New CV
          </Button>
        )}
      </div>

      {/* Error/Loading Banners */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-200 px-4 py-3 rounded-xl animate-fade-in shadow-lg shadow-red-500/5">
          {error}
        </div>
      )}
      {applying && (
        <div className="bg-blue-500/10 border border-blue-500/20 text-blue-100 px-4 py-3 rounded-xl flex items-center justify-between animate-fade-in p-6 shadow-lg shadow-blue-500/10">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/20 rounded-full">
              <Loader2 className="h-6 w-6 animate-spin text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-50">
                Generating Application...
              </h3>
              <p className="text-sm text-blue-200">
                Tailoring your CV and writing a cover letter (
                {Math.min(
                  100,
                  Math.round((applyAttempts / applyMaxAttempts) * 100)
                )}
                %)
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleCancelApply}
            className="hover:bg-blue-500/20 border-blue-500/30 text-blue-100 hover:text-white"
          >
            Cancel
          </Button>
        </div>
      )}

      {/* CV Health Indicator */}
      {cvHealth && (
        <div className="mb-4">
          <div className="flex items-center justify-between p-3 border rounded-xl bg-card border-white/10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-md">
                <FileText className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <div className="text-sm text-foreground font-medium">
                  Active CV: {cvHealth.filename}
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-muted-foreground">
                    Last uploaded:{" "}
                    {cvHealth.uploadedAt?.replace("T", " ").replace("Z", "")}
                  </div>
                  {(() => {
                    const r = formatRecency(cvHealth.uploadedAt);
                    return (
                      <Badge
                        className={
                          r.tone === "fresh"
                            ? "bg-green-500/10 text-green-400 hover:bg-green-500/20"
                            : r.tone === "warn"
                            ? "bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20"
                            : r.tone === "stale"
                            ? "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                            : "bg-white/10 text-muted-foreground hover:bg-white/20"
                        }
                      >
                        {r.label}
                      </Badge>
                    );
                  })()}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                ref={cvFileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx"
                onChange={async (e) => {
                  await handleCVUpload(e);
                  try {
                    const resp = await apiClient("/profile/current", {
                      method: "GET",
                    });
                    const data = await resp.json();
                    if (data.success) {
                      setCvHealth({
                        filename: data.cv_filename,
                        uploadedAt: data.uploaded_at,
                      });
                      track(
                        "cv_change_uploaded",
                        { filename: data.cv_filename },
                        "dashboard"
                      );
                    }
                  } catch {}
                }}
              />
              <Button
                size="sm"
                variant="outline"
                onClick={handleChangeCvClick}
                className="border-white/10 hover:bg-white/5"
              >
                Change CV
              </Button>
            </div>
          </div>
          {resumeAvailable && matchedJobs.length === 0 && (
            <div className="mt-2 p-3 border rounded-xl bg-card border-white/10 flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Previous session found. You can resume your last matches.
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={resumeLastSession}>
                  Resume Last Session
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/10 hover:bg-white/5"
                  onClick={() => {
                    toast.show({
                      title: "Searching new matches",
                      variant: "default",
                    });
                    findMatches();
                  }}
                >
                  Search New
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Content Area */}
      <div className="min-h-[500px]">
        {/* Step 1: Upload */}
        {uploadStep === "upload" && (
          <div className="text-center py-20 px-4 glass-panel rounded-2xl border-white/5 bg-card/30">
            <div className="bg-gradient-to-br from-blue-500/20 to-purple-600/20 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-8 shadow-xl shadow-blue-500/10 animate-in zoom-in duration-500 border border-white/10">
              <Sparkles className="h-12 w-12 text-blue-400" />
            </div>
            <h2 className="text-4xl font-bold text-foreground mb-4 tracking-tight">
              Find Your Perfect Job Match
            </h2>
            <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
              Upload your CV and let our AI analyze your skills, experience, and
              career goals to find the best job opportunities tailored for you.
            </p>

            <div className="max-w-xl mx-auto transform transition-all hover:scale-[1.02]">
              <label className="flex flex-col items-center justify-center w-full h-72 border-2 border-dashed rounded-2xl cursor-pointer bg-card/30 hover:bg-card/50 transition-all border-white/10 hover:border-blue-500/50 group">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <div className="p-4 bg-blue-500/10 rounded-full mb-4 group-hover:bg-blue-500/20 transition-colors">
                    <Upload className="w-10 h-10 text-blue-400" />
                  </div>
                  <p className="mb-2 text-xl font-semibold text-foreground">
                    Click to upload your CV
                  </p>
                  <p className="text-sm text-muted-foreground">
                    PDF, DOC, or DOCX (Max 10MB)
                  </p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={handleCVUpload}
                />
              </label>
            </div>
          </div>
        )}

        {/* Step 2: Analyzing */}
        {uploadStep === "analyzing" && (
          <div className="text-center py-32 animate-fade-in">
            <div className="relative w-24 h-24 mx-auto mb-8">
              <div className="absolute inset-0 border-4 border-blue-500/20 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
              <Loader2 className="h-10 w-10 text-blue-500 absolute inset-0 m-auto animate-pulse" />
            </div>
            <h3 className="text-2xl font-bold text-foreground mb-2">
              Analyzing Your CV...
            </h3>
            <p className="text-muted-foreground">
              Our AI is extracting your skills, experience, and strengths
            </p>
          </div>
        )}

        {/* Step 3: Profile Review */}
        {uploadStep === "profile" && profile && (
          <Card className="animate-fade-in overflow-hidden border-white/10 shadow-xl bg-card/40 backdrop-blur-sm">
            <CardHeader className="bg-white/5 border-b border-white/10 p-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-green-500/10 rounded-xl shadow-sm border border-green-500/20">
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl text-foreground">
                      Profile Analyzed
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                      We found the following details from your CV
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-8 p-8">
              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground flex items-center text-lg">
                    <Award className="h-5 w-5 mr-2 text-blue-400" />
                    Skills & Expertise
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {profile.skills.map((skill, idx) => (
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="px-3 py-1 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/10"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground flex items-center text-lg">
                    <Briefcase className="h-5 w-5 mr-2 text-purple-400" />
                    Experience Level
                  </h4>
                  <p className="text-foreground bg-purple-500/10 p-3 rounded-lg border border-purple-500/20 inline-block">
                    {profile.experience_level || "Not specified"}
                  </p>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground flex items-center text-lg">
                    <FileText className="h-5 w-5 mr-2 text-green-400" />
                    Education
                  </h4>
                  <p className="text-foreground bg-green-500/10 p-3 rounded-lg border border-green-500/20">
                    {profile.education || "Not specified"}
                  </p>
                </div>

                <div className="space-y-3">
                  <h4 className="font-semibold text-foreground flex items-center text-lg">
                    <TrendingUp className="h-5 w-5 mr-2 text-orange-400" />
                    Key Strengths
                  </h4>
                  <ul className="space-y-2">
                    {profile.strengths.map((strength, idx) => (
                      <li
                        key={idx}
                        className="text-muted-foreground text-sm flex items-start gap-2"
                      >
                        <div className="h-1.5 w-1.5 rounded-full bg-orange-400 mt-2 flex-shrink-0" />
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {profile.career_goals && (
                <div className="pt-6 border-t border-white/10">
                  <h4 className="font-semibold text-foreground mb-3 flex items-center text-lg">
                    <Target className="h-5 w-5 mr-2 text-red-400" />
                    Career Goals
                  </h4>
                  <p className="text-muted-foreground bg-white/5 p-4 rounded-xl border border-white/5">
                    {profile.career_goals}
                  </p>
                </div>
              )}
            </CardContent>
            <CardFooter className="bg-white/5 p-6 border-t border-white/10">
              <Button
                onClick={findMatches}
                className="w-full h-12 text-lg shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 bg-blue-600 hover:bg-blue-500 text-white"
                size="lg"
              >
                Find Matching Jobs
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* Step 4: Matching */}
        {uploadStep === "matching" && (
          <div className="text-center py-32 animate-fade-in">
            <div className="relative w-24 h-24 mx-auto mb-8">
              <div className="absolute inset-0 border-4 border-purple-500/20 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-purple-500 rounded-full border-t-transparent animate-spin"></div>
              <Sparkles className="h-10 w-10 text-purple-400 absolute inset-0 m-auto animate-pulse" />
            </div>
            <h3 className="text-2xl font-bold text-foreground mb-2">
              Finding Your Perfect Matches...
            </h3>
            <p className="text-muted-foreground">
              Analyzing thousands of jobs to find the best fit for you
            </p>
          </div>
        )}

        {/* Step 5: Results */}
        {uploadStep === "results" && (
          <Suspense
            fallback={
              <div className="p-12 text-center text-muted-foreground">
                Loading results component...
              </div>
            }
          >
            <MatchedResults
              filteredMatchedJobs={filteredMatchedJobs}
              minMatchScore={minMatchScore}
              setMinMatchScore={setMinMatchScore}
              useDemoJobs={useDemoJobs}
              setUseDemoJobs={setUseDemoJobs}
              location={location}
              setLocation={setLocation}
              manualTitle={manualTitle}
              setManualTitle={setManualTitle}
              manualDescription={manualDescription}
              setManualDescription={setManualDescription}
              findMatches={findMatches}
              handleApply={handleApply}
            />
          </Suspense>
        )}
      </div>

      {/* Generated Files Dialog */}
      <Dialog
        open={!!generatedFiles}
        onOpenChange={() => {
          setGeneratedFiles(null);
          setGeneratedATS(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center justify-center mb-4">
              <div className="bg-green-500/10 w-16 h-16 rounded-full flex items-center justify-center animate-in zoom-in">
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </div>
            <DialogTitle className="text-center text-2xl">
              Application Generated!
            </DialogTitle>
            <DialogDescription className="text-center">
              Your tailored documents are ready for download.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 mt-4">
            {generatedATS && (
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
                <div className="font-medium text-yellow-500">
                  ATS Score: {generatedATS.score ?? "N/A"}%
                </div>
                {generatedATS.analysis && (
                  <p className="text-yellow-400 text-sm mt-1">
                    {generatedATS.analysis}
                  </p>
                )}
              </div>
            )}
            {generatedFiles && (
              <>
                <a
                  href={`${API_ORIGIN}${generatedFiles.cv}`}
                  download
                  className="flex items-center justify-between p-4 bg-blue-500/10 rounded-lg hover:bg-blue-500/20 transition-colors group border border-blue-500/10"
                >
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 text-blue-400 mr-3 group-hover:scale-110 transition-transform" />
                    <span className="font-medium text-blue-100">
                      Tailored CV
                    </span>
                  </div>
                  <Upload className="h-4 w-4 text-blue-400 rotate-180" />
                </a>

                <a
                  href={`${API_ORIGIN}${generatedFiles.cover_letter}`}
                  download
                  className="flex items-center justify-between p-4 bg-purple-500/10 rounded-lg hover:bg-purple-500/20 transition-colors group border border-purple-500/10"
                >
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 text-purple-400 mr-3 group-hover:scale-110 transition-transform" />
                    <span className="font-medium text-purple-100">
                      Cover Letter
                    </span>
                  </div>
                  <Upload className="h-4 w-4 text-purple-400 rotate-180" />
                </a>

                {generatedFiles.interview_prep && (
                  <a
                    href={`${API_ORIGIN}${generatedFiles.interview_prep}`}
                    download
                    className="flex items-center justify-between p-4 bg-green-500/10 rounded-lg hover:bg-green-500/20 transition-colors group border border-green-500/10"
                  >
                    <div className="flex items-center">
                      <Sparkles className="h-5 w-5 text-green-400 mr-3 group-hover:scale-110 transition-transform" />
                      <span className="font-medium text-green-100">
                        Interview Prep
                      </span>
                    </div>
                    <Upload className="h-4 w-4 text-green-400 rotate-180" />
                  </a>
                )}
              </>
            )}
          </div>

          <Button
            onClick={() => {
              setGeneratedFiles(null);
              setGeneratedATS(null);
            }}
            className="w-full mt-4"
            variant="outline"
          >
            Close
          </Button>
        </DialogContent>
      </Dialog>

      {/* Apply Template Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Choose a Template</DialogTitle>
            <DialogDescription>
              Select how your CV will be formatted
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="flex items-center gap-3 p-3 border rounded-lg">
              <input
                type="radio"
                name="tpl"
                checked={applyTemplate === "MODERN"}
                onChange={() => setApplyTemplate("MODERN")}
              />
              <div>
                <div className="font-medium">Modern</div>
                <div className="text-sm text-muted-foreground">
                  Two-column layout with highlighted skills
                </div>
              </div>
            </label>
            <label className="flex items-center gap-3 p-3 border rounded-lg">
              <input
                type="radio"
                name="tpl"
                checked={applyTemplate === "PROFESSIONAL"}
                onChange={() => setApplyTemplate("PROFESSIONAL")}
              />
              <div>
                <div className="font-medium">Professional</div>
                <div className="text-sm text-muted-foreground">
                  Classic single-column, formal styling
                </div>
              </div>
            </label>
            <label className="flex items-center gap-3 p-3 border rounded-lg">
              <input
                type="radio"
                name="tpl"
                checked={applyTemplate === "ACADEMIC"}
                onChange={() => setApplyTemplate("ACADEMIC")}
              />
              <div>
                <div className="font-medium">Academic</div>
                <div className="text-sm text-muted-foreground">
                  Academic-focused emphasis and typography
                </div>
              </div>
            </label>
          </div>
          <div className="flex gap-2 mt-4">
            <Button className="flex-1" onClick={previewApply}>
              Preview
            </Button>
            <Button className="flex-1" onClick={confirmApply}>
              Continue
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => setShowTemplateDialog(false)}
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>Preview</DialogTitle>
            <DialogDescription>
              Review your documents before generation
            </DialogDescription>
          </DialogHeader>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="border rounded p-2 overflow-auto max-h-[60vh]">
              {previewContent && (
                <div
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(previewContent.cv_html),
                  }}
                />
              )}
            </div>
            <div className="border rounded p-2 overflow-auto max-h-[60vh]">
              {previewContent && (
                <div
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(
                      previewContent.cover_letter_html
                    ),
                  }}
                />
              )}
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button
              className="flex-1"
              onClick={() => {
                setPreviewOpen(false);
                confirmApply();
              }}
            >
              Looks Good
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => setPreviewOpen(false)}
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
