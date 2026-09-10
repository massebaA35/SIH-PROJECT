import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, clearToken, getToken, setToken } from '../services/api'
import type { User } from '../types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  error: string
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  const login = async (username: string, password: string) => {
    setError('')
    try {
      const res = await api.post('/auth/login', { username, password })
      setToken(res.data.access_token)
      setUser(res.data.user)
      return true
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed. Check your credentials.')
      return false
    }
  }

  const logout = () => {
    api.post('/auth/logout').catch(() => {})
    clearToken()
    setUser(null)
    window.location.href = '/login'
  }

  return <AuthContext.Provider value={{ user, loading, error, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
