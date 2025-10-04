export interface FilterState {
  search: string
  organism: string
  year: string
  source: string
}

export interface Message {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}
