const BASE = '/api'

export async function sendMessage(message, sender = 'user') {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sender, message }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Chat service unavailable')
  }
  return res.json()
}

export async function getRestaurants({ aspect, polarity, limit = 20, search } = {}) {
  const params = new URLSearchParams()
  if (aspect)   params.set('aspect', aspect)
  if (polarity) params.set('polarity', polarity)
  if (search)   params.set('search', search)
  params.set('limit', limit)
  const res = await fetch(`${BASE}/restaurants?${params}`)
  if (!res.ok) throw new Error('Failed to fetch restaurants')
  return res.json()
}

export async function getRestaurant(name) {
  const res = await fetch(`${BASE}/restaurants/${encodeURIComponent(name)}`)
  if (!res.ok) throw new Error('Restaurant not found')
  return res.json()
}

export async function getStats() {
  const res = await fetch(`${BASE}/stats`)
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}
