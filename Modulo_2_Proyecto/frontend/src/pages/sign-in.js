import template from './sign-in.html?raw'
import { navigate, getRedirectAfterLogin } from '../router.js'
import { setTokens } from '../infrastructure/auth/auth.js'

export function signInPage(app) {
  app.innerHTML = template
  setupSignInForm()
}

function setupSignInForm() {
  const form = document.getElementById('sign-in-form')
  const errorContainer = document.getElementById('form-error')
  const submitBtn = form.querySelector('button[type="submit"]')
  const btnText = submitBtn.querySelector('.btn-text')
  const btnLoader = submitBtn.querySelector('.btn-loader')

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    
    const formData = new FormData(form)
    const email = formData.get('email')
    const password = formData.get('password')

    setLoading(true)
    hideError()

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Invalid credentials')
      }

      // Store tokens using auth module
      setTokens(data.access_token, data.refresh_token)

      // Redirect to intended destination or dashboard
      const redirectPath = getRedirectAfterLogin()
      navigate(redirectPath)
    } catch (error) {
      showError(error.message)
    } finally {
      setLoading(false)
    }
  })

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading
    btnText.hidden = isLoading
    btnLoader.hidden = !isLoading
  }

  function showError(message) {
    errorContainer.textContent = message
    errorContainer.hidden = false
  }

  function hideError() {
    errorContainer.hidden = true
  }
}
