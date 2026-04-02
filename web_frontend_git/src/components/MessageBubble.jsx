import { useEffect, useRef } from 'react'

/**
 * Renders a chat message bubble.
 * Supports basic markdown-lite formatting from RASA responses:
 *   **bold**, *italic*, bullet lists, numbered lists, line breaks
 */
export default function MessageBubble({ message, onButtonClick }) {
  const { role, text, buttons, isError } = message
  const isBot = role === 'bot'
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.classList.add('bubble-enter')
    }
  }, [])

  const formatted = formatText(text)

  return (
    <div className={`message ${isBot ? 'bot-message' : 'user-message'}`} ref={ref}>
      {isBot && <div className="bot-avatar">🍽️</div>}

      <div className={`bubble ${isBot ? 'bubble-bot' : 'bubble-user'} ${isError ? 'bubble-error' : ''}`}>
        <div
          className="bubble-text"
          dangerouslySetInnerHTML={{ __html: formatted }}
        />

        {buttons && buttons.length > 0 && (
          <div className="bubble-buttons">
            {buttons.map((btn, i) => (
              <button
                key={i}
                className="bubble-btn"
                onClick={() => onButtonClick(btn)}
              >
                {btn.title}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function formatText(text) {
  if (!text) return ''

  return text
    // Escape HTML first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Bold: **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic: *text*
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Bullet items: lines starting with - or •
    .replace(/^[-•]\s(.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/((<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>')
    // Numbered list: lines starting with 1. 2. etc
    .replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>')
    // Newlines to <br>
    .replace(/\n/g, '<br />')
    // Clean up <br> inside lists
    .replace(/<ul><br \/>/g, '<ul>')
    .replace(/<\/li><br \/>/g, '</li>')
}
