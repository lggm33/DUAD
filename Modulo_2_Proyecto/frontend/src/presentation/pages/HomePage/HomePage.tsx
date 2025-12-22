import reactLogo from '../../../assets/react.svg'
import viteLogo from '/vite.svg'

import { useHealthCheck } from './hooks/useHealthCheck'

export function HomePage() {
  const { healthData, healthError, isHealthLoading, healthPretty, runHealthCheck } = useHealthCheck()

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank" rel="noreferrer">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" rel="noreferrer">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={runHealthCheck} disabled={isHealthLoading}>
          {isHealthLoading ? 'Checking backend health...' : 'Check backend health (no CORS)'}
        </button>
        <p>
          This calls <code>/api/v1/health</code> via Vite proxy.
        </p>
        {healthError ? (
          <pre style={{ textAlign: 'left', color: '#ff6b6b', whiteSpace: 'pre-wrap' }}>{healthError}</pre>
        ) : null}
        {healthData ? <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap' }}>{healthPretty}</pre> : null}
      </div>
      <p className="read-the-docs">Click on the Vite and React logos to learn more</p>
    </>
  )
}


