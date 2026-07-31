import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

// ── Request interceptor ──
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// ── Response interceptor ──
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

// ── API Functions ──

/**
 * POST /diagnose
 * @param {FormData} formData - contains: image (File), crop?, latitude?, longitude?
 */
export const diagnoseImage = (formData) =>
  api.post('/diagnose', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

/**
 * GET /history
 * @param {number} page
 * @param {number} pageSize
 */
export const getHistory = (page = 1, pageSize = 20) =>
  api.get('/history', { params: { page, page_size: pageSize } })

/**
 * GET /history/:sessionId
 */
export const getHistoryDetail = (sessionId) =>
  api.get(`/history/${sessionId}`)

/**
 * DELETE /history/:sessionId
 */
export const deleteHistory = (sessionId) =>
  api.delete(`/history/${sessionId}`)

/**
 * GET /weather
 */
export const getWeather = (latitude, longitude) =>
  api.get('/weather', { params: { latitude, longitude } })

/**
 * GET /market
 */
export const getMarket = (crop) =>
  api.get('/market', { params: { crop } })

/**
 * GET /health
 */
export const getHealth = () =>
  api.get('/health')

export default api
