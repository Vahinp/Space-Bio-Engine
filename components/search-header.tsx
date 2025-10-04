"use client"

import { Search, X, SlidersHorizontal, Info } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

interface SearchHeaderProps {
  searchQuery: string
  onSearchQueryChange: (query: string) => void
  showFilters: boolean
  onToggleFilters: () => void
}

export function SearchHeader({ searchQuery, onSearchQueryChange, showFilters, onToggleFilters }: SearchHeaderProps) {
  return (
    <div className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by keyword, organism, mission, microgravity, radiation, tissue, result…"
              value={searchQuery}
              onChange={(e) => onSearchQueryChange(e.target.value)}
              className="h-11 pl-10 pr-4 text-base"
            />
          </div>
          <Button size="lg" className="gap-2 transition-all hover:scale-105">
            <Search className="h-4 w-4" />
            Search
          </Button>
          {searchQuery && (
            <Button
              variant="ghost"
              size="lg"
              onClick={() => onSearchQueryChange("")}
              className="gap-2 transition-colors"
            >
              <X className="h-4 w-4" />
              Clear
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={showFilters ? "secondary" : "outline"}
            size="sm"
            onClick={onToggleFilters}
            className="gap-2 transition-all hover:scale-105"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
          </Button>

          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2 bg-transparent transition-colors hover:bg-accent">
                <Info className="h-4 w-4" />
                Advanced
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="start">
              <div className="space-y-3">
                <h4 className="font-semibold text-sm">Boolean Search Tips</h4>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p>
                    <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">AND</code> - All terms must appear
                  </p>
                  <p>
                    <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">OR</code> - Any term can appear
                  </p>
                  <p>
                    <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">NOT</code> - Exclude terms
                  </p>
                  <p>
                    <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">"..."</code> - Exact phrase
                  </p>
                </div>
                <div className="pt-2 border-t border-border">
                  <p className="text-xs text-muted-foreground">
                    Example: <span className="text-foreground">"bone loss" AND microgravity NOT mice</span>
                  </p>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>
    </div>
  )
}
