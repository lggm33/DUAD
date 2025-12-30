/**
 * Parses JSON response safely, returning empty object for empty responses
 * @param {Response} response 
 * @returns {Promise<unknown>}
 */
async function parseJsonSafely(response) {
  const text = await response.text()

  if (!text) {
    return {}
  }

  return JSON.parse(text)
}

/**
 * Builds a descriptive error message from a failed response
 * @param {Response} response 
 * @param {unknown} body 
 * @returns {string}
 */
function buildErrorMessage(response, body) {
  const statusText = response.statusText || 'Unknown error'
  const stringBody = typeof body === 'string' ? body : JSON.stringify(body)

  return `Request failed: ${response.status} ${statusText}. Body: ${stringBody}`
}

/**
 * Makes an HTTP request and returns the JSON response
 * @param {Object} options
 * @param {'GET' | 'POST' | 'PUT' | 'DELETE'} options.method
 * @param {string} options.path
 * @param {AbortSignal} [options.signal]
 * @returns {Promise<unknown>}
 */
export async function requestJson(options) {
  const response = await fetch(options.path, {
    method: options.method,
    headers: {
      Accept: 'application/json',
    },
    signal: options.signal,
  })

  const body = await parseJsonSafely(response)

  if (!response.ok) {
    throw new Error(buildErrorMessage(response, body))
  }

  return body
}

