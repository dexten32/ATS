import { ThemeSwitcher } from '@/components/ThemeSwitcher'

export function Header({ currentView, setCurrentView }) {
  return (
    <header className="bg-card border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center text-primary-foreground shadow-sm">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m9 15 2 2 4-4"/></svg>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">ATS<span className="text-primary">Pro</span></h1>
        </div>
        <div className="flex items-center">
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground mr-4">
            <button onClick={() => setCurrentView('home')} className={`hover:text-foreground transition-colors ${currentView === 'home' ? 'text-primary font-semibold' : ''}`}>Dashboard</button>
            <button onClick={() => setCurrentView('jobs')} className={`hover:text-foreground transition-colors ${currentView === 'jobs' ? 'text-primary font-semibold' : ''}`}>Scraped Jobs</button>
            <a href="#" className="hover:text-foreground transition-colors">Settings</a>
          </nav>
          <ThemeSwitcher />
        </div>
      </div>
    </header>
  )
}
