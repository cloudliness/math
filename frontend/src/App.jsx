import { useState, useEffect } from 'react'
import ChatPanel from './components/ChatPanel'
import UploadPanel from './components/UploadPanel'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

function App() {
  const [documents, setDocuments] = useState([])
  const [activeDocuments, setActiveDocuments] = useState([])
  const [sessions, setSessions] = useState([])
  const [activeTab, setActiveTab] = useState('chat')
  const [activeSessionId, setActiveSessionId] = useState(localStorage.getItem('activeSessionId') || null)

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_URL}/documents`)
      const data = await res.json()
      const docs = data.documents || []

      setDocuments(docs)
      // Any new document is active by default. 
      // We merge with existing activeDocuments so we don't overwrite user choices
      setActiveDocuments(prev => {
        const activeSet = new Set(prev)
        const newActive = docs.filter(doc => !prev.includes(doc)) // if it wasn't tracked, make it active
        return [...prev, ...newActive]
      })
    } catch { /* backend might not be running */ }
  }

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_URL}/chat/session`)
      const data = await res.json()
      setSessions(data || [])
    } catch { /* backend might not be running */ }
  }

  const deleteSession = async (id, e) => {
    e.stopPropagation()
    try {
      await fetch(`${API_URL}/chat/session/${id}`, { method: 'DELETE' })
      if (activeSessionId === id) {
        setActiveSessionId(null)
        localStorage.removeItem('activeSessionId')
      }
      fetchSessions()
    } catch (err) {
      console.error(err)
    }
  }

  const deleteDocument = async (filename, e) => {
    e.stopPropagation()
    try {
      await fetch(`${API_URL}/documents/${filename}`, { method: 'DELETE' })
      setActiveDocuments(prev => prev.filter(doc => doc !== filename))
      fetchDocuments()
    } catch (err) {
      console.error("Failed to delete document:", err)
    }
  }

  const toggleDocument = (filename) => {
    setActiveDocuments(prev =>
      prev.includes(filename)
        ? prev.filter(doc => doc !== filename)
        : [...prev, filename]
    )
  }

  const handleSelectSession = (id) => {
    setActiveSessionId(id)
    setActiveTab('chat')
    localStorage.setItem('activeSessionId', id)
  }

  const handleNewChat = () => {
    setActiveSessionId(null)
    setActiveTab('chat')
    localStorage.removeItem('activeSessionId')
  }

  useEffect(() => {
    fetchDocuments()
    fetchSessions()
  }, [])

  return (
    <div className="app-container">
      {/* Animated background orbs */}
      <div className="bg-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <span>∑</span>
          </div>
          <div className="sidebar-brand-text">
            <span className="brand-name">MathFlow</span>
            <span className="brand-tag">AI Tutor</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`sidebar-link ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            id="nav-chat"
          >
            <div className="link-icon">💬</div>
            <div className="link-content">
              <span className="link-label">Chat</span>
              <span className="link-desc">Ask questions</span>
            </div>
          </button>
          <button
            className={`sidebar-link ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
            id="nav-upload"
          >
            <div className="link-icon">📤</div>
            <div className="link-content">
              <span className="link-label">Upload</span>
              <span className="link-desc">Add documents</span>
            </div>
          </button>
          <button className="sidebar-link" id="nav-graph">
            <div className="link-icon">🔗</div>
            <div className="link-content">
              <span className="link-label">Knowledge Graph</span>
              <span className="link-desc">Coming soon</span>
            </div>
          </button>
        </nav>

        <div className="sidebar-sessions">
          <div className="sidebar-docs-header">
            <span>💬 Chat History</span>
            <button className="new-chat-btn" onClick={handleNewChat}>+ New</button>
          </div>
          <div className="sessions-list">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${activeSessionId === session.id ? 'active' : ''}`}
                onClick={() => handleSelectSession(session.id)}
              >
                <div className="session-title">{session.title}</div>
                <button
                  className="session-delete"
                  onClick={(e) => deleteSession(session.id, e)}
                  title="Delete chat"
                >
                  ×
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <div className="doc-empty">No past chats</div>
            )}
          </div>
        </div>

        {/* Document pills */}
        <div className="sidebar-docs">
          <div className="sidebar-docs-header">
            <span>📚 Library</span>
            <span className="doc-count">{documents.length}</span>
          </div>
          {documents.map((doc, i) => (
            <div key={i} className="doc-pill">
              <input
                type="checkbox"
                className="doc-pill-checkbox"
                checked={activeDocuments.includes(doc)}
                onChange={() => toggleDocument(doc)}
                title="Toggle document context"
              />
              <span className="doc-pill-icon">📄</span>
              <span className="doc-pill-name">{doc.replace('.pdf', '')}</span>
              <button
                className="doc-pill-delete"
                onClick={(e) => deleteDocument(doc, e)}
                title="Delete document"
              >×</button>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="doc-empty">No documents yet</div>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className="status-dot"></span>
            <span>System Online</span>
          </div>
          <div className="sidebar-model">⚡ stepfun/3.5-flash</div>
        </div>
      </aside>

      <main className="main-content">
        {activeTab === 'chat' && (
          <ChatPanel
            sessionId={activeSessionId}
            activeDocuments={activeDocuments}
            onSessionCreated={(id) => {
              setActiveSessionId(id)
              localStorage.setItem('activeSessionId', id)
              fetchSessions()
            }}
          />
        )}
        {activeTab === 'upload' && <UploadPanel onUploadComplete={fetchDocuments} />}
      </main>
    </div>
  )
}

export default App
