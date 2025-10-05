"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function TopicClusters() {
  // Mock topic clusters data - in a real implementation, this would come from your backend
  const clusters = [
    {
      id: "microgravity",
      name: "Microgravity Effects",
      papers: 45,
      keywords: ["bone density", "muscle atrophy", "cardiovascular", "fluid shifts"],
      color: "#ef4444"
    },
    {
      id: "radiation",
      name: "Space Radiation",
      papers: 32,
      keywords: ["galactic cosmic rays", "solar particles", "shielding", "dosimetry"],
      color: "#f59e0b"
    },
    {
      id: "immune",
      name: "Immune System",
      papers: 28,
      keywords: ["T-cells", "cytokines", "stress response", "microbiome"],
      color: "#8b5cf6"
    },
    {
      id: "plants",
      name: "Plant Biology",
      papers: 24,
      keywords: ["root orientation", "photosynthesis", "life support", "crop growth"],
      color: "#10b981"
    },
    {
      id: "cellular",
      name: "Cellular Biology",
      papers: 31,
      keywords: ["gene expression", "protein synthesis", "cell division", "apoptosis"],
      color: "#06b6d4"
    }
  ]

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold mb-2">Research Topic Clusters</h3>
        <p className="text-sm text-muted-foreground">
          Papers grouped by research themes and keywords
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clusters.map((cluster) => (
          <Card key={cluster.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{cluster.name}</CardTitle>
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: cluster.color }}
                />
              </div>
              <CardDescription>
                {cluster.papers} papers in this cluster
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground mb-2">Key topics:</div>
                <div className="flex flex-wrap gap-1">
                  {cluster.keywords.map((keyword) => (
                    <Badge 
                      key={keyword} 
                      variant="secondary" 
                      className="text-xs"
                    >
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6 p-4 bg-muted/50 rounded-lg">
        <h4 className="font-semibold mb-2">How clusters are determined:</h4>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• Papers are analyzed for common keywords and themes</li>
          <li>• Machine learning algorithms group similar research</li>
          <li>• Clusters help identify research trends and gaps</li>
          <li>• Each cluster represents a major research direction</li>
        </ul>
      </div>
    </div>
  )
}