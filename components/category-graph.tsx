"use client"

import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"

interface CategoryNode {
  id: string
  name: string
  count: number
  papers: any[]
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface CategoryLink {
  source: string
  target: string
  weight: number
  sourceNode?: CategoryNode
  targetNode?: CategoryNode
}

interface CategoryGraphProps {
  papers: any[]
  category: string
  className?: string
}

export function CategoryGraph({ papers, category, className }: CategoryGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [hoveredNode, setHoveredNode] = useState<CategoryNode | null>(null)

  // Extract category information from text when field is null
  const extractCategoryFromText = (paper: any, categoryKey: string): string => {
    const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase()
    
    console.log(`Extracting ${categoryKey} from text:`, text.substring(0, 100) + '...')
    
    switch (categoryKey) {
      case 'organism':
        if (text.includes('human') || text.includes('homo sapiens')) return 'Human'
        if (text.includes('mouse') || text.includes('mus musculus')) return 'Mouse'
        if (text.includes('rat') || text.includes('rattus')) return 'Rat'
        if (text.includes('plant') || text.includes('arabidopsis')) return 'Plant'
        if (text.includes('microbe') || text.includes('bacteria')) return 'Microbe'
        if (text.includes('drosophila') || text.includes('fruit fly')) return 'Drosophila'
        if (text.includes('c. elegans') || text.includes('caenorhabditis')) return 'C. elegans'
        return 'Unknown'
        
      case 'mission':
        if (text.includes('iss') || text.includes('international space station') || text.includes('expedition')) {
          console.log('Found ISS mission')
          return 'ISS'
        }
        if (text.includes('space shuttle') || text.includes('sts-') || text.includes('shuttle')) {
          console.log('Found Space Shuttle mission')
          return 'Space Shuttle'
        }
        if (text.includes('artemis') || text.includes('lunar') || text.includes('moon')) {
          console.log('Found Artemis mission')
          return 'Artemis'
        }
        if (text.includes('parabolic flight') || text.includes('parabola') || text.includes('zero-g')) {
          console.log('Found Parabolic Flight mission')
          return 'Parabolic Flight'
        }
        if (text.includes('analog') || text.includes('bed rest') || text.includes('simulation') || text.includes('ground-based')) {
          console.log('Found Analog Studies mission')
          return 'Analog Studies'
        }
        if (text.includes('mars') || text.includes('planetary')) {
          console.log('Found Mars Mission')
          return 'Mars Mission'
        }
        if (text.includes('satellite') || text.includes('orbital')) {
          console.log('Found Satellite mission')
          return 'Satellite'
        }
        console.log('No mission found, returning Unknown Mission')
        return 'Unknown Mission'
        
      case 'environment':
        if (text.includes('microgravity') || text.includes('zero gravity') || text.includes('weightlessness') || text.includes('0g')) {
          console.log('Found Microgravity environment')
          return 'Microgravity'
        }
        if (text.includes('radiation') || text.includes('cosmic') || text.includes('solar') || text.includes('gamma')) {
          console.log('Found Radiation environment')
          return 'Radiation'
        }
        if (text.includes('hypergravity') || text.includes('centrifuge') || text.includes('high-g')) {
          console.log('Found Hypergravity environment')
          return 'Hypergravity'
        }
        if (text.includes('isolation') || text.includes('confinement') || text.includes('closed') || text.includes('habitat')) {
          console.log('Found Isolation environment')
          return 'Isolation'
        }
        if (text.includes('vacuum') || text.includes('space vacuum')) {
          console.log('Found Vacuum environment')
          return 'Vacuum'
        }
        if (text.includes('temperature') || text.includes('thermal') || text.includes('cold') || text.includes('heat')) {
          console.log('Found Temperature environment')
          return 'Temperature'
        }
        if (text.includes('pressure') || text.includes('atmospheric') || text.includes('hypobaric')) {
          console.log('Found Pressure environment')
          return 'Pressure'
        }
        console.log('No environment found, returning Space Environment')
        return 'Space Environment'
        
      case 'tissue':
        if (text.includes('bone') || text.includes('skeletal') || text.includes('osteoporosis') || text.includes('calcium')) return 'Bone'
        if (text.includes('muscle') || text.includes('muscular') || text.includes('atrophy') || text.includes('myofiber')) return 'Muscle'
        if (text.includes('cardiovascular') || text.includes('heart') || text.includes('cardiac') || text.includes('vascular')) return 'Cardiovascular'
        if (text.includes('immune') || text.includes('immunity') || text.includes('lymphocyte') || text.includes('antibody')) return 'Immune'
        if (text.includes('neural') || text.includes('brain') || text.includes('neuron') || text.includes('cognitive')) return 'Neural'
        if (text.includes('skin') || text.includes('dermal') || text.includes('epidermal')) return 'Skin'
        if (text.includes('liver') || text.includes('hepatic')) return 'Liver'
        if (text.includes('kidney') || text.includes('renal')) return 'Kidney'
        return 'Unknown Tissue'
        
      case 'assay':
        if (text.includes('rna-seq') || text.includes('transcriptome') || text.includes('gene expression') || text.includes('mrna')) return 'RNA-seq'
        if (text.includes('proteomics') || text.includes('protein') || text.includes('proteome') || text.includes('mass spectrometry')) return 'Proteomics'
        if (text.includes('metabolomics') || text.includes('metabolite') || text.includes('metabolism') || text.includes('metabolic')) return 'Metabolomics'
        if (text.includes('imaging') || text.includes('microscopy') || text.includes('microscope') || text.includes('fluorescence')) return 'Imaging'
        if (text.includes('behavioral') || text.includes('behavior') || text.includes('performance') || text.includes('cognitive')) return 'Behavioral'
        if (text.includes('pcr') || text.includes('polymerase')) return 'PCR'
        if (text.includes('western') || text.includes('blot')) return 'Western Blot'
        return 'Unknown Assay'
        
      case 'outcome':
        if (text.includes('up-regulated') || text.includes('upregulated') || text.includes('increased') || text.includes('enhanced') || text.includes('elevated')) return 'Up-regulated'
        if (text.includes('down-regulated') || text.includes('downregulated') || text.includes('decreased') || text.includes('reduced') || text.includes('suppressed')) return 'Down-regulated'
        if (text.includes('morphology') || text.includes('morphological') || text.includes('structure') || text.includes('shape')) return 'Morphology Change'
        if (text.includes('behavioral') || text.includes('behavior') || text.includes('performance') || text.includes('function')) return 'Behavioral Change'
        if (text.includes('atrophy') || text.includes('wasting') || text.includes('loss')) return 'Atrophy'
        if (text.includes('hypertrophy') || text.includes('growth') || text.includes('increase')) return 'Hypertrophy'
        return 'Unknown Outcome'
        
      default:
        return 'Unknown'
    }
  }

  // Calculate similarity between two category groups based on content
  const calculateCategorySimilarity = (papers1: any[], papers2: any[], categoryKey: string): number => {
    if (categoryKey === 'organism') {
      // For organisms, check if papers mention multiple organisms
      let sharedPapers = 0
      papers1.forEach(paper1 => {
        const text1 = `${paper1.title || ''} ${paper1.abstract || ''}`.toLowerCase()
        papers2.forEach(paper2 => {
          const text2 = `${paper2.title || ''} ${paper2.abstract || ''}`.toLowerCase()
          // Check if papers share common research themes
          const commonThemes = ['microgravity', 'space', 'radiation', 'bone', 'muscle', 'immune', 'cardiovascular', 'neural']
          const sharedThemes = commonThemes.filter(theme => text1.includes(theme) && text2.includes(theme))
          if (sharedThemes.length > 0) {
            sharedPapers += 1
          }
        })
      })
      return Math.min(sharedPapers / (papers1.length * papers2.length), 0.5)
    }
    
    // For other categories, use keyword similarity
    const keywords1 = new Set<string>()
    const keywords2 = new Set<string>()
    
    papers1.forEach(paper => {
      const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase()
      const words = text.split(/\s+/).filter(word => 
        word.length > 4 && 
        !['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'].includes(word)
      )
      words.forEach(word => keywords1.add(word))
    })
    
    papers2.forEach(paper => {
      const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase()
      const words = text.split(/\s+/).filter(word => 
        word.length > 4 && 
        !['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use', 'this', 'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'].includes(word)
      )
      words.forEach(word => keywords2.add(word))
    })
    
    // Calculate Jaccard similarity
    const intersection = new Set([...keywords1].filter(x => keywords2.has(x)))
    const union = new Set([...keywords1, ...keywords2])
    
    return intersection.size / union.size
  }

  // Calculate research theme overlap between two node groups
  const calculateActualOverlap = (papers1: any[], papers2: any[]): number => {
    // Extract research themes from both groups
    const themes1 = new Set<string>()
    const themes2 = new Set<string>()
    
    // Common research themes in space biology
    const researchThemes = [
      'microgravity', 'space', 'radiation', 'bone', 'muscle', 'immune', 'cardiovascular', 
      'neural', 'metabolism', 'stress', 'aging', 'regeneration', 'adaptation', 'physiology',
      'gene', 'protein', 'cell', 'tissue', 'organ', 'system', 'function', 'structure',
      'development', 'growth', 'repair', 'injury', 'disease', 'health', 'medicine'
    ]
    
    papers1.forEach(paper => {
      const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase()
      researchThemes.forEach(theme => {
        if (text.includes(theme)) {
          themes1.add(theme)
        }
      })
    })
    
    papers2.forEach(paper => {
      const text = `${paper.title || ''} ${paper.abstract || ''}`.toLowerCase()
      researchThemes.forEach(theme => {
        if (text.includes(theme)) {
          themes2.add(theme)
        }
      })
    })
    
    // Calculate Jaccard similarity of research themes
    const intersection = new Set([...themes1].filter(theme => themes2.has(theme)))
    const union = new Set([...themes1, ...themes2])
    
    // Return the number of shared themes (scaled for display)
    return Math.round(intersection.size * 2) // Scale up for better visibility
  }

  // Process papers into category nodes and links
  const processCategoryData = (papers: any[], categoryKey: string) => {
    if (!papers || papers.length === 0) return { nodes: [], links: [] }

    // Group papers by category value
    const categoryGroups: { [key: string]: any[] } = {}
    
    console.log(`Processing ${categoryKey} category with ${papers.length} papers`)
    
    papers.forEach((paper, index) => {
      let value = paper[categoryKey]
      
      // Always try to extract from text for better categorization
      const extractedValue = extractCategoryFromText(paper, categoryKey)
      console.log(`Paper ${index}: Original=${value}, Extracted=${extractedValue}`)
      value = extractedValue
      
      if (!categoryGroups[value]) {
        categoryGroups[value] = []
      }
      categoryGroups[value].push(paper)
    })
    
    console.log(`Category groups for ${categoryKey}:`, Object.keys(categoryGroups).map(key => `${key}: ${categoryGroups[key].length}`))

    // Create nodes for each category value
    const nodes: CategoryNode[] = Object.entries(categoryGroups).map(([name, paperList]) => ({
      id: name.toLowerCase().replace(/\s+/g, '-'),
      name: name,
      count: paperList.length,
      papers: paperList
    }))

    // Create links between categories based on content similarity
    const links: CategoryLink[] = []
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        // Calculate similarity based on shared keywords in abstracts/titles
        const similarity = calculateCategorySimilarity(nodes[i].papers, nodes[j].papers, categoryKey)
        
        if (similarity > 0.1) { // Only create links if similarity > 10%
          links.push({
            source: nodes[i].id,
            target: nodes[j].id,
            weight: similarity,
            sourceNode: nodes[i],
            targetNode: nodes[j]
          })
        }
      }
    }

    return { nodes, links }
  }

  useEffect(() => {
    console.log('CategoryGraph - papers received:', papers?.length, 'category:', category)
    
    if (!papers || papers.length === 0) {
      console.log('CategoryGraph - no papers')
      return
    }

    let handleKeyDown: ((event: KeyboardEvent) => void) | null = null

    const timer = setTimeout(() => {
      if (!svgRef.current) {
        console.log('CategoryGraph - no svg ref after delay')
        return
      }

      const svg = d3.select(svgRef.current)
      svg.selectAll("*").remove()

      const { nodes, links } = processCategoryData(papers, category)
      console.log('CategoryGraph - processed nodes:', nodes.length, 'links:', links.length)
      
      if (nodes.length === 0) {
        console.log('CategoryGraph - no nodes to render')
        return
      }

      const svgElement = svgRef.current
      const width = svgElement.clientWidth || window.innerWidth
      const height = svgElement.clientHeight || window.innerHeight
      
      console.log('CategoryGraph - dimensions:', width, height)

      // Dark background
      svg.append("rect")
        .attr("width", width)
        .attr("height", height)
        .attr("fill", "#1f2937")

      // Create simulation
      const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id((d: any) => d.id).distance(150))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(60))

      // Create links with hover tooltips
      const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .join("line")
        .style("stroke", "#6b7280")
        .style("stroke-width", (d: any) => Math.max(1, d.weight * 5))
        .style("stroke-opacity", 0.6)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d: any) {
          // Use the node data directly from the link
          const sourceNode = d.sourceNode
          const targetNode = d.targetNode
          
          // Calculate actual overlap
          const overlap = calculateActualOverlap(sourceNode?.papers || [], targetNode?.papers || [])
          
          // Create tooltip
          const tooltip = svg.append("g")
            .attr("class", "edge-tooltip")
            .style("pointer-events", "none")
          
          const [mouseX, mouseY] = d3.pointer(event, svg.node())
          
          tooltip.append("rect")
            .attr("x", mouseX - 60)
            .attr("y", mouseY - 30)
            .attr("width", 120)
            .attr("height", 50)
            .attr("fill", "rgba(0, 0, 0, 0.8)")
            .attr("stroke", "#ffffff")
            .attr("rx", 5)
          
          tooltip.append("text")
            .attr("x", mouseX)
            .attr("y", mouseY - 15)
            .attr("text-anchor", "middle")
            .style("fill", "#ffffff")
            .style("font-size", "12px")
            .style("font-weight", "600")
            .text(`${sourceNode?.name || 'Unknown'} ↔ ${targetNode?.name || 'Unknown'}`)
          
          tooltip.append("text")
            .attr("x", mouseX)
            .attr("y", mouseY + 5)
            .attr("text-anchor", "middle")
            .style("fill", "#ffffff")
            .style("font-size", "10px")
            .text(`${overlap} shared research themes`)
        })
        .on("mouseout", function() {
          svg.selectAll(".edge-tooltip").remove()
        })

      // Create node groups
      const node = svg.append("g")
        .selectAll<SVGGElement, CategoryNode>("g")
        .data(nodes)
        .join("g")
        .call(drag(simulation))

      // Add circles with size proportional to paper count
      const maxCount = Math.max(...nodes.map(n => n.count))
      const minRadius = 15
      const maxRadius = 80
      
      node.append("circle")
        .attr("r", (d: any) => {
          const ratio = d.count / maxCount
          return minRadius + (maxRadius - minRadius) * ratio
        })
        .attr("fill", (d: any, i: number) => {
          const colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
          return colors[i % colors.length]
        })
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 3)
        .style("cursor", "pointer")

      // Add category names
      node.append("text")
        .text((d: any) => d.name)
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .style("font-size", "14px")
        .style("font-weight", "600")
        .style("fill", "#ffffff")
        .style("pointer-events", "none")
        .style("text-shadow", "0 1px 2px rgba(0, 0, 0, 0.8)")

      // Add count labels
      node.append("text")
        .text((d: any) => `${d.count} papers`)
        .attr("text-anchor", "middle")
        .attr("dy", "1.5em")
        .style("font-size", "10px")
        .style("fill", "#d1d5db")
        .style("pointer-events", "none")

      // Add tooltips
      node.append("title")
        .text((d: any) => `${d.name}\n${d.count} papers`)

      // Zoom functionality
      const zoom = d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => {
          svg.selectAll("g").attr("transform", event.transform)
        })

      svg.call(zoom)

      // Keyboard zoom shortcuts
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

      document.addEventListener('keydown', handleKeyDown)

      // Add legend
      const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width - 200}, 20)`)

      legend.append("rect")
        .attr("width", 180)
        .attr("height", 80)
        .attr("fill", "rgba(31, 41, 55, 0.9)")
        .attr("stroke", "#4b5563")
        .attr("rx", 6)

      legend.append("text")
        .attr("x", 90)
        .attr("y", 20)
        .attr("text-anchor", "middle")
        .style("fill", "#e5e7eb")
        .style("font-size", "14px")
        .style("font-weight", "600")
        .text(`${category.charAt(0).toUpperCase() + category.slice(1)} Categories`)

      legend.append("text")
        .attr("x", 15)
        .attr("y", 40)
        .style("fill", "#e5e7eb")
        .style("font-size", "11px")
        .text("Node size ∝ Paper count")

      legend.append("text")
        .attr("x", 15)
        .attr("y", 55)
        .style("fill", "#e5e7eb")
        .style("font-size", "11px")
        .text("Hover edges for overlap info")

      // Event handlers
      node
        .on("mouseover", (event, d: any) => {
          setHoveredNode(d)
          const currentRadius = d3.select(event.currentTarget).select("circle").attr("r")
          d3.select(event.currentTarget)
            .select("circle")
            .transition()
            .duration(100)
            .attr("r", parseFloat(currentRadius) + 10)
        })
        .on("mouseout", (event, d: any) => {
          setHoveredNode(null)
          const ratio = d.count / maxCount
          const originalRadius = minRadius + (maxRadius - minRadius) * ratio
          d3.select(event.currentTarget)
            .select("circle")
            .transition()
            .duration(100)
            .attr("r", originalRadius)
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

      // Drag function
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

        return d3.drag<SVGGElement, CategoryNode, unknown>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      }

    }, 100)

    return () => {
      clearTimeout(timer)
      if (handleKeyDown) {
        document.removeEventListener('keydown', handleKeyDown)
      }
    }
  }, [papers, category])

  return (
    <div className="w-full h-screen" style={{ height: '100vh' }}>
      <svg ref={svgRef} className="w-full h-full" style={{ width: '100%', height: '100vh' }} />
    </div>
  )
}
