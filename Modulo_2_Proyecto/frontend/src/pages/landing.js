import template from './landing.html?raw'

export function landingPage(app) {
  app.innerHTML = template
  setupSmoothScroll()
}

function setupSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (event) => {
      const targetId = anchor.getAttribute('href')
      if (targetId === '#') return
      
      const targetElement = document.querySelector(targetId)
      if (targetElement) {
        event.preventDefault()
        targetElement.scrollIntoView({ behavior: 'smooth' })
      }
    })
  })
}

