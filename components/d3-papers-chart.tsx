"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import * as d3 from "d3"

interface PaperData {
  year: string
  count: number
}

interface D3PapersChartProps {
  data?: PaperData[]
  className?: string
}

export function D3PapersChart({ data, className }: D3PapersChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hoveredPoint, setHoveredPoint] = useState<PaperData | null>(null)

  // Default data if none provided
  const defaultData: PaperData[] = [
    { year: "2018", count: 45 },
    { year: "2019", count: 52 },
    { year: "2020", count: 48 },
    { year: "2021", count: 67 },
    { year: "2022", count: 89 },
    { year: "2023", count: 103 },
    { year: "2024", count: 78 },
  ]

  const chartData = data || defaultData

  useEffect(() => {
    if (!svgRef.current || !chartData.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove() // Clear previous renders

    const margin = { top: 20, right: 30, bottom: 70, left: 40 }
    const width = 400 - margin.left - margin.right
    const height = 300 - margin.top - margin.bottom

    // Create main group
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
      .padding(0.1)

    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(chartData, d => d.count) || 0])
      .range([height, 0])
      .nice()

    // Create gradient
    const gradient = svg
      .append("defs")
      .append("linearGradient")
      .attr("id", "areaGradient")
      .attr("gradientUnits", "userSpaceOnUse")
      .attr("x1", 0)
      .attr("y1", height)
      .attr("x2", 0)
      .attr("y2", 0)

    gradient
      .append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "hsl(var(--primary))")
      .attr("stop-opacity", 0.3)

    gradient
      .append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "hsl(var(--primary))")
      .attr("stop-opacity", 0.05)

    // Area generator
    const area = d3
      .area<PaperData>()
      .x(d => (xScale(d.year) || 0) + xScale.bandwidth() / 2)
      .y0(height)
      .y1(d => yScale(d.count))
      .curve(d3.curveCardinal.tension(0.4))

    // Line generator
    const line = d3
      .line<PaperData>()
      .x(d => (xScale(d.year) || 0) + xScale.bandwidth() / 2)
      .y(d => yScale(d.count))
      .curve(d3.curveCardinal.tension(0.4))

    // Add area
    g.append("path")
      .datum(chartData)
      .attr("fill", "url(#areaGradient)")
      .attr("d", area)
      .style("opacity", 0)
      .transition()
      .duration(1000)
      .style("opacity", 1)

    // Add line
    g.append("path")
      .datum(chartData)
      .attr("fill", "none")
      .attr("stroke", "hsl(var(--primary))")
      .attr("stroke-width", 3)
      .attr("d", line)
      .style("opacity", 0)
      .transition()
      .duration(1000)
      .delay(200)
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
      .attr("fill", "hsl(var(--primary))")
      .attr("stroke", "hsl(var(--background))")
      .attr("stroke-width", 3)
      .style("cursor", "pointer")
      .on("mouseover", function(event, d) {
        setHoveredPoint(d)
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 8)
      })
      .on("mouseout", function() {
        setHoveredPoint(null)
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", 6)
      })

    // Animate dots
    dots
      .transition()
      .duration(1000)
      .delay((d, i) => i * 100)
      .attr("r", 6)

    // Add hover line
    const hoverLine = g
      .append("line")
      .attr("class", "hover-line")
      .attr("stroke", "hsl(var(--muted-foreground))")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "3,3")
      .style("opacity", 0)

    // Add tooltip
    const tooltip = g
      .append("g")
      .attr("class", "tooltip")
      .style("opacity", 0)

    tooltip
      .append("rect")
      .attr("width", 80)
      .attr("height", 40)
      .attr("fill", "hsl(var(--popover))")
      .attr("stroke", "hsl(var(--border))")
      .attr("rx", 6)

    tooltip
      .append("text")
      .attr("x", 40)
      .attr("y", 20)
      .attr("text-anchor", "middle")
      .attr("fill", "hsl(var(--popover-foreground))")
      .attr("font-size", "12px")
      .attr("font-weight", "500")

    // Update tooltip on hover
    dots.on("mousemove", function(event, d) {
      const [mouseX, mouseY] = d3.pointer(event, g.node())
      
      hoverLine
        .attr("x1", mouseX)
        .attr("x2", mouseX)
        .attr("y1", 0)
        .attr("y2", height)
        .style("opacity", 1)

      tooltip
        .attr("transform", `translate(${mouseX - 40}, ${mouseY - 50})`)
        .style("opacity", 1)
        .select("text")
        .text(`${d.year}: ${d.count}`)
    })

    dots.on("mouseout", function() {
      hoverLine.style("opacity", 0)
      tooltip.style("opacity", 0)
    })

    // X axis with angled labels
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .style("color", "hsl(var(--muted-foreground))")
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "hsl(var(--muted-foreground))")
      .style("text-anchor", "end")
      .attr("transform", "rotate(-45)")
      .attr("dx", "-0.5em")
      .attr("dy", "0.5em")

    // Y axis
    g.append("g")
      .call(d3.axisLeft(yScale))
      .style("color", "hsl(var(--muted-foreground))")
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "hsl(var(--muted-foreground))")

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
      .style("color", "hsl(var(--border))")
      .style("opacity", 0.3)

    g.append("g")
      .attr("class", "grid")
      .call(
        d3
          .axisLeft(yScale)
          .tickSize(-width)
          .tickFormat(() => "")
      )
      .style("color", "hsl(var(--border))")
      .style("opacity", 0.3)

  }, [chartData])

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-base">Papers by Year</CardTitle>
        <CardDescription>Publication trends over time</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <svg ref={svgRef} className="w-full h-[300px]" />
          {hoveredPoint && (
            <div className="absolute top-4 right-4 bg-popover text-popover-foreground px-3 py-2 rounded-md shadow-lg border text-sm">
              <div className="font-semibold">{hoveredPoint.year}</div>
              <div className="text-muted-foreground">{hoveredPoint.count} papers</div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
