import { useState, useRef, useEffect, useCallback } from 'react'
import { sendMessage } from '../api/client'
import MessageBubble from './MessageBubble'

const SUGGESTIONS = [
  'Top 5 restaurants in Legazpi',
  'Best food quality restaurants',
  'Restaurants with great ambiance',
  'Best value for money',
  'Tell me about Brew Print Cafe',
  'Restaurants with good service',
]

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'bot',
      text: "Hi there! 🍽️ I'm Eatsplorer, your guide to the best dining spots in Legazpi City! I use real customer review analysis to recommend restaurants. What are you looking for today?",
      ts: Date.now(),
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const sessionId = useRef(`user_${Date.now()}`)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userMsg = { id: Date.now(), role: 'user', text: trimmed, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const responses = await sendMessage(trimmed, sessionId.current)
      const botMsgs = responses.map((r, i) => ({
        id: `bot_${Date.now()}_${i}`,
        role: 'bot',
        text: r.text,
        buttons: r.buttons,
        ts: Date.now() + i,
      }))
      setMessages(prev => [...prev, ...botMsgs])
    } catch (err) {
      setError(err.message)
      setMessages(prev => [...prev, {
        id: `err_${Date.now()}`,
        role: 'bot',
        text: `⚠️ ${err.message}`,
        isError: true,
        ts: Date.now(),
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [loading])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  const handleButtonClick = (btn) => {
    send(btn.payload || btn.title)
  }

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-avatar">🤖</div>
        <div>
          <div className="chat-title">Eatsplorer AI</div>
          <div className="chat-status">
            <span className={`status-dot ${loading ? 'thinking' : 'online'}`} />
            {loading ? 'Thinking...' : 'Online'}
          </div>
        </div>
        <button className="chat-clear" onClick={() => {
          setMessages([{
            id: 'welcome',
            role: 'bot',
            text: "Hi! I'm Eatsplorer. What dining experience are you looking for in Legazpi City? 🍽️",
            ts: Date.now(),
          }])
          sessionId.current = `user_${Date.now()}`
        }} title="Clear conversation">↺</button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onButtonClick={handleButtonClick}
          />
        ))}

        {loading && (
          <div className="message bot-message">
            <div className="bubble bubble-bot typing-bubble">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestions (shown only at start) */}
      {messages.length <= 2 && (
        <div className="suggestions">
          <p className="suggestions-label">Try asking:</p>
          <div className="suggestions-list">
            {SUGGESTIONS.map((s) => (
              <button key={s} className="suggestion-chip" onClick={() => send(s)}>
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="chat-input-area">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Ask about restaurants in Legazpi City..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={1}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          aria-label="Send message"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
