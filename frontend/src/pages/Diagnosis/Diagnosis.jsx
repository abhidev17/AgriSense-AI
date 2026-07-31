import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { diagnoseImage } from '../../api'
import { useDiagnosis } from '../../context/DiagnosisContext'
import styles from './Diagnosis.module.css'

/* ── SVG Icons ── */
const IconUpload = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
  </svg>
)

const IconCamera = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3Z"/>
    <circle cx="12" cy="13" r="3"/>
  </svg>
)

const IconLeaf = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
  </svg>
)

const IconPin = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
    <circle cx="12" cy="10" r="3"/>
  </svg>
)

const IconSettings = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)

const IconMicroscope = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 18h8"/><path d="M3 22h18"/>
    <path d="M14 22a7 7 0 1 0 0-14h-1"/>
    <path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
    <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
  </svg>
)

const IconCapture = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3Z"/>
    <circle cx="12" cy="13" r="3"/>
  </svg>
)

const IconArrow = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M12 5l7 7-7 7"/>
  </svg>
)

const IconClock = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
)

const CROP_OPTIONS = [
  'Tomato','Potato','Pepper','Wheat','Rice','Maize','Cotton',
  'Soybean','Grape','Apple','Mango','Banana','Onion','Garlic',
  'Brinjal','Cauliflower','Cabbage','Spinach','Sugarcane',
]

export default function Diagnosis({ toast }) {
  const navigate = useNavigate()
  const { setDiagnosisResult, setIsLoading } = useDiagnosis()

  const [activeTab,  setActiveTab]   = useState('upload')
  const [image,      setImage]       = useState(null)
  const [preview,    setPreview]     = useState(null)
  const [dragOver,   setDragOver]    = useState(false)
  const fileInputRef = useRef(null)

  const videoRef  = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [cameraOn, setCameraOn] = useState(false)

  const [crop,      setCrop]      = useState('')
  const [latitude,  setLatitude]  = useState('')
  const [longitude, setLongitude] = useState('')
  const [geoLoading,  setGeoLoading]  = useState(false)
  const [submitting,  setSubmitting]  = useState(false)

  /* ── drag & drop ── */
  const onDragOver  = (e) => { e.preventDefault(); setDragOver(true) }
  const onDragLeave = () => setDragOver(false)
  const onDrop = (e) => {
    e.preventDefault(); setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleFile = (file) => {
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file (JPEG, PNG, WebP)'); return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Image must be under 10 MB'); return
    }
    setImage(file)
    setPreview(URL.createObjectURL(file))
  }

  const onFileChange = (e) => { const f = e.target.files[0]; if (f) handleFile(f) }
  const removeImage  = () => {
    setImage(null); setPreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  /* ── camera ── */
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setCameraOn(true)
    } catch {
      toast.error('Could not access camera. Please check permissions.')
    }
  }

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    setCameraOn(false)
  }

  const capturePhoto = () => {
    const video = videoRef.current; const canvas = canvasRef.current
    if (!video || !canvas) return
    canvas.width = video.videoWidth; canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    canvas.toBlob(blob => {
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
      setImage(file); setPreview(URL.createObjectURL(blob))
      stopCamera(); setActiveTab('upload')
    }, 'image/jpeg', 0.9)
  }

  /* ── geolocation ── */
  const getLocation = () => {
    if (!navigator.geolocation) { toast.error('Geolocation not supported'); return }
    setGeoLoading(true)
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLatitude(coords.latitude.toFixed(6))
        setLongitude(coords.longitude.toFixed(6))
        setGeoLoading(false)
        toast.success('Location detected')
      },
      () => { setGeoLoading(false); toast.error('Could not get location') }
    )
  }

  /* ── submit ── */
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!image) { toast.error('Please add a crop image first'); return }
    setSubmitting(true); setIsLoading(true)
    const formData = new FormData()
    formData.append('image', image)
    if (crop) formData.append('crop', crop)
    if (latitude)  formData.append('latitude',  parseFloat(latitude))
    if (longitude) formData.append('longitude', parseFloat(longitude))
    try {
      navigate('/loading')
      const { data } = await diagnoseImage(formData)
      setDiagnosisResult(data)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.message || 'Diagnosis failed. Please try again.')
      navigate('/diagnose')
    } finally {
      setSubmitting(false); setIsLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Page Hero */}
      <div className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroBadge}>AI-Powered Analysis</div>
          <h1 className={styles.heroTitle}>Crop Disease Diagnosis</h1>
          <p className={styles.heroDesc}>
            Upload a photo of your crop leaf and receive an instant AI-powered diagnosis
          </p>
        </div>
      </div>

      <main className={styles.main}>
        <form onSubmit={handleSubmit} noValidate>

          {/* ── Step 1: Image ── */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.stepBadge}>01</div>
              <div>
                <h2 className={styles.cardTitle}>Add Crop Image</h2>
                <p className={styles.cardSubtitle}>Upload from device or capture with camera</p>
              </div>
            </div>

            {/* Tabs */}
            <div className={styles.tabs} role="tablist">
              <button
                type="button" role="tab"
                className={`${styles.tab} ${activeTab === 'upload' ? styles.tabActive : ''}`}
                onClick={() => { setActiveTab('upload'); stopCamera() }}
                id="tab-upload"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
                </svg>
                Upload Image
              </button>
              <button
                type="button" role="tab"
                className={`${styles.tab} ${activeTab === 'camera' ? styles.tabActive : ''}`}
                onClick={() => { setActiveTab('camera'); startCamera() }}
                id="tab-camera"
              >
                <IconCapture />
                Camera Capture
              </button>
            </div>

            <div className={styles.cardBody}>
              {/* Upload zone (no preview) */}
              {activeTab === 'upload' && !preview && (
                <div
                  className={`${styles.dropZone} ${dragOver ? styles.dropZoneActive : ''}`}
                  onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
                  onClick={() => fileInputRef.current?.click()}
                  role="button" tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
                  aria-label="Upload crop image"
                >
                  <div className={styles.dropZoneIcon}><IconUpload /></div>
                  <p className={styles.dropZoneTitle}>Drag & drop your crop photo here</p>
                  <p className={styles.dropZoneSub}>JPEG · PNG · WebP &nbsp;·&nbsp; Max 10 MB</p>
                  <button type="button" className={styles.browseBtn}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
                    </svg>
                    Browse Files
                  </button>
                  <input
                    ref={fileInputRef} type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className={styles.fileInput}
                    onChange={onFileChange}
                    id="image-upload"
                  />
                </div>
              )}

              {/* Preview */}
              {preview && (
                <div className={styles.previewWrap}>
                  <img src={preview} alt="Crop preview" className={styles.previewImg} />
                  <div className={styles.previewOverlay}>
                    <div className={styles.previewCheckBadge}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Image ready
                    </div>
                    <button type="button" className={styles.removeBtn} onClick={removeImage}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                      Remove
                    </button>
                  </div>
                </div>
              )}

              {/* Camera */}
              {activeTab === 'camera' && (
                <div>
                  {cameraOn ? (
                    <div>
                      <div className={styles.cameraWrap}>
                        <video ref={videoRef} autoPlay playsInline muted className={styles.cameraVideo} />
                        <div className={styles.cameraGuideWrap}>
                          <div className={styles.cameraGuide} />
                          <div className={styles.cameraScanLine} />
                        </div>
                        <div className={styles.cameraLabel}>Position leaf in frame</div>
                      </div>
                      <div className={styles.cameraControls}>
                        <button type="button" className={styles.captureBtn} onClick={capturePhoto} aria-label="Capture">
                          <div className={styles.captureBtnInner} />
                        </button>
                        <button type="button" className={styles.stopBtn} onClick={stopCamera}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                          </svg>
                          Stop Camera
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className={styles.dropZone} onClick={startCamera} role="button" tabIndex={0}>
                      <div className={styles.dropZoneIcon}><IconCamera /></div>
                      <p className={styles.dropZoneTitle}>Open Camera</p>
                      <p className={styles.dropZoneSub}>Allow camera permission when prompted</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* ── Step 2: Options ── */}
          <div className={styles.card} style={{ marginTop: 20, animationDelay: '0.08s' }}>
            <div className={styles.cardHeader}>
              <div className={styles.stepBadge}>02</div>
              <div>
                <h2 className={styles.cardTitle}>Diagnosis Options</h2>
                <p className={styles.cardSubtitle}>Select crop type and location for better results</p>
              </div>
            </div>

            <div className={styles.cardBody}>
              {/* Crop Select */}
              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="crop-select">
                  <IconLeaf />
                  Crop Type
                  <span className={styles.optionalTag}>optional — AI will auto-detect</span>
                </label>
                <div className={styles.selectWrap}>
                  <select
                    id="crop-select"
                    className={styles.select}
                    value={crop}
                    onChange={e => setCrop(e.target.value)}
                  >
                    <option value="">Auto Detect (Recommended)</option>
                    {CROP_OPTIONS.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                  <svg className={styles.selectArrow} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </div>
                <p className={styles.hint}>
                  Select your crop for more accurate detection, or leave blank for AI auto-detection.
                </p>
              </div>

              {/* Location */}
              <div className={styles.formGroup}>
                <label className={styles.label}>
                  <IconPin />
                  Location Coordinates
                  <span className={styles.optionalTag}>optional — enables weather data</span>
                </label>
                <div className={styles.coordRow}>
                  <div className={styles.coordField}>
                    <label className={styles.subLabel} htmlFor="latitude">Latitude</label>
                    <input
                      id="latitude" type="number" step="any" min="-90" max="90"
                      className={styles.input}
                      placeholder="e.g. 18.5204"
                      value={latitude}
                      onChange={e => setLatitude(e.target.value)}
                    />
                  </div>
                  <div className={styles.coordField}>
                    <label className={styles.subLabel} htmlFor="longitude">Longitude</label>
                    <input
                      id="longitude" type="number" step="any" min="-180" max="180"
                      className={styles.input}
                      placeholder="e.g. 73.8567"
                      value={longitude}
                      onChange={e => setLongitude(e.target.value)}
                    />
                  </div>
                  <div className={styles.geoColumn}>
                    <label className={styles.subLabel}>&nbsp;</label>
                    <button
                      type="button" className={styles.geoBtn}
                      onClick={getLocation} disabled={geoLoading}
                      id="get-location-btn"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                        <circle cx="12" cy="10" r="3"/>
                      </svg>
                      {geoLoading ? 'Detecting...' : 'Auto Detect'}
                    </button>
                  </div>
                </div>
                <p className={styles.hint}>
                  Providing your location enables weather-based treatment recommendations.
                </p>
              </div>
            </div>
          </div>

          {/* ── Submit ── */}
          <div className={styles.submitCard}>
            <div className={styles.submitLeft}>
              <div className={styles.submitIcon}>
                <IconMicroscope />
              </div>
              <div>
                <div className={styles.submitTitle}>Ready to diagnose?</div>
                <div className={styles.submitSub}>
                  <IconClock /> Processing takes under 3 seconds
                </div>
              </div>
            </div>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={!image || submitting}
              id="diagnose-submit-btn"
            >
              {submitting ? (
                <>
                  <div className={styles.spinnerSm} />
                  Analyzing...
                </>
              ) : (
                <>
                  Run Diagnosis
                  <IconArrow />
                </>
              )}
            </button>
          </div>

          <p className={styles.privacyNote}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            Your images are processed securely and are not shared.
          </p>
        </form>
      </main>
    </div>
  )
}
