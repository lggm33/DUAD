import { requestJson } from './http'

export interface HealthCheckResponse {
  status: string
  checks: {
    db: string
    redis: string
  }
}

export async function fetchHealthCheck(signal?: AbortSignal): Promise<HealthCheckResponse> {
  return await requestJson<HealthCheckResponse>({
    method: 'GET',
    path: '/api/v1/health',
    signal,
  })
}


