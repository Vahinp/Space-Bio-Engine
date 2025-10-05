"use client"

import { BarChart3, Tags } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { OverviewCharts } from "@/components/overview-charts"
import { TopicClusters } from "@/components/topic-clusters"

interface InsightsTabsProps {
}

export function InsightsTabs({}: InsightsTabsProps) {
  return (
    <div className="border-b border-border bg-muted/30">
      <Tabs defaultValue="overview" className="w-full">
        <div className="px-6">
          <TabsList className="h-10 bg-transparent border-b-0">
            <TabsTrigger
              value="overview"
              className="gap-2 transition-all duration-200 hover:scale-105 hover:bg-accent/50 active:scale-95 data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-sm"
            >
              <BarChart3 className="h-4 w-4 transition-transform duration-200 group-hover:rotate-12" />
              Overview
            </TabsTrigger>
            <TabsTrigger
              value="topics"
              className="gap-2 transition-all duration-200 hover:scale-105 hover:bg-accent/50 active:scale-95 data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-sm"
            >
              <Tags className="h-4 w-4 transition-transform duration-200 group-hover:rotate-12" />
              Topics
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview" className="m-0 p-6 pt-4">
          <OverviewCharts />
        </TabsContent>

        <TabsContent value="topics" className="m-0 p-6 pt-4">
          <TopicClusters />
        </TabsContent>
      </Tabs>
    </div>
  )
}
