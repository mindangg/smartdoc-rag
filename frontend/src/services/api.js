const BASE = '/api'

export async function streamSSE({ url, body = null, formData = null, onEvent, onError }) {
  try {
    const options = {
      method: 'POST',
      headers: formData ? undefined : { 'Content-Type': 'application/json' },
      body: formData ?? (body ? JSON.stringify(body) : undefined),
    }

    const response = await fetch(BASE + url, options)

    if (!response.ok) {
      const text = await response.text()
      throw new Error(`HTTP ${response.status}: ${text}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Split on double-newline (SSE message boundary)
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''   // keep the incomplete tail

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onEvent(data)
            } catch {
              /* skip malformed lines */
            }
          }
        }
      }
    }
  } catch (err) {
    onError?.(err)
  }
}

// ── Upload ────────────────────────────────────────────────────────────────────
export function uploadFile({ file, onEvent, onError }) {
  const formData = new FormData()
  formData.append('file', file)
  return streamSSE({ url: '/upload', formData, onEvent, onError })
}

// ── Query ─────────────────────────────────────────────────────────────────────
export function queryDocuments({ question, sessionId = 'default', onEvent, onError }) {
  return streamSSE({
    url: '/query',
    body: { question, session_id: sessionId },
    onEvent,
    onError,
  })
}
