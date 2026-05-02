import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function AnalysisResults({ results }) {
  if (!results) return null

  const { score, insights, parsed_data, missing_skills } = results
  const scoreValue = typeof score === "number" ? Math.round(score * 100) : 0

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 mt-12">
      
      <div className="flex flex-col md:flex-row gap-8">
        
        {/* Score Card */}
        <Card className="flex-1 shadow-sm border border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Match Score</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <div className="relative w-48 h-48 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="transparent" stroke="currentColor" className="text-muted/30" strokeWidth="8" />
                <circle 
                  cx="50" cy="50" r="45" fill="transparent" 
                  stroke={scoreValue >= 75 ? "#10b981" : scoreValue >= 50 ? "#f59e0b" : "#ef4444"} 
                  strokeWidth="8" 
                  strokeDasharray={`${scoreValue * 2.83} 283`}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-5xl font-extrabold text-foreground">{scoreValue}%</span>
                <span className="text-sm font-medium text-muted-foreground mt-1">Match</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Insights Card */}
        <Card className="flex-[2] shadow-sm border border-border bg-card flex flex-col">
          <CardHeader className="pb-4 border-b border-border/50">
            <CardTitle className="text-lg font-bold text-card-foreground flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary"><path d="M2 12h4l3-9 5 18 3-9h5"/></svg>
              AI Evaluation Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6 flex-1 bg-muted/20">
            <ul className="space-y-4">
              {insights && insights.map((insight, idx) => (
                <li key={idx} className="flex items-start gap-3 text-foreground">
                  <div className="min-w-1.5 h-1.5 rounded-full bg-primary mt-2"></div>
                  <span className="leading-relaxed">{insight}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Skills Analysis */}
      <Card className="shadow-sm border border-border bg-card">
        <CardHeader className="pb-4 border-b border-border/50">
          <CardTitle className="text-lg font-bold text-card-foreground">Skills Analysis</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
            
            {/* Found Skills */}
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500"><polyline points="20 6 9 17 4 12"/></svg>
                Identified Skills
              </h3>
              <div className="flex flex-wrap gap-2">
                {parsed_data?.skills && parsed_data.skills.map((skill, idx) => (
                  <Badge key={idx} variant="outline" className="border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-3 py-1 text-sm font-medium rounded-md">
                    {skill}
                  </Badge>
                ))}
                {(!parsed_data?.skills || parsed_data.skills.length === 0) && (
                  <span className="text-muted-foreground text-sm">No specific skills identified from the text.</span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>
                Missing Requirements
              </h3>
              <div className="flex flex-wrap gap-2">
                {missing_skills && missing_skills.map((skill, idx) => (
                  <Badge key={idx} variant="outline" className="border-red-500/20 bg-red-500/10 text-red-600 dark:text-red-400 px-3 py-1 text-sm font-medium rounded-md">
                    {skill}
                  </Badge>
                ))}
                {(!missing_skills || missing_skills.length === 0) && (
                  <span className="text-muted-foreground text-sm">No obvious missing requirements found.</span>
                )}
              </div>
            </div>

          </div>
        </CardContent>
      </Card>

      {/* Contact Info (if available) */}
      {parsed_data?.contact && (parsed_data.contact.email || parsed_data.contact.phone) && (
        <Card className="shadow-sm border border-border bg-card">
          <CardContent className="py-5 flex flex-wrap gap-8 items-center text-sm">
            <span className="font-semibold text-muted-foreground uppercase tracking-wider">Contact Info:</span>
            {parsed_data.contact.email && (
              <div className="flex items-center gap-2 text-foreground">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                {parsed_data.contact.email}
              </div>
            )}
            {parsed_data.contact.phone && (
              <div className="flex items-center gap-2 text-foreground">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></svg>
                {parsed_data.contact.phone}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
