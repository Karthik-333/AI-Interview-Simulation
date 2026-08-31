import { create } from 'zustand'

export type AuthUser = {
  id?: number
  username: string
  email?: string | null
}

type Store = {
  token: string | null
  authUser: AuthUser | null
  sessionId: number | null
  currentQuestion: string | null
  history: Array<Record<string, unknown>>
  score: number
  userName: string
  backendUrl: string
  setToken: (token: string | null) => void
  setAuthUser: (user: AuthUser | null) => void
  setSessionId: (sessionId: number | null) => void
  setCurrentQuestion: (question: string | null) => void
  setHistory: (history: Array<Record<string, unknown>>) => void
  setScore: (score: number) => void
  setUserName: (name: string) => void
  setBackendUrl: (url: string) => void
  resetInterview: () => void
  logout: () => void
}

export const useAppStore = create<Store>((set) => ({
  token: sessionStorage.getItem('ai-interview-token'),
  authUser: null,
  sessionId: null,
  currentQuestion: null,
  history: [],
  score: 0,
  userName: 'Karthik',
  backendUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  setToken: (token) => {
    set({ token })
    if (token) {
      sessionStorage.setItem('ai-interview-token', token)
    } else {
      sessionStorage.removeItem('ai-interview-token')
    }
  },
  setAuthUser: (authUser) => set({ authUser }),
  setSessionId: (sessionId) => set({ sessionId }),
  setCurrentQuestion: (currentQuestion) => set({ currentQuestion }),
  setHistory: (history) => set({ history }),
  setScore: (score) => set({ score }),
  setUserName: (userName) => set({ userName }),
  setBackendUrl: (backendUrl) => set({ backendUrl }),
  resetInterview: () => set({ sessionId: null, currentQuestion: null, history: [], score: 0 }),
  logout: () => set({ token: null, authUser: null, sessionId: null, currentQuestion: null, history: [], score: 0 }),
}))
