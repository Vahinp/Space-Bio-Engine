import { FilterState } from '../lib/types'

interface FilterBarProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
}

export default function FilterBar({ filters, onFiltersChange }: FilterBarProps) {
  const handleChange = (key: keyof FilterState, value: string) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            id="search"
            type="text"
            value={filters.search}
            onChange={(e) => handleChange('search', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Search studies"
            placeholder="Search studies..."
          />
        </div>

        <div>
          <label htmlFor="organism" className="block text-sm font-medium text-gray-700 mb-1">
            Organism
          </label>
          <select
            id="organism"
            value={filters.organism}
            onChange={(e) => handleChange('organism', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Filter by organism"
          >
            <option value="">All Organisms</option>
            <option value="human">Human</option>
            <option value="mouse">Mouse</option>
            <option value="rat">Rat</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-1">
            Year
          </label>
          <select
            id="year"
            value={filters.year}
            onChange={(e) => handleChange('year', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Filter by year"
          >
            <option value="">All Years</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
            <option value="2021">2021</option>
            <option value="2020">2020</option>
          </select>
        </div>

        <div>
          <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-1">
            Source
          </label>
          <select
            id="source"
            value={filters.source}
            onChange={(e) => handleChange('source', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Filter by source"
          >
            <option value="">All Sources</option>
            <option value="pubmed">PubMed</option>
            <option value="arxiv">arXiv</option>
            <option value="bioRxiv">bioRxiv</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
    </div>
  )
}
