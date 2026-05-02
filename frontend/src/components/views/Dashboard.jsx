import { useState } from 'react'
import { ResumeUploader } from '@/components/ResumeUploader'
import { AnalysisResults } from '@/components/AnalysisResults'

export function Dashboard() {
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (file, jobDescription) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_description", jobDescription);

    try {
      const response = await fetch("/api/v1/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Analysis failed with status ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error("Error during analysis:", err);
      setError("Failed to analyze resume. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="text-center mb-12 space-y-3">
        <h2 className="text-4xl font-extrabold tracking-tight text-foreground">
          Evaluate Candidates <span className="text-primary">Intelligently</span>
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-medium">
          Upload a resume and provide a job description. Our system instantly matches the candidate profile against your requirements.
        </p>
      </div>

      <ResumeUploader onAnalyze={handleAnalyze} isLoading={isLoading} />
      
      {error && (
        <div className="w-full max-w-3xl mx-auto mt-6 p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-md flex items-center gap-3 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
          <span className="font-medium">{error}</span>
        </div>
      )}

      {results && <AnalysisResults results={results} />}
    </>
  )
}
