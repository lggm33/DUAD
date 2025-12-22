export type HttpMethod = 'GET'

export interface HttpRequestOptions {
  method: HttpMethod
  path: string
  signal?: AbortSignal
}

async function parseJsonSafely<T>(response: Response): Promise<T> {
  const text = await response.text()

  if (!text) {
    return {} as T
  }

  return JSON.parse(text) as T
}

function buildErrorMessage(response: Response, body: unknown): string {
  const statusText = response.statusText || 'Unknown error'
  const stringBody = typeof body === 'string' ? body : JSON.stringify(body)

  return `Request failed: ${response.status} ${statusText}. Body: ${stringBody}`
}

export async function requestJson<T>(options: HttpRequestOptions): Promise<T> {
  const response = await fetch(options.path, {
    method: options.method,
    headers: {
      Accept: 'application/json',
    },
    signal: options.signal,
  })

  const body = await parseJsonSafely<unknown>(response)

  if (!response.ok) {
    throw new Error(buildErrorMessage(response, body))
  }

  return body as T
}


