import { useMemo, useState } from 'react'

import type { HealthCheck } from '../../../../domain/health/HealthCheck'
import { fetchHealthCheck } from '../../../../infrastructure/api/health'

export interface UseHealthCheckState {
  healthData: HealthCheck | null
  healthError: string | null
  isHealthLoading: boolean
  healthPretty: string
  runHealthCheck: () => Promise<void>
}

export function useHealthCheck(): UseHealthCheckState {
  const [healthData, setHealthData] = useState<HealthCheck | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [isHealthLoading, setIsHealthLoading] = useState(false)

  const healthPretty = useMemo(() => {
    if (!healthData) {
      return ''
    }

    return JSON.stringify(healthData, null, 2)
  }, [healthData])

  async function runHealthCheck() {
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

  return {
    healthData,
    healthError,
    isHealthLoading,
    healthPretty,
    runHealthCheck,
  }
}


