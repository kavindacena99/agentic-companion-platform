const ACCESS_TOKEN_KEY = 'companio_access_token'
const REFRESH_TOKEN_KEY = 'companio_refresh_token'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function saveTokens(tokens) {
  if (tokens?.access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access)
  }
  if (tokens?.refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh)
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}
