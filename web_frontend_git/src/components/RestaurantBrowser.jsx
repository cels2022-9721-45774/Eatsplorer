import { useState, useEffect, useCallback } from 'react'
import { getRestaurants } from '../api/client'
import RestaurantCard from './RestaurantCard'

const ASPECTS = [
  { key: null,           label: 'Overall',      icon: '⭐' },
  { key: 'food_quality', label: 'Food Quality',  icon: '🍴' },
  { key: 'service',      label: 'Service',       icon: '🛎️' },
  { key: 'ambiance',     label: 'Ambiance',      icon: '🌿' },
  { key: 'price_value',  label: 'Price / Value', icon: '💰' },
]

const POLARITIES = [
  { key: null,       label: 'All' },
  { key: 'Positive', label: '✅ Positive' },
  { key: 'Neutral',  label: '🟡 Neutral' },
  { key: 'Negative', label: '❌ Negative' },
]

const LIMITS = [10, 20, 50, 175]

export default function RestaurantBrowser() {
  const [restaurants, setRestaurants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [aspect, setAspect]     = useState(null)
  const [polarity, setPolarity] = useState(null)
  const [search, setSearch]     = useState('')
  const [limit, setLimit]       = useState(20)
  const [selected, setSelected] = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getRestaurants({ aspect, polarity, limit, search: search || undefined })
      setRestaurants(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [aspect, polarity, limit, search])

  useEffect(() => {
    const t = setTimeout(fetchData, 300)
    return () => clearTimeout(t)
  }, [fetchData])

  const activeAspect = ASPECTS.find(a => a.key === aspect) || ASPECTS[0]

  return (
    <div className="browser">
      {/* Browser Header */}
      <div className="browser-header">
        <h2 className="browser-title">Restaurant Explorer</h2>
        <p className="browser-sub">
          {loading ? 'Loading...' : `${restaurants.length} restaurants`}
        </p>
      </div>

      {/* Search */}
      <div className="browser-search">
        <span className="search-icon">🔍</span>
        <input
          className="search-input"
          type="text"
          placeholder="Search restaurants..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button className="search-clear" onClick={() => setSearch('')}>✕</button>
        )}
      </div>

      {/* Aspect Filter */}
      <div className="filter-group">
        <span className="filter-label">Sort by aspect</span>
        <div className="filter-chips">
          {ASPECTS.map(a => (
            <button
              key={a.key ?? 'overall'}
              className={`chip ${aspect === a.key ? 'chip-active' : ''}`}
              onClick={() => setAspect(a.key)}
            >
              {a.icon} {a.label}
            </button>
          ))}
        </div>
      </div>

      {/* Polarity Filter */}
      <div className="filter-group">
        <span className="filter-label">Sentiment</span>
        <div className="filter-chips">
          {POLARITIES.map(p => (
            <button
              key={p.key ?? 'all'}
              className={`chip chip-sm ${polarity === p.key ? 'chip-active' : ''}`}
              onClick={() => setPolarity(p.key)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Limit */}
      <div className="filter-group filter-row">
        <span className="filter-label">Show</span>
        <div className="filter-chips">
          {LIMITS.map(l => (
            <button
              key={l}
              className={`chip chip-sm ${limit === l ? 'chip-active' : ''}`}
              onClick={() => setLimit(l)}
            >
              {l === 175 ? 'All' : l}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="browser-results">
        {error && (
          <div className="browser-error">
            ⚠️ {error}
            <button onClick={fetchData}>Retry</button>
          </div>
        )}

        {!error && !loading && restaurants.length === 0 && (
          <div className="browser-empty">
            No restaurants found. Try adjusting your filters.
          </div>
        )}

        {loading && (
          <div className="browser-loading">
            {[1,2,3,4,5].map(i => <div key={i} className="card-skeleton" />)}
          </div>
        )}

        {!loading && restaurants.map((r, i) => (
          <RestaurantCard
            key={r.restaurant_name}
            restaurant={r}
            rank={i + 1}
            activeAspect={aspect}
            isSelected={selected === r.restaurant_name}
            onSelect={() => setSelected(
              selected === r.restaurant_name ? null : r.restaurant_name
            )}
          />
        ))}
      </div>
    </div>
  )
}
