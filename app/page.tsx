"use client"

import { useState } from "react"
import { AppHeader } from "@/components/app-header"
import { SearchBar } from "@/components/search-bar"
import { FilterPanel } from "@/components/filter-panel"
import { InsightsTabs } from "@/components/insights-tabs"
import { ResultsList } from "@/components/results-list"
import { ChatbotPanel } from "@/components/chatbot-panel"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MessageSquare, FileSearch, Database, Loader2 } from "lucide-react"
import { usePapers } from "@/hooks/use-papers"

export default function Home() {
  const { papers, loading, error, searchQuery, setSearchQuery, searchPapers, enriching, enrichAllPapers, enrichmentStatus } = usePapers()
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

  // Convert frontend filters to Elasticsearch format
  const convertFiltersToES = (frontendFilters: typeof filters) => {
    const esFilters: any = {
      year_gte: frontendFilters.yearRange[0],
      year_lte: frontendFilters.yearRange[1],
    }

    // Only add filters if they have values
    if (frontendFilters.organisms.length > 0) {
      esFilters.organism = frontendFilters.organisms[0] // ES supports single value for now
    }
    if (frontendFilters.missions.length > 0) {
      esFilters.mission = frontendFilters.missions[0]
    }
    if (frontendFilters.environments.length > 0) {
      esFilters.environment = frontendFilters.environments[0]
    }
    if (frontendFilters.hasOSDR) {
      esFilters.hasOSDR = true
    }

    return esFilters
  }

  // Handle filter changes and trigger search
  const handleFilterSearch = (frontendFilters: typeof filters) => {
    const esFilters = convertFiltersToES(frontendFilters)
    // Search with current query and filters, or just filters if no query
    const query = searchQuery.trim() || ""
    searchPapers(query, esFilters)
  }

  // Handle individual filter changes and update search query
  const handleFiltersChange = (newFilters: typeof filters) => {
    setFilters(newFilters)
    
    // Build search query from filters
    const filterTerms = []
    
    if (newFilters.organisms.length > 0) {
      filterTerms.push(`organism:${newFilters.organisms.join(',')}`)
    }
    if (newFilters.missions.length > 0) {
      filterTerms.push(`mission:${newFilters.missions.join(',')}`)
    }
    if (newFilters.environments.length > 0) {
      filterTerms.push(`environment:${newFilters.environments.join(',')}`)
    }
    if (newFilters.tissues.length > 0) {
      filterTerms.push(`tissue:${newFilters.tissues.join(',')}`)
    }
    if (newFilters.assays.length > 0) {
      filterTerms.push(`assay:${newFilters.assays.join(',')}`)
    }
    if (newFilters.outcomes.length > 0) {
      filterTerms.push(`outcome:${newFilters.outcomes.join(',')}`)
    }
    if (newFilters.hasOSDR) {
      filterTerms.push('hasOSDR:true')
    }
    if (newFilters.yearRange[0] !== 2000 || newFilters.yearRange[1] !== 2024) {
      filterTerms.push(`year:${newFilters.yearRange[0]}-${newFilters.yearRange[1]}`)
    }
    
    // Update search query with filter terms
    const filterQuery = filterTerms.join(' ')
    setSearchQuery(filterQuery)
  }

  // Handle search query changes
  const handleSearchQueryChange = (query: string) => {
    setSearchQuery(query)
    // Auto-search when query changes (including from filters)
    const esFilters = convertFiltersToES(filters)
    searchPapers(query, esFilters)
  }

  // Handle search button click
  const handleSearchClick = () => {
    const esFilters = convertFiltersToES(filters)
    searchPapers(searchQuery, esFilters)
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <AppHeader />

      <main className="flex-1 flex flex-col">
            {/* Search Section */}
            <div className="border-b border-border bg-background sticky top-0 z-40">
              <div className="px-6 py-4">
                <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <SearchBar 
                          value={searchQuery}
                          onSearch={handleSearchQueryChange} 
                          onSearchClick={handleSearchClick} 
                        />
                      </div>
                  <button
                    onClick={enrichAllPapers}
                    disabled={enriching}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {enriching ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Database className="h-4 w-4" />
                    )}
                    {enriching ? 'Enriching...' : 'Enrich Papers'}
                  </button>
                </div>
                {enrichmentStatus && (
                  <div className="mt-3 p-3 bg-muted rounded-md text-sm">
                    <div className="flex items-center gap-4">
                      <span>Total: {enrichmentStatus.total}</span>
                      <span className="text-green-600">Enriched: {enrichmentStatus.enriched}</span>
                      <span className="text-yellow-600">Skipped: {enrichmentStatus.skipped}</span>
                      <span className="text-red-600">Errors: {enrichmentStatus.errors}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Sidebar */}
              <aside className="w-80 border-r border-border bg-muted/30 overflow-y-auto">
                <FilterPanel 
                  filters={filters} 
                  onFiltersChange={handleFiltersChange} 
                  onSearchWithFilters={handleFilterSearch}
                />
              </aside>

          {/* Content Area with Tabs */}
          <div className="flex-1 flex flex-col">
            <Tabs defaultValue="search" className="flex-1 flex flex-col">
              <div className="border-b border-border bg-background">
                <TabsList className="h-12 bg-transparent border-b-0 px-6">
                  <TabsTrigger value="search" className="gap-2 transition-all hover:scale-105">
                    <FileSearch className="h-4 w-4" />
                    Search & Insights
                  </TabsTrigger>
                  <TabsTrigger value="chat" className="gap-2 transition-all hover:scale-105">
                    <MessageSquare className="h-4 w-4" />
                    AI Assistant
                  </TabsTrigger>
                </TabsList>
              </div>

                  <TabsContent value="search" className="flex-1 flex flex-col m-0">
                    <InsightsTabs papers={papers} searchQuery={searchQuery} />
                    <div className="flex-1 overflow-y-auto">
                      <ResultsList 
                        searchQuery={searchQuery} 
                        filters={filters} 
                        papers={papers}
                        loading={loading}
                        error={error}
                      />
                    </div>
                  </TabsContent>

              <TabsContent value="chat" className="flex-1 m-0">
                <ChatbotPanel />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  )
}
