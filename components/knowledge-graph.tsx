"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import * as d3 from "d3"

interface PaperNode {
  id: string
  title: string
  year: number
  authors: string
  abstract?: string
  doi?: string
  hasOSDR?: boolean
  hasDOI?: boolean
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface KnowledgeGraphProps {
  papers: any[]
  searchQuery?: string
  className?: string
}

export function KnowledgeGraph({ papers, searchQuery, className }: KnowledgeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<PaperNode | null>(null)
  const [hoveredNode, setHoveredNode] = useState<PaperNode | null>(null)

  // Process papers into nodes - simple visualization
  const processGraphData = (papers: any[]) => {
    if (!papers || papers.length === 0) return { nodes: [], links: [] }

    // Create nodes from papers
    const nodes: PaperNode[] = papers.map((paper, index) => ({
      id: paper.id || `paper-${index}`,
      title: paper.title || 'Untitled',
      year: paper.year || 2023,
      authors: paper.authors || 'Unknown Authors',
      abstract: paper.abstract,
      doi: paper.doi,
      hasOSDR: paper.hasOSDR || false,
      hasDOI: paper.hasDOI || false
    }))

    // Create simple links between nearby papers
    const links: any[] = []
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < Math.min(i + 3, nodes.length); j++) {
        links.push({
          source: nodes[i].id,
          target: nodes[j].id,
          weight: 0.5
        })
      }
    }

    return { nodes, links }
  }

  useEffect(() => {
    console.log('KnowledgeGraph - papers received:', papers?.length)
    
    if (!papers || papers.length === 0) {
      console.log('KnowledgeGraph - no papers')
      return
    }

    // Define handleKeyDown outside setTimeout
    let handleKeyDown: ((event: KeyboardEvent) => void) | null = null

    // Small delay to ensure SVG is mounted
    const timer = setTimeout(() => {
      if (!svgRef.current) {
        console.log('KnowledgeGraph - no svg ref after delay')
        return
      }

      const svg = d3.select(svgRef.current)
      svg.selectAll("*").remove()

      const { nodes, links } = processGraphData(papers)
      console.log('KnowledgeGraph - processed nodes:', nodes.length, 'links:', links.length)
      
      if (nodes.length === 0) {
        console.log('KnowledgeGraph - no nodes to render')
        return
      }

      // Get the actual SVG dimensions
      const svgElement = svgRef.current
      const width = svgElement.clientWidth || window.innerWidth
      const height = svgElement.clientHeight || window.innerHeight
      
      console.log('KnowledgeGraph - dimensions:', width, height)

    // Simple dark background
    svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "#1f2937")

    // Create mind map-style simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("radial", d3.forceRadial((d: any, i: number) => {
        // Create radial zones based on paper importance
        if (d.hasOSDR) return 50 + (i % 3) * 30  // OSDR papers closer to center
        if (d.hasDOI) return 100 + (i % 4) * 40  // DOI papers in middle ring
        return 150 + (i % 5) * 50  // Other papers in outer rings
      }, width / 2, height / 2).strength(0.1))

    // Create simple links
    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .style("stroke", "#6b7280")
      .style("stroke-width", 1)
      .style("stroke-opacity", 0.5)

    // Create node groups for circles and text
    const node = svg.append("g")
      .selectAll<SVGGElement, PaperNode>("g")
      .data(nodes)
      .join("g")
      .call(drag(simulation))

    // Add circles
    node.append("circle")
      .attr("r", 25)
      .attr("fill", (d: any) => {
        if (d.hasOSDR) return "#10b981"
        if (d.hasDOI) return "#3b82f6"
        return "#6b7280"
      })
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")

    // Add paper titles as text labels
    node.append("text")
      .text((d: any) => {
        const title = d.title || 'Untitled'
        return title.length > 30 ? title.substring(0, 30) + '...' : title
      })
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .style("font-size", "10px")
      .style("font-weight", "600")
      .style("fill", "#ffffff")
      .style("pointer-events", "none")
      .style("text-shadow", "0 1px 2px rgba(0, 0, 0, 0.8)")

    // Add year labels
    node.append("text")
      .text((d: any) => d.year)
      .attr("text-anchor", "middle")
      .attr("dy", "1.5em")
      .style("font-size", "8px")
      .style("fill", "#d1d5db")
      .style("pointer-events", "none")

    // Simple tooltips
    node.append("title")
      .text((d: any) => `${d.title}\nYear: ${d.year}\nAuthors: ${d.authors}`)

    // Enhanced zoom with pan
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        // Apply zoom to all elements
        svg.selectAll("g").attr("transform", event.transform)
      })

    svg.call(zoom)

    // Add keyboard zoom shortcuts
    handleKeyDown = (event: KeyboardEvent) => {
      const svgNode = svg.node()
      if (!svgNode) return
      const currentTransform = d3.zoomTransform(svgNode)
      let newScale = currentTransform.k
      
      if (event.key === '+' || event.key === '=') {
        newScale = Math.min(currentTransform.k * 1.2, 4)
      } else if (event.key === '-') {
        newScale = Math.max(currentTransform.k / 1.2, 0.1)
      } else if (event.key === '0') {
        newScale = 1
      }
      
      if (newScale !== currentTransform.k) {
        svg.transition()
          .duration(300)
          .call(zoom.transform, d3.zoomIdentity.scale(newScale).translate(currentTransform.x, currentTransform.y))
      }
    }

    // Add keyboard event listener
    document.addEventListener('keydown', handleKeyDown)

    // Add legend
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${width - 200}, 20)`)

    // Legend background
    legend.append("rect")
      .attr("width", 180)
      .attr("height", 100)
      .attr("fill", "rgba(31, 41, 55, 0.9)")
      .attr("stroke", "#4b5563")
      .attr("rx", 6)

    // Legend title
    legend.append("text")
      .attr("x", 90)
      .attr("y", 20)
      .attr("text-anchor", "middle")
      .style("fill", "#e5e7eb")
      .style("font-size", "14px")
      .style("font-weight", "600")
      .text("Paper Types")

    // Legend items
    const legendItems = [
      { label: "OSDR Available", color: "#10b981", y: 40 },
      { label: "DOI Available", color: "#3b82f6", y: 60 },
      { label: "No Special Access", color: "#6b7280", y: 80 }
    ]

    legendItems.forEach((item) => {
      legend.append("circle")
        .attr("cx", 20)
        .attr("cy", item.y)
        .attr("r", 8)
        .attr("fill", item.color)
      
      legend.append("text")
        .attr("x", 35)
        .attr("y", item.y + 3)
        .style("fill", "#e5e7eb")
        .style("font-size", "11px")
        .text(item.label)
    })

    // Event handlers
    node
      .on("mouseover", (event, d: any) => {
        setHoveredNode(d)
        d3.select(event.currentTarget)
          .select("circle")
          .transition()
          .duration(100)
          .attr("r", 30)
      })
      .on("mouseout", (event, d: any) => {
        setHoveredNode(null)
        d3.select(event.currentTarget)
          .select("circle")
          .transition()
          .duration(100)
          .attr("r", 25)
      })

    // Update positions
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)
      
      node
        .attr("transform", (d: any) => `translate(${d.x},${d.y})`)
    })

    // Simple drag
    function drag(simulation: any) {
      function dragstarted(event: any, d: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      }

      function dragged(event: any, d: any) {
        d.fx = event.x
        d.fy = event.y
      }

      function dragended(event: any, d: any) {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      }

      return d3.drag<SVGGElement, PaperNode, unknown>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
    }

    }, 100) // 100ms delay

    return () => {
      clearTimeout(timer)
      if (handleKeyDown) {
        document.removeEventListener('keydown', handleKeyDown)
      }
    }
  }, [papers, searchQuery])

  return (
    <div className="w-full h-screen" style={{ height: '100vh' }}>
      <svg ref={svgRef} className="w-full h-full" style={{ width: '100%', height: '100vh' }} />
          </div>
  )
}