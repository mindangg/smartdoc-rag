/**
 * Zustand store — global state for SmartDoc RAG
 */
import { create } from 'zustand'

const useChatStore = create((set, get) => ({
  sessionId: 'default',
  setSessionId: (id) => set({ sessionId: id }),

  // ── Documents ─────────────────────────────────────────────────────────────
  documents: [],          // { id, name, chunks, vectors, uploadedAt }
  vectorCount: 0,
  addDocument: (doc) =>
    set((s) => ({ documents: [doc, ...s.documents] })),
  setDocuments: (docs) => set({ documents: docs }),
  setVectorCount: (n) => set({ vectorCount: n }),
  clearAllDocuments: () => set({ documents: [], vectorCount: 0 }),

  // ── Chat Messages ─────────────────────────────────────────────────────────
  messages: [],           // { id, role, ragContent, coragContent, ragCitations, coragCitations, usedWeb, ts, ragDone, coragDone }
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),
  updateLastAssistantMessage: (patch) =>
    set((s) => {
      const msgs = [...s.messages]
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant') {
          msgs[i] = { ...msgs[i], ...patch }
          break
        }
      }
      return { messages: msgs }
    }),
  clearMessages: () => set({ messages: [] }),

  // ── Upload State ──────────────────────────────────────────────────────────
  isUploading: false,
  uploadSteps: [],        // { step, message, progress, status }
  setIsUploading: (v) => set({ isUploading: v }),
  setUploadSteps: (steps) => set({ uploadSteps: steps }),
  pushUploadStep: (step) =>
    set((s) => {
      const steps = [...s.uploadSteps]
      const idx = steps.findIndex((st) => st.step === step.step)
      if (idx >= 0) {
        steps[idx] = step        // update existing
      } else {
        steps.push(step)         // new step
      }
      return { uploadSteps: steps }
    }),
  resetUpload: () => set({ isUploading: false, uploadSteps: [] }),

  isQuerying: false,
  querySteps: [],         // { step, message, status, score?, usedWeb? }
  setIsQuerying: (v) => set({ isQuerying: v }),
  pushQueryStep: (step) =>
    set((s) => ({ querySteps: [...s.querySteps, step] })),
  resetQuery: () => set({ isQuerying: false, querySteps: [] }),
}))

export default useChatStore
