"use client"

import { useState } from "react"
import { ExternalLink, FileText, Database, ChevronLeft, ChevronRight, Bookmark, Loader2, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { PaperDetailDrawer } from "@/components/paper-detail-drawer"
import { BulkActionsBar } from "@/components/bulk-actions-bar"
import { useToast } from "@/hooks/use-toast"
import { Paper } from "@/lib/api"

interface ResultsListProps {
  searchQuery: string
  filters: any
  papers: Paper[]
  loading: boolean
  error: string | null
}

const MOCK_PAPERS = [
  {
    id: "1",
    title: "Microgravity-Induced Changes in Bone Density and Muscle Atrophy in Long-Duration Spaceflight",
    authors: "Smith, J., Johnson, M., Williams, K.",
    year: 2023,
    organism: "Human",
    mission: "ISS",
    environment: "Microgravity",
    summary:
      "Study reveals significant bone density loss (1.5% per month) and muscle atrophy in astronauts during 6-month ISS missions. Resistance exercise protocols showed partial mitigation effects.",
    citations: 42,
    hasOSDR: true,
    hasDOI: true,
    bookmarked: false,
    abstract:
      "Long-duration spaceflight exposes astronauts to microgravity conditions that significantly impact musculoskeletal health. This study examined bone density and muscle mass changes in 24 astronauts during 6-month missions aboard the International Space Station. Using dual-energy X-ray absorptiometry (DEXA) and MRI imaging, we quantified changes in bone mineral density and muscle cross-sectional area before, during, and after spaceflight.",
    keyResults: [
      "Bone mineral density decreased by 1.5% per month on average, with greatest losses in weight-bearing bones",
      "Muscle cross-sectional area reduced by 12-17% in lower extremities",
      "Resistance exercise protocols (ARED) reduced bone loss by approximately 40%",
      "Recovery to baseline took 6-12 months post-flight depending on exercise compliance",
    ],
    methods:
      "24 astronauts (12 male, 12 female, ages 35-52) participated in this longitudinal study. DEXA scans were performed at L-180, L-30, R+0, R+30, and R+180 days. MRI imaging of thigh and calf muscles was conducted at the same timepoints. Exercise logs were maintained throughout the mission.",
    conclusions:
      "Microgravity-induced bone and muscle loss remains a significant challenge for long-duration spaceflight. While current countermeasures provide partial protection, additional interventions may be necessary for missions beyond low Earth orbit. Future research should focus on pharmacological adjuncts and optimized exercise protocols.",
    doi: "10.1234/example.2023.001",
    osdrLink: "https://osdr.nasa.gov/example",
  },
  {
    id: "2",
    title: "Radiation Effects on Plant Growth and Development in Simulated Martian Conditions",
    authors: "Chen, L., Rodriguez, A., Park, S.",
    year: 2024,
    organism: "Plant",
    mission: "Analog Studies",
    environment: "Radiation",
    summary:
      "Arabidopsis plants exposed to Mars-equivalent radiation showed altered gene expression in DNA repair pathways. Growth rates reduced by 30% compared to controls.",
    citations: 18,
    hasOSDR: true,
    hasDOI: true,
    bookmarked: false,
    abstract:
      "Understanding plant responses to Martian radiation is critical for future life support systems. This study exposed Arabidopsis thaliana to simulated Mars surface radiation levels (0.67 mSv/day) for 60 days in a controlled environment chamber with Mars-analog regolith and atmospheric composition.",
    keyResults: [
      "30% reduction in overall growth rate compared to Earth-normal controls",
      "Upregulation of DNA repair genes (RAD51, BRCA1 homologs) by 2-3 fold",
      "Increased production of antioxidant compounds",
      "Delayed flowering time by approximately 10 days",
    ],
    methods:
      "Arabidopsis seeds were germinated in Mars-analog regolith under 0.6 kPa CO2 atmosphere. Radiation exposure used a Cs-137 source calibrated to Mars surface levels. RNA-seq was performed at 20, 40, and 60 days. Growth parameters were measured weekly.",
    conclusions:
      "Plants demonstrate adaptive responses to Mars-level radiation but with significant growth penalties. Genetic engineering approaches targeting radiation tolerance pathways may be necessary for productive Martian agriculture. Shielding strategies should also be considered for greenhouse designs.",
    doi: "10.1234/example.2024.002",
    osdrLink: "https://osdr.nasa.gov/example2",
  },
  {
    id: "3",
    title: "Immune System Dysregulation in Microgravity: A Comprehensive RNA-seq Analysis",
    authors: "Taylor, R., Anderson, B., Lee, H.",
    year: 2023,
    organism: "Mouse",
    mission: "Space Shuttle",
    environment: "Microgravity",
    summary:
      "RNA-seq data reveals down-regulation of key immune response genes in mice exposed to microgravity. T-cell function significantly impaired after 30 days.",
    citations: 67,
    hasOSDR: true,
    hasDOI: false,
    bookmarked: true,
    abstract:
      "Spaceflight is associated with immune system dysfunction, increasing infection risk for astronauts. This study used RNA-seq to comprehensively profile immune cell gene expression in mice during 30-day spaceflight missions.",
    keyResults: [
      "1,247 differentially expressed genes in T-cells, with 68% showing downregulation",
      "Key cytokine genes (IL-2, IFN-γ) reduced by 40-60%",
      "T-cell proliferation capacity decreased by 55% in flight samples",
      "Partial recovery observed within 7 days of return to Earth",
    ],
    methods:
      "C57BL/6 mice (n=20 flight, n=20 ground control) were housed in specialized habitats. Splenocytes were isolated immediately post-flight and subjected to RNA-seq. Flow cytometry assessed T-cell populations and function.",
    conclusions:
      "Microgravity induces profound transcriptional changes in immune cells, particularly affecting T-cell activation pathways. Understanding these mechanisms is essential for developing countermeasures to protect crew health during long-duration missions.",
    osdrLink: "https://osdr.nasa.gov/example3",
  },
  {
    id: "4",
    title: "Microbial Behavior and Biofilm Formation in Spacecraft Environments",
    authors: "Kumar, P., White, D., Garcia, M.",
    year: 2022,
    organism: "Microbe",
    mission: "ISS",
    environment: "Microgravity",
    summary:
      "Bacterial biofilms form 40% faster in microgravity conditions. Enhanced antibiotic resistance observed in E. coli cultures aboard ISS.",
    citations: 91,
    hasOSDR: false,
    hasDOI: true,
    bookmarked: false,
    abstract:
      "Microbial contamination poses risks to spacecraft systems and crew health. This study investigated biofilm formation kinetics and antibiotic susceptibility of E. coli and S. aureus in microgravity aboard the ISS.",
    keyResults: [
      "Biofilm formation rate increased by 40% in microgravity",
      "Thicker, more robust biofilm architecture observed",
      "Minimum inhibitory concentrations (MIC) for common antibiotics increased 2-4 fold",
      "Enhanced expression of efflux pump genes",
    ],
    methods:
      "Bacterial cultures were grown in specialized fluidic devices aboard ISS for 7 days. Biofilm mass was quantified using crystal violet staining. Antibiotic susceptibility testing followed CLSI guidelines. Gene expression analyzed via qRT-PCR.",
    conclusions:
      "Microgravity enhances bacterial biofilm formation and antibiotic resistance, presenting challenges for spacecraft hygiene and crew health. Novel antimicrobial strategies may be required for long-duration missions.",
    doi: "10.1234/example.2022.004",
  },
]

export function ResultsList({ searchQuery, filters, papers, loading, error }: ResultsListProps) {
  const [selectedPapers, setSelectedPapers] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null)
  const [compareMode, setCompareMode] = useState(false)
  const [comparisonPaper, setComparisonPaper] = useState<Paper | null>(null)
  const { toast } = useToast()

  const togglePaperSelection = (paperId: string) => {
    setSelectedPapers((prev) => (prev.includes(paperId) ? prev.filter((id) => id !== paperId) : [...prev, paperId]))
  }

  const toggleBookmark = (paperId: string) => {
    // Note: In a real app, this would make an API call to save bookmarks
    toast({
      title: "Bookmark saved",
      description: "Paper bookmarked (local storage)",
    })
  }

  const handleViewDetails = (paper: Paper) => {
    if (compareMode && selectedPaper && selectedPaper.id !== paper.id) {
      setComparisonPaper(paper)
    } else {
      setSelectedPaper(paper)
      setComparisonPaper(null)
    }
  }

  const handleBulkBookmark = () => {
    // Note: In a real app, this would make an API call to save bookmarks
    toast({
      title: "Papers bookmarked",
      description: `${selectedPapers.length} ${selectedPapers.length === 1 ? "paper" : "papers"} added to bookmarks`,
    })
    setSelectedPapers([])
  }

  const handleBulkDelete = () => {
    toast({
      title: "Papers removed",
      description: `${selectedPapers.length} ${selectedPapers.length === 1 ? "paper" : "papers"} removed from results`,
    })
    setSelectedPapers([])
  }

  const handleBulkShare = () => {
    toast({
      title: "Share link copied",
      description: "Link to selected papers copied to clipboard",
    })
  }

  const handleBulkSendToChat = () => {
    toast({
      title: "Sent to chat",
      description: `${selectedPapers.length} ${selectedPapers.length === 1 ? "paper" : "papers"} sent to AI assistant`,
    })
  }

  const handleExport = (format: string, fields: string[]) => {
    toast({
      title: "Export started",
      description: `Exporting ${selectedPapers.length} ${selectedPapers.length === 1 ? "paper" : "papers"} as ${format.toUpperCase()}`,
    })
  }

  const hasResults = papers.length > 0

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Loader2 className="h-16 w-16 text-muted-foreground/40 mb-4 animate-spin" />
        <h3 className="text-lg font-semibold mb-2">Loading Papers...</h3>
        <p className="text-sm text-muted-foreground">Fetching data from the backend</p>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <AlertCircle className="h-16 w-16 text-destructive/40 mb-4" />
        <h3 className="text-lg font-semibold mb-2">Error Loading Papers</h3>
        <p className="text-sm text-muted-foreground mb-4">{error}</p>
        <Button onClick={() => window.location.reload()}>Try Again</Button>
      </div>
    )
  }

  return (
    <>
      <div className="p-6 space-y-6">
        {!hasResults && !searchQuery ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <FileText className="h-16 w-16 text-muted-foreground/40 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Start Your Search</h3>
            <p className="text-sm text-muted-foreground max-w-md mb-6">
              Try searching for topics like "microgravity bone loss", "radiation effects on plants", or "ISS immune
              system studies"
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <Badge variant="outline" className="cursor-pointer hover:bg-accent">
                microgravity + bone loss
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-accent">
                radiation studies 2020-2024
              </Badge>
              <Badge variant="outline" className="cursor-pointer hover:bg-accent">
                ISS plant experiments
              </Badge>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Found <span className="font-semibold text-foreground">{papers.length}</span> papers
                {selectedPapers.length > 0 && (
                  <span className="ml-2">
                    · <span className="font-semibold text-foreground">{selectedPapers.length}</span> selected
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Show</span>
                <Select value={pageSize.toString()} onValueChange={(value) => setPageSize(Number(value))}>
                  <SelectTrigger className="w-20 h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="25">25</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-4">
              {papers.map((paper) => (
                <Card
                  key={paper.id}
                  className="hover:border-primary/50 hover:shadow-lg hover:scale-[1.01] transition-all duration-200"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={selectedPapers.includes(paper.id.toString())}
                        onCheckedChange={() => togglePaperSelection(paper.id.toString())}
                        className="mt-1"
                      />
                      <div className="flex-1 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <h3
                            className="font-semibold leading-tight text-balance hover:text-primary cursor-pointer transition-colors duration-200"
                            onClick={() => handleViewDetails(paper)}
                          >
                            {paper.title}
                          </h3>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 shrink-0 hover:scale-110 transition-transform duration-200"
                            onClick={() => toggleBookmark(paper.id.toString())}
                          >
                            <Bookmark className="h-4 w-4 transition-all duration-200" />
                          </Button>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                          {paper.year && <span>{paper.year}</span>}
                          {paper.organism && (
                            <>
                              <span>·</span>
                              <span>{paper.organism}</span>
                            </>
                          )}
                          {paper.source && (
                            <>
                              <span>·</span>
                              <span>{paper.source}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {paper.organism && (
                        <Badge variant="secondary">{paper.organism}</Badge>
                      )}
                      {paper.source && (
                        <Badge variant="outline">{paper.source}</Badge>
                      )}
                      {paper.year && (
                        <Badge variant="outline">{paper.year}</Badge>
                      )}
                      <Badge variant="default" className="gap-1">
                        <ExternalLink className="h-3 w-3" />
                        View Paper
                      </Badge>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(paper.url, '_blank')}
                        className="hover:scale-105 transition-transform duration-200"
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Open Paper
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDetails(paper)}
                        className="hover:scale-105 transition-transform duration-200"
                      >
                        View Details
                      </Button>
                      <Button variant="ghost" size="sm" className="hover:scale-105 transition-transform duration-200">
                        Send to Chat
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4">
              <div className="text-sm text-muted-foreground">
                Page {currentPage} of {Math.ceil(papers.length / pageSize)}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="hover:scale-105 transition-transform duration-200 disabled:hover:scale-100"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => p + 1)}
                  disabled={currentPage >= Math.ceil(papers.length / pageSize)}
                  className="hover:scale-105 transition-transform duration-200 disabled:hover:scale-100"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>

      <BulkActionsBar
        selectedCount={selectedPapers.length}
        onClearSelection={() => setSelectedPapers([])}
        onBookmark={handleBulkBookmark}
        onDelete={handleBulkDelete}
        onShare={handleBulkShare}
        onSendToChat={handleBulkSendToChat}
        onExport={handleExport}
      />

      <PaperDetailDrawer
        paper={selectedPaper}
        onClose={() => {
          setSelectedPaper(null)
          setComparisonPaper(null)
          setCompareMode(false)
        }}
        compareMode={compareMode}
        onCompareModeChange={setCompareMode}
        comparisonPaper={comparisonPaper}
        onSendToChat={() => {
          toast({
            title: "Sent to chat",
            description: "Paper sent to AI assistant",
          })
        }}
      />
    </>
  )
}
