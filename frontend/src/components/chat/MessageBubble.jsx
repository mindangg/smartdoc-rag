import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CitationCard from './CitationCard'

export default function MessageBubble({ message }) {
  const { role, content, ragContent, coragContent, ragCitations, coragCitations, usedWeb, ts, ragDone, coragDone } = message
  const isUser = role === 'user'
  
  if (isUser) {
    return (
      <div className={`message-row ${role}`} id={`msg-${message.id}`}>
        <div className={`message-avatar ${role}`}>U</div>
        <div className="message-body">
          <div className={`message-bubble ${role}`}>
            {content}
          </div>
          <div className="message-meta">
            <span>{ts}</span>
          </div>
        </div>
      </div>
    )
  }

  // Assistant Message - 2 columns
  return (
    <div className={`message-row ${role}`} id={`msg-${message.id}`} style={{ alignItems: 'flex-start' }}>
      <div className={`message-avatar ${role}`}>AI</div>
      <div className="message-body" style={{ width: '100%' }}>
        <div style={{ display: 'flex', gap: '20px', width: '100%' }}>
          
          {/* RAG Column */}
          <div className="dual-column" style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-muted)' }}>RAG</div>
            <div className={`message-bubble ${role}`} style={{ width: '100%' }}>
              {!ragDone && !ragContent ? (
                <div className="typing-dots"><div className="typing-dot"/><div className="typing-dot"/><div className="typing-dot"/></div>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{ragContent}</ReactMarkdown>
              )}
            </div>
            {ragDone && ragCitations && ragCitations.length > 0 && (
              <CitationCard citations={ragCitations} />
            )}
          </div>

          {/* CoRAG Column */}
          <div className="dual-column" style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-muted)' }}>CoRAG</div>
            <div className={`message-bubble ${role}`}>
              {!coragDone && !coragContent ? (
                <div className="typing-dots"><div className="typing-dot"/><div className="typing-dot"/><div className="typing-dot"/></div>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{coragContent}</ReactMarkdown>
              )}
            </div>
            {coragDone && (
              <div className="message-meta" style={{ marginTop: 8 }}>
                {usedWeb && <span className="web-badge" style={{ marginBottom: 8, display: 'inline-block' }}>Web enhanced</span>}
              </div>
            )}
            {coragDone && coragCitations && coragCitations.length > 0 && (
              <CitationCard citations={coragCitations} />
            )}
          </div>

        </div>
        <div className="message-meta" style={{ marginTop: 12 }}>
          <span>{ts}</span>
        </div>
      </div>
    </div>
  )
}

