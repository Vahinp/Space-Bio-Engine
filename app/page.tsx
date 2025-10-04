"use client"

import { useState } from "react"
import { AppHeader } from "@/components/app-header"
import { SearchBar } from "@/components/search-bar"
import { FilterPanel } from "@/components/filter-panel"
import { InsightsTabs } from "@/components/insights-tabs"
import { ResultsList } from "@/components/results-list"
import { ChatbotPanel } from "@/components/chatbot-panel"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MessageSquare, FileSearch } from "lucide-react"

export default function Home() {
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
    <div className="min-h-screen bg-background flex flex-col">
      <AppHeader />

      <main className="flex-1 flex flex-col">
        {/* Search Section */}
        <div className="border-b border-border bg-background sticky top-0 z-40">
          <div className="px-6 py-4">
            <SearchBar onSearch={setSearchQuery} />
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Sidebar */}
          <aside className="w-80 border-r border-border bg-muted/30 overflow-y-auto">
            <FilterPanel filters={filters} onFiltersChange={setFilters} />
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
                <InsightsTabs />
                <div className="flex-1 overflow-y-auto">
                  <ResultsList searchQuery={searchQuery} filters={filters} />
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
