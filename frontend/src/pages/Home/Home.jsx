import { Link } from 'react-router-dom'
import styles from './Home.module.css'

/* ── Inline SVG Icon Components ── */
const IconMicroscope = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/>
    <path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
    <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
  </svg>
)

const IconCloud = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
    <path d="M22 10a3 3 0 0 0-3-3h-2.207a5.502 5.502 0 0 0-10.702.5"/>
  </svg>
)

const IconTrendingUp = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
    <polyline points="16 7 22 7 22 13"/>
  </svg>
)

const IconCalendar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>
    <line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/>
    <line x1="3" x2="21" y1="10" y2="10"/>
    <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/>
  </svg>
)

const IconCamera = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3Z"/>
    <circle cx="12" cy="13" r="3"/>
  </svg>
)

const IconHistory = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
    <path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>
  </svg>
)

const IconUpload = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
  </svg>
)

const IconCpu = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/>
    <rect x="9" y="9" width="6" height="6"/>
    <path d="M15 2v2M15 20v2M9 2v2M9 20v2M2 15h2M20 15h2M2 9h2M20 9h2"/>
  </svg>
)

const IconBarChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" x2="18" y1="20" y2="10"/>
    <line x1="12" x2="12" y1="20" y2="4"/>
    <line x1="6" x2="6" y1="20" y2="14"/>
  </svg>
)

const IconLeaf = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
  </svg>
)

const FEATURES = [
  {
    Icon: IconMicroscope,
    color: '#16a34a',
    bg: 'rgba(22,163,74,0.1)',
    title: 'AI Disease Detection',
    desc: 'Upload a crop photo and get instant AI-powered disease identification with confidence scores and severity assessment.',
    tag: 'Core Feature',
  },
  {
    Icon: IconCloud,
    color: '#0ea5e9',
    bg: 'rgba(14,165,233,0.1)',
    title: 'Real-Time Weather',
    desc: 'Treatment recommendations adapt to current weather conditions — temperature, humidity, and rainfall forecasts.',
    tag: 'Live Data',
  },
  {
    Icon: IconTrendingUp,
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
    title: 'Market Intelligence',
    desc: 'Get current and predicted crop prices with smart sell/hold recommendations to maximize your profit.',
    tag: 'Market Data',
  },
  {
    Icon: IconCalendar,
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.1)',
    title: 'Recovery Plan',
    desc: 'A day-by-day AI recovery timeline tells you exactly what actions to take to save your crop.',
    tag: 'AI Powered',
  },
  {
    Icon: IconCamera,
    color: '#ec4899',
    bg: 'rgba(236,72,153,0.1)',
    title: 'Camera Capture',
    desc: 'Capture images directly from your device camera or upload from your gallery — works seamlessly on mobile.',
    tag: 'Mobile Ready',
  },
  {
    Icon: IconHistory,
    color: '#06b6d4',
    bg: 'rgba(6,182,212,0.1)',
    title: 'Diagnosis History',
    desc: 'All your past diagnoses are saved and accessible anytime so you can track crop health over time.',
    tag: 'Data Storage',
  },
]

const STEPS = [
  {
    num: '01',
    Icon: IconUpload,
    title: 'Upload Photo',
    desc: 'Take a photo of your crop leaf or upload one from your device gallery.',
  },
  {
    num: '02',
    Icon: IconCpu,
    title: 'AI Analyzes',
    desc: 'Our AI model scans the image and identifies diseases with 98% accuracy.',
  },
  {
    num: '03',
    Icon: IconBarChart,
    title: 'Get Results',
    desc: 'Receive a detailed diagnosis with weather context and market data.',
  },
  {
    num: '04',
    Icon: IconLeaf,
    title: 'Follow Plan',
    desc: 'Execute the day-by-day recovery plan to restore your crop to health.',
  },
]

export default function Home() {
  return (
    <div className={styles.page}>

      {/* ── Hero ── */}
      <section className={styles.hero} aria-label="Hero">
        <div className={styles.heroBg} />

        <div className={styles.heroContent}>
          <div className={styles.heroLeft}>
            <div className={styles.heroBadge}>
              <span className={styles.heroBadgeDot} />
              AI-Powered Agriculture Platform
            </div>

            <h1 className={styles.heroTitle}>
              Diagnose Crop Diseases{' '}
              <span className={styles.heroHighlight}>Instantly with AI</span>
            </h1>

            <p className={styles.heroDesc}>
              Upload a photo of your crop and receive a full AI-powered diagnosis — complete with
              treatment plans, real-time weather insights, and live market price recommendations.
            </p>

            <div className={styles.heroActions}>
              <Link to="/diagnose" className={styles.btnPrimary} id="hero-start-diagnosis">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 18h8"/><path d="M3 22h18"/>
                  <path d="M14 22a7 7 0 1 0 0-14h-1"/>
                  <path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
                  <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
                </svg>
                Start Diagnosis
              </Link>
              <Link to="/history" className={styles.btnSecondary} id="hero-view-history">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                  <path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>
                </svg>
                View History
              </Link>
            </div>

            <div className={styles.heroStats}>
              <div className={styles.stat}>
                <span className={styles.statValue}>50+</span>
                <span className={styles.statLabel}>Crops Supported</span>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.stat}>
                <span className={styles.statValue}>98%</span>
                <span className={styles.statLabel}>Accuracy Rate</span>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.stat}>
                <span className={styles.statValue}>&lt;3s</span>
                <span className={styles.statLabel}>Diagnosis Time</span>
              </div>
            </div>
          </div>

          {/* Hero Visual Card */}
          <div className={styles.heroRight}>
            <div className={styles.heroCard}>
              <div className={styles.heroCardHeader}>
                <div className={styles.heroCardDot} style={{ background: '#ef4444' }} />
                <div className={styles.heroCardDot} style={{ background: '#f59e0b' }} />
                <div className={styles.heroCardDot} style={{ background: '#22c55e' }} />
                <span className={styles.heroCardLabel}>Live Diagnosis Preview</span>
              </div>

              <div className={styles.heroCardImage}>
                <div className={styles.heroCardScanLine} />
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="1.5">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                </svg>
                <div className={styles.heroCardBadgeAI}>AI Scanning...</div>
              </div>

              <div className={styles.heroCardResult}>
                <div className={styles.resultRow}>
                  <span className={styles.resultKey}>Crop</span>
                  <span className={`${styles.resultVal} ${styles.green}`}>Tomato</span>
                </div>
                <div className={styles.resultRow}>
                  <span className={styles.resultKey}>Disease</span>
                  <span className={styles.resultVal}>Early Blight</span>
                </div>
                <div className={styles.resultRow}>
                  <span className={styles.resultKey}>Severity</span>
                  <span className={`${styles.resultVal} ${styles.orange}`}>Medium</span>
                </div>
                <div className={styles.resultRow}>
                  <span className={styles.resultKey}>Confidence</span>
                  <div className={styles.confRow}>
                    <div className={styles.barTrack}>
                      <div className={styles.barFill} style={{ width: '97%' }} />
                    </div>
                    <span className={`${styles.resultVal} ${styles.green}`}>97%</span>
                  </div>
                </div>
                <div className={styles.resultRow}>
                  <span className={styles.resultKey}>Market</span>
                  <span className={`${styles.resultVal} ${styles.green}`}>
                    ₹24/kg
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                      <polyline points="16 7 22 7 22 13"/>
                    </svg>
                  </span>
                </div>
              </div>
            </div>

            {/* Floating pills */}
            <div className={`${styles.floatPill} ${styles.floatPill1}`}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Disease Identified
            </div>
            <div className={`${styles.floatPill} ${styles.floatPill2}`}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" strokeWidth="2.5">
                <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
              </svg>
              Weather Checked
            </div>
            <div className={`${styles.floatPill} ${styles.floatPill3}`}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2.5">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
                <polyline points="16 7 22 7 22 13"/>
              </svg>
              Market Updated
            </div>
          </div>
        </div>
      </section>

      {/* ── Trusted By Banner ── */}
      <div className={styles.trustBanner}>
        <div className={styles.trustInner}>
          <span className={styles.trustLabel}>Trusted by farmers growing</span>
          {['Tomato', 'Wheat', 'Rice', 'Cotton', 'Potato', 'Maize', 'Mango'].map(crop => (
            <span key={crop} className={styles.trustCrop}>{crop}</span>
          ))}
        </div>
      </div>

      {/* ── Features ── */}
      <section className={styles.features} aria-label="Features">
        <div className={styles.featuresInner}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionLabel}>Why AgriSense AI</span>
            <h2 className={styles.sectionTitle}>
              Everything you need to<br />protect your crops
            </h2>
            <p className={styles.sectionDesc}>
              From AI disease detection to market timing — AgriSense AI gives farmers
              the intelligence they need to maximize yield and profit.
            </p>
          </div>

          <div className={styles.featureGrid}>
            {FEATURES.map((f, i) => (
              <article
                key={f.title}
                className={styles.featureCard}
                style={{ animationDelay: `${i * 0.08}s` }}
              >
                <div className={styles.featureTopRow}>
                  <div
                    className={styles.featureIconWrap}
                    style={{ background: f.bg, color: f.color }}
                  >
                    <f.Icon />
                  </div>
                  <span className={styles.featureTag} style={{ color: f.color, background: f.bg }}>
                    {f.tag}
                  </span>
                </div>
                <h3 className={styles.featureTitle}>{f.title}</h3>
                <p className={styles.featureDesc}>{f.desc}</p>
                <div className={styles.featureArrow} style={{ color: f.color }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                  Learn more
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className={styles.howItWorks} aria-label="How it works">
        <div className={styles.howItWorksInner}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionLabel}>Simple Process</span>
            <h2 className={styles.sectionTitle}>Diagnosis in 4 simple steps</h2>
            <p className={styles.sectionDesc}>
              From photo to recovery plan in under 10 seconds. No expertise required.
            </p>
          </div>

          <div className={styles.stepsGrid}>
            {STEPS.map((s, i) => (
              <div key={s.title} className={styles.step}>
                <div className={styles.stepTop}>
                  <div className={styles.stepNum}>{s.num}</div>
                  {i < STEPS.length - 1 && <div className={styles.stepConnector} />}
                </div>
                <div className={styles.stepIconWrap}>
                  <s.Icon />
                </div>
                <h3 className={styles.stepTitle}>{s.title}</h3>
                <p className={styles.stepDesc}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats Section ── */}
      <section className={styles.statsSection}>
        <div className={styles.statsInner}>
          {[
            { value: '50+', label: 'Crop Varieties', sub: 'Supported for diagnosis' },
            { value: '98%', label: 'Accuracy Rate', sub: 'AI disease detection' },
            { value: '<3s', label: 'Response Time', sub: 'Average diagnosis speed' },
            { value: '6+', label: 'Data Sources', sub: 'Weather, market & AI' },
          ].map(s => (
            <div key={s.label} className={styles.statCard}>
              <div className={styles.statCardValue}>{s.value}</div>
              <div className={styles.statCardLabel}>{s.label}</div>
              <div className={styles.statCardSub}>{s.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className={styles.ctaBanner} aria-label="Call to action">
        <div className={styles.ctaBannerInner}>
          <div className={styles.ctaBannerIcon}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
              <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
            </svg>
          </div>
          <h2 className={styles.ctaBannerTitle}>Ready to protect your harvest?</h2>
          <p className={styles.ctaBannerDesc}>
            Get an instant AI diagnosis for your crops — completely free.
            No sign-up required.
          </p>
          <div className={styles.ctaBannerActions}>
            <Link to="/diagnose" className={styles.ctaBannerBtn} id="cta-start-diagnosis">
              Start Free Diagnosis
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </Link>
            <Link to="/history" className={styles.ctaBannerBtnSec}>
              View Past Diagnoses
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <div className={styles.footerBrand}>
            <div className={styles.footerLogo}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
              </svg>
              AgriSense AI
            </div>
            <span className={styles.footerTagline}>AI-powered crop intelligence for every farmer</span>
          </div>
          <div className={styles.footerLinks}>
            <Link to="/" className={styles.footerLink}>Home</Link>
            <Link to="/diagnose" className={styles.footerLink}>Diagnose</Link>
            <Link to="/history" className={styles.footerLink}>History</Link>
          </div>
          <span className={styles.footerCopy}>© 2025 AgriSense AI. Built for farmers.</span>
        </div>
      </footer>
    </div>
  )
}
