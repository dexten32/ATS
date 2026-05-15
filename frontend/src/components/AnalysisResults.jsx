import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { CheckCircle2, AlertCircle, Zap, Target, Award, Brain, Fingerprint, Activity } from "lucide-react"

export function AnalysisResults({ results }) {
  if (!results) return null

  const isAudit = results.mode === "audit"

  if (isAudit) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-8 pb-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Main Score */}
          <Card className="md:col-span-1 bg-gradient-to-br from-primary to-primary/80 text-primary-foreground border-none shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:scale-110 transition-transform">
               <Brain className="h-24 w-24" />
            </div>
            <CardContent className="pt-8 text-center space-y-4 relative z-10">
              <div className="inline-flex items-center justify-center p-3 bg-white/10 rounded-2xl mb-2">
                <Brain className="h-8 w-8" />
              </div>
              <div>
                <span className="text-6xl font-black tracking-tighter">{Math.round(results.overall_score)}%</span>
                <p className="text-[10px] uppercase font-bold tracking-widest opacity-70 mt-2">Hireability Score</p>
              </div>
              <div className="pt-4 border-t border-white/10">
                 <p className="text-[9px] uppercase font-black tracking-widest opacity-50">Market Intelligence Match</p>
                 <p className="text-sm font-bold">{Math.round(results.success_prediction)}% Selection Probability</p>
              </div>
            </CardContent>
          </Card>

          {/* Section Health - Promoted to Top */}
          <Card className="md:col-span-1 border-border/40 shadow-xl overflow-hidden">
             <CardHeader className="bg-muted/30 border-b pb-3">
               <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                 <Activity className="h-3 w-3" />
                 Core Integrity
               </CardTitle>
             </CardHeader>
             <CardContent className="pt-6 space-y-4">
               {results.section_health && Object.entries(results.section_health).map(([section, status]) => (
                 <div key={section} className="flex items-center justify-between">
                   <span className="text-xs font-bold text-muted-foreground uppercase tracking-tight">{section}</span>
                   {status ? (
                     <Badge className="bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/10 border-none px-1.5 h-5">
                       <CheckCircle2 className="h-3 w-3" />
                     </Badge>
                   ) : (
                     <Badge className="bg-red-500/10 text-red-600 hover:bg-red-500/10 border-none px-1.5 h-5">
                       <AlertCircle className="h-3 w-3" />
                     </Badge>
                   )}
                 </div>
               ))}
             </CardContent>
          </Card>

          {/* AI Suggestions Card */}
          <Card className="md:col-span-2 border-border/40 shadow-xl overflow-hidden">
            <CardHeader className="bg-primary/5 border-b pb-4">
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                <Zap className="h-4 w-4" />
                AI Suggestions
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {results.remedies && results.remedies.length > 0 ? (
                <div className="space-y-4">
                  <div className="space-y-3">
                    {results.remedies.map((remedy, i) => (
                      <div key={i} className="flex items-start gap-4 p-4 rounded-xl border border-border/60 bg-background hover:border-primary/50 transition-all group">
                        <div className="mt-1 flex-shrink-0">
                           <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-[10px] font-bold text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                             {i + 1}
                           </div>
                        </div>
                        <div className="flex-grow">
                          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">{remedy.type}</p>
                          <p className="text-sm font-medium text-foreground leading-relaxed">{remedy.text}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-10 text-center space-y-4">
                  <CheckCircle2 className="h-10 w-10 text-primary opacity-20" />
                  <p className="text-sm text-muted-foreground font-medium">Profile is highly optimized.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Impact Analysis */}
          <Card className="shadow-xl border-border/40 overflow-hidden group">
            <div className="h-1 w-full bg-primary/20 group-hover:bg-primary transition-colors" />
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold uppercase tracking-widest flex items-center gap-2 text-muted-foreground">
                <Target className="h-4 w-4 text-primary" />
                Impact & Metrics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-end justify-between">
                <div>
                  <span className="text-4xl font-black text-primary">{results.impact_metrics.count}</span>
                  <span className="text-muted-foreground ml-2 text-xs uppercase font-bold">Quantifiable Hits</span>
                </div>
                <Badge variant="outline" className="border-primary/20 text-primary">
                  {results.impact_metrics.score >= 80 ? 'EXCEPTIONAL' : 'NEEDS FOCUS'}
                </Badge>
              </div>
              <Progress value={results.impact_metrics.score} className="h-2 bg-primary/10" />
              <p className="text-xs text-muted-foreground leading-relaxed">
                Recruiters prioritize resumes with quantifiable achievements (%, $, numbers). Aim for 8+ high-impact metrics.
              </p>
            </CardContent>
          </Card>

          {/* Verb Strength */}
          <Card className="shadow-xl border-border/40 overflow-hidden group">
            <div className="h-1 w-full bg-primary/20 group-hover:bg-primary transition-colors" />
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold uppercase tracking-widest flex items-center gap-2 text-muted-foreground">
                <Zap className="h-4 w-4 text-primary" />
                Linguistic Intensity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
               <div className="flex items-end justify-between">
                <div>
                  <span className="text-4xl font-black text-primary">{results.verb_strength.power_verbs_count}</span>
                  <span className="text-muted-foreground ml-2 text-xs uppercase font-bold">Power Verbs</span>
                </div>
                <Badge variant="outline" className="border-primary/20 text-primary">
                  {Math.round(results.verb_strength.score)}% ACTIVE
                </Badge>
              </div>
              <Progress value={results.verb_strength.score} className="h-2 bg-primary/10" />
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="p-3 bg-muted/50 rounded-lg border border-border/40">
                   <p className="text-[9px] uppercase font-bold text-muted-foreground mb-2">Strong Signals</p>
                   <p className="text-xl font-black text-emerald-600 mb-2">{results.verb_strength.power_verbs_count}</p>
                   <div className="flex flex-wrap gap-1">
                      {results.verb_strength.found_power && results.verb_strength.found_power.map((v, i) => (
                        <span key={i} className="text-[8px] bg-emerald-500/10 text-emerald-700 px-1 rounded uppercase font-bold">{v}</span>
                      ))}
                   </div>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg border border-border/40">
                   <p className="text-[9px] uppercase font-bold text-muted-foreground mb-2">Weak Signals</p>
                   <p className="text-xl font-black text-red-500 mb-2">{results.verb_strength.weak_verbs_count}</p>
                   <div className="flex flex-wrap gap-1">
                      {results.verb_strength.found_weak && results.verb_strength.found_weak.map((v, i) => (
                        <span key={i} className="text-[8px] bg-red-500/10 text-red-700 px-1 rounded uppercase font-bold">{v}</span>
                      ))}
                   </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Identity Cloud */}
        <Card className="border-border/40 bg-muted/5 shadow-xl">
          <CardHeader className="border-b bg-background/50 pb-4">
            <CardTitle className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground flex items-center gap-2">
              <Fingerprint className="h-4 w-4 text-primary" />
              Marketplace Identity Cloud
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-8">
            {results.keyword_cloud && results.keyword_cloud.length > 0 ? (
              <div className="flex flex-wrap gap-3 justify-center">
                {results.keyword_cloud.map((kw, i) => (
                  <Badge key={i} variant="outline" className="px-5 py-2.5 text-xs font-bold bg-background border-border/60 hover:border-primary hover:text-primary transition-all cursor-default shadow-sm rounded-full">
                    {kw}
                  </Badge>
                ))}
              </div>
            ) : (
              <div className="py-10 text-center">
                <p className="text-sm text-muted-foreground italic">AI is currently indexing your unique skill clusters...</p>
              </div>
            )}
            <div className="mt-8 pt-6 border-t border-border/40 flex items-center justify-between">
              <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">
                Search Engine Profile Status: <span className="text-primary ml-2">ACTIVE & INDEXED</span>
              </p>
              <Fingerprint className="h-6 w-6 text-primary/20" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Standard Match Results
  const scoreValue = results.score || results.overall_score || 0

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 pb-20">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Main Score Column */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="shadow-2xl border-primary/20 bg-primary/5 overflow-hidden">
            <div className="h-2 w-full bg-primary" />
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-xs font-black uppercase tracking-[0.2em] text-primary">Match Accuracy</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center py-6">
              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="44" fill="transparent" stroke="currentColor" className="text-primary/10" strokeWidth="12" />
                  <circle 
                    cx="50" cy="50" r="44" fill="transparent" 
                    stroke="currentColor" 
                    strokeWidth="12" 
                    strokeDasharray={`${scoreValue * 2.76} 276`}
                    strokeLinecap="round"
                    className="text-primary transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-black text-foreground tracking-tighter">{Math.round(scoreValue)}%</span>
                </div>
              </div>
              
              <div className="mt-8 grid grid-cols-2 gap-4 w-full text-center">
                <div className="space-y-1">
                   <p className="text-[10px] font-bold text-muted-foreground uppercase">Skills</p>
                   <p className="text-lg font-black text-foreground">{Math.round(results.skill_match || 0)}%</p>
                </div>
                <div className="space-y-1">
                   <p className="text-[10px] font-bold text-muted-foreground uppercase">Exp</p>
                   <p className="text-lg font-black text-foreground">{Math.round(results.exp_match || 0)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/40">
             <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Award className="h-4 w-4 text-amber-500" />
                  Confidence Level
                </CardTitle>
             </CardHeader>
             <CardContent>
                <div className="flex items-center justify-between">
                   <Badge className={results.confidence === "High" ? "bg-emerald-500" : "bg-amber-500"}>
                     {results.confidence}
                   </Badge>
                   <span className="text-xs font-mono text-muted-foreground">{results.confidence_value}% certainty</span>
                </div>
             </CardContent>
          </Card>
        </div>

        {/* Feedback Column */}
        <div className="lg:col-span-8 space-y-6">
           <Card className="border-border/40 shadow-sm h-full">
              <CardHeader className="border-b bg-muted/20">
                 <CardTitle className="text-lg flex items-center gap-2">
                   <Brain className="h-5 w-5 text-primary" />
                   AI Optimization Feedback
                 </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-8">
                 {/* Strengths */}
                 <div className="space-y-3">
                    <h4 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Core Strengths</h4>
                    <div className="flex flex-wrap gap-2">
                       {results.feedback?.strengths?.map((s, i) => (
                         <Badge key={i} variant="outline" className="bg-emerald-50 border-emerald-200 text-emerald-700 font-bold">
                           {s}
                         </Badge>
                       ))}
                    </div>
                 </div>

                 {/* Improvements */}
                 <div className="space-y-3">
                    <h4 className="text-xs font-bold text-amber-600 uppercase tracking-widest">Optimization Needed</h4>
                    <div className="space-y-3">
                       {results.feedback?.resume_updates?.map((u, i) => (
                         <div key={i} className="flex items-start gap-3 p-3 bg-amber-50/50 rounded-lg border border-amber-100 text-sm">
                            <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                            <span className="text-amber-900 font-medium">{u}</span>
                         </div>
                       ))}
                    </div>
                 </div>

                 {/* Gaps */}
                 <div className="space-y-3">
                    <h4 className="text-xs font-bold text-red-600 uppercase tracking-widest">Critical Gaps</h4>
                    <div className="space-y-3">
                       {results.feedback?.missing_requirements?.map((m, i) => (
                         <div key={i} className="flex items-start gap-3 p-3 bg-red-50/50 rounded-lg border border-red-100 text-sm">
                            <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                            <span className="text-red-900 font-medium">{m}</span>
                         </div>
                       ))}
                    </div>
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  )
}

