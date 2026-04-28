import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

// --- JWT INTERCEPTOR: inject token on every request ---
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- AUTH ---
export const authAPI = {
  register: (email, username, password) =>
    api.post('/auth/register', { email, username, password }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
}

// --- REPOS ---
export const repoAPI = {
  list: () => api.get('/repos/'),
  get: (id) => api.get(`/repos/${id}`),
  ingestGithub: (formData) => api.post('/repos/github', formData),
  uploadZip: (formData) =>
    api.post('/repos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    }),
  delete: (id) => api.delete(`/repos/${id}`),
  getAnalysis: (id) => api.get(`/repos/${id}/analysis`),
  getDependencies: (id) => api.get(`/repos/${id}/dependencies`),
}

// --- CHAT ---
export const chatAPI = {
  query: (data) => api.post('/chat/query', data, { timeout: 120000 }),
  history: (repoId) => api.get(`/chat/history/${repoId}`),
  feedback: (queryId, feedback) =>
    api.post(`/chat/feedback/${queryId}`, { feedback }),
  architecture: (repoId) => api.get(`/chat/architecture/${repoId}`),
}

export default api
