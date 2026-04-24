import React, { useCallback, useEffect, useRef, useState } from 'react'
import useChatStore from '../../store/chatStore'
import { queryDocuments, clearChatHistory, fetchChatHistory } from '../../services/api'
import MessageBubble from './MessageBubble'
import QueryProgress from '../query/QueryProgress'

function now() {
  return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

export default function ChatPanel() {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const {
    messages,
    addMessage,
    updateLastAssistantMessage,
    clearMessages,
    setMessages,
    isQuerying,
    setIsQuerying,
    pushQueryStep,
    resetQuery,
    vectorCount,
    sessionId,
  } = useChatStore()

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Fetch chat history on mount
  useEffect(() => {
    fetchChatHistory(sessionId)
      .then(res => {
        if (res.status === 'success' && res.messages) {
          const loadedMsgs = res.messages.map((m, i) => ({
            id: Date.now() + i,
            role: m.role,
            content: m.role === 'user' ? m.content : undefined,
            coragContent: m.role === 'assistant' ? m.content : undefined,
            ragContent: m.role === 'assistant' ? m.content : undefined,
            ragDone: true,
            coragDone: true,
            usedWeb: m.used_web || false,
            ragCitations: m.citations || [],
            coragCitations: m.citations || []
          }))
          setMessages(loadedMsgs)
        }
      })
      .catch(console.error)
  }, [sessionId, setMessages])

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

    // Add placeholder assistant message (shows typing dots)
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
      onEvent: (data) => {
        // Push to progress panel
        pushQueryStep(data)

        // On final answer
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
              ragContent: `Cảnh báo: ${data.message}`, coragContent: `Cảnh báo: ${data.message}`,
              ragDone: true, coragDone: true
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
    
    // Stream fully finished
    setIsQuerying(false)
    setTimeout(resetQuery, 3000)
  }, [
    input, isQuerying, addMessage, updateLastAssistantMessage,
    resetQuery, setIsQuerying, pushQueryStep,
  ])

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const canSend = input.trim().length > 0 && !isQuerying

  const handleClearChat = async () => {
    try {
      await clearChatHistory(sessionId)
      clearMessages()
    } catch (err) {
      console.error(err)
      alert('Lỗi khi xóa lịch sử chat: ' + err.message)
    }
  }

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
        {messages.length > 0 && (
          <button
            id="clear-chat-btn"
            onClick={handleClearChat}
            title="Xóa cuộc hội thoại"
            style={{
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-muted)',
              padding: '6px 10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 12,
              transition: 'var(--transition)',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--rose-400)')}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
          >
            Xóa
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="chat-messages" id="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-state">

            <div className="empty-state-title">SmartDoc RAG</div>
            <div className="empty-state-hint">
              Upload tài liệu PDF hoặc hình ảnh ở thanh bên trái, rồi đặt câu hỏi về nội dung.
              Hệ thống sẽ tự động đánh giá và kết hợp kết quả từ tài liệu + web (CoRAG).
            </div>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
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
            style={{
              height: 'auto',
            }}
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
    </main>
  )
}
