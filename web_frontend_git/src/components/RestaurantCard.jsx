const POLARITY_COLOR = {
  Positive: 'var(--positive)',
  Neutral:  'var(--neutral)',
  Negative: 'var(--negative)',
}

const POLARITY_EMOJI = {
  Positive: '✅',
  Neutral:  '🟡',
  Negative: '❌',
}

const ASPECTS = [
  { key: 'food_quality', label: 'Food Quality',  icon: '🍴' },
  { key: 'service',      label: 'Service',        icon: '🛎️' },
  { key: 'ambiance',     label: 'Ambiance',       icon: '🌿' },
  { key: 'price_value',  label: 'Price / Value',  icon: '💰' },
]

export default function RestaurantCard({ restaurant: r, rank, activeAspect, isSelected, onSelect }) {
  const overall = r.overall_score
  const polarity = r.overall_polarity
  const polarityColor = POLARITY_COLOR[polarity] || 'var(--text-muted)'

  return (
    <div
      className={`restaurant-card ${isSelected ? 'card-expanded' : ''}`}
      onClick={onSelect}
    >
      {/* Rank + Name */}
      <div className="card-header">
        <div className="card-rank">#{rank}</div>
        <div className="card-info">
          <div className="card-name">{r.restaurant_name}</div>
          <div className="card-meta">
            <span style={{ color: polarityColor }}>
              {POLARITY_EMOJI[polarity] || '⬜'} {polarity || 'N/A'}
            </span>
            <span className="card-dot">·</span>
            <span className="card-reviews">{r.total_reviews} reviews</span>
          </div>
        </div>
        <div className="card-score-badge" style={{ borderColor: polarityColor }}>
          <span className="score-num">
            {overall != null ? overall.toFixed(2) : 'N/A'}
          </span>
          <span className="score-denom">/5</span>
        </div>
      </div>

      {/* Highlighted aspect (if filtering by one) */}
      {activeAspect && r[activeAspect] && r[activeAspect].avg != null && (
        <div className="card-highlight">
          {ASPECTS.find(a => a.key === activeAspect)?.icon}{' '}
          <strong>{ASPECTS.find(a => a.key === activeAspect)?.label}:</strong>{' '}
          {r[activeAspect].avg.toFixed(2)}/5.00{' '}
          <span style={{ color: POLARITY_COLOR[r[activeAspect].polarity] }}>
            ({r[activeAspect].polarity})
          </span>
        </div>
      )}

      {/* Overall score bar */}
      <div className="score-bar-row">
        <ScoreBar value={overall} color={polarityColor} />
      </div>

      {/* Expanded: full aspect breakdown */}
      {isSelected && (
        <div className="card-aspects" onClick={e => e.stopPropagation()}>
          <div className="aspects-divider" />
          {ASPECTS.map(a => {
            const asp = r[a.key]
            const hasData = asp && asp.avg != null
            const color = hasData ? (POLARITY_COLOR[asp.polarity] || 'var(--text-muted)') : 'var(--border)'
            return (
              <div key={a.key} className="aspect-row">
                <span className="aspect-icon">{a.icon}</span>
                <span className="aspect-label">{a.label}</span>
                {hasData ? (
                  <>
                    <div className="aspect-bar-wrap">
                      <div
                        className="aspect-bar-fill"
                        style={{ width: `${(asp.avg / 5) * 100}%`, background: color }}
                      />
                    </div>
                    <span className="aspect-score" style={{ color }}>
                      {asp.avg.toFixed(2)}
                    </span>
                    <span className="aspect-count">({asp.review_count})</span>
                  </>
                ) : (
                  <span className="aspect-na">— N/A</span>
                )}
              </div>
            )
          })}
          <div className="aspects-footer">
            {r.aspects_scored}/4 aspects scored · {r.total_reviews} total reviews
          </div>
        </div>
      )}

      <div className="card-expand-hint">
        {isSelected ? '▲ Less' : '▼ Details'}
      </div>
    </div>
  )
}

function ScoreBar({ value, color }) {
  const pct = value != null ? (value / 5) * 100 : 0
  return (
    <div className="score-bar-track">
      <div
        className="score-bar-fill"
        style={{ width: `${pct}%`, background: color }}
      />
    </div>
  )
}
