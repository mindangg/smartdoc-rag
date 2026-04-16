import React, { useState } from 'react'

export default function CitationCard({ citations }) {
  const [open, setOpen] = useState(false)
  if (!citations || citations.length === 0) return null

  return (
    <div className="citations-section" id="citations-section">
      <button className="citations-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? '[-]' : '[+]'} {open ? 'Ẩn' : 'Xem'} {citations.length} nguồn trích dẫn
      </button>

      {open && (
        <div className="citations-list">
          {citations.map((c) => (
            <div key={c.id} className="citation-card">
              <div className="citation-header">
                <div className="citation-num">{c.id}</div>
                <div className="citation-title" title={c.title}>
                  {c.type === 'web' ? 'Web: ' : 'Doc: '}
                  {c.title || c.source}
                </div>
                {c.page && (
                  <span style={{ color: 'var(--text-muted)', fontSize: 11, flexShrink: 0 }}>
                    Trang {c.page}
                  </span>
                )}
              </div>

              <div className="citation-snippet">{c.snippet}</div>

              {c.url && (
                <a
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="citation-url"
                >
                  Link: {c.url.length > 50 ? c.url.slice(0, 50) + '…' : c.url}
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
