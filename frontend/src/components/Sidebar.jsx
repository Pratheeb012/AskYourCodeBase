import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useRepoStore, useChatStore } from '../store'
import { repoAPI } from '../api'
import toast from 'react-hot-toast'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, 
  Github, 
  FileArchive, 
  Trash2, 
  ChevronRight, 
  Box, 
  Link as LinkIcon, 
  Loader2,
  Database,
  Info
} from 'lucide-react'

function UploadSection({ onClose }) {
  const [tab, setTab] = useState('github')
  const [url, setUrl] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const { addRepo, startPolling } = useRepoStore()

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/zip': ['.zip'] },
    maxFiles: 1,
  })

  const handleGithub = async () => {
    if (!url.trim()) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('github_url', url.trim())
      const res = await repoAPI.ingestGithub(fd)
      addRepo(res.data)
      startPolling(res.data.id)
      toast.success('Repository queued for ingestion!')
      onClose?.()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add repository')
    } finally {
      setLoading(false)
    }
  }

  const handleZip = async () => {
    if (!file) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await repoAPI.uploadZip(fd)
      addRepo(res.data)
      startPolling(res.data.id)
      toast.success('ZIP uploaded and processing!')
      onClose?.()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="sidebar-section"
    >
      <div className="glass-panel" style={{ padding: '16px', borderRadius: 'var(--radius-lg)' }}>
        <div className="upload-tabs" style={{ background: 'var(--bg-active)', padding: '4px', borderRadius: 'var(--radius-md)', display: 'flex', marginBottom: '16px' }}>
          <button
            className={`tab ${tab === 'github' ? 'active' : ''}`}
            onClick={() => setTab('github')}
            style={{ flex: 1 }}
          >
            <Github size={14} /> GitHub
          </button>
          <button
            className={`tab ${tab === 'zip' ? 'active' : ''}`}
            onClick={() => setTab('zip')}
            style={{ flex: 1 }}
          >
            <FileArchive size={14} /> ZIP
          </button>
        </div>

        <div className="upload-content">
          {tab === 'github' && (
            <div className="form-group">
              <label className="form-label">Repository URL</label>
              <input
                id="github-url-input"
                className="form-input"
                placeholder="https://github.com/user/repo"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleGithub()}
              />
              <button
                id="github-ingest-btn"
                className="btn btn-primary btn-full btn-sm"
                style={{ marginTop: '12px' }}
                onClick={handleGithub}
                disabled={loading || !url.trim()}
              >
                {loading ? <Loader2 className="animate-spin" size={16} /> : 'Connect Repository'}
              </button>
            </div>
          )}

          {tab === 'zip' && (
            <div className="form-group">
              <label className="form-label">Source Archive</label>
              <div
                {...getRootProps()}
                className={`upload-area ${isDragActive ? 'dragging' : ''}`}
                style={{
                  border: '2px dashed var(--border-default)',
                  borderRadius: 'var(--radius-md)',
                  padding: '24px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: isDragActive ? 'var(--bg-active)' : 'var(--bg-surface)',
                  transition: 'all 0.2s ease'
                }}
              >
                <input {...getInputProps()} />
                <FileArchive size={28} style={{ marginBottom: '8px', color: 'var(--accent-primary)' }} />
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  {file ? file.name : 'Drop ZIP or browse'}
                </div>
              </div>
              <button
                id="zip-upload-btn"
                className="btn btn-primary btn-full btn-sm"
                style={{ marginTop: '12px' }}
                onClick={handleZip}
                disabled={loading || !file}
              >
                {loading ? <Loader2 className="animate-spin" size={16} /> : 'Upload Bundle'}
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function RepoItem({ repo, isActive, onClick, onDelete }) {
  const [deleting, setDeleting] = useState(false)

  const statusClass = {
    ready: 'badge-ready',
    processing: 'badge-processing',
    pending: 'badge-pending',
    error: 'badge-error',
  }[repo.status] || 'badge-pending'

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm(`Are you sure you want to delete "${repo.name}"?`)) return
    setDeleting(true)
    try { await onDelete(repo.id) }
    finally { setDeleting(false) }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ x: 4 }}
      className={`repo-card ${isActive ? 'active' : ''}`}
      onClick={() => repo.status === 'ready' && onClick(repo)}
      style={{ opacity: deleting ? 0.5 : 1 }}
    >
      <div className="repo-card-header">
        <div className="repo-card-name">
          {repo.source_type === 'github' ? <Github size={16} className="repo-card-icon" /> : <Box size={16} className="repo-card-icon" />}
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{repo.name}</span>
        </div>
        <button className="delete-btn" onClick={handleDelete} title="Delete repository">
          <Trash2 size={14} />
        </button>
      </div>
      <div className="repo-card-meta">
        <span className={`repo-card-badge ${statusClass}`}>
          {repo.status === 'processing' && <Loader2 size={10} className="animate-spin" style={{ marginRight: '4px' }} />}
          {repo.status}
        </span>
        {repo.status === 'ready' && (
          <span className="repo-card-count" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-muted)' }}>
            <Database size={11} /> {repo.chunk_count}
          </span>
        )}
      </div>
    </motion.div>
  )
}

export default function Sidebar() {
  const [showUpload, setShowUpload] = useState(false)
  const { repos, activeRepo, setActiveRepo, deleteRepo, loading } = useRepoStore()
  const { clearMessages } = useChatStore()

  const handleSelectRepo = (repo) => {
    setActiveRepo(repo)
    clearMessages()
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-scroll">
        <div className="sidebar-section">
          <button
            className={`btn ${showUpload ? 'btn-secondary' : 'btn-primary'} btn-full btn-sm`}
            onClick={() => setShowUpload((v) => !v)}
            style={{ marginBottom: '8px' }}
          >
            {showUpload ? 'Cancel' : <><Plus size={16} /> New Repository</>}
          </button>
        </div>

        <AnimatePresence>
          {showUpload && <UploadSection onClose={() => setShowUpload(false)} />}
        </AnimatePresence>

        <div className="sidebar-section" style={{ marginTop: '12px' }}>
          <span className="sidebar-section-label">
            <Database size={12} /> Indexed Repositories
          </span>
        </div>

        <div className="repos-list">
          <AnimatePresence mode="popLayout">
            {loading && repos.length === 0 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="sidebar-state-msg"
              >
                <Loader2 className="animate-spin" size={20} style={{ margin: '0 auto 12px' }} />
                <span>Loading your workspace...</span>
              </motion.div>
            )}
            {!loading && repos.length === 0 && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="sidebar-state-msg"
              >
                <Info size={32} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                <span>No repositories found.<br/>Add one to get started.</span>
              </motion.div>
            )}
            {repos.map((repo) => (
              <RepoItem
                key={repo.id}
                repo={repo}
                isActive={activeRepo?.id === repo.id}
                onClick={handleSelectRepo}
                onDelete={deleteRepo}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>

      <div className="sidebar-footer">
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 10px var(--success)' }}></div>
          Engine Operational
        </div>
      </div>
    </aside>
  )
}
