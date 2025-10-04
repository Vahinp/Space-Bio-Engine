import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Dashboard from '../routes/Dashboard'

describe('Dashboard', () => {
  it('renders FilterBar controls and ensures they are focusable', () => {
    render(<Dashboard />)
    
    // Check if filter controls are rendered
    const searchInput = screen.getByLabelText('Search studies')
    const organismSelect = screen.getByLabelText('Filter by organism')
    const yearSelect = screen.getByLabelText('Filter by year')
    const sourceSelect = screen.getByLabelText('Filter by source')
    
    expect(searchInput).toBeInTheDocument()
    expect(organismSelect).toBeInTheDocument()
    expect(yearSelect).toBeInTheDocument()
    expect(sourceSelect).toBeInTheDocument()
    
    // Check if controls are focusable
    expect(searchInput).not.toHaveAttribute('disabled')
    expect(organismSelect).not.toHaveAttribute('disabled')
    expect(yearSelect).not.toHaveAttribute('disabled')
    expect(sourceSelect).not.toHaveAttribute('disabled')
  })
})
