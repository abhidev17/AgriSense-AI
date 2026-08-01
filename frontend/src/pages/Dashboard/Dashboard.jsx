import { Link, useNavigate } from 'react-router-dom'
import { useDiagnosis } from '../../context/DiagnosisContext'
import styles from './Dashboard.module.css'

// ── SVG Icon Components ──
const IconMicroscope = () => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/>
    <path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
    <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
  </svg>
)

const IconLeaf = () => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
  </svg>
)

const IconSearch = () => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
  </svg>
)

const IconBulb = () => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1 .3 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>
    <path d="M9 18h6"/><path d="M10 22h4"/>
  </svg>
)

const IconPill = () => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>
  </svg>
)

const IconCloud = () => (
  <svg className={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
  </svg>
)

const IconTrendingUp = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
    <polyline points="16 7 22 7 22 13"/>
  </svg>
)

const IconTrendingDown = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/>
    <polyline points="16 17 22 17 22 11"/>
  </svg>
)

const IconStable = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12"/>
    <polyline points="12 5 19 12 12 19"/>
  </svg>
)

const IconThermometer = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>
  </svg>
)

const IconDroplet = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22a7 7 0 0 0 7-7c0-4.3-7-11-7-11S5 10.7 5 15a7 7 0 0 0 7 7Z"/>
  </svg>
)

const IconRain = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 14.89a6 6 0 1 1 11.83-1.5 4 4 0 0 1 5.92 4.67"/>
    <line x1="8" y1="19" x2="6" y2="22"/>
    <line x1="12" y1="19" x2="10" y2="22"/>
    <line x1="16" y1="19" x2="14" y2="22"/>
  </svg>
)

const IconWind = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59-3.41A2 2 0 1 1 14 6H2m15.59 2.59A2 2 0 1 1 19 12H2"/>
  </svg>
)

const IconInfo = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
  </svg>
)

const IconCheck = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

// ── Severity Helpers ──
const severityClass = (s = '') => {
  const sev = s.toLowerCase()
  if (sev === 'low')      return styles.severityLow
  if (sev === 'moderate') return styles.severityModerate
  if (sev === 'high')     return styles.severityHigh
  if (sev === 'critical') return styles.severityCritical
  return styles.severityModerate
}

// ── Trend Badge ──
const TrendBadge = ({ trend }) => {
  const t = (trend || '').toLowerCase()
  const cls  = t === 'up' ? styles.trendUp : t === 'down' ? styles.trendDown : styles.trendStable
  const icon = t === 'up' ? <IconTrendingUp /> : t === 'down' ? <IconTrendingDown /> : <IconStable />
  return (
    <span className={`${styles.trendBadge} ${cls}`}>
      {icon} <span className={styles.trendText}>{trend || 'Stable'}</span>
    </span>
  )
}

// ── Build Action Plan ──
function buildActionPlan(data) {
  if (data.action_plan) return data.action_plan

  const timeline = [
    {
      day: 'Today',
      action: data.treatment_recommendations?.[0] || 'Inspect and isolate infected plants',
      reason: 'Immediate action limits disease spread.',
      statusType: 'today'
    },
    {
      day: 'Tomorrow',
      action: data.treatment_recommendations?.[1] || `Apply treatment for ${data.disease?.name || 'crop disease'}`,
      reason: data.weather?.condition
        ? `Weather is ${data.weather.condition} — ideal for treatment.`
        : 'Follow treatment schedule for best results.',
      statusType: 'tomorrow'
    },
    {
      day: 'After 3 Days',
      action: data.treatment_recommendations?.[2] || 'Apply NPK fertilizer',
      reason: 'Supports plant recovery and boosts immunity.',
      statusType: 'after3days'
    },
    {
      day: 'Next Week',
      action: 'Inspect new leaf growth',
      reason: 'Ensure disease has stopped spreading.',
      statusType: 'nextweek'
    },
    {
      day: 'Harvest',
      action: data.market?.predicted_price_per_kg
        ? `Expected selling price ₹${data.market.predicted_price_per_kg}/kg`
        : 'Monitor market before selling',
      reason: data.market?.recommendation || 'Time your sale for maximum profit.',
      statusType: 'harvest'
    },
  ]

  return {
    overall_risk: data.disease?.severity === 'high' ? 'High' :
                  data.disease?.severity === 'low'  ? 'Low'  : 'Medium',
    risk_score: data.disease?.severity === 'high' ? 75 :
                data.disease?.severity === 'low'  ? 25 : 55,
    estimated_recovery: '85–95%',
    timeline,
  }
}

export default function Dashboard() {
  const { diagnosisResult, clearResult } = useDiagnosis()
  const navigate = useNavigate()

  if (!diagnosisResult) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <div className={styles.emptyIconWrap}>
            <IconMicroscope />
          </div>
          <h1 className={styles.emptyTitle}>No Diagnosis Found</h1>
          <p className={styles.emptyDesc}>
            Run a crop health diagnosis first to see your results here.
          </p>
          <Link to="/diagnose" className={styles.emptyBtn}>
            Start Diagnosis
          </Link>
        </div>
      </div>
    )
  }

  const d = diagnosisResult
  const actionPlan = buildActionPlan(d)

  const handleNewDiagnosis = () => {
    clearResult()
    navigate('/diagnose')
  }

  return (
    <div className={styles.page}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.headerLeft}>
            <div className={styles.sessionBadge}>
              <span className={styles.sessionBadgeText}>ID: {d.session_id?.slice(0, 12)}</span>
            </div>
            <h1 className={styles.headerTitle}>
              {d.crop?.name} &mdash; <span className={styles.headerDiseaseName}>{d.disease?.name}</span>
            </h1>
            <div className={styles.headerMeta}>
              <div className={styles.metaItem}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
                  <line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/>
                  <line x1="3" x2="21" y1="10" y2="10"/>
                </svg>
                <span>{new Date(d.timestamp).toLocaleString()}</span>
              </div>
              {d.processing_time_ms && (
                <div className={styles.metaItem}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                  </svg>
                  <span>{Math.round(d.processing_time_ms)}ms</span>
                </div>
              )}
              {d.weather?.location && (
                <div className={styles.metaItem}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
                  </svg>
                  <span>{d.weather.location}</span>
                </div>
              )}
            </div>
          </div>
          <div className={styles.headerActions}>
            <button
              className={`${styles.actionBtn} ${styles.actionBtnPrimary}`}
              onClick={handleNewDiagnosis}
              id="new-diagnosis-btn"
            >
              <IconMicroscope />
              <span>New Diagnosis</span>
            </button>
            <Link to="/history" className={`${styles.actionBtn} ${styles.actionBtnSecondary}`}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                <path d="M3 3v5h5"/>
              </svg>
              <span>History</span>
            </Link>
          </div>
        </div>
      </div>

      <main className={styles.main}>
        <div className={styles.grid}>

          {/* ── Crop Card ── */}
          <div className={`${styles.card} ${styles.gridLeft}`}>
            <div className={styles.cardHeader}>
              <div className={styles.cardHeaderIcon}><IconLeaf /></div>
              <span className={styles.cardHeaderTitle}>Crop Detected</span>
            </div>
            <div className={styles.cardBody}>
              <div className={styles.cropName}>{d.crop?.name}</div>
              <div className={styles.sourceTag}>
                <span className={styles.sourceTagDot} />
                {d.crop?.source === 'user' ? 'Manually Selected' : 'AI Auto Detected'}
              </div>
              <div className={styles.confidenceRow}>
                <span className={styles.confidenceLabel}>AI Confidence</span>
                <div className={styles.confidenceTrack}>
                  <div
                    className={styles.confidenceFill}
                    style={{ width: `${(d.crop?.confidence || 0) * 100}%` }}
                  />
                </div>
                <span className={styles.confidenceValue}>{d.crop?.confidence_percent}</span>
              </div>
            </div>
          </div>

          {/* ── Disease Card ── */}
          <div className={`${styles.card} ${styles.gridRight}`}>
            <div className={styles.cardHeader}>
              <div className={styles.cardHeaderIcon}><IconSearch /></div>
              <span className={styles.cardHeaderTitle}>Disease Identification</span>
            </div>
            <div className={styles.cardBody}>
              <div className={styles.diseaseName}>{d.disease?.name}</div>
              <div className={`${styles.severityBadge} ${severityClass(d.disease?.severity)}`}>
                <span className={styles.severityDot} />
                Severity: {d.disease?.severity}
              </div>
              {d.disease?.affected_area_percent != null && (
                <div className={styles.affectedArea}>
                  <div className={styles.affectedAreaHeader}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
                      <line x1="9" x2="15" y1="9" y2="15"/><line x1="15" x2="9" y1="9" y2="15"/>
                    </svg>
                    <span>Estimated Affected Area</span>
                  </div>
                  <div className={styles.affectedAreaValue}>{d.disease.affected_area_percent}% leaf surface</div>
                </div>
              )}
              <div className={styles.confidenceRow} style={{ marginTop: 16 }}>
                <span className={styles.confidenceLabel}>Confidence</span>
                <div className={styles.confidenceTrack}>
                  <div
                    className={styles.confidenceFill}
                    style={{ width: `${(d.disease?.confidence || 0) * 100}%` }}
                  />
                </div>
                <span className={styles.confidenceValue}>{d.disease?.confidence_percent}</span>
              </div>
            </div>
          </div>

          {/* ── AI Explanation ── */}
          <div className={`${styles.card} ${styles.gridFull}`}>
            <div className={styles.cardHeader}>
              <div className={styles.cardHeaderIcon}><IconBulb /></div>
              <span className={styles.cardHeaderTitle}>AI Explanation & Analysis</span>
            </div>
            <div className={styles.cardBody}>
              <p className={styles.explanation}>{d.explanation}</p>
            </div>
          </div>

          {/* ── Treatment Card ── */}
          <div className={`${styles.card} ${styles.gridFull}`}>
            <div className={styles.cardHeader}>
              <div className={styles.cardHeaderIcon}><IconPill /></div>
              <span className={styles.cardHeaderTitle}>Treatment & Care Protocol</span>
            </div>
            <div className={styles.cardBody}>
              {d.treatment_recommendations?.length > 0 ? (
                <ul className={styles.treatmentList}>
                  {d.treatment_recommendations.map((rec, i) => (
                    <li key={i} className={styles.treatmentItem}>
                      <span className={styles.treatmentNum}>{i + 1}</span>
                      <span className={styles.treatmentText}>{rec}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className={styles.explanation}>No treatment recommendations specified.</p>
              )}
            </div>
          </div>

          {/* ── Weather Card ── */}
          {d.weather && (
            <div className={`${styles.card} ${styles.gridLeft}`}>
              <div className={styles.cardHeader}>
                <div className={styles.cardHeaderIcon}><IconCloud /></div>
                <span className={styles.cardHeaderTitle}>Weather & Environment</span>
              </div>
              <div className={styles.cardBody}>
                <div className={styles.weatherGrid}>
                  <div className={styles.weatherItem}>
                    <div className={styles.weatherHeader}>
                      <IconThermometer />
                      <span className={styles.weatherLabel}>Temperature</span>
                    </div>
                    <span className={styles.weatherValue}>{d.weather.temperature_celsius}°C</span>
                  </div>
                  <div className={styles.weatherItem}>
                    <div className={styles.weatherHeader}>
                      <IconDroplet />
                      <span className={styles.weatherLabel}>Humidity</span>
                    </div>
                    <span className={styles.weatherValue}>{d.weather.humidity_percent}%</span>
                  </div>
                  {d.weather.rainfall_mm != null && (
                    <div className={styles.weatherItem}>
                      <div className={styles.weatherHeader}>
                        <IconRain />
                        <span className={styles.weatherLabel}>Precipitation</span>
                      </div>
                      <span className={styles.weatherValue}>{d.weather.rainfall_mm} mm</span>
                    </div>
                  )}
                  {d.weather.wind_speed_kmh != null && (
                    <div className={styles.weatherItem}>
                      <div className={styles.weatherHeader}>
                        <IconWind />
                        <span className={styles.weatherLabel}>Wind Speed</span>
                      </div>
                      <span className={styles.weatherValue}>{d.weather.wind_speed_kmh} km/h</span>
                    </div>
                  )}
                </div>
                {d.weather.condition && (
                  <div className={styles.weatherConditionAlert}>
                    <IconInfo />
                    <span>Forecast: {d.weather.condition}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Market Intelligence ── */}
          {d.market && (
            <div className={`${styles.card} ${d.weather ? styles.gridRight : styles.gridFull}`}>
              <div className={styles.cardHeader}>
                <div className={styles.cardHeaderIcon}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                  </svg>
                </div>
                <span className={styles.cardHeaderTitle}>Market intelligence</span>
              </div>
              <div className={styles.cardBody}>
                <div className={styles.marketPrices}>
                  <div className={`${styles.priceCard} ${styles.priceCurrent}`}>
                    <div className={styles.priceLabel}>Current market Price</div>
                    <div className={styles.priceValue}>
                      ₹{d.market.current_price_per_kg ?? '—'}/kg
                    </div>
                    <TrendBadge trend={d.market.price_trend} />
                  </div>
                  <div className={`${styles.priceCard} ${styles.pricePredicted}`}>
                    <div className={styles.priceLabel}>Expected selling Price</div>
                    <div className={styles.priceValue}>
                      ₹{d.market.predicted_price_per_kg ?? '—'}/kg
                    </div>
                    <TrendBadge trend="up" />
                  </div>
                </div>
                {d.market.recommendation && (
                  <div className={styles.marketRec}>
                    <IconInfo />
                    <span>{d.market.recommendation}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Recovery Plan (Main Feature) ── */}
          <div className={`${styles.card} ${styles.gridFull}`}>
            <div className={styles.cardHeader}>
              <div className={styles.cardHeaderIcon}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
              </div>
              <span className={styles.cardHeaderTitle}>🌾 AI Crop Recovery Plan</span>
            </div>
            <div className={styles.cardBody}>
              {/* Score header */}
              <div className={styles.timelineHeader}>
                <div className={styles.timelineHeaderLeft}>
                  <h3 className={styles.timelineHeaderTitle}>Action roadmap for crop restoration</h3>
                  <p className={styles.timelineHeaderDesc}>Follow this scheduled plan to minimize damage and restore crop health</p>
                </div>
                <div className={styles.riskScorePanel}>
                  <div className={styles.riskCircle} style={{ '--score': actionPlan.risk_score }}>
                    <div className={styles.riskCircleInner}>
                      <span className={styles.riskScoreVal}>{actionPlan.risk_score}</span>
                      <span className={styles.riskScoreMax}>/100</span>
                    </div>
                  </div>
                  <div className={styles.riskInfo}>
                    <span className={styles.riskLabel}>Overall Risk Score</span>
                    <span className={styles.riskValue}>{actionPlan.overall_risk}</span>
                    <span className={styles.riskRecovery}>Est. Recovery: {actionPlan.estimated_recovery}</span>
                  </div>
                </div>
              </div>

              {/* Recovery Timeline */}
              <div className={styles.timeline}>
                {actionPlan.timeline?.map((item, idx) => {
                  let dotColorClass = styles.dotDefault
                  if (item.statusType === 'today') dotColorClass = styles.dotToday
                  if (item.statusType === 'tomorrow') dotColorClass = styles.dotTomorrow
                  if (item.statusType === 'after3days') dotColorClass = styles.dotAfter3days
                  if (item.statusType === 'nextweek') dotColorClass = styles.dotNextweek
                  if (item.statusType === 'harvest') dotColorClass = styles.dotHarvest

                  return (
                    <div key={idx} className={styles.timelineItem}>
                      <div className={`${styles.timelineDot} ${dotColorClass}`}>
                        <div className={styles.timelineDotInner} />
                      </div>
                      <div className={styles.timelineContent}>
                        <span className={styles.timelineDay}>{item.day}</span>
                        <h4 className={styles.timelineAction}>
                          <IconCheck />
                          {item.action}
                        </h4>
                        {item.reason && <p className={styles.timelineReason}>{item.reason}</p>}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Harvest Outlook sub-card */}
              {d.market && (
                <div className={styles.harvestOutlook}>
                  <div className={styles.harvestHeader}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="20" x2="18" y2="10"/>
                      <line x1="12" y1="20" x2="12" y2="4"/>
                      <line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                    <span className={styles.harvestTitle}>📈 Harvest Outlook</span>
                  </div>
                  <div className={styles.harvestGrid}>
                    <div className={styles.harvestItem}>
                      <span className={styles.harvestItemLabel}>Expected price</span>
                      <span className={styles.harvestItemValue}>₹{d.market.predicted_price_per_kg ?? d.market.current_price_per_kg}/kg</span>
                    </div>
                    <div className={styles.harvestItem}>
                      <span className={styles.harvestItemLabel}>Selling recommendation</span>
                      <span className={styles.harvestItemValue} style={{ fontWeight: '600', fontSize: '14px' }}>
                        {d.market.recommendation || 'Analyze weather and store product for best pricing.'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}
