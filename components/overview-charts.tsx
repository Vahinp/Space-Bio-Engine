"use client"

import { D3AdvancedChart } from "@/components/d3-advanced-chart"

interface OverviewChartsProps {
  papers?: any[]
  searchQuery?: string
}

export function OverviewCharts({ papers, searchQuery }: OverviewChartsProps) {
  return (
    <D3AdvancedChart 
      papers={papers}
      searchQuery={searchQuery}
    />
  )
}
