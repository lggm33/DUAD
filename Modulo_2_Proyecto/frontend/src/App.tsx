import { useMemo, useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { fetchHealthCheck, type HealthCheckResponse } from './api/health'

function App() {
  const [count, setCount] = useState(0)
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [isHealthLoading, setIsHealthLoading] = useState(false)

  const healthPretty = useMemo(() => {
    if (!healthData) {
      return ''
    }

    return JSON.stringify(healthData, null, 2)
  }, [healthData])

  async function handleHealthCheckClick() {
    setIsHealthLoading(true)
    setHealthError(null)

    try {
      const result = await fetchHealthCheck()
      setHealthData(result)
    } catch (error) {
      setHealthData(null)
      setHealthError(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setIsHealthLoading(false)
    }
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <div className="card">
        <button onClick={handleHealthCheckClick} disabled={isHealthLoading}>
          {isHealthLoading ? 'Checking backend health...' : 'Check backend health (no CORS)'}
        </button>
        <p>
          This calls <code>/api/v1/health</code> via Vite proxy.
        </p>
        {healthError ? (
          <pre style={{ textAlign: 'left', color: '#ff6b6b', whiteSpace: 'pre-wrap' }}>
            {healthError}
          </pre>
        ) : null}
        {healthData ? (
          <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap' }}>
            {healthPretty}
          </pre>
        ) : null}
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
