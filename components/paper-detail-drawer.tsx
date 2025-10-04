"use client"

import { X, ExternalLink, Database, FileText, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Paper } from "@/lib/api"

interface PaperDetailDrawerProps {
  paper: Paper | null
  onClose: () => void
  compareMode: boolean
  onCompareModeChange: (enabled: boolean) => void
  comparisonPaper?: Paper | null
  onSendToChat: () => void
}

export function PaperDetailDrawer({
  paper,
  onClose,
  compareMode,
  onCompareModeChange,
  comparisonPaper,
  onSendToChat,
}: PaperDetailDrawerProps) {
  if (!paper) return null

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
      <div className="fixed inset-x-0 bottom-0 z-50 h-[85vh] border-t border-border bg-background shadow-lg animate-in slide-in-from-bottom duration-300">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold">Paper Details</h2>
              <div className="flex items-center gap-2">
                <Switch id="compare-mode" checked={compareMode} onCheckedChange={onCompareModeChange} />
                <Label htmlFor="compare-mode" className="text-sm cursor-pointer">
                  Compare Mode
                </Label>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onSendToChat}
                className="gap-2 bg-transparent transition-all hover:scale-105"
              >
                <MessageSquare className="h-4 w-4" />
                Send to Chat
              </Button>
              <Button variant="ghost" size="icon" onClick={onClose} className="transition-colors hover:bg-accent">
                <X className="h-4 w-4" />
                <span className="sr-only">Close</span>
              </Button>
            </div>
          </div>

          {/* Content */}
          <ScrollArea className="flex-1">
            <div className={compareMode && comparisonPaper ? "grid grid-cols-2 divide-x divide-border" : ""}>
              <PaperContent paper={paper} />
              {compareMode && comparisonPaper && <PaperContent paper={comparisonPaper} />}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}

function PaperContent({ paper }: { paper: Paper }) {
  return (
    <div className="p-6 space-y-6">
      {/* Title and Metadata */}
      <div className="space-y-3">
        <h3 className="text-xl font-semibold leading-tight text-balance">{paper.title}</h3>
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <span>{paper.authors}</span>
          <span>·</span>
          <span>{paper.year}</span>
          <span>·</span>
          <span className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {paper.citations} citations
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{paper.organism}</Badge>
          <Badge variant="outline">{paper.mission}</Badge>
        </div>
      </div>

      {/* Links */}
      <div className="flex flex-wrap gap-2">
        {paper.doi && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2 bg-transparent transition-all hover:scale-105 hover:border-primary/50"
          >
            <ExternalLink className="h-4 w-4" />
            DOI
          </Button>
        )}
        {paper.osdrLink && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2 bg-transparent transition-all hover:scale-105 hover:border-primary/50"
          >
            <Database className="h-4 w-4" />
            OSDR
          </Button>
        )}
        {paper.taskBookLink && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2 bg-transparent transition-all hover:scale-105 hover:border-primary/50"
          >
            <FileText className="h-4 w-4" />
            Task Book
          </Button>
        )}
      </div>

      <Separator />

      {/* Abstract */}
      <div className="space-y-2">
        <h4 className="font-semibold text-sm">Abstract</h4>
        <p className="text-sm text-muted-foreground leading-relaxed">{paper.abstract}</p>
      </div>

      <Separator />

      {/* Key Results */}
      <div className="space-y-2">
        <h4 className="font-semibold text-sm">Key Results</h4>
        <ul className="space-y-2">
          {paper.keyResults.map((result, index) => (
            <li key={index} className="flex gap-2 text-sm text-muted-foreground">
              <span className="text-primary">•</span>
              <span className="leading-relaxed">{result}</span>
            </li>
          ))}
        </ul>
      </div>

      <Separator />

      {/* Methods */}
      <div className="space-y-2">
        <h4 className="font-semibold text-sm">Methods</h4>
        <p className="text-sm text-muted-foreground leading-relaxed">{paper.methods}</p>
      </div>

      <Separator />

      {/* Conclusions */}
      <div className="space-y-2">
        <h4 className="font-semibold text-sm">Conclusions & Implications</h4>
        <p className="text-sm text-muted-foreground leading-relaxed">{paper.conclusions}</p>
      </div>
    </div>
  )
}
