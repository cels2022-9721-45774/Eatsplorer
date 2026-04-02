import { useState, useEffect } from 'react'
import ChatPanel from './components/ChatPanel'
import RestaurantBrowser from './components/RestaurantBrowser'
import { getStats } from './api/client'
import './App.css'

export default function App() {
  const [stats, setStats] = useState(null)
  const [activeTab, setActiveTab] = useState('chat') // mobile: 'chat' | 'browse'

  useEffect(() => {
    getStats().then(setStats).catch(() => {})
  }, [])

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="app-header">
        <div className="header-brand">
            <img className="header-icon" src="/eatsplorer_icon_logo.png" alt="Eatsplorer Logo" />
          <div>
            <img className="header-logo" src="/eatsplorer_long_logo.png" alt="Eatsplorer Long Logo" />
            <p className="header-sub">Legazpi City Dining Discovery</p>
          </div>
        </div>

        {stats && (
          <div className="header-stats">
            <Stat label="Restaurants" value={stats.total_restaurants} />
            <Stat label="Positive" value={stats.positive_count} accent="positive" />
            <Stat label="Avg Score" value={stats.avg_overall_score.toFixed(2)} />
            <Stat label="Fully Scored" value={stats.fully_scored_count} />
          </div>
        )}

        {/* Mobile tabs */}
        <div className="mobile-tabs">
          <button
            className={`mobile-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >💬 Chat</button>
          <button
            className={`mobile-tab ${activeTab === 'browse' ? 'active' : ''}`}
            onClick={() => setActiveTab('browse')}
          >🔍 Browse</button>
        </div>
      </header>

      {/* ── Main Layout ── */}
      <main className="app-main">
        <div className={`panel panel-browser ${activeTab === 'browse' ? 'mobile-visible' : 'mobile-hidden'}`}>
          <RestaurantBrowser />
        </div>
        <div className={`panel panel-chat ${activeTab === 'chat' ? 'mobile-visible' : 'mobile-hidden'}`}>
          <ChatPanel />
        </div>
      </main>
    </div>
  )
}

function Stat({ label, value, accent }) {
  return (
    <div className={`header-stat ${accent ? `stat-${accent}` : ''}`}>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}
