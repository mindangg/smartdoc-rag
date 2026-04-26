import React, { useCallback, useEffect, useRef, useState } from 'react'
import useChatStore from '../../store/chatStore'
import { queryDocuments, fetchHistory, clearHistory } from '../../services/api'
import MessageBubble from './MessageBubble'
import QueryProgress from '../query/QueryProgress'
import ConfirmDialog from '../ConfirmDialog'

function now() {
  return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

/** Convert history DB items (newest-first) into message pairs for the chatbox */
function historyToMessages(items) {
  const msgs = []
  // items are newest-first → reverse to show oldest at top
  const chronological = [...items].reverse()
  for (const item of chronological) {
    const ts = item.created_at.replace('T', ' ').slice(0, 16)
    msgs.push({
      id: `hist-user-${item.id}`,
      role: 'user',
      content: item.question,
      ts,
      fromHistory: true,
    })
    msgs.push({
      id: `hist-asst-${item.id}`,
      role: 'assistant',
      ragContent: item.rag_answer || '',
      coragContent: item.corag_answer || '',
      ragCitations: [],
      coragCitations: [],
      usedWeb: false,
      ragDone: true,
      coragDone: true,
      ts,
      fromHistory: true,
    })
  }
  return msgs
}

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const [confirmClear, setConfirmClear] = useState(false)
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const {
    messages,
    addMessage,
    setMessages,
    updateLastAssistantMessage,
    clearMessages,
    isQuerying,
    setIsQuerying,
    pushQueryStep,
    resetQuery,
    vectorCount,
    sessionId,
  } = useChatStore()

  useEffect(() => {
    if (historyLoaded) return
    fetchHistory(sessionId)
      .then((data) => {
        const histMsgs = historyToMessages(data.items || [])
        if (histMsgs.length > 0) {
          setMessages(histMsgs)
        }
      })
      .catch((err) => console.error('History load error:', err))
      .finally(() => setHistoryLoaded(true))
  }, [sessionId, historyLoaded, setMessages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = useCallback(async () => {
    const question = input.trim()
    if (!question || isQuerying) return

    setInput('')
    resetQuery()
    setIsQuerying(true)

    // Add user message
    addMessage({
      id: Date.now(),
      role: 'user',
      content: question,
      ts: now(),
    })

    addMessage({
      id: Date.now() + 1,
      role: 'assistant',
      ragContent: '',
      coragContent: '',
      ragCitations: [],
      coragCitations: [],
      usedWeb: false,
      ragDone: false,
      coragDone: false,
      ts: now(),
    })

    await queryDocuments({
      question,
      sessionId,
      onEvent: (data) => {
        pushQueryStep(data)

        if (data.step === 'answer') {
          if (data.source === 'rag') {
            updateLastAssistantMessage({
              ragContent: data.answer,
              ragCitations: data.citations ?? [],
              ragDone: true,
              ts: now(),
            })
          } else if (data.source === 'corag') {
            updateLastAssistantMessage({
              coragContent: data.answer,
              coragCitations: data.citations ?? [],
              usedWeb: data.used_web ?? false,
              coragDone: true,
              ts: now(),
            })
          }
        }

        if (data.step === 'error') {
          if (data.source === 'rag') {
            updateLastAssistantMessage({ ragContent: `Cảnh báo: ${data.message}`, ragDone: true })
          } else if (data.source === 'corag') {
            updateLastAssistantMessage({ coragContent: `Cảnh báo: ${data.message}`, coragDone: true })
          } else {
            updateLastAssistantMessage({
              ragContent: `Cảnh báo: ${data.message}`,
              coragContent: `Cảnh báo: ${data.message}`,
              ragDone: true,
              coragDone: true,
            })
          }
        }
      },
      onError: (err) => {
        updateLastAssistantMessage({
          ragContent: `Lỗi kết nối: ${err.message}`,
          coragContent: `Lỗi kết nối: ${err.message}`,
          ragDone: true,
          coragDone: true,
          ts: now(),
        })
        pushQueryStep({ step: 'error', message: err.message })
      },
    })

    setIsQuerying(false)
    setTimeout(resetQuery, 3000)
  }, [
    input, isQuerying, sessionId, addMessage, updateLastAssistantMessage,
    resetQuery, setIsQuerying, pushQueryStep,
  ])

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleClearConfirmed = async () => {
    clearMessages()
    try {
      await clearHistory(sessionId)
    } catch (err) {
      console.error('Failed to clear history:', err)
    }
    setConfirmClear(false)
  }

  const canSend = input.trim().length > 0 && !isQuerying
  const hasMessages = messages.length > 0

  return (
    <main className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div>
          <div className="chat-title">Hỏi Đáp Thông Minh</div>
          <div className="chat-subtitle">
            {vectorCount > 0
              ? `${vectorCount.toLocaleString()} vectors đã index • RAG + CoRAG`
              : 'Upload tài liệu để bắt đầu'}
          </div>
        </div>

        {hasMessages && (
          <button
            id="clear-chat-btn"
            onClick={() => setConfirmClear(true)}
            title="Xóa toàn bộ lịch sử chat"
            className="chat-header-btn danger"
          >
            Xóa lịch sử
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="chat-messages" id="chat-messages">
        {!hasMessages ? (
          <div className="empty-state">
            <div className="empty-state-title">SmartDoc RAG</div>
            <div className="empty-state-hint">
              Upload tài liệu PDF, DOCX hoặc hình ảnh ở thanh bên trái, rồi đặt câu hỏi về nội dung.
              Hệ thống sẽ tự động đánh giá và kết hợp kết quả từ tài liệu + web (CoRAG).
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Real-time query progress overlay */}
      <QueryProgress />

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-wrap">
          <textarea
            ref={textareaRef}
            id="chat-input"
            className="chat-input"
            placeholder={
              vectorCount === 0
                ? 'Upload tài liệu trước để đặt câu hỏi…'
                : 'Đặt câu hỏi về tài liệu… (Enter để gửi)'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            disabled={isQuerying}
            style={{ height: 'auto' }}
            onInput={(e) => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            id="send-btn"
            className="send-btn"
            onClick={handleSubmit}
            disabled={!canSend}
            title="Gửi câu hỏi"
          >
            Gửi
          </button>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
          Shift+Enter để xuống dòng • Enter để gửi
        </div>
      </div>

      {/* Confirm clear all history */}
      <ConfirmDialog
        open={confirmClear}
        title="Xóa toàn bộ lịch sử chat?"
        message="Tất cả tin nhắn trong phiên này sẽ bị xóa vĩnh viễn khỏi màn hình và cơ sở dữ liệu."
        confirmLabel="Xóa tất cả"
        danger
        onConfirm={handleClearConfirmed}
        onCancel={() => setConfirmClear(false)}
      />
    </main>
  )
}
