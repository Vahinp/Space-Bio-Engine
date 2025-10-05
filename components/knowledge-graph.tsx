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
    
    if (!svgRef.current || !papers || papers.length === 0) {
      console.log('KnowledgeGraph - no papers or svg ref')
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

    const container = svgRef.current.parentElement
    const width = container?.clientWidth || 800
    const height = container?.clientHeight || 600

    // Simple dark background
    svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .attr("fill", "#1f2937")

    // Create simple simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))

    // Create simple links
    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .style("stroke", "#6b7280")
      .style("stroke-width", 1)
      .style("stroke-opacity", 0.5)

    // Create simple nodes
    const node = svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", 20)
      .attr("fill", (d: any) => {
        if (d.hasOSDR) return "#10b981"
        if (d.hasDOI) return "#3b82f6"
        return "#6b7280"
      })
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")
      .call(drag(simulation))

    // Simple tooltips
    node.append("title")
      .text((d: any) => `${d.title}\nYear: ${d.year}`)

    // Simple zoom
    const zoom = d3.zoom()
      .scaleExtent([0.5, 2])
      .on("zoom", (event) => {
        svg.selectAll("g").attr("transform", event.transform)
      })

    svg.call(zoom)

    // Event handlers
    node
      .on("mouseover", (event, d: any) => {
        setHoveredNode(d)
        d3.select(event.currentTarget)
          .transition()
          .duration(100)
          .attr("r", 25)
      })
      .on("mouseout", (event, d: any) => {
        setHoveredNode(null)
        d3.select(event.currentTarget)
          .transition()
          .duration(100)
          .attr("r", 20)
      })

    // Update positions
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)
      
      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y)
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

      return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
    }

  }, [papers, searchQuery])

  return (
    <div className="w-full h-screen">
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  )
}