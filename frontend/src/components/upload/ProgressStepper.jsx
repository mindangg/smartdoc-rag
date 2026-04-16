import React from 'react'

// Ordered list of all possible upload steps
const ALL_STEPS = [
  { step: 'reading_file', label: 'Đọc file' },
  { step: 'ocr',         label: 'OCR / Phân tích' },
  { step: 'chunking',    label: 'Chunking' },
  { step: 'indexing',    label: 'Lưu FAISS' },
  { step: 'done',        label: 'Hoàn thành' },
]

const STEP_MAP = {
  reading_file:  'reading_file',
  ocr:           'ocr',
  ocr_done:      'ocr',
  chunking:      'chunking',
  chunking_done: 'chunking',
  indexing:      'indexing',
  done:          'done',
  error:         null,
}

function dotIcon(status) {
  if (status === 'done')    return '✓'
  if (status === 'active')  return ''
  if (status === 'error')   return '✕'
  return ''
}

export default function ProgressStepper({ steps }) {
  // Find the highest completed canonical step
  const arrivedSteps = new Set(
    steps
      .map((s) => STEP_MAP[s.step])
      .filter(Boolean)
  )

  const hasError = steps.some((s) => s.step === 'error')
  const errorMsg = steps.find((s) => s.step === 'error')?.message

  // Progress 0-100 from latest progress field
  const progress = steps.reduce((acc, s) => Math.max(acc, s.progress ?? 0), 0)

  return (
    <div className="progress-stepper" id="upload-progress">
      {/* Progress bar */}
      <div className="progress-bar-wrap" style={{ marginBottom: 12 }}>
        <div
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      {ALL_STEPS.map(({ step, label }) => {
        const isDone   = arrivedSteps.has(step)
        const isActive =
          !isDone &&
          steps.some((s) => STEP_MAP[s.step] === step)
        const status = isDone ? 'done' : isActive ? 'active' : 'pending'
        const matchedMsg = steps.findLast?.((s) => STEP_MAP[s.step] === step)?.message

        return (
          <div key={step} className={`step-item ${status}`}>
            <div className={`step-dot ${status}`}>
              {dotIcon(status)}
            </div>
            <div className="step-content">
              <div className={`step-message ${status}`}>
                {matchedMsg || label}
              </div>
            </div>
          </div>
        )
      })}

      {/* Error */}
      {hasError && (
        <div className="step-item error" style={{ marginTop: 4 }}>
          <div className="step-dot error">✕</div>
          <div className="step-content">
            <div className="step-message" style={{ color: 'var(--rose-400)' }}>
              {errorMsg}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
