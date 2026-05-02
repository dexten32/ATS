import { useState, useRef } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export function ResumeUploader({ onAnalyze, isLoading }) {
  const [file, setFile] = useState(null)
  const [jobDescription, setJobDescription] = useState("")
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!file || !jobDescription) return
    onAnalyze(file, jobDescription)
  }

  return (
    <Card className="w-full max-w-3xl mx-auto shadow-sm border border-border bg-card">
      <CardHeader className="pb-6 border-b border-border/50 mb-6">
        <CardTitle className="text-xl font-bold text-card-foreground">Start Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="space-y-3">
            <label className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              1. Candidate Resume
            </label>
            <div 
              className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${file ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-muted/50'}`}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept=".pdf,.docx,.txt"
              />
              {file ? (
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 mb-3 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m9 15 2 2 4-4"/></svg>
                  </div>
                  <p className="font-semibold text-foreground">{file.name}</p>
                  <p className="text-sm text-muted-foreground mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 mb-3 flex items-center justify-center text-muted-foreground">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                  </div>
                  <p className="font-medium text-foreground">Select a file or drag and drop here</p>
                  <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, or TXT up to 10MB</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              2. Job Description
            </label>
            <textarea
              className="flex min-h-[160px] w-full rounded-lg border border-input bg-background px-4 py-3 text-base text-foreground shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              placeholder="Paste the full job description requirements here..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>
          
          <div className="pt-4 flex justify-end">
            <Button 
              type="button"
              className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium px-8 py-6 rounded-md shadow-sm transition-all" 
              onClick={handleSubmit} 
              disabled={!file || !jobDescription || isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                   <svg className="animate-spin h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                     <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                     <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                   </svg>
                   Analyzing...
                </span>
              ) : "Run Analysis"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
