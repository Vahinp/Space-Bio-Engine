"use client"

import { Rocket, Bookmark, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"

export function AppHeader() {
  return (
    <header className="border-b border-border bg-background sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center">
              <Rocket className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-bold leading-none">BioSpace Explorer</h1>
              <p className="text-xs text-muted-foreground">NASA Space Biology Research</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="gap-2 transition-all hover:scale-105">
            <Bookmark className="h-4 w-4" />
            Bookmarks
          </Button>
          <Button variant="ghost" size="icon" className="transition-colors hover:bg-accent">
            <Settings className="h-4 w-4" />
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
