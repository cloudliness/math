import { useState, useRef, useEffect } from 'react'
import './UploadPanel.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

export default function UploadPanel({ onUploadComplete }) {
    const [dragging, setDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [logs, setLogs] = useState([])
    const [activeFile, setActiveFile] = useState(localStorage.getItem('activeUpload') || null)
    const fileRef = useRef(null)
    const wsRef = useRef(null)

    // Check status on mount if we have an active file
    useEffect(() => {
        if (activeFile) {
            setUploading(true)
            checkStatus(activeFile)
        }
    }, [activeFile])

    const checkStatus = async (filename) => {
        try {
            const res = await fetch(`${API_URL}/upload/status/${filename}`)
            const data = await res.json()

            if (data.status === 'success') {
                setResult(data)
                setUploading(false)
                localStorage.removeItem('activeUpload')
                setActiveFile(null)
                onUploadComplete?.()
            } else if (data.status === 'error') {
                setError(data.error)
                setUploading(false)
                localStorage.removeItem('activeUpload')
                setActiveFile(null)
            } else if (data.status === 'processing') {
                // Still processing, poll again in 3s
                setTimeout(() => checkStatus(filename), 3000)
            } else {
                // Unknown status (maybe server restarted)
                setUploading(false)
                localStorage.removeItem('activeUpload')
                setActiveFile(null)
            }
        } catch (err) {
            // Server might be down, try again quietly
            setTimeout(() => checkStatus(filename), 5000)
        }
    }

    useEffect(() => {
        const wsUrl = API_URL.replace('http', 'ws')
        wsRef.current = new WebSocket(`${wsUrl}/ws/logs`)

        wsRef.current.onmessage = (event) => {
            const data = event.data
            // Intercept special completion token
            if (data.startsWith("COMPLETE|")) {
                const parts = data.split("|")
                if (parts[1] === activeFile) {
                    setResult({ filename: parts[1], chunks_indexed: parseInt(parts[2], 10) })
                    setUploading(false)
                    localStorage.removeItem('activeUpload')
                    setActiveFile(null)
                    onUploadComplete?.()
                }
            } else {
                setLogs(prev => [...prev, data])
            }
        }

        return () => {
            if (wsRef.current) wsRef.current.close()
        }
    }, [activeFile, onUploadComplete])

    const handleUpload = async (file) => {
        if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
            setError('Please select a PDF file.')
            return
        }

        setUploading(true)
        setError(null)
        setResult(null)
        setLogs([]) // Clear previous logs

        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            })

            if (!res.ok) {
                const errData = await res.json()
                throw new Error(errData.detail || 'Upload failed')
            }

            const data = await res.json()

            if (data.status === 'processing') {
                // Background task started
                localStorage.setItem('activeUpload', file.name)
                setActiveFile(file.name)
                // Start polling just in case WS misses the complete token
                checkStatus(file.name)
            } else {
                setResult(data)
                setUploading(false)
                onUploadComplete?.()
            }
        } catch (err) {
            setError(err.message)
            setUploading(false)
        }
    }

    const onDrop = (e) => {
        e.preventDefault()
        setDragging(false)
        const file = e.dataTransfer.files[0]
        handleUpload(file)
    }

    const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
    const onDragLeave = () => setDragging(false)

    return (
        <div className="upload-panel">
            <div className="upload-header">
                <div className="upload-header-icon">📤</div>
                <div>
                    <h2>Upload Documents</h2>
                    <span className="upload-header-sub">
                        Add PDF textbooks to expand the knowledge base
                    </span>
                </div>
            </div>

            <div className="upload-body">
                <div
                    className={`upload-dropzone ${dragging ? 'dragging' : ''} ${uploading ? 'uploading' : ''}`}
                    onDrop={onDrop}
                    onDragOver={onDragOver}
                    onDragLeave={onDragLeave}
                    onClick={() => !uploading && fileRef.current?.click()}
                >
                    <input
                        ref={fileRef}
                        type="file"
                        accept=".pdf"
                        onChange={e => handleUpload(e.target.files[0])}
                        hidden
                    />

                    {uploading ? (
                        <div className="upload-progress">
                            <div className="upload-spinner"></div>
                            <span className="upload-progress-text">Processing & indexing...</span>

                            <div className="upload-logs">
                                {logs.map((log, i) => (
                                    <div key={i} className="upload-log-item">
                                        <span className="log-time">{new Date().toLocaleTimeString()}</span>
                                        <span className="log-msg">{log}</span>
                                    </div>
                                ))}
                                {logs.length === 0 && <span className="upload-progress-sub">Checking ingestion status...</span>}
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="dropzone-icon">
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                                    <polyline points="17 8 12 3 7 8" />
                                    <line x1="12" y1="3" x2="12" y2="15" />
                                </svg>
                            </div>
                            <span className="dropzone-title">Drop your PDF here</span>
                            <span className="dropzone-sub">or click to browse</span>
                            <div className="dropzone-formats">
                                <span className="format-badge">PDF</span>
                                <span className="format-info">Textbooks, notes, papers</span>
                            </div>
                        </>
                    )}
                </div>

                {result && (
                    <div className="upload-result success">
                        <div className="result-icon">✅</div>
                        <div className="result-content">
                            <span className="result-title">{result.filename}</span>
                            <span className="result-detail">
                                {result.chunks_indexed} chunks indexed — ready for Q&A!
                            </span>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="upload-result error">
                        <div className="result-icon">❌</div>
                        <div className="result-content">
                            <span className="result-title">Upload Failed</span>
                            <span className="result-detail">{error}</span>
                        </div>
                    </div>
                )}

                <div className="upload-tips">
                    <h3>💡 Tips</h3>
                    <ul>
                        <li>PDFs with text (not scanned images) work best</li>
                        <li>Mathematical notation and LaTeX are preserved</li>
                        <li>Large files may take a few minutes to process</li>
                    </ul>
                </div>
            </div>
        </div>
    )
}
