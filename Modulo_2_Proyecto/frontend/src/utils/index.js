import { getAccessToken } from '../infrastructure/auth/auth.js'

/**
 * Makes an HTTP request with authentication token
 * @param {string} url - The URL to fetch
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function fetchWithAuth(url, options = {}) {
  const token = getAccessToken()
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  })
}

/**
 * Escapes HTML special characters to prevent XSS
 * @param {string} text - The text to escape
 * @returns {string} - The escaped HTML string
 */
export function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Formats a date string to a readable format
 * @param {string} dateString - The date string to format
 * @returns {string} - The formatted date
 */
export function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Gets initials from a name string
 * @param {string} name - The name to get initials from
 * @returns {string} - The initials (max 2 characters)
 */
export function getInitials(name) {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

