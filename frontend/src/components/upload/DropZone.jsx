import React, { useCallback, useRef, useState } from 'react'
import useChatStore from '../../store/chatStore'
import { uploadFile } from '../../services/api'
import ProgressStepper from './ProgressStepper'

const ACCEPTED = '.pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp,.docx'

const UPLOAD_STEPS_ORDER = [
  'reading_file',
  'ocr',
  'ocr_done',
  'chunking',
  'chunking_done',
  'embedding',
  'indexing',
  'done',
]

export default function DropZone() {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef()
  const {
    isUploading,
    uploadSteps,
    setIsUploading,
    pushUploadStep,
    resetUpload,
    addDocument,
    setVectorCount,
  } = useChatStore()

  const handleFile = useCallback(
    async (file) => {
      if (!file) return
      resetUpload()
      setIsUploading(true)

      await uploadFile({
        file,
        onEvent: (data) => {
          const status =
            data.step === 'done'
              ? 'done'
              : data.step === 'error'
              ? 'error'
              : UPLOAD_STEPS_ORDER.indexOf(data.step) >=
                UPLOAD_STEPS_ORDER.indexOf('done')
              ? 'done'
              : 'active'

          pushUploadStep({ ...data, status })

          if (data.step === 'done') {
            addDocument({
              id: Date.now(),
              name: file.name,
              chunks: data.chunk_count ?? '?',
              vectors: data.total_vectors ?? '?',
              uploadedAt: new Date().toLocaleTimeString('vi-VN'),
            })
            if (data.total_vectors != null) setVectorCount(data.total_vectors)
            setIsUploading(false)
          }

          if (data.step === 'error') {
            setIsUploading(false)
          }
        },
        onError: (err) => {
          pushUploadStep({ step: 'error', message: `Lỗi: ${err.message}`, progress: 0, status: 'error' })
          setIsUploading(false)
        },
      })
    },
    [resetUpload, setIsUploading, pushUploadStep, addDocument, setVectorCount]
  )

  const onInputChange = (e) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''   // allow re-uploading same file
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  return (
    <div className="upload-section">
      {/* Drop Zone */}
      <div
        id="upload-dropzone"
        className={`dropzone ${dragOver ? 'drag-over' : ''} ${isUploading ? 'uploading' : ''}`}
        onClick={() => !isUploading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        style={{ cursor: isUploading ? 'default' : 'pointer', pointerEvents: isUploading ? 'none' : 'auto' }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          onChange={onInputChange}
          style={{ display: 'none' }}
          id="file-input"
        />

        <div className="dropzone-title">
          {isUploading ? 'Đang xử lý…' : 'Upload tài liệu'}
        </div>
        <div className="dropzone-hint">
          {isUploading
            ? 'Vui lòng chờ'
            : 'PDF, DOCX hoặc Hình ảnh • Kéo thả hoặc click'}
        </div>

      </div>

      {/* Progress */}
      {uploadSteps.length > 0 && <ProgressStepper steps={uploadSteps} />}
    </div>
  )
}
