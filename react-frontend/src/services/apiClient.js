import axios from 'axios'
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '../utils/storage'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

let refreshRequest = null

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const refreshToken = getRefreshToken()

    if (
      error.response?.status === 401 &&
      refreshToken &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/token/refresh/')
    ) {
      originalRequest._retry = true
      refreshRequest ||= apiClient
        .post('/auth/token/refresh/', { refresh: refreshToken })
        .then((response) => {
          saveTokens({ access: response.data.access })
          return response.data.access
        })
        .finally(() => {
          refreshRequest = null
        })

      try {
        const access = await refreshRequest
        originalRequest.headers.Authorization = `Bearer ${access}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        clearTokens()
        window.dispatchEvent(new Event('companio:unauthorized'))
        return Promise.reject(refreshError)
      }
    }

    if (error.response?.status === 401) {
      window.dispatchEvent(new Event('companio:unauthorized'))
    }

    return Promise.reject(error)
  },
)

export function getApiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (typeof data === 'string') return data

  const firstField = Object.keys(data)[0]
  const firstValue = data[firstField]
  if (Array.isArray(firstValue)) return firstValue[0]
  if (typeof firstValue === 'string') return firstValue
  return fallback
}
