import React, { useEffect, useRef } from 'react'

export default function ConfirmDialog({
  open,
  title = 'Xác nhận',
  message,
  confirmLabel = 'Xác nhận',
  cancelLabel = 'Hủy',
  danger = false,
  onConfirm,
  onCancel,
}) {
  const confirmRef = useRef(null)

  // Focus the confirm button when dialog opens
  useEffect(() => {
    if (open) confirmRef.current?.focus()
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (e.key === 'Escape') onCancel?.() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onCancel])

  if (!open) return null

  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div
        className="confirm-dialog"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
      >
        <div className="confirm-header">
          <span id="confirm-title" className="confirm-title">{title}</span>
        </div>
        {message && (
          <div className="confirm-body">{message}</div>
        )}
        <div className="confirm-actions">
          <button
            id="confirm-cancel-btn"
            className="confirm-btn confirm-btn-cancel"
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            id="confirm-ok-btn"
            ref={confirmRef}
            className={`confirm-btn ${danger ? 'confirm-btn-danger' : 'confirm-btn-primary'}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
