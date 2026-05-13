import { useState } from 'react'
import { ThemeProvider } from '@/components/ThemeProvider'
import { Header } from '@/components/layout/Header'
import { Dashboard } from '@/components/views/Dashboard'
import { ScrapedJobs } from '@/components/ScrapedJobs'

function App() {
  const [currentView, setCurrentView] = useState('home');

  return (
    <ThemeProvider defaultTheme="light" storageKey="ats-ui-theme">
      <div className="min-h-screen bg-background text-foreground font-sans transition-colors duration-200 selection:bg-primary/20 selection:text-primary">
        
        <Header currentView={currentView} setCurrentView={setCurrentView} />

        <main className={`container mx-auto px-4 py-12 ${currentView === 'home' ? 'max-w-5xl' : 'max-w-7xl'}`}>
          {currentView === 'home' ? <Dashboard setCurrentView={setCurrentView} /> : <ScrapedJobs />}
        </main>
        
      </div>
    </ThemeProvider>
  )
}

export default App
