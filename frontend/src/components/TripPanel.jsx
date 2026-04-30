import { useState } from 'react'
import { addTripMember, createTrip } from '../api/client'
import { useAuth } from '../context/AuthContext'

function MemberTag({ email, isOwner }) {
  return (
    <div className="flex items-center gap-2 bg-zinc-800 rounded-lg px-3 py-2 text-sm">
      <div className="w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
        {email[0].toUpperCase()}
      </div>
      <span className="text-zinc-300 truncate">{email}</span>
      {isOwner && <span className="text-xs text-orange-400 ml-auto">owner</span>}
    </div>
  )
}

function AddMemberForm({ tripId, onAdded }) {
  const { token } = useAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await addTripMember(token, tripId, email.trim())
      setEmail('')
      onAdded()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3">
      <div className="flex gap-2">
        <input
          type="email"
          placeholder="Friend's email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="flex-1 bg-zinc-800 text-zinc-100 placeholder-zinc-500 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm px-3 py-2 rounded-lg transition-colors"
        >
          {loading ? '...' : 'Add'}
        </button>
      </div>
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </form>
  )
}

function TripCard({ trip, onMemberAdded, onOpenChat }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-zinc-800 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div
          className="flex-1 cursor-pointer"
          onClick={() => setExpanded((v) => !v)}
        >
          <p className="text-zinc-100 font-medium text-sm">{trip.name}</p>
          <p className="text-zinc-500 text-xs mt-0.5">
            {trip.members.length} member{trip.members.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onOpenChat(trip)}
            className="text-orange-400 hover:text-orange-300 transition-colors"
            title="Open chat"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </button>
          <svg
            className={`w-4 h-4 text-zinc-500 transition-transform cursor-pointer ${expanded ? 'rotate-180' : ''}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
            onClick={() => setExpanded((v) => !v)}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {expanded && (
        <div className="space-y-2 pt-1 border-t border-zinc-700">
          {trip.members.map((m) => (
            <MemberTag key={m.user_id} email={m.email} isOwner={m.user_id === trip.owner_id} />
          ))}
          <AddMemberForm tripId={trip.id} onAdded={onMemberAdded} />
        </div>
      )}
    </div>
  )
}

export default function TripPanel({ trips, onTripCreated, onOpenChat }) {
  const { token } = useAuth()
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await createTrip(token, name.trim())
      setName('')
      setShowForm(false)
      onTripCreated()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <h2 className="text-zinc-100 font-semibold text-sm">Trips</h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-orange-400 hover:text-orange-300 text-xs transition-colors"
        >
          {showForm ? 'Cancel' : '+ New trip'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="px-4 py-3 border-b border-zinc-800 flex gap-2">
          <input
            autoFocus
            type="text"
            placeholder="Trip name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 bg-zinc-800 text-zinc-100 placeholder-zinc-500 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-500"
          />
          <button
            type="submit"
            disabled={loading || !name.trim()}
            className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm px-3 py-2 rounded-lg transition-colors"
          >
            {loading ? '...' : 'Create'}
          </button>
        </form>
      )}

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {trips.length === 0 ? (
          <p className="text-zinc-600 text-xs text-center mt-4">No trips yet</p>
        ) : (
          trips.map((trip) => (
            <TripCard key={trip.id} trip={trip} onMemberAdded={onTripCreated} onOpenChat={onOpenChat} />
          ))
        )}
      </div>
    </div>
  )
}
