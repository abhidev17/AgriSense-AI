import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDiagnosis } from '../../context/DiagnosisContext'
import styles from './Loading.module.css'

const STEPS = [
  {
    label: 'Analyzing Crop',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
        <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
      </svg>
    ),
  },
  {
    label: 'Detecting Disease',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
    ),
  },
  {
    label: 'Generating Explanation',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  },
  {
    label: 'Checking Weather',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
      </svg>
    ),
  },
  {
    label: 'Checking Market Prices',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
        <polyline points="16 7 22 7 22 13"/>
      </svg>
    ),
  },
  {
    label: 'Preparing Recovery Plan',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
        <line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/>
        <line x1="3" x2="21" y1="10" y2="10"/>
      </svg>
    ),
  },
]

export default function Loading() {
  const navigate = useNavigate()
  const { diagnosisResult, isLoading } = useDiagnosis()
  const [currentStep, setCurrentStep] = useState(0)
  const [progress,    setProgress]    = useState(0)

  useEffect(() => {
    if (diagnosisResult && !isLoading) navigate('/dashboard', { replace: true })
  }, [diagnosisResult, isLoading, navigate])

  useEffect(() => {
    if (!isLoading) {
      const t = setTimeout(() => navigate('/', { replace: true }), 2000)
      return () => clearTimeout(t)
    }
  }, [isLoading, navigate])

  useEffect(() => {
    let idx = 0
    const si = setInterval(() => { idx = (idx + 1) % STEPS.length; setCurrentStep(idx) }, 1500)
    let p = 0
    const pi = setInterval(() => { p = Math.min(p + 1.4, 90); setProgress(p) }, 120)
    return () => { clearInterval(si); clearInterval(pi) }
  }, [])

  return (
    <div className={styles.page}>
      <div className={styles.container}>

        {/* Scanner */}
        <div className={styles.scanner}>
          <div className={styles.ripple1} /><div className={styles.ripple2} /><div className={styles.ripple3} />
          <div className={styles.outerRing} />
          <div className={styles.innerRing} />
          <div className={styles.core}>
            <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
              <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
            </svg>
          </div>
          <div className={styles.scanLine} />
        </div>

        {/* Title */}
        <h1 className={styles.title}>AI is analyzing your crop</h1>
        <p className={styles.subtitle}>This usually takes 2–5 seconds</p>

        {/* Active Step */}
        <div className={styles.activeStep} key={currentStep}>
          <div className={styles.activeDot} />
          <span className={styles.activeStepIcon}>{STEPS[currentStep].icon}</span>
          <span className={styles.activeStepText}>{STEPS[currentStep].label}</span>
        </div>

        {/* Progress */}
        <div className={styles.progressWrap}>
          <div
            className={styles.progressBar}
            role="progressbar"
            aria-valuenow={Math.round(progress)}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div className={styles.progressFill} style={{ width: `${progress}%` }} />
            <div className={styles.progressGlow} style={{ left: `${progress}%` }} />
          </div>
          <div className={styles.progressLabels}>
            <span>Processing...</span>
            <span>{Math.round(progress)}%</span>
          </div>
        </div>

        {/* Checklist */}
        <ul className={styles.checklist} aria-label="Processing steps">
          {STEPS.map((s, i) => (
            <li
              key={s.label}
              className={`${styles.checkItem} ${i < currentStep ? styles.done : ''} ${i === currentStep ? styles.current : ''}`}
            >
              <div className={styles.checkIcon}>
                {i < currentStep ? (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : i === currentStep ? (
                  <div className={styles.checkDot} />
                ) : (
                  <div className={styles.checkEmpty} />
                )}
              </div>
              <span className={styles.checkLabel}>{s.label}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
