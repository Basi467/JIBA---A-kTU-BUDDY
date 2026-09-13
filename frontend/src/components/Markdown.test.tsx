import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Markdown, { MarkdownInline } from './Markdown'

describe('Markdown', () => {
  it('renders headings, bold, and list items with the themed components', () => {
    render(<Markdown>{'# Heading\n\n**bold text** and a list:\n\n- one\n- two'}</Markdown>)

    expect(screen.getByRole('heading', { level: 3, name: 'Heading' })).toBeInTheDocument()
    expect(screen.getByText('bold text').tagName).toBe('STRONG')
    expect(screen.getByText('one').tagName).toBe('LI')
    expect(screen.getByText('two').tagName).toBe('LI')
  })

  it('renders inline code and links', () => {
    render(<Markdown>{'Use `npm install` then visit [docs](https://example.com).'}</Markdown>)

    expect(screen.getByText('npm install').tagName).toBe('CODE')
    const link = screen.getByRole('link', { name: 'docs' })
    expect(link).toHaveAttribute('href', 'https://example.com')
    expect(link).toHaveAttribute('target', '_blank')
  })
})

describe('MarkdownInline', () => {
  it('does not wrap content in a block-level paragraph', () => {
    const { container } = render(<MarkdownInline>{'Just **bold** text'}</MarkdownInline>)
    expect(container.querySelector('p')).not.toBeInTheDocument()
    expect(screen.getByText('bold').tagName).toBe('STRONG')
  })
})
