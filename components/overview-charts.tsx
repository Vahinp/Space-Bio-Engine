"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const papersByYear = [
  { year: "2018", count: 45 },
  { year: "2019", count: 52 },
  { year: "2020", count: 48 },
  { year: "2021", count: 67 },
  { year: "2022", count: 89 },
  { year: "2023", count: 103 },
  { year: "2024", count: 78 },
]

export function OverviewCharts() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Papers by Year</CardTitle>
        <CardDescription>Publication trends over time</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{
            count: {
              label: "Papers",
              color: "hsl(var(--chart-1))",
            },
          }}
          className="h-[300px]"
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={papersByYear}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="year" className="text-xs" />
              <YAxis className="text-xs" />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={{ fill: "hsl(var(--chart-1))", r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
