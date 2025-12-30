/**
 * Simple SPA Router for Lyfter DnD
 * Handles client-side navigation without page reloads
 * Supports protected routes with authentication guards
 */

import { isAuthenticated } from './infrastructure/auth/auth.js'

const routes = {}
const dynamicRoutes = []
const protectedRoutes = new Set()
const guestOnlyRoutes = new Set()
let currentRoute = null
let currentParams = {}

/**
 * Register a public route (accessible to everyone)
 */
export function registerRoute(path, handler) {
  routes[path] = handler
}

/**
 * Register a protected route (requires authentication)
 * Redirects to /sign-in if not authenticated
 */
export function registerProtectedRoute(path, handler) {
  routes[path] = handler
  protectedRoutes.add(path)
}

/**
 * Register a guest-only route (only accessible when NOT authenticated)
 * Redirects to /dashboard if already authenticated
 */
export function registerGuestRoute(path, handler) {
  routes[path] = handler
  guestOnlyRoutes.add(path)
}

/**
 * Register a dynamic protected route with parameters (e.g., /game/:id)
 * Supports path parameters like :id that will be extracted and passed to handler
 */
export function registerDynamicProtectedRoute(pattern, handler) {
  const paramNames = []
  const regexPattern = pattern.replace(/:([^/]+)/g, (_, paramName) => {
    paramNames.push(paramName)
    return '([^/]+)'
  })
  const regex = new RegExp(`^${regexPattern}$`)
  dynamicRoutes.push({ pattern, regex, paramNames, handler, isProtected: true })
}

/**
 * Get current route parameters
 */
export function getRouteParams() {
  return { ...currentParams }
}

export function navigate(path) {
  if (currentRoute === path) return
  
  window.history.pushState({}, '', path)
  renderRoute(path)
}

export function renderRoute(path) {
  // Check if route requires authentication
  if (protectedRoutes.has(path) && !isAuthenticated()) {
    sessionStorage.setItem('redirect_after_login', path)
    navigate('/sign-in')
    return
  }

  // Check if route is guest-only (sign-in, sign-up)
  if (guestOnlyRoutes.has(path) && isAuthenticated()) {
    navigate('/dashboard')
    return
  }

  // Try static routes first
  let handler = routes[path]
  currentParams = {}

  // If no static route, try dynamic routes
  if (!handler) {
    for (const route of dynamicRoutes) {
      const match = path.match(route.regex)
      if (match) {
        // Check authentication for protected dynamic routes
        if (route.isProtected && !isAuthenticated()) {
          sessionStorage.setItem('redirect_after_login', path)
          navigate('/sign-in')
          return
        }

        // Extract parameters
        const params = {}
        route.paramNames.forEach((name, index) => {
          params[name] = match[index + 1]
        })
        currentParams = params
        handler = route.handler
        break
      }
    }
  }

  // Fallback to 404 or home
  handler = handler || routes['/404'] || routes['/']
  currentRoute = path
  
  if (handler) {
    handler()
  }
}

/**
 * Get the redirect path after successful login
 */
export function getRedirectAfterLogin() {
  const redirect = sessionStorage.getItem('redirect_after_login')
  sessionStorage.removeItem('redirect_after_login')
  return redirect || '/dashboard'
}

export function initRouter() {
  // Handle browser back/forward buttons
  window.addEventListener('popstate', () => {
    renderRoute(window.location.pathname)
  })

  // Handle link clicks with data-link attribute
  document.addEventListener('click', (event) => {
    const link = event.target.closest('[data-link]')
    if (link) {
      event.preventDefault()
      const path = link.getAttribute('href')
      navigate(path)
    }
  })

  // Render initial route
  renderRoute(window.location.pathname)
}
