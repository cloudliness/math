import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import './ChatPanel.css'

const API_URL = 'http://127.0.0.1:8000/api/v1'

export default function ChatPanel({ sessionId, onSessionCreated }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Load history when sessionId changes
  useEffect(() => {
    if (!sessionId) {
      setMessages([
        {
          role: 'assistant',
          content: 'Hello! I\'m your **discrete mathematics tutor**. Ask me anything about logic, proofs, sets, or any topic from the textbook. 📚',
          sources: []
        }
      ])
      return
    }

    const fetchHistory = async () => {
      setLoadingHistory(true)
      try {
        const res = await fetch(`${API_URL}/chat/session/${sessionId}`)
        if (res.ok) {
          const data = await res.json()
          setMessages(data.messages || [])
        }
      } catch (err) {
        console.error('Failed to load chat history', err)
      } finally {
        setLoadingHistory(false)
      }
    }
    fetchHistory()
  }, [sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const trimmed = input.trim()
    if (!trimmed || loading) return

    const userMsg = { role: 'user', content: trimmed, sources: [] }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    let currentSessionId = sessionId

    try {
      // Create session if it doesn't exist
      if (!currentSessionId) {
        const sessionRes = await fetch(`${API_URL}/chat/session`, { method: 'POST' })
        const sessionData = await sessionRes.json()
        currentSessionId = sessionData.id
        onSessionCreated?.(currentSessionId)
      }

      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, message: trimmed })
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const data = await response.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || 'I wasn\'t able to generate a response. Please try rephrasing.',
        sources: data.sources || []
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ Connection error: ${err.message}. Make sure the backend is running.`,
        sources: []
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header-icon">∑</div>
        <div>
          <h2>Discrete Math Tutor</h2>
          <span className="chat-header-sub">Powered by RAG • Logic & Proofs</span>
        </div>
      </div>

      <div className="chat-messages">
        {loadingHistory ? (
          <div className="chat-loading-history">Loading history...</div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`chat-msg chat-msg-${msg.role}`}>
              <div className="chat-msg-avatar">
                {msg.role === 'user' ? '👤' : '🧠'}
              </div>
              <div className="chat-msg-body">
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                >
                  {msg.content}
                </ReactMarkdown>
                {msg.sources?.length > 0 && (
                  <div className="chat-sources">
                    <span className="chat-sources-label">📖 Sources</span>
                    {msg.sources.map((s, i) => (
                      <div key={i} className="chat-source-item">
                        <span className="chat-source-score">
                          {(s.score * 100).toFixed(0)}% match
                        </span>
                        <span className="chat-source-text">{s.text}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-msg-avatar">🧠</div>
            <div className="chat-msg-body">
              <div className="chat-loading">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about discrete math..."
          rows={1}
          disabled={loading}
          id="chat-input"
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="chat-send-btn"
          id="send-button"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
