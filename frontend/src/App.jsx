import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useRepoStore, useAuthStore } from './store'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import CodePanel from './components/CodePanel'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import { motion } from 'framer-motion'
import { Sun, Moon } from 'lucide-react'
import './index.css'

function ProtectedRoute({ children }) {
  const { token, user, restoreSession } = useAuthStore()

  useEffect(() => {
    if (token && !user) restoreSession()
  }, [token, user, restoreSession])

  if (!token) return <Navigate to="/login" replace />
  return children
}

function NavBar() {
  const { user, logout, theme, toggleTheme } = useAuthStore()
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <motion.div 
          initial={{ rotate: -10, scale: 0.9 }}
          animate={{ rotate: 0, scale: 1 }}
          className="navbar-logo-icon"
        >
          🧠
        </motion.div>
        <span className="navbar-title">CodeAI</span>
        <div className="navbar-badge">
          <span style={{ color: 'var(--accent-primary)' }}>●</span> Groq Agent
        </div>
      </div>
      <div className="navbar-right">
        <button
          className="btn-icon theme-toggle"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        {user && (
          <>
            <div className="navbar-user">
              <div className="navbar-avatar">{user.username[0].toUpperCase()}</div>
              <span className="navbar-username">{user.username}</span>
            </div>
            <button
              id="logout-btn"
              className="btn btn-secondary btn-sm"
              onClick={logout}
              title="Sign out"
            >
              Sign out
            </button>
          </>
        )}
      </div>
    </nav>
  )
}

function MainApp() {
  const { fetchRepos } = useRepoStore()

  useEffect(() => {
    fetchRepos()
  }, [])

  return (
    <div className="app-shell">
      <NavBar />
      <div className="app-layout">
        <Sidebar />
        <main className="main-area">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="chat-content"
            style={{ display: 'flex', flex: 1, overflow: 'hidden' }}
          >
            <ChatPanel />
            <CodePanel />
          </motion.div>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-subtle)',
            fontSize: '13px',
            fontFamily: 'var(--font-sans)',
          },
          success: { iconTheme: { primary: '#22c55e', secondary: 'white' } },
          error: { iconTheme: { primary: '#ef4444', secondary: 'white' } },
        }}
      />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainApp />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
