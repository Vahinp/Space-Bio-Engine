"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Plus, ArrowLeft, CheckCircle, AlertCircle } from "lucide-react"
import { apiService } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export default function AddArticlePage() {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setError("")
    setSuccess(false)

    try {
      const response = await apiService.addPaper(url.trim())
      
      if (response.error) {
        setError(response.error)
        toast({
          title: "Error",
          description: response.error,
          variant: "destructive",
        })
      } else if (response.data?.success) {
        setSuccess(true)
        toast({
          title: "Success",
          description: `Article "${response.data.paper.title}" added successfully!`,
        })
        setUrl("")
        // Refresh the main page after a short delay
        setTimeout(() => {
          router.push("/")
        }, 2000)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to add article"
      setError(errorMessage)
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="mb-4 gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <h1 className="text-3xl font-bold">Add New Article</h1>
          <p className="text-muted-foreground mt-2">
            Enter a PMC article URL to automatically parse and add it to the database
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Add Article
            </CardTitle>
          </CardHeader>
          <CardContent>
            {success ? (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Article added successfully! Redirecting to main page...
                </AlertDescription>
              </Alert>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="url" className="block text-sm font-medium mb-2">
                    PMC Article URL
                  </label>
                  <Input
                    id="url"
                    type="url"
                    placeholder="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Enter a valid PMC (PubMed Central) article URL
                  </p>
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  disabled={loading || !url.trim()}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Parsing Article...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Article
                    </>
                  )}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        <div className="mt-6 p-4 bg-muted rounded-lg">
          <h3 className="font-semibold mb-2">Supported Sources</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• PubMed Central (PMC) articles</li>
            <li>• Example: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
