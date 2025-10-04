"use client"

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const TOPICS = [
  { id: "1", name: "Bone & Muscle Loss", count: 89 },
  { id: "2", name: "Immune System Changes", count: 67 },
  { id: "3", name: "Plant Growth & Development", count: 54 },
  { id: "4", name: "Radiation Effects", count: 78 },
  { id: "5", name: "Microbial Behavior", count: 45 },
  { id: "6", name: "Cardiovascular Adaptation", count: 56 },
  { id: "7", name: "Neural & Cognitive", count: 34 },
  { id: "8", name: "Gene Expression", count: 92 },
  { id: "9", name: "Tissue Morphology", count: 41 },
  { id: "10", name: "Behavioral Changes", count: 28 },
]

export function TopicClusters() {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Research Topic Clusters</CardTitle>
        <CardDescription>Click a topic to filter results by that cluster</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {TOPICS.map((topic) => (
            <Badge
              key={topic.id}
              variant={selectedTopic === topic.id ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setSelectedTopic(selectedTopic === topic.id ? null : topic.id)}
            >
              {topic.name}
              <span className="ml-1.5 opacity-70">({topic.count})</span>
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
