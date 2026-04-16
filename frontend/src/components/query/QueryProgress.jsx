import React from 'react'
import useChatStore from '../../store/chatStore'

const STEP_CONFIG = {
  retrieval:          { label: 'Retrieval'       },
  retrieval_done:     { label: 'Đã truy xuất'    },
  evaluating:         {  label: 'Đánh giá context' },
  evaluation_done:    { label: 'Kết quả đánh giá' },
  web_search:         { label: 'Web Search'       },
  web_search_done:    { label: 'Web kết quả'      },
  context_sufficient: { label: 'Context đủ'       },
  generating:         {  label: 'Đang sinh trả lời' },
  answer:             { label: 'Hoàn thành'       },
  error:              { label: 'Lỗi'              },
}

function getStepClass(step, isLast) {
  if (step.step === 'error')   return 'error'
  if (step.step === 'answer')  return 'done'
  if (isLast)                  return 'active'
  return 'done'
}

export default function QueryProgress() {
  const { isQuerying, querySteps } = useChatStore()

  if (!isQuerying && querySteps.length === 0) return null

  const shouldShow =
    isQuerying ||
    querySteps.some((s) => s.step === 'error')

  if (!shouldShow) return null

  return (
    <div className="query-progress" id="query-progress-panel">
      <div className="query-progress-title">CoRAG Pipeline</div>
      {querySteps.map((step, idx) => {
        const isLast = idx === querySteps.length - 1
        const cfg = STEP_CONFIG[step.step] ?? { label: step.step }
        const cls = getStepClass(step, isLast)

        return (
          <div key={idx} className={`qstep ${cls} ${step.step === 'web_search' || step.step === 'web_search_done' ? 'web' : ''}`}>
            <span>{step.message || cfg.label}</span>
          </div>
        )
      })}
    </div>
  )
}
