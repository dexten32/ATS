import { useState, useEffect } from 'react'
import { ResumeUploader } from '@/components/ResumeUploader'

export function Dashboard() {
  const [resumes, setResumes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [expandedResumeId, setExpandedResumeId] = useState(null);

  const fetchResumes = async () => {
    try {
      const response = await fetch("/api/v1/resume/all/");
      if (response.ok) {
        const data = await response.json();
        setResumes(data.resumes || []);
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

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      await fetchResumes();
    } catch (err) {
      console.error("Error during upload:", err);
      setError("Failed to upload resume. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-12">
      <div className="text-center space-y-3">
        <h2 className="text-4xl font-extrabold tracking-tight text-foreground">
          Resume <span className="text-primary">Management</span>
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-medium">
          Upload and manage candidate resumes. All documents are stored securely in the local uploads directory.
        </p>
      </div>

      <ResumeUploader onUpload={handleUpload} isLoading={isLoading} />
      
      {error && (
        <div className="w-full max-w-3xl mx-auto mt-6 p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-md flex items-center gap-3 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
          <span className="font-medium">{error}</span>
        </div>
      )}

      <div className="w-full max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            Uploaded Documents
            <span className="bg-primary/10 text-primary text-xs px-2 py-0.5 rounded-full ml-2">
              {resumes.length}
            </span>
          </h3>
        </div>

        {resumes.length === 0 ? (
          <div className="text-center py-12 bg-muted/30 rounded-xl border border-dashed border-border">
            <p className="text-muted-foreground">No documents uploaded yet.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {resumes.map((resume, index) => (
              <div 
                key={resume.id || resume.filename} 
                className={`flex flex-col bg-card border rounded-lg shadow-sm transition-all group animate-in fade-in slide-in-from-bottom-2 ${
                  expandedResumeId === resume.id ? "border-primary shadow-md" : "border-border hover:border-primary/50"
                }`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div 
                  className="flex items-center justify-between p-4 cursor-pointer"
                  onClick={() => setExpandedResumeId(expandedResumeId === resume.id ? null : resume.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${
                      expandedResumeId === resume.id ? "bg-primary text-primary-foreground" : "bg-primary/10 text-primary"
                    }`}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-foreground group-hover:text-primary transition-colors">
                          {resume.display_name}
                        </p>
                        {resume.file_type && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-muted text-muted-foreground font-bold rounded uppercase">
                            {resume.file_type}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-mono">
                          {resume.filename.substring(0, 8)}...
                        </span>
                        <span>•</span>
                        <span className="text-primary/80 font-medium">{resume.domain}</span>
                        <span>•</span>
                        <span>{resume.skills?.length || 0} skills</span>
                        <span>•</span>
                        <span>
                          {resume.timestamp > 0 ? new Date(resume.timestamp * 1000).toLocaleString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          }) : 'Date unknown'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button 
                      className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-md transition-all"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                    </button>
                    <div className={`text-muted-foreground transition-transform duration-300 ${expandedResumeId === resume.id ? "rotate-180" : ""}`}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                    </div>
                  </div>
                </div>

                {expandedResumeId === resume.id && (
                  <div className="px-4 pb-4 pt-2 border-t border-muted/50 bg-muted/5 animate-in slide-in-from-top-2 duration-300">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-2">
                      <div className="md:col-span-1">
                        <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">Industry Domain</h4>
                        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                          <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                          {resume.domain}
                        </div>
                      </div>
                      <div className="md:col-span-2">
                        <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">Technical Skills</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {resume.skills && resume.skills.length > 0 ? (
                            resume.skills.map((skill, idx) => (
                              <span key={idx} className="px-2 py-0.5 bg-primary/5 text-primary text-[11px] border border-primary/10 rounded-full">
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-muted-foreground italic">No skills extracted</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
