import React from 'react'
import useChatStore from '../store/chatStore'
import DropZone from './upload/DropZone'

export default function Sidebar() {
  const { documents, vectorCount } = useChatStore()

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-header">
        <div className="logo">
          <div>
            <div className="logo-text">SmartDoc RAG</div>
            <div className="logo-sub">RAG + CoRAG Engine</div>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <DropZone />

      {/* Documents List */}
      <div className="doc-list">
        <div className="doc-list-header">
          Tài liệu đã tải ({documents.length})
        </div>

        {documents.length === 0 && (
          <div
            style={{
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: 13,
              padding: '20px 8px',
              lineHeight: 1.6,
            }}
          >
            Chưa có tài liệu.
            <br />
            Upload PDF hoặc ảnh để bắt đầu.
          </div>
        )}

        {documents.map((doc) => {
          const isImage = /\.(png|jpg|jpeg|bmp|webp|tiff?)$/i.test(doc.name)
          return (
            <div key={doc.id} className="doc-item" title={doc.name}>
              <div className="doc-icon" style={{ fontSize: 11, fontWeight: 700, color: isImage ? 'var(--cyan-400)' : 'var(--indigo-400)', display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, background: 'rgba(255,255,255,0.1)', borderRadius: 4 }}>
                {isImage ? 'IMG' : 'DOC'}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="doc-name">{doc.name}</div>
                <div className="doc-meta">
                  {doc.chunks} chunks · {doc.uploadedAt}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Stats bar */}
      <div className="stat-bar">
        <span>Vector Store</span>
        <span className="stat-badge">
          {vectorCount.toLocaleString()} vectors
        </span>
      </div>
    </aside>
  )
}
