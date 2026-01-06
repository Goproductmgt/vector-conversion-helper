import { useState, useCallback, useRef } from 'react'
import { Upload, Zap, Globe, Printer, FileText, Download, ArrowRight, Check, AlertCircle, Loader2, RotateCcw, Mail, X, Send } from 'lucide-react'
import './index.css'

type AppState = 'idle' | 'uploading' | 'processing' | 'complete' | 'error'

interface JobResult {
  job_id: string
  status: string
  files?: {
    original?: string
    svg?: string
    eps?: string
    pdf?: string
  }
  metadata?: {
    original_format?: string
    original_size_bytes?: number
    processing_time_seconds?: number
  }
  error_code?: string
  error_message?: string
}

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_FILE_TYPE: "This file type isn't supported. Please use JPG, PNG, or HEIC.",
  FILE_TOO_LARGE: "This file is too large. Maximum size is 10MB.",
  TOO_COMPLEX: "This image is too complex for automatic conversion. Works best with simple logos and icons.",
  PROCESSING_FAILED: "Something went wrong. Please try again or use a different image.",
  VECTORIZATION_FAILED: "Couldn't vectorize this image. Try a simpler graphic.",
  NETWORK_ERROR: "Couldn't connect to the server. Please check your internet and try again.",
  TIMEOUT: "Processing took too long. Please try a simpler image.",
}

function App() {
  const [state, setState] = useState<AppState>('idle')
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [result, setResult] = useState<JobResult | null>(null)
  const [error, setError] = useState<string>('')
  const [isDragging, setIsDragging] = useState(false)
  const [originalPreview, setOriginalPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailAddress, setEmailAddress] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('svg')
  const [emailSending, setEmailSending] = useState(false)
  const [emailStatus, setEmailStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [emailError, setEmailError] = useState('')

  const getApiUrl = () => ''

  const handleFile = useCallback(async (file: File) => {
    const validTypes = ['image/jpeg', 'image/png', 'image/heic']
    if (!validTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.heic')) {
      setError(ERROR_MESSAGES.INVALID_FILE_TYPE)
      setState('error')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError(ERROR_MESSAGES.FILE_TOO_LARGE)
      setState('error')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => setOriginalPreview(e.target?.result as string)
    reader.readAsDataURL(file)

    setState('uploading')
    setProgress(5)
    setStage('Uploading image...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${getApiUrl()}/api/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        const errorDetail = data.detail || ''
        if (errorDetail.includes('file type') || errorDetail.includes('INVALID_FILE_TYPE')) {
          throw new Error('INVALID_FILE_TYPE')
        } else if (errorDetail.includes('large') || errorDetail.includes('FILE_TOO_LARGE')) {
          throw new Error('FILE_TOO_LARGE')
        }
        throw new Error('PROCESSING_FAILED')
      }

      const uploadResult = await response.json()
      setState('processing')
      setProgress(10)
      setStage('Analyzing image...')
      await pollJobStatus(uploadResult.job_id)
    } catch (err) {
      const errorCode = err instanceof Error ? err.message : 'PROCESSING_FAILED'
      setError(ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.PROCESSING_FAILED)
      setState('error')
    }
  }, [])

  const pollJobStatus = async (jobId: string): Promise<void> => {
    return new Promise((resolve) => {
      let attempts = 0
      const maxAttempts = 60
      let isResolved = false

      const poll = async () => {
        if (isResolved) return

        try {
          const response = await fetch(`${getApiUrl()}/api/status/${jobId}`)
          if (!response.ok) throw new Error('PROCESSING_FAILED')

          const status = await response.json()
          if (status.progress) setProgress(status.progress)
          if (status.stage) setStage(status.stage)

          if (status.status === 'completed') {
            isResolved = true
            const resultResponse = await fetch(`${getApiUrl()}/api/result/${jobId}`)
            const resultData = await resultResponse.json()
            setResult(resultData)
            setProgress(100)
            setStage('Done!')
            setState('complete')
            resolve()
            return
          }

          if (status.status === 'failed') {
            isResolved = true
            const errorCode = status.error_code || 'PROCESSING_FAILED'
            setError(ERROR_MESSAGES[errorCode] || status.error_message || ERROR_MESSAGES.PROCESSING_FAILED)
            setState('error')
            resolve()
            return
          }

          attempts++
          if (attempts >= maxAttempts) {
            isResolved = true
            setError(ERROR_MESSAGES.TIMEOUT)
            setState('error')
            resolve()
            return
          }

          setTimeout(poll, 1000)
        } catch {
          if (!isResolved) {
            isResolved = true
            setError(ERROR_MESSAGES.NETWORK_ERROR)
            setState('error')
            resolve()
          }
        }
      }
      poll()
    })
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleClickUpload = () => fileInputRef.current?.click()

  const resetApp = () => {
    setState('idle')
    setProgress(0)
    setStage('')
    setResult(null)
    setError('')
    setOriginalPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const getDownloadUrl = (path: string) => `${getApiUrl()}${path}`

  const downloadFile = async (path: string, filename: string) => {
    try {
      const response = await fetch(getDownloadUrl(path))
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const openEmailModal = () => {
    setShowEmailModal(true)
    setEmailStatus('idle')
    setEmailError('')
  }

  const closeEmailModal = () => {
    setShowEmailModal(false)
    setEmailAddress('')
    setEmailStatus('idle')
    setEmailError('')
  }

  const sendEmail = async () => {
    if (!emailAddress || !result?.job_id) return

    setEmailSending(true)
    setEmailStatus('idle')
    setEmailError('')

    try {
      const response = await fetch(`${getApiUrl()}/api/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: result.job_id,
          recipient_email: emailAddress,
          file_format: selectedFormat,
        }),
      })

      if (response.ok) {
        setEmailStatus('success')
      } else {
        const data = await response.json().catch(() => ({}))
        setEmailError(data.detail || 'Failed to send email')
        setEmailStatus('error')
      }
    } catch {
      setEmailError('Could not connect to email service')
      setEmailStatus('error')
    } finally {
      setEmailSending(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 flex flex-col">
      <main className="flex-grow px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-4">
              <span className="text-emerald-600">Go</span>Vector
            </h1>
            <p className="text-2xl md:text-3xl text-gray-600 mb-6">
              Scale up. Never blur.
            </p>
            <div className="inline-flex items-center gap-3 bg-emerald-50 text-emerald-700 px-6 py-3 rounded-full text-lg font-medium">
              <Zap size={22} className="text-emerald-600" />
              Free conversion in under 10 seconds
            </div>
          </div>

          {state === 'idle' && (
            <>
              <div
                className={`border-2 border-dashed rounded-3xl p-16 text-center cursor-pointer transition-all mb-10 ${
                  isDragging
                    ? 'border-emerald-500 bg-emerald-50'
                    : 'border-gray-300 hover:border-emerald-400 hover:bg-white bg-white'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleClickUpload}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleClickUpload()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,.heic,image/jpeg,image/png,image/heic"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <Upload size={64} className="mx-auto mb-6 text-gray-400" strokeWidth={1.5} />
                <p className="text-2xl font-semibold text-gray-800 mb-3">
                  Drop your image here
                </p>
                <p className="text-xl text-gray-500 mb-4">or click to browse</p>
                <p className="text-base text-gray-400">
                  JPG, PNG, or HEIC up to 10MB
                </p>
              </div>

              <div className="bg-white rounded-3xl p-10 shadow-sm border border-gray-100 mb-10">
                <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
                  Your files, ready for anything
                </h2>
                <div className="grid grid-cols-3 gap-8 text-center">
                  <div className="p-6">
                    <Globe size={48} className="mx-auto mb-4 text-emerald-600" strokeWidth={1.5} />
                    <p className="text-xl font-semibold text-gray-800 mb-2">SVG</p>
                    <p className="text-base text-gray-500">
                      Web &amp; apps. Infinitely scalable, tiny file size.
                    </p>
                  </div>
                  <div className="p-6">
                    <Printer size={48} className="mx-auto mb-4 text-emerald-600" strokeWidth={1.5} />
                    <p className="text-xl font-semibold text-gray-800 mb-2">EPS</p>
                    <p className="text-base text-gray-500">
                      Print industry standard. Works with any printer.
                    </p>
                  </div>
                  <div className="p-6">
                    <FileText size={48} className="mx-auto mb-4 text-emerald-600" strokeWidth={1.5} />
                    <p className="text-xl font-semibold text-gray-800 mb-2">PDF</p>
                    <p className="text-base text-gray-500">
                      Universal format. Share with anyone, anywhere.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-emerald-50 rounded-3xl p-10 border border-emerald-100">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Why go vector?
                </h2>
                <div className="space-y-5 text-lg text-gray-700">
                  <div className="flex gap-4">
                    <ArrowRight size={24} className="text-emerald-600 flex-shrink-0 mt-1" />
                    <p><strong>Scale without limits</strong> — Print a business card or a billboard. Same file, perfect quality.</p>
                  </div>
                  <div className="flex gap-4">
                    <ArrowRight size={24} className="text-emerald-600 flex-shrink-0 mt-1" />
                    <p><strong>Tiny file sizes</strong> — Vectors describe shapes mathematically, not pixel by pixel.</p>
                  </div>
                  <div className="flex gap-4">
                    <ArrowRight size={24} className="text-emerald-600 flex-shrink-0 mt-1" />
                    <p><strong>Edit everything</strong> — Change colors, resize elements, tweak details in any design app.</p>
                  </div>
                </div>
                <p className="text-base text-gray-500 mt-6">
                  Best for: logos, icons, illustrations, graphics, and line art
                </p>
              </div>
            </>
          )}

          {(state === 'uploading' || state === 'processing') && (
            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-12 max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <Loader2 size={64} className="mx-auto mb-6 text-emerald-600 animate-spin" strokeWidth={1.5} />
                <p className="text-2xl font-semibold text-gray-800">Converting your image...</p>
              </div>
              <div className="mb-6">
                <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="flex justify-between mt-3 text-lg">
                  <span className="text-gray-600">{stage}</span>
                  <span className="text-gray-500">{progress}%</span>
                </div>
              </div>
            </div>
          )}

          {state === 'complete' && result && (
            <div className="bg-white rounded-3xl shadow-sm border border-gray-200 p-12 max-w-2xl mx-auto">
              <div className="text-center mb-8">
                <Check size={64} className="mx-auto mb-4 text-emerald-600" strokeWidth={1.5} />
                <h2 className="text-3xl font-bold text-gray-900">
                  Vectorized!
                </h2>
                <p className="text-lg text-gray-500 mt-2">Your files are ready to download or email</p>
              </div>

              {originalPreview && result.files?.svg && (
                <div className="grid grid-cols-2 gap-6 mb-8">
                  <div className="text-center">
                    <p className="text-sm text-gray-500 mb-3 uppercase tracking-wide font-medium">Before</p>
                    <div className="border-2 rounded-2xl p-4 bg-gray-50 h-40 flex items-center justify-center">
                      <img src={originalPreview} alt="Original" className="max-h-full max-w-full object-contain" />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-500 mb-3 uppercase tracking-wide font-medium">After</p>
                    <div className="border-2 rounded-2xl p-4 bg-gray-50 h-40 flex items-center justify-center">
                      <img src={getDownloadUrl(result.files.svg)} alt="Vectorized" className="max-h-full max-w-full object-contain" />
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-3 gap-4 mb-6">
                {result.files?.svg && (
                  <button
                    onClick={() => downloadFile(result.files!.svg!, 'govector-output.svg')}
                    className="flex flex-col items-center gap-3 px-6 py-6 bg-emerald-500 hover:bg-emerald-600 text-white rounded-2xl font-semibold text-lg transition-colors"
                  >
                    <Download size={28} />
                    <span>SVG</span>
                  </button>
                )}
                {result.files?.eps && (
                  <button
                    onClick={() => downloadFile(result.files!.eps!, 'govector-output.eps')}
                    className="flex flex-col items-center gap-3 px-6 py-6 bg-emerald-500 hover:bg-emerald-600 text-white rounded-2xl font-semibold text-lg transition-colors"
                  >
                    <Download size={28} />
                    <span>EPS</span>
                  </button>
                )}
                {result.files?.pdf && (
                  <button
                    onClick={() => downloadFile(result.files!.pdf!, 'govector-output.pdf')}
                    className="flex flex-col items-center gap-3 px-6 py-6 bg-emerald-500 hover:bg-emerald-600 text-white rounded-2xl font-semibold text-lg transition-colors"
                  >
                    <Download size={28} />
                    <span>PDF</span>
                  </button>
                )}
              </div>

              <button
                onClick={openEmailModal}
                className="w-full py-4 bg-gray-100 hover:bg-gray-200 rounded-2xl text-gray-700 font-semibold text-lg transition-colors flex items-center justify-center gap-3 mb-6"
              >
                <Mail size={22} />
                Email this file
              </button>

              {result.metadata?.processing_time_seconds && (
                <p className="text-center text-base text-gray-400 mb-6">
                  Converted in {result.metadata.processing_time_seconds.toFixed(1)} seconds
                </p>
              )}

              <button
                onClick={resetApp}
                className="w-full py-4 border-2 border-gray-200 rounded-2xl text-gray-700 hover:bg-gray-50 font-semibold text-lg transition-colors flex items-center justify-center gap-3"
              >
                <RotateCcw size={22} />
                Convert another image
              </button>
            </div>
          )}

          {state === 'error' && (
            <div className="bg-white rounded-3xl shadow-sm border border-red-100 p-12 max-w-2xl mx-auto">
              <div className="text-center">
                <AlertCircle size={64} className="mx-auto mb-6 text-red-500" strokeWidth={1.5} />
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Couldn't convert this one
                </h2>
                <p className="text-lg text-gray-600 mb-4">{error}</p>
                <p className="text-base text-gray-500 mb-8">
                  Tip: Simple logos, icons, and graphics work best
                </p>
                <button
                  onClick={resetApp}
                  className="px-8 py-4 bg-emerald-500 hover:bg-emerald-600 text-white rounded-2xl font-semibold text-lg transition-colors inline-flex items-center gap-3"
                >
                  <RotateCcw size={22} />
                  Try a different image
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {showEmailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Email your file</h3>
              <button onClick={closeEmailModal} className="text-gray-400 hover:text-gray-600">
                <X size={24} />
              </button>
            </div>

            {emailStatus === 'success' ? (
              <div className="text-center py-8">
                <Check size={48} className="mx-auto mb-4 text-emerald-600" />
                <p className="text-xl font-semibold text-gray-900 mb-2">Sent!</p>
                <p className="text-gray-500">Check your inbox at {emailAddress}</p>
                <button
                  onClick={closeEmailModal}
                  className="mt-6 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold transition-colors"
                >
                  Done
                </button>
              </div>
            ) : (
              <>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email address</label>
                  <input
                    type="email"
                    value={emailAddress}
                    onChange={(e) => setEmailAddress(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-lg focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">File format</label>
                  <div className="grid grid-cols-3 gap-3">
                    {result?.files?.svg && (
                      <button
                        onClick={() => setSelectedFormat('svg')}
                        className={`py-3 rounded-xl font-semibold text-lg transition-colors ${
                          selectedFormat === 'svg'
                            ? 'bg-emerald-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        SVG
                      </button>
                    )}
                    {result?.files?.eps && (
                      <button
                        onClick={() => setSelectedFormat('eps')}
                        className={`py-3 rounded-xl font-semibold text-lg transition-colors ${
                          selectedFormat === 'eps'
                            ? 'bg-emerald-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        EPS
                      </button>
                    )}
                    {result?.files?.pdf && (
                      <button
                        onClick={() => setSelectedFormat('pdf')}
                        className={`py-3 rounded-xl font-semibold text-lg transition-colors ${
                          selectedFormat === 'pdf'
                            ? 'bg-emerald-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        PDF
                      </button>
                    )}
                  </div>
                </div>

                {emailStatus === 'error' && (
                  <div className="mb-6 p-4 bg-red-50 rounded-xl text-red-700">
                    {emailError}
                  </div>
                )}

                <button
                  onClick={sendEmail}
                  disabled={!emailAddress || emailSending}
                  className="w-full py-4 bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-xl font-semibold text-lg transition-colors flex items-center justify-center gap-3"
                >
                  {emailSending ? (
                    <>
                      <Loader2 size={22} className="animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send size={22} />
                      Send file
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      <footer className="py-8 text-center border-t border-gray-200 bg-white">
        <p className="text-base text-gray-500">
          A free tool from{' '}
          <a
            href="https://goproductmgt.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-600 hover:text-emerald-700 font-semibold"
          >
            GoProductmgt
          </a>
        </p>
        <p className="text-sm text-gray-400 mt-2">
          No signup required. Your files stay private.
        </p>
      </footer>
    </div>
  )
}

export default App
