import './styles/index.css'
import './styles/app.css'
import { fetchHealthCheck } from './infrastructure/api/health.js'

const app = document.querySelector('#app')

function renderApp() {
  app.innerHTML = `
    <div class="logos">
      <a href="https://vite.dev" target="_blank" rel="noreferrer">
        <img src="/vite.svg" class="logo" alt="Vite logo" />
      </a>
      <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript" target="_blank" rel="noreferrer">
        <img src="/javascript.svg" class="logo vanilla" alt="JavaScript logo" />
      </a>
    </div>
    <h1>Vite + Vanilla JS</h1>
    <div class="card">
      <button id="health-btn">Check backend health (no CORS)</button>
      <p>
        This calls <code>/api/v1/health</code> via Vite proxy.
      </p>
      <div id="health-result"></div>
    </div>
    <p class="read-the-docs">Click on the Vite and JavaScript logos to learn more</p>
  `

  setupHealthCheck()
}

function setupHealthCheck() {
  const button = document.querySelector('#health-btn')
  const resultContainer = document.querySelector('#health-result')

  button.addEventListener('click', async () => {
    button.disabled = true
    button.textContent = 'Checking backend health...'
    resultContainer.innerHTML = ''

    try {
      const data = await fetchHealthCheck()
      resultContainer.innerHTML = `<pre class="success">${JSON.stringify(data, null, 2)}</pre>`
    } catch (error) {
      resultContainer.innerHTML = `<pre class="error">${error.message}</pre>`
    } finally {
      button.disabled = false
      button.textContent = 'Check backend health (no CORS)'
    }
  })
}

renderApp()

