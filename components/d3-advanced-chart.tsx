"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import * as d3 from "d3"

interface PaperData {
  year: string
  count: number
  category?: string
}

interface D3AdvancedChartProps {
  data?: PaperData[]
  className?: string
  searchQuery?: string
  papers?: any[] // The actual papers from search results
}

export function D3AdvancedChart({ data, className, searchQuery, papers }: D3AdvancedChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hoveredPoint, setHoveredPoint] = useState<PaperData | null>(null)
  const [selectedYear, setSelectedYear] = useState<string | null>(null)
  const [chartData, setChartData] = useState<PaperData[]>([])

  // Enhanced data with categories
  const defaultData: PaperData[] = [
    { year: "2018", count: 45, category: "Space Biology" },
    { year: "2019", count: 52, category: "Space Biology" },
    { year: "2020", count: 48, category: "Space Biology" },
    { year: "2021", count: 67, category: "Space Biology" },
    { year: "2022", count: 89, category: "Space Biology" },
    { year: "2023", count: 103, category: "Space Biology" },
    { year: "2024", count: 78, category: "Space Biology" },
  ]

  // Process search results into chart data
  const processSearchResults = (papers: any[]): PaperData[] => {
    if (!papers || papers.length === 0) return defaultData
    
    // Group papers by year
    const yearGroups = papers.reduce((acc, paper) => {
      const year = paper.year?.toString() || 'Unknown'
      acc[year] = (acc[year] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    // Convert to chart data format
    const processedData = Object.entries(yearGroups)
      .map(([year, count]) => ({
        year,
        count,
        category: "Search Results"
      }))
      .sort((a, b) => a.year.localeCompare(b.year))
    
    return processedData.length > 0 ? processedData : defaultData
  }

  // Update chart data when papers change
  useEffect(() => {
    if (papers && papers.length > 0) {
      const newData = processSearchResults(papers)
      setChartData(newData)
      console.log("D3 Chart: Updated with search results", { papersCount: papers.length, chartData: newData })
    } else if (data) {
      setChartData(data)
    } else {
      setChartData(defaultData)
    }
  }, [papers, data])

  useEffect(() => {
    if (!svgRef.current || !chartData.length) {
      console.log("D3 Chart: Missing ref or data", { ref: !!svgRef.current, dataLength: chartData.length })
      return
    }

    console.log("D3 Chart: Rendering with data", chartData)

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 30, right: 50, bottom: 50, left: 60 }
    const width = 500 - margin.left - margin.right
    const height = 350 - margin.top - margin.bottom

    const g = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Scales
    const xScale = d3
      .scaleBand()
      .domain(chartData.map(d => d.year))
      .range([0, width])
      .padding(0.2)

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(chartData, d => d.count) || 0])
      .range([height, 0])
      .nice()

    console.log("D3 Chart: Scales created", { xDomain: xScale.domain(), yDomain: yScale.domain() })

    // Create gradient
    const defs = svg.append("defs")
    const mainGradient = defs
      .append("linearGradient")
      .attr("id", "mainGradient")
      .attr("gradientUnits", "userSpaceOnUse")
      .attr("x1", 0)
      .attr("y1", height)
      .attr("x2", 0)
      .attr("y2", 0)

    mainGradient
      .append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#3b82f6")
      .attr("stop-opacity", 0.4)

    mainGradient
      .append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#3b82f6")
      .attr("stop-opacity", 0.05)

    // Area generator
    const area = d3
      .area<PaperData>()
      .x(d => (xScale(d.year) || 0) + xScale.bandwidth() / 2)
      .y0(height)
      .y1(d => yScale(d.count))
      .curve(d3.curveCardinal.tension(0.6))

    // Line generator
    const line = d3
      .line<PaperData>()
      .x(d => (xScale(d.year) || 0) + xScale.bandwidth() / 2)
      .y(d => yScale(d.count))
      .curve(d3.curveCardinal.tension(0.6))

    // Add area
    g.append("path")
      .datum(chartData)
      .attr("fill", "url(#mainGradient)")
      .attr("d", area)
      .style("opacity", 0)
      .transition()
      .duration(1500)
      .ease(d3.easeCubicInOut)
      .style("opacity", 1)

    // Add line
    g.append("path")
      .datum(chartData)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 4)
      .attr("d", line)
      .style("opacity", 0)
      .transition()
      .duration(1500)
      .delay(300)
      .ease(d3.easeCubicInOut)
      .style("opacity", 1)

    // Add dots
    const dots = g
      .selectAll(".dot")
      .data(chartData)
      .enter()
      .append("circle")
      .attr("class", "dot")
      .attr("cx", d => (xScale(d.year) || 0) + xScale.bandwidth() / 2)
      .attr("cy", d => yScale(d.count))
      .attr("r", 0)
      .attr("fill", "#3b82f6")
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 4)
      .style("cursor", "pointer")
      .on("mouseover", function(event, d) {
        setHoveredPoint(d)
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 10)
          .attr("fill", "#f59e0b")
      })
      .on("mouseout", function() {
        setHoveredPoint(null)
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 7)
          .attr("fill", "#3b82f6")
      })
      .on("click", function(event, d) {
        setSelectedYear(d.year)
      })

    // Animate dots
    dots
      .transition()
      .duration(800)
      .delay((d, i) => i * 150)
      .ease(d3.easeBackOut)
      .attr("r", 7)

    // X axis
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .style("color", "#6b7280")
      .selectAll("text")
      .style("font-size", "13px")
      .style("fill", "#6b7280")
      .style("font-weight", "500")

    // Y axis
    g.append("g")
      .call(d3.axisLeft(yScale).ticks(6))
      .style("color", "#6b7280")
      .selectAll("text")
      .style("font-size", "13px")
      .style("fill", "#6b7280")
      .style("font-weight", "500")

    // Add grid lines
    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3
          .axisBottom(xScale)
          .tickSize(-height)
          .tickFormat(() => "")
      )
      .style("color", "#e5e7eb")
      .style("opacity", 0.3)

    g.append("g")
      .attr("class", "grid")
      .call(
        d3
          .axisLeft(yScale)
          .tickSize(-width)
          .tickFormat(() => "")
      )
      .style("color", "#e5e7eb")
      .style("opacity", 0.3)

    console.log("D3 Chart: Rendering complete")

  }, [chartData])

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          📊 Papers by Year
          {selectedYear && (
            <Badge variant="secondary" className="ml-2">
              {selectedYear}
            </Badge>
          )}
          {searchQuery && (
            <Badge variant="outline" className="ml-2">
              Search: {searchQuery}
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          {searchQuery 
            ? `Showing ${chartData.reduce((sum, d) => sum + d.count, 0)} papers from search results`
            : "Interactive publication trends with smooth animations"
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <svg ref={svgRef} className="w-full h-[350px]" />
          {hoveredPoint && (
            <div className="absolute top-4 right-4 bg-popover text-popover-foreground px-4 py-3 rounded-lg shadow-xl border text-sm backdrop-blur-sm">
              <div className="font-bold text-lg">{hoveredPoint.year}</div>
              <div className="text-muted-foreground">{hoveredPoint.count} papers published</div>
              {hoveredPoint.category && (
                <div className="text-xs text-accent-foreground mt-1">{hoveredPoint.category}</div>
              )}
            </div>
          )}
          {selectedYear && (
            <div className="absolute bottom-4 left-4 bg-primary text-primary-foreground px-3 py-2 rounded-md text-sm font-medium">
              Selected: {selectedYear}
            </div>
          )}
        </div>
        <div className="mt-4 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedYear(null)}
            className="text-xs"
          >
            Clear Selection
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Trigger re-animation of dots
              const svg = d3.select(svgRef.current)
              svg.selectAll(".dot")
                .transition()
                .duration(300)
                .attr("r", 0)
                .transition()
                .duration(500)
                .delay((d, i) => i * 100)
                .ease(d3.easeBackOut)
                .attr("r", 7)
            }}
            className="text-xs"
          >
            Re-animate Dots
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
