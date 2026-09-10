import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'

const components: Components = {
  h1: ({ children }) => <h3 className="font-display mb-1.5 mt-3 text-base font-bold text-text first:mt-0">{children}</h3>,
  h2: ({ children }) => <h4 className="font-display mb-1.5 mt-3 text-sm font-bold text-text first:mt-0">{children}</h4>,
  h3: ({ children }) => <h5 className="mb-1 mt-3 text-sm font-semibold text-text first:mt-0">{children}</h5>,
  p: ({ children }) => <p className="mb-2 leading-relaxed last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-text">{children}</strong>,
  em: ({ children }) => <em className="text-text">{children}</em>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  code: ({ children }) => (
    <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[0.85em] text-accent-2">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="mb-2 overflow-x-auto rounded-lg bg-surface-2 p-3 text-xs last:mb-0">{children}</pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="mb-2 border-l-2 border-accent-2/40 pl-3 text-text-muted last:mb-0">{children}</blockquote>
  ),
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-accent-2 underline underline-offset-2">
      {children}
    </a>
  ),
  hr: () => <hr className="my-3 border-border" />,
}

export default function Markdown({ children }: { children: string }) {
  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown components={components}>{children}</ReactMarkdown>
    </div>
  )
}

const inlineComponents: Components = {
  p: ({ children }) => <>{children}</>,
  strong: ({ children }) => <strong className="font-semibold text-text">{children}</strong>,
  em: ({ children }) => <em>{children}</em>,
  code: ({ children }) => (
    <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-[0.85em] text-accent-2">{children}</code>
  ),
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-accent-2 underline underline-offset-2">
      {children}
    </a>
  ),
}

/** Renders inline markdown (bold/italic/code/links) without wrapping block
 * elements — for single-line text inside list items, table cells, etc. */
export function MarkdownInline({ children }: { children: string }) {
  return <ReactMarkdown components={inlineComponents}>{children}</ReactMarkdown>
}
