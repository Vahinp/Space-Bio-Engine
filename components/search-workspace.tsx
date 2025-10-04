"use client"

import { useState } from "react"
import { SearchHeader } from "@/components/search-header"
import { FilterPanel } from "@/components/filter-panel"
import { ResultsList } from "@/components/results-list"
import { InsightsTabs } from "@/components/insights-tabs"

export function SearchWorkspace() {
  const [showFilters, setShowFilters] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [filters, setFilters] = useState({
    yearRange: [2000, 2024] as [number, number],
    organisms: [] as string[],
    missions: [] as string[],
    environments: [] as string[],
    tissues: [] as string[],
    assays: [] as string[],
    outcomes: [] as string[],
    hasOSDR: false,
  })

  return (
    <div className="flex h-full flex-col">
      <SearchHeader
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        showFilters={showFilters}
        onToggleFilters={() => setShowFilters(!showFilters)}
      />

      <div className="flex flex-1 overflow-hidden">
        {showFilters && (
          <div className="w-64 border-r border-border overflow-y-auto">
            <FilterPanel filters={filters} onFiltersChange={setFilters} />
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          <InsightsTabs />
          <ResultsList searchQuery={searchQuery} filters={filters} />
        </div>
      </div>
    </div>
  )
}
