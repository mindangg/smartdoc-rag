import React, {useState} from 'react'
import useChatStore from '../store/chatStore'
import DropZone from './upload/DropZone'
import ConfirmDialog from './ConfirmDialog'
import {clearVectorStore} from '../services/api'

export default function Sidebar() {
    const {documents, vectorCount, clearDocuments} = useChatStore()
    const [confirmOpen, setConfirmOpen] = useState(false)
    const [deleting, setDeleting] = useState(false)

    const handleDeleteVectorStore = async () => {
        setDeleting(true)
        try {
            await clearVectorStore()
            clearDocuments()
        } catch (err) {
            console.error('Failed to clear vector store:', err)
        } finally {
            setDeleting(false)
            setConfirmOpen(false)
        }
    }

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
            <DropZone/>

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
                        <br/>
                        Upload PDF, DOCX hoặc ảnh để bắt đầu.
                    </div>
                )}

                {documents.map((doc) => {
                    const isImage = /\.(png|jpg|jpeg|bmp|webp|tiff?)$/i.test(doc.name)
                    const isDocx = /\.docx$/i.test(doc.name)
                    const label = isImage ? 'IMG' : isDocx ? 'DOCX' : 'PDF'
                    const color = isImage ? 'var(--cyan-400)' : isDocx ? 'var(--amber-400)' : 'var(--indigo-400)'
                    return (
                        <div key={doc.id} className="doc-item" title={doc.name}>
                            <div className="doc-icon" style={{
                                fontSize: 11,
                                fontWeight: 700,
                                color,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                width: 28,
                                height: 28,
                                background: 'rgba(255,255,255,0.1)',
                                borderRadius: 4
                            }}>
                                {label}
                            </div>
                            <div style={{flex: 1, minWidth: 0}}>
                                <div className="doc-name">{doc.name}</div>
                                <div className="doc-meta">
                                    {doc.chunks} chunks · {doc.uploadedAt}
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Stats bar + Delete Vector Store */}
            <div className="stat-bar">
                <span>Vector Store</span>
                <span className="stat-badge">
          {vectorCount.toLocaleString()} vectors
        </span>
            </div>

            <div style={{padding: '8px 16px 12px'}}>
                <button
                    id="delete-vectorstore-btn"
                    className="sidebar-danger-btn"
                    onClick={() => setConfirmOpen(true)}
                    disabled={deleting}
                    title="Xóa toàn bộ vector store"
                >
                    {deleting ? 'Đang xóa…' : 'Xóa Vector Store'}
                </button>
            </div>

            <ConfirmDialog
                open={confirmOpen}
                title="Xóa Vector Store?"
                message="Toàn bộ dữ liệu đã index sẽ bị xóa vĩnh viễn. Bạn cần upload lại tài liệu để sử dụng tiếp."
                confirmLabel="Xóa"
                danger
                onConfirm={handleDeleteVectorStore}
                onCancel={() => setConfirmOpen(false)}
            />
        </aside>
    )
}
