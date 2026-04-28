import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useChatStore, useRepoStore } from '../store'
import { repoAPI, chatAPI } from '../api'
import toast from 'react-hot-toast'

import { 
  FileText, 
  SearchCode, 
  Network, 
  BarChart3, 
  FileCode, 
  AlertCircle, 
  CheckCircle2, 
  Info,
  ChevronRight,
  Maximize2,
  Download,
  Loader2,
  Sparkles
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

function CodeViewer({ chunk }) {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="code-viewer-container"
    >
      <div className="code-viewer-header">
        <div className="code-viewer-file">
          <FileCode size={20} className="file-icon" />
          <div className="file-info">
            <div className="file-name">{chunk.file_path.split('/').pop()}</div>
            <div className="file-path">{chunk.file_path}</div>
          </div>
        </div>
        <div className="code-viewer-stats">
          <span className="stat-badge">Lines {chunk.start_line}–{chunk.end_line}</span>
          <span className="stat-badge">{chunk.language}</span>
          <span className="stat-badge highlight">{(chunk.score * 100).toFixed(0)}% Relevance</span>
        </div>
      </div>
      <div className="code-viewer-content">
        <SyntaxHighlighter
          language={chunk.language || 'text'}
          style={vscDarkPlus}
          showLineNumbers
          startingLineNumber={chunk.start_line}
          customStyle={{
            margin: 0,
            background: 'transparent',
            fontSize: '13px',
            lineHeight: '1.6',
            fontFamily: 'var(--font-mono)'
          }}
          lineNumberStyle={{ color: 'var(--text-muted)', minWidth: '40px', paddingRight: '16px', fontSize: '11px' }}
        >
          {chunk.content}
        </SyntaxHighlighter>
      </div>
    </motion.div>
  )
}

function AnalysisTab({ repoId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await repoAPI.getAnalysis(repoId)
      setData(res.data)
    } catch {
      toast.error('Could not load analysis')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (repoId) { setData(null); load() }
  }, [repoId])

  if (loading) return (
    <div className="sidebar-state-msg" style={{ height: '100%', justifyContent: 'center' }}>
      <Loader2 className="animate-spin" size={32} style={{ color: 'var(--accent-primary)', marginBottom: '16px' }} />
      <p>Running deep static analysis...</p>
    </div>
  )

  if (!data) return (
    <div className="sidebar-state-msg" style={{ height: '100%', justifyContent: 'center' }}>
      <button className="btn btn-primary" onClick={load}>
        <SearchCode size={18} /> Start Analysis
      </button>
    </div>
  )

  const severityOrder = { error: 0, warning: 1, info: 2 }
  const sorted = [...(data.issues || [])].sort((a, b) =>
    (severityOrder[a.severity] || 9) - (severityOrder[b.severity] || 9)
  )

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="analysis-container"
    >
      <div className="analysis-summary">
        <div className="stat-card">
          <div className="stat-label">Total Findings</div>
          <div className="stat-value">{data.total_issues}</div>
        </div>
        <div className="stat-card" style={{ borderLeft: '3px solid var(--error)' }}>
          <div className="stat-label">Critical Issues</div>
          <div className="stat-value" style={{ color: 'var(--error)' }}>{data.by_severity?.error || 0}</div>
        </div>
      </div>
      <div className="issue-list">
        {sorted.map((issue, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`issue-item`}
            style={{ borderLeft: `3px solid var(--${issue.severity === 'error' ? 'error' : issue.severity === 'warning' ? 'warning' : 'info'})` }}
          >
            <div className="issue-header">
              <span className="issue-pos">{issue.file_path.split('/').pop()}:{issue.line}</span>
              <span className={`issue-tag ${issue.severity}`}>{issue.severity}</span>
            </div>
            <div className="issue-msg">{issue.message}</div>
          </motion.div>
        ))}
        {sorted.length === 0 && (
          <div className="sidebar-state-msg">
            <CheckCircle2 size={48} style={{ color: 'var(--success)', opacity: 0.5, marginBottom: '16px' }} />
            <p>Perfect health! No issues detected.</p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function ArchitectureTab({ repoId }) {
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await chatAPI.architecture(repoId)
      setSummary(res.data.summary)
    } catch {
      toast.error('Failed to generate summary')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (repoId && !summary) load()
  }, [repoId])

  return (
    <div className="architecture-container">
      {!summary && !loading && (
        <div className="sidebar-state-msg" style={{ height: '100%', justifyContent: 'center', marginTop: '100px' }}>
          <Info size={48} style={{ opacity: 0.2, marginBottom: '24px' }} />
          <p style={{ marginBottom: '24px' }}>No overview generated yet.</p>
          <button className="btn btn-primary" onClick={load}>
            <Sparkles size={18} /> Retry Generation
          </button>
        </div>
      )}
      {loading && (
        <div className="sidebar-state-msg" style={{ height: '100%', justifyContent: 'center', marginTop: '100px' }}>
          <Loader2 className="animate-spin" size={32} style={{ color: 'var(--accent-primary)', marginBottom: '16px' }} />
          <p>Scanning codebase and synthesizing structure...</p>
        </div>
      )}
      {summary && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="message-text"
          style={{ padding: '24px' }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary}</ReactMarkdown>
        </motion.div>
      )}
    </div>
  )
}

function DependencyTab({ repoId }) {
  const [graph, setGraph] = useState(null)
  const [loading, setLoading] = useState(false)
  const [positions, setPositions] = useState({})
  const containerRef = useRef(null)

  const load = async () => {
    setLoading(true)
    try {
      const res = await repoAPI.getDependencies(repoId)
      const data = res.data
      const nodes = data.nodes || []
      const w = containerRef.current?.clientWidth || 500
      const h = containerRef.current?.clientHeight || 600
      const r = Math.min(w, h) * 0.35
      const cx = w / 2
      const cy = h / 2
      const pos = {}
      nodes.forEach((n, i) => {
        const angle = (2 * Math.PI * i) / nodes.length
        pos[n] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }
      })
      setPositions(pos)
      setGraph(data)
    } catch {
      toast.error('Failed to load graph')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (repoId && !graph) load()
  }, [repoId])

  const shortName = (path) => path.split('/').pop().replace('.py', '').replace('.js', '').replace('.jsx', '')

  if (loading) return (
    <div className="sidebar-state-msg" style={{ height: '100%', justifyContent: 'center' }}>
      <Loader2 className="animate-spin" size={32} />
    </div>
  )

  if (!graph) return (
    <div className="sidebar-state-msg" style={{ height: '100%', justifyContent: 'center', marginTop: '100px' }}>
      <Network size={48} style={{ opacity: 0.2, marginBottom: '24px' }} />
      <p style={{ marginBottom: '24px' }}>Failed to map module dependencies.</p>
      <button className="btn btn-secondary" onClick={load}>
        <Maximize2 size={16} /> Retry Visualization
      </button>
    </div>
  )

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      ref={containerRef} 
      className="dep-container"
      style={{ height: '600px', position: 'relative', overflow: 'hidden', background: '#050506' }}
    >
      <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
        <defs>
          <linearGradient id="edge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.2" />
            <stop offset="100%" stopColor="var(--accent-secondary)" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        {(graph.edges || []).map((edge, i) => {
          const s = positions[edge.from]; const t = positions[edge.to]
          if (!s || !t) return null
          return (
            <motion.line 
              key={i} 
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              x1={s.x} y1={s.y} x2={t.x} y2={t.y} 
              stroke="url(#edge-grad)" 
              strokeWidth="1.5" 
            />
          )
        })}
      </svg>
      {(graph.nodes || []).map((node, i) => {
        const pos = positions[node]
        if (!pos) return null
        return (
          <motion.div 
            key={node} 
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.02 }}
            className="dep-node" 
            style={{ 
              left: pos.x, 
              top: pos.y, 
              position: 'absolute',
              transform: 'translate(-50%, -50%)',
              padding: '6px 12px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-full)',
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              whiteSpace: 'nowrap',
              boxShadow: '0 4px 10px rgba(0,0,0,0.3)'
            }}
          >
            {shortName(node)}
          </motion.div>
        )
      })}
    </motion.div>
  )
}

export default function CodePanel() {
  const { selectedChunk } = useChatStore()
  const { activeRepo } = useRepoStore()
  const [activeTab, setActiveTab] = useState('code')

  const tabs = [
    { id: 'code', label: 'Source', icon: <FileText size={14} /> },
    { id: 'analysis', label: 'Analysis', icon: <SearchCode size={14} /> },
    { id: 'architecture', label: 'Structure', icon: <BarChart3 size={14} /> },
    { id: 'deps', label: 'Graph', icon: <Network size={14} /> },
  ]

  return (
    <aside className="code-panel">
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      <div className="code-panel-content">
        <AnimatePresence mode="wait">
          {activeTab === 'code' && (
            selectedChunk ? (
              <CodeViewer chunk={selectedChunk} key={selectedChunk.file_path + selectedChunk.start_line} />
            ) : (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="sidebar-state-msg" 
                style={{ height: '100%', justifyContent: 'center' }}
              >
                <div style={{ fontSize: '48px', marginBottom: '24px', opacity: 0.2 }}>📂</div>
                <p style={{ fontSize: '15px', color: 'var(--text-muted)' }}>Select a code reference from the chat<br />to preview the source implementation.</p>
              </motion.div>
            )
          )}

          {activeTab === 'analysis' && activeRepo && (
            <AnalysisTab repoId={activeRepo.id} key={activeRepo.id} />
          )}

          {activeTab === 'architecture' && activeRepo && (
            <ArchitectureTab repoId={activeRepo.id} key={activeRepo.id} />
          )}

          {activeTab === 'deps' && activeRepo && (
            <DependencyTab repoId={activeRepo.id} key={activeRepo.id} />
          )}

          {!activeRepo && activeTab !== 'code' && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="sidebar-state-msg"
              style={{ height: '100%', justifyContent: 'center' }}
            >
              <Info size={32} style={{ opacity: 0.3, marginBottom: '16px' }} />
              <span>Select a repository to view insights.</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </aside>
  )
}
