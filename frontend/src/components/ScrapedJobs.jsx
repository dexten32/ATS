import { useState, useEffect } from 'react';
import { ExternalLink, MapPin, Building2, Briefcase, Search, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function ScrapedJobs() {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await fetch('/api/v1/jobs');
        if (!response.ok) {
          throw new Error('Failed to fetch jobs');
        }
        const data = await response.json();
        setJobs(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchJobs();
  }, []);

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

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
          <p className="text-lg font-medium text-muted-foreground">Loading job data...</p>
        </div>
      )}

      {error && (
        <div className="w-full p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl flex items-center gap-3 shadow-sm backdrop-blur-sm">
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
            {searchTerm ? "We couldn't find any jobs matching your search criteria." : "No jobs have been scraped yet. Run the scraper script to populate this list."}
          </p>
        </div>
      )}

      {!isLoading && !error && filteredJobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredJobs.map((job, index) => (
            <Card 
              key={job.job_hash || index} 
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
                </div>
              </CardHeader>
              
              <CardContent className="flex-grow pb-4">
                <div className="flex flex-wrap gap-2 mb-4">
                  <Badge variant="secondary" className="bg-secondary/50 text-secondary-foreground hover:bg-secondary/70 flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {job.location}
                  </Badge>
                  <Badge variant="outline" className="border-primary/20 text-primary flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    New Role
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
