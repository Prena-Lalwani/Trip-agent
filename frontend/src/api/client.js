export async function register(email, password) {
  let res
  try {
    res = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
  } catch {
    throw new Error('Cannot connect to server. Make sure the backend is running.')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    if (res.status === 400) throw new Error(err.detail || 'Email already registered')
    throw new Error(err.detail || `Server error (${res.status})`)
  }
  return res.json()
}

export async function login(email, password) {
  let res
  try {
    res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
  } catch {
    throw new Error('Cannot connect to server. Make sure the backend is running.')
  }
  if (!res.ok) throw new Error('Invalid email or password')
  return res.json()
}

export async function getTrips(token) {
  const res = await fetch('/trips', { headers: { Authorization: `Bearer ${token}` } })
  if (!res.ok) throw new Error('Failed to load trips')
  return res.json()
}

export async function createTrip(token, name) {
  const res = await fetch('/trips', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error('Failed to create trip')
  return res.json()
}

export async function addTripMember(token, tripId, email) {
  const res = await fetch(`/trips/${tripId}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ email }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Failed to add member')
  return data
}

export async function acceptInvitation(token, invitationToken) {
  const res = await fetch(`/trips/invitations/${invitationToken}/accept`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Failed to accept invitation')
  }
  return res.json()
}

export async function getConversations(token) {
  const res = await fetch('/chat/conversations', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to load conversations')
  return res.json()
}

export async function streamChat(token, question, conversationId, onEvent) {
  const res = await fetch('/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message: question, conversation_id: conversationId ?? null }),
  })
  if (!res.ok) throw new Error('Stream request failed')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    const parts = buffer.split('\n\n')
    buffer = parts.pop()

    for (const part of parts) {
      if (!part.trim()) continue
      let event = 'message'
      let data = ''
      for (const line of part.split('\n')) {
        if (line.startsWith('event: ')) event = line.slice(7).trim()
        else if (line.startsWith('data: ')) data += (data ? '\n' : '') + line.slice(6)
      }
      if (data) onEvent({ event, data })
    }
  }
}
