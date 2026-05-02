import { useTheme } from "./ThemeProvider"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" className="w-9 h-9">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-foreground"><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" /></svg>
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[200px]">
        <DropdownMenuLabel className="text-xs text-muted-foreground">Light Themes</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => setTheme("light")} className={theme === "light" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-white to-slate-300 border border-border"></div>
            Light (Default)
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("theme-ocean")} className={theme === "theme-ocean" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-blue-100 to-blue-500 border border-border"></div>
            Ocean
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("theme-terracotta")} className={theme === "theme-terracotta" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-[#f6f2ea] to-[#e2725b] border border-border"></div>
            Terracotta
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("theme-lavender")} className={theme === "theme-lavender" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-[#f4f0f7] to-[#a891b7] border border-border"></div>
            Lavender
          </div>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuLabel className="text-xs text-muted-foreground">Dark Themes</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => setTheme("theme-charcoal")} className={theme === "theme-charcoal" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-[#3b82f6] to-[#1e2329] border border-border"></div>
            Charcoal (Default)
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")} className={theme === "dark" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-slate-600 to-slate-900 border border-border"></div>
            Dark
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("theme-midnight")} className={theme === "theme-midnight" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-[#8a9bcf] to-[#090b14] border border-border"></div>
            Midnight
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem onClick={() => setTheme("theme-plum")} className={theme === "theme-plum" ? "bg-accent" : ""}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-[#4a7c59] to-[#2b1b24] border border-border"></div>
            Plum
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
