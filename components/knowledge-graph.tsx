"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight } from "lucide-react"

interface GraphNode {
  id: string
  label: string
  type: "organism" | "tissue" | "outcome" | "mission"
  connections: string[]
}

const GRAPH_NODES: GraphNode[] = [
  { id: "human", label: "Human", type: "organism", connections: ["bone", "muscle", "immune"] },
  { id: "mouse", label: "Mouse", type: "organism", connections: ["immune", "neural"] },
  { id: "plant", label: "Plant", type: "organism", connections: ["growth", "morphology"] },
  { id: "bone", label: "Bone", type: "tissue", connections: ["density-loss", "iss"] },
  { id: "muscle", label: "Muscle", type: "tissue", connections: ["atrophy", "iss"] },
  { id: "immune", label: "Immune", type: "tissue", connections: ["dysregulation", "iss"] },
  { id: "neural", label: "Neural", type: "tissue", connections: ["cognitive", "iss"] },
  { id: "growth", label: "Growth", type: "tissue", connections: ["reduced", "analog"] },
  { id: "morphology", label: "Morphology", type: "tissue", connections: ["altered", "analog"] },
  { id: "density-loss", label: "Density Loss", type: "outcome", connections: ["iss"] },
  { id: "atrophy", label: "Atrophy", type: "outcome", connections: ["iss"] },
  { id: "dysregulation", label: "Dysregulation", type: "outcome", connections: ["iss"] },
  { id: "cognitive", label: "Cognitive Change", type: "outcome", connections: ["iss"] },
  { id: "reduced", label: "Reduced Growth", type: "outcome", connections: ["analog"] },
  { id: "altered", label: "Altered Structure", type: "outcome", connections: ["analog"] },
  { id: "iss", label: "ISS", type: "mission", connections: [] },
  { id: "analog", label: "Analog Studies", type: "mission", connections: [] },
]

export function KnowledgeGraph() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const selectedNodeData = selectedNode ? GRAPH_NODES.find((n) => n.id === selectedNode) : null
  const connectedNodes = selectedNodeData ? GRAPH_NODES.filter((n) => selectedNodeData.connections.includes(n.id)) : []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Knowledge Graph</CardTitle>
        <CardDescription>Explore relationships between organisms, tissues, outcomes, and missions</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="text-sm font-medium mb-2 text-muted-foreground">Organisms</h4>
          <div className="flex flex-wrap gap-2">
            {GRAPH_NODES.filter((n) => n.type === "organism").map((node) => (
              <Badge
                key={node.id}
                variant={selectedNode === node.id ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
              >
                {node.label}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-2 text-muted-foreground">Tissues/Systems</h4>
          <div className="flex flex-wrap gap-2">
            {GRAPH_NODES.filter((n) => n.type === "tissue").map((node) => (
              <Badge
                key={node.id}
                variant={selectedNode === node.id ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
              >
                {node.label}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-2 text-muted-foreground">Outcomes</h4>
          <div className="flex flex-wrap gap-2">
            {GRAPH_NODES.filter((n) => n.type === "outcome").map((node) => (
              <Badge
                key={node.id}
                variant={selectedNode === node.id ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
              >
                {node.label}
              </Badge>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-2 text-muted-foreground">Missions</h4>
          <div className="flex flex-wrap gap-2">
            {GRAPH_NODES.filter((n) => n.type === "mission").map((node) => (
              <Badge
                key={node.id}
                variant={selectedNode === node.id ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
              >
                {node.label}
              </Badge>
            ))}
          </div>
        </div>

        {selectedNodeData && connectedNodes.length > 0 && (
          <div className="p-4 rounded-lg bg-muted border">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="default">{selectedNodeData.label}</Badge>
              <ArrowRight className="h-4 w-4" />
              <span className="text-sm font-medium">Connected to:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {connectedNodes.map((node) => (
                <Badge
                  key={node.id}
                  variant="outline"
                  className="cursor-pointer"
                  onClick={() => setSelectedNode(node.id)}
                >
                  {node.label}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
