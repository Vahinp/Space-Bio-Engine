"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { ChevronDown, ChevronRight, RotateCcw, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { ScrollArea } from "@/components/ui/scroll-area"

interface FilterPanelProps {
  filters: {
    yearRange: [number, number]
    organisms: string[]
    missions: string[]
    environments: string[]
    tissues: string[]
    assays: string[]
    outcomes: string[]
    hasOSDR: boolean
  }
  onFiltersChange: (filters: any) => void
  onSearchWithFilters?: (filters: any) => void
}

const ORGANISMS = ["Human", "Mouse", "Plant", "Microbe", "Rat", "C. elegans", "Drosophila", "Unknown"]
const MISSIONS = ["ISS", "Space Shuttle", "Artemis", "Analog Studies", "Parabolic Flight", "Unknown Mission"]
const ENVIRONMENTS = ["Microgravity", "Radiation", "Hypergravity", "Isolation", "Confinement", "Space Environment"]
const TISSUES = ["Bone", "Muscle", "Cardiovascular", "Immune", "Neural", "Skin"]
const ASSAYS = ["RNA-seq", "Proteomics", "Metabolomics", "Imaging", "Behavioral"]
const OUTCOMES = ["Up-regulated", "Down-regulated", "Morphology Change", "Behavioral Change"]

export function FilterPanel({ filters, onFiltersChange, onSearchWithFilters }: FilterPanelProps) {
  const [expandedSections, setExpandedSections] = useState({
    year: true,
    organism: true,
    mission: true,
    environment: true,
    tissue: false,
    assay: false,
    outcome: false,
    data: false,
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const toggleArrayFilter = (key: keyof typeof filters, value: string) => {
    const current = filters[key] as string[]
    const updated = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
    onFiltersChange({ ...filters, [key]: updated })
  }

  const resetFilters = () => {
    onFiltersChange({
      yearRange: [2000, 2024],
      organisms: [],
      missions: [],
      environments: [],
      tissues: [],
      assays: [],
      outcomes: [],
      hasOSDR: false,
    })
  }

  // Remove automatic search trigger - let parent handle when to search

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Filters</h3>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 transition-colors hover:bg-accent"
                  onClick={resetFilters}
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                  <span className="sr-only">Reset filters</span>
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7 transition-colors hover:bg-accent">
                  <Save className="h-3.5 w-3.5" />
                  <span className="sr-only">Save filter set</span>
                </Button>
              </div>
            </div>


        {/* Year Range */}
        <FilterSection title="Year Range" expanded={expandedSections.year} onToggle={() => toggleSection("year")}>
          <div className="space-y-3">
            <Slider
              value={filters.yearRange}
              onValueChange={(value) => onFiltersChange({ ...filters, yearRange: value as [number, number] })}
              min={1990}
              max={2024}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{filters.yearRange[0]}</span>
              <span>{filters.yearRange[1]}</span>
            </div>
          </div>
        </FilterSection>

        {/* Organism */}
        <FilterSection
          title="Organism"
          expanded={expandedSections.organism}
          onToggle={() => toggleSection("organism")}
          count={filters.organisms.length}
        >
          <div className="space-y-2">
            {ORGANISMS.map((organism) => (
              <div
                key={organism}
                className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
                  filters.organisms.includes(organism) ? "bg-primary/10 hover:bg-primary/15" : ""
                }`}
                onClick={() => toggleArrayFilter("organisms", organism)}
              >
                <Checkbox
                  id={`organism-${organism}`}
                  checked={filters.organisms.includes(organism)}
                  className="transition-all duration-200 data-[state=checked]:scale-110"
                />
                <Label
                  htmlFor={`organism-${organism}`}
                  className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                    filters.organisms.includes(organism) ? "font-medium text-primary" : "group-hover:text-foreground"
                  }`}
                >
                  {organism}
                </Label>
              </div>
            ))}
          </div>
        </FilterSection>

        {/* Mission/Platform */}
        <FilterSection
          title="Mission/Platform"
          expanded={expandedSections.mission}
          onToggle={() => toggleSection("mission")}
          count={filters.missions.length}
        >
          <div className="space-y-2">
            {MISSIONS.map((mission) => (
              <div
                key={mission}
                className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
                  filters.missions.includes(mission) ? "bg-primary/10 hover:bg-primary/15" : ""
                }`}
                onClick={() => toggleArrayFilter("missions", mission)}
              >
                <Checkbox
                  id={`mission-${mission}`}
                  checked={filters.missions.includes(mission)}
                  className="transition-all duration-200 data-[state=checked]:scale-110"
                />
                <Label
                  htmlFor={`mission-${mission}`}
                  className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                    filters.missions.includes(mission) ? "font-medium text-primary" : "group-hover:text-foreground"
                  }`}
                >
                  {mission}
                </Label>
              </div>
            ))}
          </div>
        </FilterSection>

        {/* Environment */}
        <FilterSection
          title="Environment"
          expanded={expandedSections.environment}
          onToggle={() => toggleSection("environment")}
          count={filters.environments.length}
        >
          <div className="space-y-2">
            {ENVIRONMENTS.map((env) => (
              <div
                key={env}
                className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
                  filters.environments.includes(env) ? "bg-primary/10 hover:bg-primary/15" : ""
                }`}
                onClick={() => toggleArrayFilter("environments", env)}
              >
                <Checkbox
                  id={`env-${env}`}
                  checked={filters.environments.includes(env)}
                  className="transition-all duration-200 data-[state=checked]:scale-110"
                />
                <Label
                  htmlFor={`env-${env}`}
                  className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                    filters.environments.includes(env) ? "font-medium text-primary" : "group-hover:text-foreground"
                  }`}
                >
                  {env}
                </Label>
              </div>
            ))}
          </div>
        </FilterSection>

        {/* Tissue/System */}
        <FilterSection
          title="Tissue/System"
          expanded={expandedSections.tissue}
          onToggle={() => toggleSection("tissue")}
          count={filters.tissues.length}
        >
          <div className="space-y-2">
            {TISSUES.map((tissue) => (
              <div
                key={tissue}
                className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
                  filters.tissues.includes(tissue) ? "bg-primary/10 hover:bg-primary/15" : ""
                }`}
                onClick={() => toggleArrayFilter("tissues", tissue)}
              >
                <Checkbox
                  id={`tissue-${tissue}`}
                  checked={filters.tissues.includes(tissue)}
                  className="transition-all duration-200 data-[state=checked]:scale-110"
                />
                <Label
                  htmlFor={`tissue-${tissue}`}
                  className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                    filters.tissues.includes(tissue) ? "font-medium text-primary" : "group-hover:text-foreground"
                  }`}
                >
                  {tissue}
                </Label>
              </div>
            ))}
          </div>
        </FilterSection>

        {/* Assay/Omics */}
        <FilterSection
          title="Assay/Omics"
          expanded={expandedSections.assay}
          onToggle={() => toggleSection("assay")}
          count={filters.assays.length}
        >
          <div className="space-y-2">
            {ASSAYS.map((assay) => (
              <div
                key={assay}
                className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
                  filters.assays.includes(assay) ? "bg-primary/10 hover:bg-primary/15" : ""
                }`}
                onClick={() => toggleArrayFilter("assays", assay)}
              >
                <Checkbox
                  id={`assay-${assay}`}
                  checked={filters.assays.includes(assay)}
                  className="transition-all duration-200 data-[state=checked]:scale-110"
                />
                <Label
                  htmlFor={`assay-${assay}`}
                  className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                    filters.assays.includes(assay) ? "font-medium text-primary" : "group-hover:text-foreground"
                  }`}
                >
                  {assay}
                </Label>
              </div>
            ))}
          </div>
        </FilterSection>

        {/* Outcome */}
        <FilterSection
          title="Outcome"
          expanded={expandedSections.outcome}
          onToggle={() => toggleSection("outcome")}
          count={filters.outcomes.length}
        >
          <div className="space-y-2">
            {OUTCOMES.map((outcome) => (
              <div
                key={outcome}
                className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
                  filters.outcomes.includes(outcome) ? "bg-primary/10 hover:bg-primary/15" : ""
                }`}
                onClick={() => toggleArrayFilter("outcomes", outcome)}
              >
                <Checkbox
                  id={`outcome-${outcome}`}
                  checked={filters.outcomes.includes(outcome)}
                  className="transition-all duration-200 data-[state=checked]:scale-110"
                />
                <Label
                  htmlFor={`outcome-${outcome}`}
                  className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                    filters.outcomes.includes(outcome) ? "font-medium text-primary" : "group-hover:text-foreground"
                  }`}
                >
                  {outcome}
                </Label>
              </div>
            ))}
          </div>
        </FilterSection>

        {/* Data Availability */}
        <FilterSection
          title="Data Availability"
          expanded={expandedSections.data}
          onToggle={() => toggleSection("data")}
        >
          <div
            className={`flex items-center space-x-2 p-2 -mx-2 rounded-md transition-all duration-200 hover:bg-accent/50 cursor-pointer group ${
              filters.hasOSDR ? "bg-primary/10 hover:bg-primary/15" : ""
            }`}
            onClick={() => onFiltersChange({ ...filters, hasOSDR: !filters.hasOSDR })}
          >
            <Checkbox
              id="has-osdr"
              checked={filters.hasOSDR}
              className="transition-all duration-200 data-[state=checked]:scale-110"
            />
            <Label
              htmlFor="has-osdr"
              className={`text-sm font-normal cursor-pointer transition-all duration-200 ${
                filters.hasOSDR ? "font-medium text-primary" : "group-hover:text-foreground"
              }`}
            >
              OSDR link available
            </Label>
          </div>
        </FilterSection>
      </div>
    </ScrollArea>
  )
}

function FilterSection({
  title,
  expanded,
  onToggle,
  count,
  children,
}: {
  title: string
  expanded: boolean
  onToggle: () => void
  count?: number
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between text-sm font-medium hover:text-primary transition-all duration-200 hover:translate-x-1"
      >
        <span className="flex items-center gap-2">
          {title}
          {count !== undefined && count > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
              {count}
            </span>
          )}
        </span>
        {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>
      {expanded && <div className="pl-1">{children}</div>}
    </div>
  )
}
