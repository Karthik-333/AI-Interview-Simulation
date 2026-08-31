import { useAppStore } from './store'

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { token } = useAppStore.getState()
  const headers = new Headers(options.headers || {})

  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  let payload: any = null
  try {
    payload = await response.json()
  } catch {
    payload = { detail: await response.text() }
  }

  if (!response.ok) {
    const detail = payload?.detail || payload || 'Request failed'
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return payload as T
}

export const authApi = {
  register: (username: string, password: string, email?: string) =>
    apiRequest<{ message: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email: email || undefined }),
    }),
  login: (username: string, password: string) =>
    apiRequest<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => apiRequest<{ id: number; username: string; email?: string | null }>('/auth/me'),
}

export const resumeApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest<{ message?: string; file_path?: string }>('/resume/upload_resume', {
      method: 'POST',
      body: formData,
      headers: {},
    })
  },
}

export const interviewApi = {
  health: () => apiRequest<{ status: string }>('/health'),
  start: (userName: string) =>
    apiRequest<{ session_id: number; first_question?: string; message?: string }>('/interview/start', {
      method: 'POST',
      body: JSON.stringify({ user_name: userName }),
    }),
  submitAnswer: (sessionId: number, answer: string) =>
    apiRequest<{ score: number; evaluation: string; strengths?: string[]; weaknesses?: string[]; next_question: string; current_score: number }>('/interview/answer', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, answer }),
    }),
  getSession: (sessionId: number) =>
    apiRequest<{ session_id: number; user_name: string; score: number; history: Record<string, unknown>[]; suggested_next_question?: string }>('/interview/session/' + sessionId),
}
