import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const MD = {
  h1: ({ children }) => <h1 className="text-2xl font-bold mt-4 mb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-xl font-semibold mt-4 mb-2">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-semibold mt-3 mb-1">{children}</h3>,
  p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="list-disc ml-5 mb-3 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal ml-5 mb-3 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  pre: ({ children }) => <pre className="bg-zinc-900 rounded-lg p-4 overflow-x-auto text-sm font-mono mb-3">{children}</pre>,
  code: ({ children }) => <code className="bg-zinc-700 rounded px-1 text-sm font-mono">{children}</code>,
  table: ({ children }) => <div className="overflow-x-auto mb-3"><table className="min-w-full border-collapse">{children}</table></div>,
  th: ({ children }) => <th className="border border-zinc-600 px-3 py-2 text-left font-semibold bg-zinc-700 text-sm">{children}</th>,
  td: ({ children }) => <td className="border border-zinc-600 px-3 py-2 text-sm">{children}</td>,
  hr: () => <hr className="border-zinc-700 my-4" />,
  blockquote: ({ children }) => <blockquote className="border-l-4 border-orange-500 pl-4 my-3 text-zinc-300">{children}</blockquote>,
}

function UserMessage({ content }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%] bg-zinc-700 text-zinc-100 rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap">
        {content}
      </div>
    </div>
  )
}

function AssistantMessage({ content }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] text-zinc-100 text-sm">
        <Markdown remarkPlugins={[remarkGfm]} components={MD}>
          {content}
        </Markdown>
      </div>
    </div>
  )
}

function StreamingMessage({ text, label }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] text-zinc-100 text-sm">
        {text ? (
          <Markdown remarkPlugins={[remarkGfm]} components={MD}>
            {text}
          </Markdown>
        ) : (
          <div className="flex items-center gap-2 text-zinc-400 italic">
            <span className="inline-block w-2 h-2 bg-orange-500 rounded-full animate-pulse flex-shrink-0" />
            {label || 'Processing...'}
          </div>
        )}
      </div>
    </div>
  )
}

function EmptyState({ onSend }) {
  const suggestions = [
    '7-day trip to Kashmir in June',
    'Weekend getaway near Islamabad',
    'Best hill stations to visit in summer',
    'Budget trip to northern areas',
  ]

  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <span className="text-5xl mb-4">✈️</span>
      <h2 className="text-xl font-semibold text-zinc-100 mb-2">Where do you want to go?</h2>
      <p className="text-zinc-500 text-sm mb-8">Plan your perfect trip with AI</p>
      <div className="grid grid-cols-2 gap-2 w-full max-w-md">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onSend(s)}
            className="text-left bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-zinc-100 text-sm px-4 py-3 rounded-xl transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const ref = useRef(null)

  const submit = () => {
    const q = value.trim()
    if (!q || disabled) return
    onSend(q)
    setValue('')
    if (ref.current) ref.current.style.height = 'auto'
  }

  const handleChange = (e) => {
    setValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex items-end gap-3 bg-zinc-800 rounded-2xl px-4 py-3 border border-zinc-700 focus-within:border-zinc-500 transition-colors">
      <textarea
        ref={ref}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Plan a trip..."
        disabled={disabled}
        rows={1}
        className="flex-1 bg-transparent text-zinc-100 placeholder-zinc-500 text-sm resize-none focus:outline-none disabled:opacity-50 leading-relaxed"
        style={{ maxHeight: '180px' }}
      />
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        className="flex-shrink-0 bg-orange-500 hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl p-2 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  )
}

export default function ChatArea({ messages, streamingText, progressLabel, isStreaming, onSend }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText, progressLabel])

  const isEmpty = messages.length === 0 && !isStreaming

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <EmptyState onSend={onSend} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
            {messages.map((m) =>
              m.role === 'user' ? (
                <UserMessage key={m.id} content={m.content} />
              ) : (
                <AssistantMessage key={m.id} content={m.content} />
              )
            )}
            {isStreaming && (
              <StreamingMessage text={streamingText} label={progressLabel} />
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="px-4 py-4 border-t border-zinc-700">
        <div className="max-w-3xl mx-auto">
          <MessageInput onSend={onSend} disabled={isStreaming} />
        </div>
      </div>
    </main>
  )
}
