import type { HealthCheck } from '../../domain/health/HealthCheck'
import { requestJson } from './http'

export async function fetchHealthCheck(signal?: AbortSignal): Promise<HealthCheck> {
  return await requestJson<HealthCheck>({
    method: 'GET',
    path: '/api/v1/health',
    signal,
  })
}


