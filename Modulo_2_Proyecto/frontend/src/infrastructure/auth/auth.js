/**
 * Authentication utilities for Lyfter DnD
 */

const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export function isAuthenticated() {
  const token = getAccessToken()
  if (!token) return false
  
  // Check if token is expired
  return !isTokenExpired(token)
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken, refreshToken = null) {
  localStorage.setItem(TOKEN_KEY, accessToken)
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function isTokenExpired(token) {
  try {
    const payload = parseJwtPayload(token)
    if (!payload.exp) return false
    
    // exp is in seconds, Date.now() is in milliseconds
    const expirationTime = payload.exp * 1000
    const now = Date.now()
    
    // Consider expired if less than 30 seconds remaining
    return now >= (expirationTime - 30000)
  } catch {
    return true
  }
}

function parseJwtPayload(token) {
  const base64Url = token.split('.')[1]
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
  const jsonPayload = decodeURIComponent(
    atob(base64)
      .split('')
      .map(char => '%' + ('00' + char.charCodeAt(0).toString(16)).slice(-2))
      .join('')
  )
  return JSON.parse(jsonPayload)
}

export function getUserFromToken() {
  const token = getAccessToken()
  if (!token) return null
  
  try {
    return parseJwtPayload(token)
  } catch {
    return null
  }
}

