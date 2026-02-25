import template from './profile.html?raw'
import { Footer } from '../components/index.js'
import { fetchWithAuth } from '../utils/index.js'

export function profilePage(app) {
  app.innerHTML = template + Footer()
  initProfile()
}

async function initProfile() {
  const form = document.getElementById('profile-form')
  if (!form) return

  await loadUserProfile(form)
  setupProfileForm(form)
}

async function loadUserProfile(form) {
  try {
    const response = await fetchWithAuth('/api/v1/users/me')
    if (!response.ok) {
      throw new Error('Failed to load profile')
    }

    const user = await response.json()
    
    // Fill form fields
    form.name.value = user.name || ''
    form.username.value = user.username || ''
    form.email.value = user.email || ''
    
  } catch (error) {
    showMessage(error.message, 'error')
  }
}

function setupProfileForm(form) {
  const submitBtn = form.querySelector('button[type="submit"]')
  const btnText = submitBtn.querySelector('.btn-text')
  const btnLoader = submitBtn.querySelector('.btn-loader')

  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    
    const formData = new FormData(form)
    const payload = {
      name: formData.get('name'),
      username: formData.get('username') || null,
      email: formData.get('email')
    }

    setLoading(true)
    hideMessage()

    try {
      const response = await fetchWithAuth('/api/v1/users/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Update failed')
      }

      showMessage('Profile updated successfully!', 'success')
      
      // Update local storage or state if needed (though getUserFromToken parses JWT)
      // If the JWT doesn't contain the name/email, we might not need to do anything
      
    } catch (error) {
      showMessage(error.message, 'error')
    } finally {
      setLoading(false)
    }
  })

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading
    btnText.hidden = isLoading
    btnLoader.hidden = !isLoading
  }
}

function showMessage(message, type = 'info') {
  const messageEl = document.getElementById('profile-message')
  if (!messageEl) return
  
  messageEl.textContent = message
  messageEl.className = `profile-message profile-message-${type}`
  messageEl.hidden = false
}

function hideMessage() {
  const messageEl = document.getElementById('profile-message')
  if (messageEl) {
    messageEl.hidden = true
  }
}
