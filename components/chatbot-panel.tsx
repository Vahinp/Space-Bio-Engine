"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, Sparkles, FileText, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: Array<{
    id: string
    title: string
    authors: string
    year: number
  }>
}

const SUGGESTED_QUESTIONS = [
  "What are the main effects of microgravity on bone density?",
  "How does radiation affect plant growth in space?",
  "Compare immune system changes in mice vs humans during spaceflight",
  "What countermeasures exist for muscle atrophy in astronauts?",
]

export function ChatbotPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async (question?: string) => {
    const messageContent = question || input
    if (!messageContent.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageContent,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Simulate AI response with streaming
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "Based on the research papers in the database, microgravity has significant effects on bone density. Studies show that astronauts experience approximately 1-2% bone mineral density loss per month during spaceflight, particularly in weight-bearing bones like the spine, hips, and legs.\n\nKey findings include:\n\n1. **Rate of Loss**: The average bone density loss is about 1.5% per month, which is significantly higher than age-related bone loss on Earth (1% per year).\n\n2. **Countermeasures**: Resistance exercise protocols using the Advanced Resistive Exercise Device (ARED) on the ISS have shown to reduce bone loss by approximately 40%.\n\n3. **Recovery**: Post-flight recovery typically takes 6-12 months, depending on mission duration and exercise compliance during the mission.\n\n4. **Mechanisms**: The loss is attributed to reduced mechanical loading, altered calcium metabolism, and changes in bone remodeling processes.\n\nThese findings are critical for planning long-duration missions beyond low Earth orbit, where countermeasures will need to be even more effective.",
        citations: [
          {
            id: "1",
            title: "Microgravity-Induced Changes in Bone Density and Muscle Atrophy in Long-Duration Spaceflight",
            authors: "Smith, J., Johnson, M., Williams, K.",
            year: 2023,
          },
          {
            id: "5",
            title: "Bone Mineral Density Changes During ISS Missions: A 10-Year Analysis",
            authors: "Brown, T., Davis, L.",
            year: 2022,
          },
        ],
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Ask About Space Biology Research</h3>
          <p className="text-sm text-muted-foreground max-w-md mb-6">
            I can help you understand research findings, compare studies, and explore connections between papers in the
            database.
          </p>
          <div className="space-y-2 w-full max-w-lg">
            <p className="text-xs font-medium text-muted-foreground mb-3">Try asking:</p>
            {SUGGESTED_QUESTIONS.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                className="w-full justify-start text-left h-auto py-3 px-4 hover:bg-accent bg-transparent transition-all hover:translate-x-1 hover:border-primary/50"
                onClick={() => handleSubmit(question)}
              >
                <span className="text-sm text-pretty">{question}</span>
              </Button>
            ))}
          </div>
        </div>
      ) : (
        <ScrollArea className="flex-1 p-6" ref={scrollRef}>
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((message) => (
              <div key={message.id} className={message.role === "user" ? "flex justify-end" : "flex justify-start"}>
                {message.role === "user" ? (
                  <div className="bg-primary text-primary-foreground rounded-2xl px-4 py-3 max-w-[80%]">
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-w-[90%]">
                    <Card className="p-4 bg-muted/50">
                      <div className="prose prose-sm max-w-none">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground">{message.content}</p>
                      </div>
                    </Card>
                    {message.citations && message.citations.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          Sources:
                        </p>
                        <div className="space-y-2">
                          {message.citations.map((citation) => (
                            <Card
                              key={citation.id}
                              className="p-3 hover:border-primary/50 cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5"
                            >
                              <p className="text-sm font-medium leading-tight mb-1">{citation.title}</p>
                              <p className="text-xs text-muted-foreground">
                                {citation.authors} · {citation.year}
                              </p>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <Card className="p-4 bg-muted/50">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Analyzing research papers...</span>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </ScrollArea>
      )}

      <div className="border-t border-border p-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about space biology research..."
              className="min-h-[60px] max-h-[120px] resize-none"
              disabled={isLoading}
            />
            <Button
              onClick={() => handleSubmit()}
              disabled={!input.trim() || isLoading}
              size="icon"
              className="h-[60px] w-[60px] shrink-0 transition-all hover:scale-105"
            >
              {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Press Enter to send, Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  )
}
