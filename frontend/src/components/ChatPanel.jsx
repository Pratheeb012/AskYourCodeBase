import React, { useRef, useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useChatStore, useRepoStore } from '../store'
import { chatAPI } from '../api'
import toast from 'react-hot-toast'

import { 
  Send, 
  Sparkles, 
  User, 
  Bot, 
  History, 
  ThumbsUp, 
  ThumbsDown, 
  FileCode, 
  Terminal,
  ShieldCheck,
  Zap,
  LayoutGrid,
  Search,
  Loader2
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

function ThinkingBubble() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="message"
    >
      <div className="message-avatar assistant"><Bot size={20} /></div>
      <div className="message-body">
        <div className="message-meta">
          <span className="message-author">Assistant</span>
        </div>
        <div className="thinking-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </motion.div>
  )
}

function Message({ msg, activeRepoId }) {
  const { setSelectedChunk } = useChatStore()
  const [feedback, setFeedback] = useState(msg.feedback || null)

  const handleFeedback = async (type) => {
    if (!msg.queryId || feedback) return
    try {
      await chatAPI.feedback(msg.queryId, type)
      setFeedback(type)
      toast.success(type === 'positive' ? 'Thanks for the feedback!' : 'Noted!')
    } catch {
      toast.error('Could not save feedback')
    }
  }

  const ts = msg.ts
    ? new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : ''

  if (msg.loading) return <ThinkingBubble />

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="message"
    >
      <div className={`message-avatar ${msg.role}`}>
        {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
      </div>
      <div className="message-body">
        <div className="message-meta">
          <span className="message-author">
            {msg.role === 'user' ? 'You' : 'Assistant'}
          </span>
          <span className="message-time">{ts}</span>
          {msg.tokensUsed && (
            <span className="navbar-badge" style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
              <Zap size={10} /> {msg.tokensUsed} tokens
            </span>
          )}
        </div>

        {msg.rewrittenQuery && msg.rewrittenQuery !== msg.content && (
          <div className="query-rewrite-strip">
            <Search size={12} style={{ marginRight: '8px' }} />
            Optimized query: {msg.rewrittenQuery}
          </div>
        )}

        <div className="message-text">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '')
                const language = match ? match[1] : 'text'
                
                return !inline ? (
                  <div className="code-block-wrapper" style={{ margin: '12px 0', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-default)' }}>
                    {match && <div className="code-block-lang" style={{ background: 'var(--bg-active)', padding: '4px 12px', fontSize: '10px', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-default)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{language}</div>}
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={language}
                      PreTag="div"
                      customStyle={{ margin: 0, padding: '16px', fontSize: '13px', background: 'transparent' }}
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className={className} {...props}>{children}</code>
                )
              },
            }}
          >
            {msg.content}
          </ReactMarkdown>
        </div>

        {msg.references?.length > 0 && (
          <div className="references">
            <div className="references-title">Source Context</div>
            <div className="references-list">
              {msg.references.map((ref, i) => (
                <button
                  key={i}
                  className="ref-chip"
                  onClick={() => setSelectedChunk(ref)}
                  title={ref.file_path}
                >
                  <FileCode size={14} /> {ref.file_path.split('/').pop()}
                  <span className="ref-chip-score">{(ref.score * 100).toFixed(0)}%</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {msg.role === 'assistant' && !msg.error && msg.queryId && (
          <div className="message-feedback">
            <button
              className={`feedback-btn ${feedback === 'positive' ? 'active-pos' : ''}`}
              onClick={() => handleFeedback('positive')}
              disabled={!!feedback}
            ><ThumbsUp size={14} /></button>
            <button
              className={`feedback-btn ${feedback === 'negative' ? 'active-neg' : ''}`}
              onClick={() => handleFeedback('negative')}
              disabled={!!feedback}
            ><ThumbsDown size={14} /></button>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function WelcomeScreen({ onSuggestion }) {
  const { activeRepo } = useRepoStore()

  const suggestions = [
    { icon: <LayoutGrid size={24} />, title: 'Architecture', desc: 'Project structure overview', query: 'Explain the overall architecture of this codebase' },
    { icon: <ShieldCheck size={24} />, title: 'Security', desc: 'Auth and data protection', query: 'How is security and authentication handled?' },
    { icon: <Zap size={24} />, title: 'Entry Points', desc: 'Where the app starts', query: 'What are the main entry points of the application?' },
    { icon: <History size={24} />, title: 'Data Flow', desc: 'Models and database', query: 'Explain the data models and how data flows through the app' },
  ]

  return (
    <div className="welcome-screen">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="welcome-hero"
      >
        <div className="navbar-logo-icon" style={{ fontSize: '64px', marginBottom: '24px' }}>🧠</div>
        <h1 className="welcome-title">RepoMind</h1>
        <p className="welcome-subtitle">
          {activeRepo
            ? `Analyzing ${activeRepo.name} with ${activeRepo.chunk_count} code segments indexed.`
            : 'Select a repository from the workspace to begin exploration.'}
        </p>
      </motion.div>

      {activeRepo && (
        <div className="welcome-cards">
          {suggestions.map((s, i) => (
            <motion.button
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="welcome-card"
              onClick={() => onSuggestion(s.query)}
            >
              <div className="welcome-card-icon">{s.icon}</div>
              <div className="welcome-card-title">{s.title}</div>
              <div className="welcome-card-desc">{s.desc}</div>
            </motion.button>
          ))}
        </div>
      )}

      {!activeRepo && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="welcome-empty"
        >
          <p style={{ color: 'var(--text-muted)', fontSize: '15px' }}>Connect a GitHub repository or upload a ZIP archive to start querying your codebase.</p>
        </motion.div>
      )}
    </div>
  )
}

export default function ChatPanel() {
  const { messages, loading, sendQuery, clearMessages } = useChatStore()
  const { activeRepo } = useRepoStore()
  const [input, setInput] = useState('')
  const [rewrite, setRewrite] = useState(true)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    const q = input.trim()
    if (!q || loading || !activeRepo) return
    setInput('')
    textareaRef.current.style.height = 'auto'
    await sendQuery(q, activeRepo.id, rewrite)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaChange = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
  }

  const handleSuggestion = (query) => {
    if (!activeRepo || loading) return
    sendQuery(query, activeRepo.id, rewrite)
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestion={handleSuggestion} />
        ) : (
          messages.map((msg) => (
            <Message key={msg.id} msg={msg} activeRepoId={activeRepo?.id} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            id="chat-input"
            ref={textareaRef}
            className="chat-textarea"
            rows={1}
            placeholder={
              activeRepo
                ? `Ask about ${activeRepo.name}...`
                : 'Choose a repository to start...'
            }
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            disabled={!activeRepo || loading}
          />
          <button
            id="chat-send-btn"
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!activeRepo || loading || !input.trim()}
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
          </button>
        </div>
        <div className="chat-options">
          <label className="chat-option-toggle">
            <input
              type="checkbox"
              checked={rewrite}
              onChange={(e) => setRewrite(e.target.checked)}
            />
            <Sparkles size={12} style={{ color: 'var(--accent-primary)' }} /> AI Query Refinement
          </label>
          <span className="navbar-badge" style={{ marginLeft: 'auto', opacity: 0.8, display: 'flex', gap: '6px', alignItems: 'center' }}>
            <Terminal size={12} /> Groq Llama3
          </span>
        </div>
      </div>
    </div>
  )
}
