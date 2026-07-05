import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import { api, setAuthToken, getAuthToken } from '@/api/client'
import { useToast } from '@/components/Toast'

interface User {
  id: number
  email: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
}

interface AuthContextValue {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    const saved = getAuthToken()
    if (saved) {
      setToken(saved) // eslint-disable-line react-hooks/set-state-in-effect
      api.me()
        .then((u) => { setUser(u) })
        .catch(() => {
          setToken(null)
          setAuthToken(null)
          toast('Session expired. Please log in again.', 'error')
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.login(email, password)
    setAuthToken(data.access_token)
    setToken(data.access_token)
    const me = await api.me()
    setUser(me)
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await api.register(email, password)
    await login(email, password)
  }, [login])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // ignore logout errors
    }
    setAuthToken(null)
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
