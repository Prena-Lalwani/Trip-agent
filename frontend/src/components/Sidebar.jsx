import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import TripPanel from './TripPanel'

function getTitle(conv) {
  const first = conv.messages.find((m) => m.role === 'user')
  if (!first) return 'New Chat'
  return first.content.length > 32 ? first.content.slice(0, 32) + '…' : first.content
}

function groupByDate(convs) {
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterdayStart = new Date(todayStart - 86_400_000)
  const weekStart = new Date(todayStart - 7 * 86_400_000)

  const groups = { Today: [], Yesterday: [], 'Past 7 days': [], Older: [] }
  for (const c of convs) {
    const d = new Date(c.created_at)
    if (d >= todayStart) groups['Today'].push(c)
    else if (d >= yesterdayStart) groups['Yesterday'].push(c)
    else if (d >= weekStart) groups['Past 7 days'].push(c)
    else groups['Older'].push(c)
  }
  return groups
}

export default function Sidebar({
  conversations, activeConvId, onSelect, onNewChat,
  trips, onTripCreated, onOpenTripChat,
}) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('chats')
  const groups = groupByDate(conversations)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-[#171717] flex flex-col h-full">

      {/* Tab switcher */}
      <div className="flex border-b border-zinc-800">
        {['chats', 'trips'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-3 text-sm font-medium transition-colors capitalize ${
              tab === t
                ? 'text-zinc-100 border-b-2 border-orange-500'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Chats tab */}
      {tab === 'chats' && (
        <>
          <div className="p-3">
            <button
              onClick={onNewChat}
              className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-zinc-300 hover:bg-zinc-800 transition-colors text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Chat
            </button>
          </div>

          <nav className="flex-1 overflow-y-auto px-2 pb-2">
            {Object.entries(groups).map(([label, convs]) =>
              convs.length === 0 ? null : (
                <div key={label} className="mb-4">
                  <p className="text-xs text-zinc-500 px-2 py-1 font-medium">{label}</p>
                  {convs.map((conv) => (
                    <button
                      key={conv.id}
                      onClick={() => onSelect(conv)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                        conv.id === activeConvId
                          ? 'bg-zinc-700 text-zinc-100'
                          : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                      }`}
                    >
                      {getTitle(conv)}
                    </button>
                  ))}
                </div>
              )
            )}
            {conversations.length === 0 && (
              <p className="text-zinc-600 text-xs px-3 mt-2">No conversations yet</p>
            )}
          </nav>
        </>
      )}

      {/* Trips tab */}
      {tab === 'trips' && (
        <div className="flex-1 overflow-hidden">
          <TripPanel trips={trips} onTripCreated={onTripCreated} onOpenChat={onOpenTripChat} />
        </div>
      )}

      <div className="p-3 border-t border-zinc-800">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors text-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v1" />
          </svg>
          Sign out
        </button>
      </div>
    </aside>
  )
}
