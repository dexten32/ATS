import { useState, useEffect } from 'react'
import { ResumeUploader } from '@/components/ResumeUploader'
import { AnalysisResults } from '@/components/AnalysisResults'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Search, Loader2, BarChart3, FileText, ClipboardList } from 'lucide-react'

export function Dashboard({ setCurrentView }) {
  const [resumes, setResumes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [expandedResumeId, setExpandedResumeId] = useState(null);
  
  // Analysis State
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResults, setAnalysisResults] = useState(null);
  
  // Strategy Constraints
  const [canLearnSkills, setCanLearnSkills] = useState(true);
  const [canAddProjects, setCanAddProjects] = useState(true);

  const fetchResumes = async () => {
    try {
      const response = await fetch("/api/v1/resume/all/");
      if (response.ok) {
        const data = await response.json();
        setResumes(data.resumes || []);
        if (data.resumes && data.resumes.length > 0 && !selectedResumeId) {
          setSelectedResumeId(data.resumes[0].id.toString());
        }
      }
    } catch (err) {
      console.error("Error fetching resumes:", err);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleUpload = async (file) => {
    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("resume_file", file);

    try {
      const response = await fetch("/api/v1/upload-resume", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error(`Upload failed`);
      await fetchResumes();
    } catch (err) {
      setError("Failed to upload resume.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`/api/v1/resume/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setResumes(resumes.filter(r => r.id !== id));
        if (selectedResumeId === id.toString()) {
          setSelectedResumeId('');
        }
      }
    } catch (err) {
      console.error("Error deleting resume:", err);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedResumeId) {
      setError("Please select a resume to analyze.");
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setAnalysisResults(null);

    try {
      const response = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_id: parseInt(selectedResumeId),
          job_description: jobDescription || "general",
          constraints: {
            can_learn_skills: canLearnSkills,
            can_add_projects: canAddProjects
          }
        }),
      });

      if (!response.ok) throw new Error("Analysis failed");
      const data = await response.json();
      setAnalysisResults(data);
    } catch (err) {
      setError("Failed to analyze resume. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-12 pb-20">
      <div className="text-center space-y-3">
        <h2 className="text-4xl font-extrabold tracking-tight text-foreground">
          AI <span className="text-primary">Resume Analyst</span>
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-medium">
          Upload your resume and get an instant professional audit or match it against a specific job description.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Left Side: Upload & Manage */}
        <div className="space-y-8">
          <ResumeUploader onUpload={handleUpload} isLoading={isLoading} />
          
          <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-muted/30 flex items-center justify-between">
              <h3 className="font-bold flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                Your Documents
              </h3>
              <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold">
                {resumes.length}
              </span>
            </div>
            <div className="max-h-[400px] overflow-y-auto">
              {resumes.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground text-sm italic">
                  No documents uploaded yet.
                </div>
              ) : (
                <div className="divide-y">
                  {resumes.map((resume) => (
                    <div 
                      key={resume.id} 
                      onClick={() => setSelectedResumeId(resume.id.toString())}
                      className={`p-4 flex items-center justify-between cursor-pointer transition-colors ${selectedResumeId === resume.id.toString() ? 'bg-primary/5 border-l-4 border-primary' : 'hover:bg-muted/50'}`}
                    >
                      <div className="flex flex-col">
                        <span className="font-semibold text-sm truncate max-w-[180px]">{resume.display_name}</span>
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{resume.domain}</span>
                      </div>
                      <div className="flex items-center gap-3">
                         <button 
                           className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-all"
                           onClick={(e) => {
                             e.stopPropagation();
                             handleDelete(resume.id);
                           }}
                           title="Delete"
                         >
                           <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                         </button>
                         {selectedResumeId === resume.id.toString() && <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Analysis Controls */}
        <div className="bg-card border rounded-xl shadow-lg p-6 space-y-6 sticky top-24">
          <div className="space-y-2">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Configure Analysis
            </h3>
            <p className="text-sm text-muted-foreground">
              Paste a Job Description for a specific match, or leave it blank for a general professional audit.
            </p>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                Job Description (Optional)
              </label>
              <Textarea 
                placeholder="Paste the job description here for precision matching... or leave blank for a general audit."
                className="min-h-[200px] bg-muted/10 focus:bg-background transition-all"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
              />
            </div>

            {/* Strategy Toggles */}
            <div className="p-4 bg-primary/5 rounded-xl border border-primary/10 space-y-4">
              <p className="text-[10px] font-bold text-primary uppercase tracking-[0.2em]">Strategy Configuration</p>
              <div className="flex flex-col gap-3">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative flex items-center">
                    <input 
                      type="checkbox" 
                      checked={canLearnSkills} 
                      onChange={(e) => setCanLearnSkills(e.target.checked)}
                      className="w-4 h-4 rounded border-primary/50 text-primary focus:ring-primary transition-all"
                    />
                  </div>
                  <span className="text-sm font-medium text-foreground group-hover:text-primary transition-colors italic">
                    I have time to learn and add new skills
                  </span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className="relative flex items-center">
                    <input 
                      type="checkbox" 
                      checked={canAddProjects} 
                      onChange={(e) => setCanAddProjects(e.target.checked)}
                      className="w-4 h-4 rounded border-primary/50 text-primary focus:ring-primary transition-all"
                    />
                  </div>
                  <span className="text-sm font-medium text-foreground group-hover:text-primary transition-colors italic">
                    I can add or replace projects in my resume
                  </span>
                </label>
              </div>
            </div>

            <Button 
              className="w-full py-6 text-lg font-bold shadow-xl shadow-primary/20 hover:shadow-primary/40 transition-all"
              onClick={handleAnalyze}
              disabled={isAnalyzing || resumes.length === 0}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Analyzing Quality...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-5 w-5" />
                  {jobDescription ? "Match Against JD" : "Run Professional Audit"}
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-lg flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-destructive" />
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Results Section */}
      {analysisResults && (
        <div className="mt-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="flex items-center gap-4 mb-6">
            <div className="h-px flex-grow bg-border" />
            <div className="flex items-center gap-2 text-muted-foreground">
              <ClipboardList className="h-5 w-5" />
              <span className="font-bold uppercase tracking-widest text-xs">Analysis Results</span>
            </div>
            <div className="h-px flex-grow bg-border" />
          </div>
          <AnalysisResults results={analysisResults} />
        </div>
      )}
    </div>
  )
}

