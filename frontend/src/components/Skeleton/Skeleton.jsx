import styles from './Skeleton.module.css'

export function SkeletonText({ width = '100%', height = '16px', className = '' }) {
  return (
    <div
      className={`skeleton ${styles.skeletonText} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  )
}

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`${styles.skeletonCard} ${className}`} aria-hidden="true">
      <div className={styles.cardHeader}>
        <div className={`skeleton ${styles.avatar}`} />
        <div className={styles.headerText}>
          <SkeletonText width="60%" height="18px" />
          <SkeletonText width="40%" height="14px" />
        </div>
      </div>
      <SkeletonText width="100%" height="14px" />
      <SkeletonText width="80%" height="14px" />
      <SkeletonText width="90%" height="14px" />
    </div>
  )
}

export function SkeletonHistoryItem({ className = '' }) {
  return (
    <div className={`${styles.historyItem} ${className}`} aria-hidden="true">
      <div className={`skeleton ${styles.historyImg}`} />
      <div className={styles.historyBody}>
        <SkeletonText width="50%" height="18px" />
        <SkeletonText width="35%" height="14px" />
        <SkeletonText width="25%" height="12px" />
      </div>
      <div className={`skeleton ${styles.historyBadge}`} />
    </div>
  )
}
