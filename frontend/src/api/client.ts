import * as Sentry from '@sentry/react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

const TOKEN_STORAGE_KEY = 'jiba_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// If a token expires or gets revoked mid-session, any authenticated call
// will start 401ing. Without this, the app would just show a broken/empty
// screen with no explanation. Login/register are excluded since a wrong
// password there is a normal 401, not a session expiry.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const url = error.config?.url ?? ''
      const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register')
      if (!isAuthEndpoint && getStoredToken()) {
        clearStoredToken()
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    } else if (axios.isAxiosError(error) && (error.response?.status ?? 0) >= 500) {
      // 4xx are expected user-input/permission outcomes; a 5xx means the
      // backend broke, which is worth seeing in Sentry same as a frontend
      // crash would be.
      Sentry.captureException(error)
    }
    return Promise.reject(error)
  },
)

export function apiErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}
