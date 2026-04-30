import { useCallback, useEffect, useState } from 'react'
import { getConversations, getTrips, streamChat } from '../api/client'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import ChatArea from '../components/ChatArea'
import TripChatArea from '../components/TripChatArea'

export default function ChatPage() {
  const { token } = useAuth()
  const [conversations, setConversations] = useState([])
  const [trips, setTrips] = useState([])
  const [activeConvId, setActiveConvId] = useState(null)
  const [localMessages, setLocalMessages] = useState([])
  const [streamingText, setStreamingText] = useState('')
  const [progressLabel, setProgressLabel] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [activeTrip, setActiveTrip] = useState(null)
  const [tripMessages, setTripMessages] = useState({}) // { [tripId]: msg[] }

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations(token)
      setConversations(data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
    } catch {
      // silently ignore
    }
  }, [token])

  const loadTrips = useCallback(async () => {
    try {
      const data = await getTrips(token)
      setTrips(data)
    } catch {
      // silently ignore
    }
  }, [token])

  useEffect(() => {
    loadConversations()
    loadTrips()
  }, [loadConversations, loadTrips])

  const selectConversation = (conv) => {
    setActiveConvId(conv.id)
    setLocalMessages(conv.messages)
    setStreamingText('')
    setProgressLabel('')
  }

  const newChat = () => {
    setActiveConvId(null)
    setLocalMessages([])
    setStreamingText('')
    setProgressLabel('')
  }

  const sendMessage = async (question) => {
    if (isStreaming) return

    const userMsg = { id: `tmp-${Date.now()}`, role: 'user', content: question }
    setLocalMessages((prev) => [...prev, userMsg])
    setIsStreaming(true)
    setStreamingText('')
    setProgressLabel('')

    let currentConvId = activeConvId

    try {
      await streamChat(token, question, currentConvId, ({ event, data }) => {
        if (event === 'meta') {
          const parsed = JSON.parse(data)
          currentConvId = parsed.conversation_id
          setActiveConvId(parsed.conversation_id)
        } else if (event === 'progress') {
          setProgressLabel(data)
        } else if (event === 'token') {
          setStreamingText((prev) => prev + data)
          setProgressLabel('')
        }
      })
    } catch {
      setLocalMessages((prev) => [
        ...prev,
        { id: `err-${Date.now()}`, role: 'assistant', content: 'Something went wrong. Please try again.' },
      ])
    } finally {
      setIsStreaming(false)
      setStreamingText('')
      setProgressLabel('')
      const updated = await getConversations(token)
      const sorted = updated.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      setConversations(sorted)
      const active = sorted.find((c) => c.id === currentConvId)
      if (active) setLocalMessages(active.messages)
    }
  }

  return (
    <div className="flex h-screen bg-[#212121] overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelect={selectConversation}
        onNewChat={newChat}
        trips={trips}
        onTripCreated={loadTrips}
        onOpenTripChat={setActiveTrip}
      />
      {activeTrip ? (
        <TripChatArea
          trip={activeTrip}
          messages={tripMessages[activeTrip.id] ?? []}
          onReplaceMessages={(msgs) =>
            setTripMessages((prev) => ({ ...prev, [activeTrip.id]: msgs }))
          }
          onNewMessage={(msg) =>
            setTripMessages((prev) => ({
              ...prev,
              [activeTrip.id]: [...(prev[activeTrip.id] ?? []), msg],
            }))
          }
          onBack={() => setActiveTrip(null)}
        />
      ) : (
        <ChatArea
          messages={localMessages}
          streamingText={streamingText}
          progressLabel={progressLabel}
          isStreaming={isStreaming}
          onSend={sendMessage}
        />
      )}
    </div>
  )
}
