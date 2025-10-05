"use client"
    
import { usePapers } from "@/hooks/use-papers"
import { KnowledgeGraph } from "@/components/knowledge-graph"
import { CategoryGraph } from "@/components/category-graph"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useState } from "react"

export default function VisualizePage() {
  const { papers, loading, error } = usePapers()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  console.log('VisualizePage - papers:', papers?.length, 'loading:', loading, 'error:', error)

  if (loading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white text-lg">Loading papers...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gray-900">
        <div className="text-red-400 text-lg">Error loading papers: {error}</div>
      </div>
    )
  }

  if (!papers || papers.length === 0) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gray-900">
        <div className="text-white text-lg">No papers found. Please search for papers first.</div>
      </div>
    )
  }

  const categories = [
    { key: 'organism', label: 'Organism', icon: '🧬' },
    { key: 'mission', label: 'Mission/Platform', icon: '🚀' },
    { key: 'environment', label: 'Environment', icon: '🌌' },
    { key: 'tissue', label: 'Tissue/System', icon: '🔬' },
    { key: 'assay', label: 'Assay/Omics', icon: '🧪' },
    { key: 'outcome', label: 'Outcome', icon: '📊' }
  ]

  return (
    <div className="w-full h-screen bg-gray-900 relative">
      {/* Back button */}
      <div className="absolute top-4 left-4 z-10">
        <Link href="/">
          <Button variant="outline" className="bg-gray-800 border-gray-600 text-white hover:bg-gray-700">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </Link>
      </div>

      {/* Paper count indicator */}
      <div className="absolute top-4 right-4 z-10 bg-gray-800 text-white px-3 py-2 rounded-lg text-sm">
        {papers?.length || 0} papers
      </div>

      {/* Category buttons */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10 flex gap-2">
        {categories.map((category) => (
          <Button
            key={category.key}
            variant={selectedCategory === category.key ? "default" : "outline"}
            className={`w-40 justify-start ${
              selectedCategory === category.key 
                ? "bg-blue-600 text-white" 
                : "bg-gray-800 border-gray-600 text-white hover:bg-gray-700"
            }`}
            onClick={() => setSelectedCategory(selectedCategory === category.key ? null : category.key)}
          >
            <span className="mr-2">{category.icon}</span>
            {category.label}
          </Button>
        ))}
      </div>

      {/* Graph - Full Screen */}
      {selectedCategory ? (
        <CategoryGraph papers={papers || []} category={selectedCategory} />
      ) : (
        <KnowledgeGraph papers={papers || []} />
      )}
    </div>
  )
}
