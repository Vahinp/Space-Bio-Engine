"use client"

import { Bookmark, Trash2, Share2, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ExportDialog } from "@/components/export-dialog"

interface BulkActionsBarProps {
  selectedCount: number
  onClearSelection: () => void
  onBookmark: () => void
  onDelete: () => void
  onShare: () => void
  onSendToChat: () => void
  onExport: (format: string, fields: string[]) => void
}

export function BulkActionsBar({
  selectedCount,
  onClearSelection,
  onBookmark,
  onDelete,
  onShare,
  onSendToChat,
  onExport,
}: BulkActionsBarProps) {
  if (selectedCount === 0) return null

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-5 duration-300">
      <div className="bg-background border border-border rounded-full shadow-lg px-4 py-3 flex items-center gap-2">
        <span className="text-sm font-medium px-2">
          {selectedCount} {selectedCount === 1 ? "paper" : "papers"} selected
        </span>
        <div className="h-6 w-px bg-border" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onBookmark}
          className="gap-2 rounded-full transition-all hover:scale-105 hover:bg-accent"
        >
          <Bookmark className="h-4 w-4" />
          Bookmark
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onSendToChat}
          className="gap-2 rounded-full transition-all hover:scale-105 hover:bg-accent"
        >
          <MessageSquare className="h-4 w-4" />
          Send to Chat
        </Button>
        <ExportDialog selectedCount={selectedCount} onExport={onExport} />
        <Button
          variant="ghost"
          size="sm"
          onClick={onShare}
          className="gap-2 rounded-full transition-all hover:scale-105 hover:bg-accent"
        >
          <Share2 className="h-4 w-4" />
          Share
        </Button>
        <div className="h-6 w-px bg-border" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onDelete}
          className="gap-2 rounded-full text-destructive transition-all hover:scale-105 hover:bg-destructive/10"
        >
          <Trash2 className="h-4 w-4" />
          Remove
        </Button>
        <div className="h-6 w-px bg-border" />
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          className="rounded-full transition-colors hover:bg-accent"
        >
          Clear
        </Button>
      </div>
    </div>
  )
}
