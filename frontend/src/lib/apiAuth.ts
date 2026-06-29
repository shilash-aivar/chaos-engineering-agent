/** API key for protected deployments — mirrors CHAOS_AGENT_API_KEY on the backend. */
export function getApiKey(): string | undefined {
  const fromEnv = import.meta.env.VITE_CHAOS_AGENT_API_KEY as string | undefined
  if (fromEnv?.trim()) return fromEnv.trim()
  const stored = localStorage.getItem('chaos_agent_api_key')
  return stored?.trim() || undefined
}

export function apiAuthHeaders(): Record<string, string> {
  const key = getApiKey()
  return key ? { 'X-API-Key': key } : {}
}

export function wsAuthQuery(): string {
  const key = getApiKey()
  return key ? `?token=${encodeURIComponent(key)}` : ''
}
