# AgriSense AI — Frontend

A modern, professional React + Vite frontend for the AgriSense AI plant disease diagnosis platform.

## Tech Stack

| Tool | Purpose |
|------|---------|
| React 18 | UI library |
| Vite 5 | Build tool & dev server |
| React Router v6 | Client-side routing |
| Axios | HTTP client for REST API |
| CSS Modules | Scoped component styling |

## Features

- 🔬 **Crop Diagnosis** — Upload or capture crop images for AI analysis
- 📷 **Camera Capture** — Use device camera with real-time preview
- 🌿 **Auto Crop Detection** — AI auto-detects crop type or manual selection from 20+ crops
- 📍 **Geolocation** — Auto-detect GPS coordinates for weather-based recommendations
- 🌦️ **Weather Integration** — Real-time weather data enriches treatment plans
- 📈 **Market Intelligence** — Current & predicted crop prices with sell/hold advice
- 🗺️ **AI Recovery Timeline** — Beautiful vertical timeline with day-by-day action plan
- 📋 **Diagnosis History** — Paginated history with skeleton loading
- 🔔 **Toast Notifications** — Success/error/warning/info toasts with progress bars
- 📱 **Fully Responsive** — Mobile, tablet, and desktop layouts

## Getting Started

### Prerequisites
- Node.js 18+
- AgriSense AI backend running at `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:3000**

## Pages & Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Hero, features, how-it-works, CTA |
| `/diagnose` | Diagnosis | Upload/camera, crop select, coordinates |
| `/loading` | Loading | Animated AI scanning screen |
| `/dashboard` | Dashboard | Full results with recovery plan |
| `/history` | History | Paginated diagnosis history |
| `*` | 404 | Not Found page |

## Backend API Endpoints

All requests target `http://localhost:8000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/diagnose` | Submit image for diagnosis (multipart/form-data) |
| `GET` | `/history` | Paginated list of past diagnoses |
| `GET` | `/history/{id}` | Single diagnosis detail |
| `GET` | `/weather` | Weather by lat/lng |
| `GET` | `/market` | Market price by crop name |

### POST /diagnose Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | ✅ | Crop image (JPEG/PNG/WebP, max 10MB) |
| `crop` | string | ❌ | Crop name (omit for auto-detect) |
| `latitude` | float | ❌ | GPS latitude for weather |
| `longitude` | float | ❌ | GPS longitude for weather |

## Project Structure

```
src/
├── api/
│   └── index.js          # Axios instance + all API functions
├── components/
│   ├── Navbar/            # Responsive navbar with mobile menu
│   ├── Toast/             # Toast notification system
│   └── Skeleton/          # Loading skeleton components
├── context/
│   └── DiagnosisContext.jsx  # Shared diagnosis result state
├── hooks/
│   └── useToast.js        # Toast state management hook
├── pages/
│   ├── Home/              # Landing page with hero & features
│   ├── Diagnosis/         # Upload form with camera & geo
│   ├── Loading/           # Animated AI loading screen
│   ├── Dashboard/         # Results dashboard + recovery plan
│   ├── History/           # Paginated diagnosis history
│   └── NotFound/          # 404 page
├── styles/
│   └── global.css         # Design system tokens & animations
├── App.jsx                # Router + providers
└── main.jsx               # React entry point
```

## Design System

- **Primary:** `#16a34a` (Agriculture Green)
- **Background:** `#f0fdf4` (Light Green Tint)
- **Typography:** Inter (Google Fonts)
- **Glassmorphism** cards and navbar
- **Smooth animations** with CSS keyframes
- **Mobile-first** responsive design
