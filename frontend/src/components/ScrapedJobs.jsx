import { useState, useEffect, useRef } from 'react';
import { ExternalLink, MapPin, Building2, Briefcase, Search, Loader2, Play } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function ScrapedJobs() {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isScraping, setIsScraping] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Scraper Status State
  const [scraperIsRunning, setScraperIsRunning] = useState(false);
  const [scraperLogs, setScraperLogs] = useState([]);
  const terminalRef = useRef(null);
  
  // Scraper Controls State
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [location, setLocation] = useState('India');
  const [maxJobs, setMaxJobs] = useState(10);
  
  const selectedResumeRef = useRef(selectedResumeId);
  useEffect(() => {
    selectedResumeRef.current = selectedResumeId;
  }, [selectedResumeId]);

  const fetchResumes = async () => {
    try {
      const response = await fetch('/api/v1/resume/all/');
      if (response.ok) {
        const data = await response.json();
        setResumes(data.resumes || []);
        if (data.resumes && data.resumes.length > 0) {
          setSelectedResumeId(data.resumes[0].id.toString());
        }
      }
    } catch (err) {
      console.error("Failed to fetch resumes:", err);
    }
  };

  const fetchJobs = async (isPolling = false) => {
    try {
      if (!isPolling) setIsLoading(true);
      const url = selectedResumeRef.current 
        ? `/api/v1/jobs?resume_id=${selectedResumeRef.current}` 
        : '/api/v1/jobs';
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch jobs');
      const data = await response.json();
      setJobs(data);
    } catch (err) {
      if (!isPolling) setError(err.message);
    } finally {
      if (!isPolling) setIsLoading(false);
    }
  };

  const fetchScraperStatus = async () => {
    try {
      const response = await fetch('/api/v1/scraper/status');
      if (response.ok) {
        const data = await response.json();
        setScraperIsRunning(data.is_running);
        setScraperLogs(data.logs || []);
        
        // Auto-scroll terminal to bottom
        if (terminalRef.current) {
          terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
      }
    } catch (err) {
      console.error("Failed to fetch scraper status:", err);
    }
  };

  useEffect(() => {
    fetchJobs();
    fetchResumes();

    // Poll for jobs every 5 seconds to catch automated background scraping
    const interval = setInterval(() => {
      fetchJobs(true);
      fetchScraperStatus();
    }, 5000);
    
    // Initial fetch for status
    fetchScraperStatus();
    
    return () => clearInterval(interval);
  }, []);

  const handleScrape = async () => {
    try {
      setIsScraping(true);
      setError(null);
      const selectedResume = resumes.find(r => r.id.toString() === selectedResumeId);
      const searchKeyword = selectedResume ? selectedResume.domain : 'Software Engineering';

      const response = await fetch('/api/v1/jobs/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword: searchKeyword, location, max_jobs: parseInt(maxJobs), resume_id: parseInt(selectedResumeId) || null })
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to start scraping');
      }
      
      // Re-fetch jobs after successful scrape
      await fetchJobs();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsScraping(false);
    }
  };

  const filteredJobs = jobs.filter(job => 
    job.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
    job.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="w-full max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
            Scraped Opportunities
          </h2>
          <p className="text-muted-foreground mt-1 font-medium">
            Discover the latest roles automatically extracted from LinkedIn.
          </p>
        </div>
        
        <div className="relative w-full md:w-72 group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
          <Input 
            type="text" 
            placeholder="Search jobs, companies, locations..." 
            className="pl-9 bg-card border-border/50 focus:border-primary transition-all duration-300 shadow-sm hover:shadow-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Scraper Control Panel */}
      <Card className="mb-8 border-border/40 bg-card/50 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Play className="h-5 w-5 text-primary" />
            Live Scraper
          </CardTitle>
          <CardDescription>Configure parameters to extract new jobs directly from LinkedIn.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="w-full md:w-1/3">
              <label className="text-sm font-medium mb-1.5 block text-muted-foreground">Select Resume (for Domain)</label>
              <select 
                value={selectedResumeId} 
                onChange={(e) => setSelectedResumeId(e.target.value)} 
                disabled={isScraping || resumes.length === 0}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {resumes.length === 0 ? (
                  <option value="" disabled>No resumes uploaded</option>
                ) : (
                  resumes.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.display_name} ({r.domain || 'Software Engineering'})
                    </option>
                  ))
                )}
              </select>
            </div>
            <div className="w-full md:w-1/3">
              <label className="text-sm font-medium mb-1.5 block text-muted-foreground">Location</label>
              <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Remote" disabled={isScraping} />
            </div>
            <div className="w-full md:w-1/4">
              <label className="text-sm font-medium mb-1.5 block text-muted-foreground">Max Jobs</label>
              <Input type="number" min="1" max="50" value={maxJobs} onChange={(e) => setMaxJobs(Math.min(50, Math.max(1, parseInt(e.target.value) || 1)))} disabled={isScraping} />
            </div>
            <Button 
              onClick={handleScrape} 
              disabled={isScraping}
              className="w-full md:w-auto font-semibold shadow-sm transition-all"
            >
              {isScraping ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scraping...
                </>
              ) : (
                "Start Scraping"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Live Terminal UI */}
      {(scraperIsRunning || scraperLogs.length > 0) && (
        <Card className="mb-8 border-border/40 bg-[#0d1117] text-gray-300 shadow-xl overflow-hidden">
          <CardHeader className="pb-2 pt-3 border-b border-white/10 bg-black/40 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-mono flex items-center gap-2 text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>
              scraper_console.log
            </CardTitle>
            {scraperIsRunning && (
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-xs text-emerald-500 font-medium tracking-wide">SCRAPING ACTIVE</span>
              </div>
            )}
          </CardHeader>
          <CardContent className="p-0">
            <div 
              ref={terminalRef}
              className="h-48 md:h-64 overflow-y-auto p-4 font-mono text-[11px] md:text-xs leading-relaxed"
              style={{ scrollBehavior: 'smooth' }}
            >
              {scraperLogs.length === 0 ? (
                <div className="text-gray-500 italic flex items-center gap-2">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Waiting for scraper output...
                </div>
              ) : (
                scraperLogs.map((log, i) => (
                  <div key={i} className="mb-1.5 flex gap-2">
                    <span className="text-blue-400/50 shrink-0">~</span>
                    <span className={
                      log.includes("Error") || log.includes("failed") ? "text-red-400" : 
                      log.includes("Scraped") ? "text-emerald-400 font-medium" : 
                      log.includes("Starting") ? "text-blue-300" :
                      "text-gray-300"
                    }>
                      {log}
                    </span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {(isLoading && !isScraping && !scraperIsRunning) && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
          <p className="text-lg font-medium text-muted-foreground">Loading job data...</p>
        </div>
      )}

      {error && (
        <div className="w-full p-4 mb-6 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl flex items-center gap-3 shadow-sm backdrop-blur-sm">
          <div className="bg-destructive/20 p-2 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>
          </div>
          <span className="font-semibold">{error}</span>
        </div>
      )}

      {!isLoading && !error && filteredJobs.length === 0 && (
        <div className="text-center py-20 bg-card/50 rounded-2xl border border-dashed border-border">
          <div className="bg-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-xl font-bold mb-2 text-foreground">No jobs found</h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            {searchTerm ? "We couldn't find any jobs matching your search criteria." : "No jobs have been scraped yet. Use the control panel above to start."}
          </p>
        </div>
      )}

      {!isLoading && !error && filteredJobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredJobs.map((job, index) => (
            <Card 
              key={`${job.job_hash}-${index}`} 
              className="group flex flex-col overflow-hidden border-border/40 bg-card hover:bg-card/80 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1"
            >
              <div className="h-2 w-full bg-gradient-to-r from-primary/40 to-blue-500/40 group-hover:from-primary group-hover:to-blue-500 transition-all duration-500" />
              <CardHeader className="pb-4">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <CardTitle className="text-xl font-bold leading-tight line-clamp-2 mb-2 group-hover:text-primary transition-colors">
                      {job.title}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-1.5 text-base font-medium text-foreground/80">
                      <Building2 className="h-4 w-4 text-muted-foreground" />
                      {job.company}
                    </CardDescription>
                  </div>
                  {job.platform && (
                    <Badge variant="outline" className={`shrink-0 ${job.platform === 'LinkedIn' ? 'text-blue-500 border-blue-200' : 'text-indigo-500 border-indigo-200'}`}>
                      {job.platform}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              
              <CardContent className="flex-grow pb-4">
                <div className="flex flex-wrap gap-2 mb-4">
                  <Badge variant="secondary" className="bg-secondary/50 text-secondary-foreground hover:bg-secondary/70 flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {job.location}
                  </Badge>
                  <Badge variant="outline" className="border-primary/20 text-primary flex items-center gap-1">
                    Score: {job.score !== undefined ? job.score : 0}
                  </Badge>
                </div>
                
                <div className="relative">
                  <p className="text-sm text-muted-foreground line-clamp-4 leading-relaxed">
                    {job.full_description !== "Description not found" ? job.full_description : "No description available for this role."}
                  </p>
                  <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-card to-transparent group-hover:from-card/80 transition-all" />
                </div>
              </CardContent>
              
              <CardFooter className="pt-4 border-t border-border/40 mt-auto bg-muted/20">
                <Button 
                  variant="default" 
                  className="w-full font-semibold shadow-sm group-hover:shadow-md transition-all duration-300" 
                  onClick={() => window.open(job.link, '_blank')}
                >
                  View Application
                  <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
