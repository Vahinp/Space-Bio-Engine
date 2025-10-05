"use client"

import { usePapers } from "@/hooks/use-papers"
import { KnowledgeGraph } from "@/components/knowledge-graph"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function VisualizePage() {
  const { papers, loading, error } = usePapers()

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

      {/* Knowledge Graph - Full Screen */}
      <KnowledgeGraph papers={papers || []} />
    </div>
  )
}
