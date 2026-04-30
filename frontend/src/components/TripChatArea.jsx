import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'

function AgentAvatar() {
  return (
    <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 017 7H3a7 7 0 017-7h1V5.73A2 2 0 0112 2zM3 16h18v1a2 2 0 01-2 2H5a2 2 0 01-2-2v-1zm4 4h10v1a1 1 0 01-1 1H8a1 1 0 01-1-1v-1z"/>
      </svg>
    </div>
  )
}

function UserAvatar({ email }) {
  return (
    <div className="w-7 h-7 rounded-full bg-orange-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
      {email[0].toUpperCase()}
    </div>
  )
}

function Message({ msg, currentUserId }) {
  const isAgent = msg.is_agent
  const isOwn = !isAgent && msg.user_id === currentUserId

  return (
    <div className={`flex items-start gap-2 ${isOwn ? 'flex-row-reverse' : ''}`}>
      {isAgent ? <AgentAvatar /> : <UserAvatar email={msg.user_email} />}
      <div className={`max-w-[72%] flex flex-col gap-0.5 ${isOwn ? 'items-end' : 'items-start'}`}>
        {!isOwn && (
          <span className={`text-xs px-1 ${isAgent ? 'text-blue-400 font-medium' : 'text-zinc-500'}`}>
            {isAgent ? 'Travel Agent' : msg.user_email}
          </span>
        )}
        <div
          className={`px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
            isAgent
              ? 'bg-blue-950 text-blue-100 rounded-tl-sm border border-blue-800'
              : isOwn
              ? 'bg-orange-500 text-white rounded-tr-sm'
              : 'bg-zinc-700 text-zinc-100 rounded-tl-sm'
          }`}
        >
          {msg.content}
        </div>
        <span className="text-zinc-600 text-xs px-1">
          {new Date(msg.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  )
}

export default function TripChatArea({ trip, messages, onReplaceMessages, onNewMessage, onBack }) {
  const { token, user } = useAuth()
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  // Track which messages came from the initial history burst
  const historyDoneRef = useRef(false)

  useEffect(() => {
    historyDoneRef.current = false
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(
      `${protocol}://${window.location.host}/trips/${trip.id}/ws?token=${token}`
    )

    const historyBatch = []
    let flushTimer = null

    ws.onopen = () => setConnected(true)

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)

      if (!historyDoneRef.current) {
        // Collect history messages; flush once stream goes quiet (5 ms)
        historyBatch.push(msg)
        clearTimeout(flushTimer)
        flushTimer = setTimeout(() => {
          historyDoneRef.current = true
          onReplaceMessages(historyBatch.slice())
        }, 5)
      } else {
        onNewMessage(msg)
      }
    }

    ws.onclose = () => setConnected(false)

    wsRef.current = ws
    return () => {
      clearTimeout(flushTimer)
      ws.close()
    }
  }, [trip.id, token]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    const text = input.trim()
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(text)
    setInput('')
    inputRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col flex-1 min-w-0 h-full bg-[#212121]">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800 flex-shrink-0">
        <button
          onClick={onBack}
          className="text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <p className="text-zinc-100 font-semibold text-sm">{trip.name}</p>
          <p className="text-zinc-500 text-xs">
            {trip.members.length} member{trip.members.length !== 1 ? 's' : ''} &middot;{' '}
            <span className={connected ? 'text-green-400' : 'text-zinc-600'}>
              {connected ? 'connected' : 'connecting...'}
            </span>
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-zinc-600 text-sm text-center mt-8">
            No messages yet. Say hello!
          </p>
        )}
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} currentUserId={user?.id} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-zinc-800 flex-shrink-0">
        <div className="flex items-end gap-2 bg-zinc-800 rounded-2xl px-4 py-2">
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message the group..."
            disabled={!connected}
            className="flex-1 bg-transparent text-zinc-100 placeholder-zinc-500 text-sm resize-none focus:outline-none disabled:opacity-40 max-h-32"
            style={{ overflowY: input.split('\n').length > 3 ? 'auto' : 'hidden' }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || !connected}
            className="flex-shrink-0 w-8 h-8 bg-orange-500 hover:bg-orange-600 disabled:opacity-30 disabled:cursor-not-allowed rounded-full flex items-center justify-center transition-colors"
          >
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
