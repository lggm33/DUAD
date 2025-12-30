import template from './sign-up.html?raw'
import { navigate } from '../router.js'
import { setTokens } from '../infrastructure/auth/auth.js'

export function signUpPage(app) {
  app.innerHTML = template
  setupSignUpForm()
}

function setupSignUpForm() {
  const form = document.getElementById('sign-up-form')
  const errorContainer = document.getElementById('form-error')
  const submitBtn = form.querySelector('button[type="submit"]')
  const btnText = submitBtn.querySelector('.btn-text')
  const btnLoader = submitBtn.querySelector('.btn-loader')

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    
    const formData = new FormData(form)
    const payload = {
      name: formData.get('name'),
      email: formData.get('email'),
      password: formData.get('password')
    }

    // Validate passwords match
    if (formData.get('password') !== formData.get('confirm_password')) {
      showError('Passwords do not match')
      return
    }

    setLoading(true)
    hideError()

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      // Store tokens using auth module
      setTokens(data.access_token, data.refresh_token)
      // Redirect to sign in
      navigate('/dashboard')
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

