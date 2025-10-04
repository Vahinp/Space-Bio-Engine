"use client"

import { D3AdvancedChart } from "@/components/d3-advanced-chart"

interface OverviewChartsProps {
  papers?: any[]
  searchQuery?: string
}

const papersByYear = [
  { year: "2018", count: 45, category: "Space Biology" },
  { year: "2019", count: 52, category: "Space Biology" },
  { year: "2020", count: 48, category: "Space Biology" },
  { year: "2021", count: 67, category: "Space Biology" },
  { year: "2022", count: 89, category: "Space Biology" },
  { year: "2023", count: 103, category: "Space Biology" },
  { year: "2024", count: 78, category: "Space Biology" },
]

export function OverviewCharts({ papers, searchQuery }: OverviewChartsProps) {
  return (
    <D3AdvancedChart 
      data={papersByYear} 
      papers={papers}
      searchQuery={searchQuery}
    />
  )
}
