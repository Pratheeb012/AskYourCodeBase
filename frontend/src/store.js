import { create } from 'zustand'
import { repoAPI, authAPI } from './api'

// --- AUTH STORE ---
export const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token') || null,
  loading: false,
  theme: 'dark',

  // Restore session on app load
  restoreSession: async () => {
    const token = localStorage.getItem('token')
    if (!token) return
    try {
      const res = await authAPI.me()
      set({ user: res.data, token })
    } catch {
      localStorage.removeItem('token')
      set({ user: null, token: null })
    }
  },

  login: async (email, password) => {
    set({ loading: true })
    try {
      const res = await authAPI.login(email, password)
      const { access_token } = res.data
      localStorage.setItem('token', access_token)
      const meRes = await authAPI.me()
      set({ user: meRes.data, token: access_token })
    } finally {
      set({ loading: false })
    }
  },

  register: async (email, username, password) => {
    set({ loading: true })
    try {
      await authAPI.register(email, username, password)
      // Auto-login after registration
      const res = await authAPI.login(email, password)
      const { access_token } = res.data
      localStorage.setItem('token', access_token)
      const meRes = await authAPI.me()
      set({ user: meRes.data, token: access_token })
    } finally {
      set({ loading: false })
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null })
    // Clear other stores
    useRepoStore.getState().clearRepos()
    useChatStore.getState().clearMessages()
  },

  toggleTheme: () => {
    const newTheme = get().theme === 'dark' ? 'light' : 'dark'
    document.documentElement.setAttribute('data-theme', newTheme)
    set({ theme: newTheme })
  },
}))

export const useRepoStore = create((set, get) => ({
  repos: [],
  activeRepo: null,
  loading: false,

  fetchRepos: async () => {
    set({ loading: true })
    try {
      const res = await repoAPI.list()
      set({ repos: res.data })
    } finally {
      set({ loading: false })
    }
  },

  setActiveRepo: (repo) => set({ activeRepo: repo }),

  clearRepos: () => set({ repos: [], activeRepo: null }),

  addRepo: (repo) => set((s) => ({ repos: [repo, ...s.repos] })),

  updateRepo: (id, updates) =>
    set((s) => ({
      repos: s.repos.map((r) => (r.id === id ? { ...r, ...updates } : r)),
      activeRepo:
        s.activeRepo?.id === id
          ? { ...s.activeRepo, ...updates }
          : s.activeRepo,
    })),

  startPolling: (id) => {
    const interval = setInterval(async () => {
      try {
        const res = await repoAPI.get(id)
        get().updateRepo(id, res.data)
        if (res.data.status === 'ready' || res.data.status === 'error') {
          clearInterval(interval)
        }
      } catch {
        clearInterval(interval)
      }
    }, 3000)
  },

  deleteRepo: async (id) => {
    await repoAPI.delete(id)
    set((s) => ({
      repos: s.repos.filter((r) => r.id !== id),
      activeRepo: s.activeRepo?.id === id ? null : s.activeRepo,
    }))
  },
}))

export const useChatStore = create((set, get) => ({
  messages: [],
  loading: false,
  selectedChunk: null,

  setSelectedChunk: (chunk) => {
    set({ selectedChunk: chunk })
    useUIStore.getState().setActiveTab('code')
  },

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, { ...msg, id: Date.now() }] })),

  updateLastMessage: (updates) =>
    set((s) => {
      const msgs = [...s.messages]
      if (msgs.length === 0) return s
      msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], ...updates }
      return { messages: msgs }
    }),

  clearMessages: () => set({ messages: [], selectedChunk: null }),

  sendQuery: async (query, repoId, rewriteQuery = true) => {
    const { addMessage, updateLastMessage } = get()
    addMessage({ role: 'user', content: query, ts: new Date() })
    addMessage({ role: 'assistant', content: null, loading: true, ts: new Date() })
    set({ loading: true })

    try {
      const { chatAPI } = await import('./api')
      const res = await chatAPI.query({
        query,
        repository_id: repoId,
        rewrite_query: rewriteQuery,
      })
      const data = res.data
      updateLastMessage({
        loading: false,
        content: data.answer,
        queryId: data.query_id,
        references: data.references,
        rewrittenQuery: data.rewritten_query,
        tokensUsed: data.tokens_used,
        responseTimeMs: data.response_time_ms,
        feedback: null,
      })
    } catch (err) {
      updateLastMessage({
        loading: false,
        content:
          '⚠️ ' +
          (err.response?.data?.detail || 'Something went wrong. Please try again.'),
        error: true,
      })
    } finally {
      set({ loading: false })
    }
  },
}))

// --- UI STORE ---
export const useUIStore = create((set) => ({
  activeTab: 'code',
  setActiveTab: (tab) => set({ activeTab: tab }),
}))
