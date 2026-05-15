import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { authService } from '../services/authService'
import { clearTokens, getAccessToken, saveTokens } from '../utils/storage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(getAccessToken() ? 'loading' : 'guest')

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    setStatus('guest')
  }, [])

  const restoreSession = useCallback(async () => {
    if (!getAccessToken()) {
      setStatus('guest')
      return
    }

    try {
      const currentUser = await authService.me()
      setUser(currentUser)
      setStatus('authenticated')
    } catch {
      logout()
    }
  }, [logout])

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  useEffect(() => {
    window.addEventListener('companio:unauthorized', logout)
    return () => window.removeEventListener('companio:unauthorized', logout)
  }, [logout])

  async function login(payload) {
    const data = await authService.login(payload)
    saveTokens(data)
    setUser(data.user)
    setStatus('authenticated')
    return data
  }

  async function register(payload) {
    const data = await authService.register(payload)
    saveTokens(data.tokens)
    setUser(data.user)
    setStatus('authenticated')
    return data
  }

  const value = useMemo(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isLoading: status === 'loading',
      login,
      register,
      logout,
      restoreSession,
    }),
    [user, status, logout, restoreSession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
