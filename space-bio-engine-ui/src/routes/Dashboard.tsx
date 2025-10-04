import { useState } from 'react'
import FilterBar from '../components/FilterBar'
import ResultsPlaceholder from '../components/ResultsPlaceholder'
import ChatbotDrawer from '../components/ChatbotDrawer'
import { FilterState } from '../lib/types'

export default function Dashboard() {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    organism: '',
    year: '',
    source: '',
  })
  const [isChatOpen, setIsChatOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-gray-900">
              Space Bio Engine
            </h1>
            <button
              onClick={() => setIsChatOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Open Chat
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <FilterBar filters={filters} onFiltersChange={setFilters} />
        <ResultsPlaceholder />
      </main>

      <ChatbotDrawer
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  )
}
