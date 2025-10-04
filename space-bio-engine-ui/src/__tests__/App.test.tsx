import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders the app and finds the Open Chat button', () => {
    render(<App />)
    
    const openChatButton = screen.getByText('Open Chat')
    expect(openChatButton).toBeInTheDocument()
  })
})
