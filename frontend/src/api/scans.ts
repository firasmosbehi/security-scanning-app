const API_BASE = '/api'

async function fetchApi(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || err.message || res.statusText)
  }
  return res.json()
}

export async function getScannersHealth(): Promise<{
  trivy: { available: boolean; path: string | null }
  checkov: { available: boolean; path: string | null }
  infracost: { available: boolean; path: string | null; api_key_set: boolean }
}> {
  return fetchApi('/health/scanners')
}

export async function createScan(formData: FormData): Promise<{ scan_id: string; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/scans`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || err.message || res.statusText)
  }
  return res.json()
}

export async function getScan(scanId: string): Promise<{
  status: string
  findings: unknown[]
  error?: string
}> {
  return fetchApi(`/scans/${scanId}`)
}
