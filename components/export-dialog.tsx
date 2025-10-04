"use client"

import { useState } from "react"
import { Download, FileText, Table, FileJson } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"

interface ExportDialogProps {
  selectedCount: number
  onExport: (format: string, fields: string[]) => void
}

const EXPORT_FORMATS = [
  { id: "csv", label: "CSV", icon: Table, description: "Comma-separated values for spreadsheets" },
  { id: "json", label: "JSON", icon: FileJson, description: "Structured data format" },
  { id: "bibtex", label: "BibTeX", icon: FileText, description: "Citation format for LaTeX" },
  { id: "ris", label: "RIS", icon: FileText, description: "Citation format for reference managers" },
]

const EXPORT_FIELDS = [
  { id: "title", label: "Title", default: true },
  { id: "authors", label: "Authors", default: true },
  { id: "year", label: "Year", default: true },
  { id: "abstract", label: "Abstract", default: true },
  { id: "keywords", label: "Keywords", default: true },
  { id: "doi", label: "DOI", default: true },
  { id: "citations", label: "Citation Count", default: false },
  { id: "methods", label: "Methods", default: false },
  { id: "results", label: "Key Results", default: false },
  { id: "conclusions", label: "Conclusions", default: false },
]

export function ExportDialog({ selectedCount, onExport }: ExportDialogProps) {
  const [format, setFormat] = useState("csv")
  const [selectedFields, setSelectedFields] = useState<string[]>(
    EXPORT_FIELDS.filter((f) => f.default).map((f) => f.id),
  )
  const [open, setOpen] = useState(false)

  const toggleField = (fieldId: string) => {
    setSelectedFields((prev) => (prev.includes(fieldId) ? prev.filter((id) => id !== fieldId) : [...prev, fieldId]))
  }

  const handleExport = () => {
    onExport(format, selectedFields)
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2 bg-transparent transition-all hover:scale-105">
          <Download className="h-4 w-4" />
          Export ({selectedCount})
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Export Papers</DialogTitle>
          <DialogDescription>
            Export {selectedCount} selected {selectedCount === 1 ? "paper" : "papers"} in your preferred format
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-3">
            <Label className="text-base font-semibold">Export Format</Label>
            <RadioGroup value={format} onValueChange={setFormat} className="grid grid-cols-2 gap-3">
              {EXPORT_FORMATS.map((fmt) => (
                <Label
                  key={fmt.id}
                  htmlFor={fmt.id}
                  className="flex items-start gap-3 rounded-lg border border-border p-4 cursor-pointer hover:bg-accent transition-all hover:shadow-sm [&:has(:checked)]:border-primary [&:has(:checked)]:bg-primary/5 [&:has(:checked)]:shadow-sm"
                >
                  <RadioGroupItem value={fmt.id} id={fmt.id} className="mt-0.5" />
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <fmt.icon className="h-4 w-4" />
                      <span className="font-medium">{fmt.label}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{fmt.description}</p>
                  </div>
                </Label>
              ))}
            </RadioGroup>
          </div>

          <div className="space-y-3">
            <Label className="text-base font-semibold">Include Fields</Label>
            <div className="grid grid-cols-2 gap-3">
              {EXPORT_FIELDS.map((field) => (
                <Label
                  key={field.id}
                  htmlFor={field.id}
                  className="flex items-center gap-2 cursor-pointer hover:text-foreground transition-colors"
                >
                  <Checkbox
                    id={field.id}
                    checked={selectedFields.includes(field.id)}
                    onCheckedChange={() => toggleField(field.id)}
                  />
                  <span className="text-sm">{field.label}</span>
                </Label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setOpen(false)} className="transition-colors">
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            disabled={selectedFields.length === 0}
            className="transition-all hover:scale-105"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
