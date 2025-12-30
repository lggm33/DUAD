import { requestJson } from './http.js'

/**
 * Fetches the health check status from the backend API
 * @param {AbortSignal} [signal]
 * @returns {Promise<{status: string, checks: {db: string, redis: string}}>}
 */
export async function fetchHealthCheck(signal) {
  return await requestJson({
    method: 'GET',
    path: '/api/v1/health',
    signal,
  })
}

