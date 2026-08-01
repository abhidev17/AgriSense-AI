import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { getHistory } from '../../api'
import { SkeletonHistoryItem } from '../../components/Skeleton/Skeleton'
import styles from './History.module.css'

const PAGE_SIZE = 10

/* ── SVG crop icon map ── */
const CropIcon = ({ name = '' }) => {
  const n = name.toLowerCase()
  const color =
    n.includes('tomato')  ? '#ef4444' :
    n.includes('wheat') || n.includes('maize') ? '#f59e0b' :
    n.includes('rice')    ? '#84cc16' :
    n.includes('mango') || n.includes('apple') ? '#f97316' :
    '#16a34a'

  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
    </svg>
  )
}

const severityStyle = (s = '') => {
  const sev = s.toLowerCase()
  if (sev === 'low')      return styles.sevLow
  if (sev === 'moderate') return styles.sevModerate
  if (sev === 'high')     return styles.sevHigh
  if (sev === 'critical') return styles.sevCritical
  return styles.sevUnknown
}

const formatDate = (ts) => {
  if (!ts) return 'Unknown date'
  try {
    return new Date(ts).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return ts }
}

export default function History({ toast }) {
  const [items,   setItems]   = useState([])
  const [total,   setTotal]   = useState(0)
  const [page,    setPage]    = useState(1)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const fetchHistory = useCallback(async (p = 1) => {
    setLoading(true); setError(null)
    try {
      const { data } = await getHistory(p, PAGE_SIZE)
      setItems(data.items || [])
      setTotal(data.total || 0)
      setPage(p)
    } catch (err) {
      setError(err.message || 'Failed to load history')
      toast?.error('Could not load diagnosis history')
    } finally { setLoading(false) }
  }, [toast])

  useEffect(() => { fetchHistory(1) }, [fetchHistory])

  return (
    <div className={styles.page}>
      {/* Hero */}
      <div className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroBadge}>Diagnosis Records</div>
          <h1 className={styles.heroTitle}>Diagnosis History</h1>
          <p className={styles.heroDesc}>Browse and revisit all your past crop diagnoses</p>
        </div>
      </div>

      <main className={styles.main}>
        {/* Toolbar */}
        <div className={styles.toolbar}>
          <div>
            <h2 className={styles.toolbarTitle}>
              {loading ? 'Loading records...' : `${total} Diagnosis${total !== 1 ? 'es' : ''}`}
            </h2>
            <p className={styles.toolbarSub}>Page {page} of {totalPages}</p>
          </div>
          <button
            className={styles.refreshBtn}
            onClick={() => fetchHistory(page)}
            disabled={loading}
            id="refresh-history-btn"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M8 16H3v5"/>
            </svg>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Error */}
        {error && !loading && (
          <div className={styles.errorState}>
            <div className={styles.errorIconWrap}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <h3 className={styles.errorTitle}>Failed to load history</h3>
            <p className={styles.errorDesc}>{error}</p>
            <button className={styles.retryBtn} onClick={() => fetchHistory(page)}>Try Again</button>
          </div>
        )}

        {/* Skeletons */}
        {loading && (
          <div className={styles.list}>
            {Array.from({ length: 6 }).map((_, i) => <SkeletonHistoryItem key={i} />)}
          </div>
        )}

        {/* Empty */}
        {!loading && !error && items.length === 0 && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIconWrap}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            <h2 className={styles.emptyTitle}>No diagnoses yet</h2>
            <p className={styles.emptyDesc}>
              Run your first crop diagnosis and results will appear here automatically.
            </p>
            <Link to="/diagnose" className={styles.emptyBtn}>
              Start First Diagnosis
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </Link>
          </div>
        )}

        {/* List */}
        {!loading && !error && items.length > 0 && (
          <>
            <div className={styles.list} role="list">
              {items.map((item, i) => (
                <div
                  key={item.session_id}
                  className={styles.historyCard}
                  role="listitem"
                  style={{ animationDelay: `${i * 0.04}s` }}
                >
                  <div className={styles.cardIconWrap}>
                    <CropIcon name={item.crop_name} />
                  </div>

                  <div className={styles.cardBody}>
                    <div className={styles.cardCrop}>{item.crop_name}</div>
                    <div className={styles.cardDisease}>
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                      </svg>
                      {item.disease_name}
                    </div>
                    <div className={styles.cardDate}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                      </svg>
                      {formatDate(item.timestamp)}
                    </div>
                  </div>

                  <div className={styles.cardRight}>
                    <span className={`${styles.sevBadge} ${severityStyle(item.disease_severity)}`}>
                      {item.disease_severity || 'Unknown'}
                    </span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 18l6-6-6-6"/>
                    </svg>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <nav className={styles.pagination} aria-label="Pagination">
                <button
                  className={styles.pageBtn}
                  onClick={() => fetchHistory(page - 1)}
                  disabled={page <= 1 || loading}
                  aria-label="Previous page"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 18l-6-6 6-6"/>
                  </svg>
                </button>

                {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                  const pn = Math.max(1, Math.min(totalPages - 4, page - 2)) + i
                  if (pn > totalPages) return null
                  return (
                    <button
                      key={pn}
                      className={`${styles.pageBtn} ${pn === page ? styles.pageBtnActive : ''}`}
                      onClick={() => fetchHistory(pn)}
                      disabled={loading}
                      aria-current={pn === page ? 'page' : undefined}
                    >
                      {pn}
                    </button>
                  )
                })}

                <button
                  className={styles.pageBtn}
                  onClick={() => fetchHistory(page + 1)}
                  disabled={page >= totalPages || loading}
                  aria-label="Next page"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 18l6-6-6-6"/>
                  </svg>
                </button>
              </nav>
            )}
          </>
        )}
      </main>
    </div>
  )
}
