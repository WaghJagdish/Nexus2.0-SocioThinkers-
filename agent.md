# KisanSetu — Agent Documentation

> **Version:** 2.4.0
> **Stack:** React + Vite, CSS Modules, react-router-dom, i18n (JSON locales)
> **Languages:** English, Hindi, Marathi

---

## 1. System Overview

KisanSetu is a precision agriculture platform for farm owners, agronomists, and agri-enterprises.
It provides real-time GIS intelligence, AI crop recommendations, offline-first data management,
a voice assistant, and multi-language support (EN/HI/MR).

Each page is an **agent integration surface** — a point where AI agents can read context,
trigger actions, and surface insights automatically.

---

## 2. Module Breakdown

### 2.1 Dashboard (/ — Dashboard.jsx)

**Purpose:** Primary intelligence cockpit for GIS, soil, climate, and yield data.

**Key UI Components:**
- GIS Suitability Map — hero card with Nitrogen/Yield overlay badges
- Recommendation Card — AI crop pick (Soybean, 94% Fit Score)
- Soil Diagnostics Card — texture, pH, moisture progress bars
- Nutrients (NPK) Card — animated bar chart (PPM)
- Climate Outlook Card — temperature, humidity, rain forecast
- Yield Prediction Heatmap — satellite multispectral overlay with legend

**User Interactions:**
- View GIS data → tap Generate Planting Plan
- Read soil/climate snapshot → navigate to Voice for queries
- Export yield prediction data as CSV/PDF

**Agent Integration:**
| Agent | Role |
|-------|------|
| GIS Analysis Agent | Satellite tile analysis, NDVI map updates |
| Crop Recommendation Agent | Soil + climate → optimal crop + Fit Score |
| Alert Agent | Anomaly detection → dashboard priority banner |

**Future Scope:**
- Real-time NDVI from drone/satellite APIs
- Predictive yield simulation with weather API
- Multi-field ML comparison dashboard

---

### 2.2 Fields (/fields — Fields.jsx)

**Purpose:** Field management hub with health, AI scores, and zone actions.

**Key UI Components:**
- Field Cards — gradient header, crop type, zone area, status badge
- Moisture Progress Bar — live sensor read
- AI Fit Score Bar — model confidence for current crop
- Analyze / More Actions buttons

**User Interactions:**
- Tap Analyze → field-specific GIS page
- Add new field via Add Field CTA
- Tap status badge → alert detail drill-down

**Agent Integration:**
| Agent | Role |
|-------|------|
| Field Health Agent | Sensor monitoring, anomaly flagging, badge updates |
| Harvest Timing Agent | Optimal harvest window prediction |
| Soil Action Agent | Fertilizer schedule from NPK deficits |

**Future Scope:**
- AI-generated Field Report PDF
- Automated irrigation trigger via IoT
- Satellite change-detection alerts per boundary

---

### 2.3 Voice Assistant (/voice — Voice.jsx)

**Purpose:** Hands-free natural language interface for field conditions.

**Key UI Components:**
- Animated Mic Button — gradient pulse-ripple
- Ripple Rings — 3-layer radial animation on active listening
- Waveform Visualizer — 20-bar real-time equalizer
- Transcription Card — live glassmorphic transcript
- Status Text — contextual prompt

**User Interactions:**
- Tap mic → listen → transcribe → agent route
- Query: "What is the nitrogen level in Field B?"
- Command: "Schedule harvest for corn in Zone A14"
- Multilingual response via language toggle

**Agent Integration:**
| Agent | Role |
|-------|------|
| ASR Agent | Whisper / Google STT → transcript |
| NLU/Intent Agent | Classify intent: query / command / alert |
| Field Query Agent | Fetch real-time field data answer |
| TTS Agent | Response → audio in EN/HI/MR |

**Future Scope:**
- Multilingual voice response in Marathi/Hindi dialects
- Agent memory for follow-up queries
- On-device Whisper.cpp for fully offline voice

---

### 2.4 Offline Mode (/offline — Offline.jsx)

**Purpose:** Graceful degradation when connectivity is lost; shows queued data and retry options.

**Key UI Components:**
- Offline Banner — animated cloud_off with pulsing text
- Field Status Hero — zone name + aerial image
- Pending Updates List — 3 queued items, pending badges
- Cached Weather Card — last-known temperature + glassmorphism overlay
- Offline Tips Panel — available local data hints
- Sync Notification Card — retry CTA

**User Interactions:**
- View queued pending uploads
- Tap RETRY to attempt reconnection
- Read offline tips for local data availability

**Agent Integration:**
| Agent | Role |
|-------|------|
| Connectivity Monitor Agent | Network poll, UI state triggers |
| Queue Manager Agent | Priority-ordered upload queue |
| Local Cache Agent | IndexedDB lifecycle + staleness detection |

**Future Scope:**
- Intelligent delta sync (changed records only)
- Predictive connectivity: "Tower nearby, sync in ~12 min"
- Compressed offline bundles for satellite areas

---

### 2.5 Sync Status (/sync — Sync.jsx)

**Purpose:** Real-time sync dashboard with progress, synced modules, and pending uploads.

**Key UI Components:**
- SVG Circular Progress — animated arc + percentage
- Sync Now Button — spinning icon during active sync
- Recently Synced List — Fields, Soil Data, Weather + timestamps
- Pending Uploads List — Crop Imagery 84.2 MB, Sensor Logs 12 KB
- Network Optimization Panel — satellite image + explanation

**User Interactions:**
- Tap Sync Now → manual data push trigger
- Monitor circular progress arc
- View pending upload sizes

**Agent Integration:**
| Agent | Role |
|-------|------|
| Sync Orchestrator Agent | Multi-module sync priority order |
| Compression Agent | Pre-compress imagery for upload |
| Conflict Resolution Agent | Detect + reconcile local/remote conflicts |

**Future Scope:**
- Auto-schedule sync during off-peak network windows
- AI-prioritized queue: pest alerts before bulk imagery
- Voice sync readout via TTS

---

### 2.6 Settings (/settings — Settings.jsx)

**Purpose:** User config hub for profile, preferences, data management, and support.

**Key UI Components:**
- Account Section — avatar, editable name and email inputs
- App Preferences — Offline Mode toggle, Push Notifications toggle
- Data Section — Clear Cache + Export All Data
- Support Section — Help Center + Privacy Policy links
- Version Footer — app version + brand tagline

**User Interactions:**
- Edit profile name and email
- Toggle offline mode and notifications
- Export field data for compliance/reporting
- Access help docs or privacy policy

**Agent Integration:**
| Agent | Role |
|-------|------|
| Profile Agent | Validate + persist profile to backend |
| Notification Agent | Manage push subscription by toggle state |
| Export Agent | Generate PDF/CSV report via async job |

**Future Scope:**
- Monthly AI-generated agronomist summary
- Smart notification: agent learns which alerts user acts on
- DPDP-compliant data deletion orchestration

---

## 3. i18n Architecture

| Locale  | File                    | Coverage |
|---------|-------------------------|----------|
| English | src/locales/en.json     | 100%     |
| Hindi   | src/locales/hi.json     | 100%     |
| Marathi | src/locales/mr.json     | 100%     |

- LanguageContext.jsx wraps app with useState language store
- useLanguage() hook exposes t(key) via dot-notation traversal
- Language switch re-renders all consumers instantly — no reload
- Font stack includes Noto Sans Devanagari for HI/MR script

---

## 4. Folder Structure

```
/frontend
  /src
    /assets          logo.png
    /components      Navbar.jsx, BottomNav.jsx
    /context         LanguageContext.jsx
    /layouts         MainLayout.jsx
    /locales         en.json, hi.json, mr.json
    /pages           Dashboard, Fields, Voice, Sync, Offline, Settings
    /styles          globals.css (design system tokens)
    App.jsx
    main.jsx
  index.html         SEO meta + Material Symbols CDN
  vite.config.js
  package.json
```

---

## 5. Design System Tokens

| Token        | Value                            |
|--------------|----------------------------------|
| Primary      | #00450d / #1b5e20                |
| Background   | #f7fbf1                          |
| Glass        | blur(20px) + rgba(255,255,255,0.65) |
| Radius       | 8px / 16px / 24px                |
| Font         | Manrope + Noto Sans Devanagari   |
| Shadow tint  | rgba(0,77,64,0.08)               |
| Spacing unit | 8px                              |

---

## 6. Running the Project

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build        # production bundle
```

---

## 7. Agent Integration Roadmap

```
Phase 1 (Now)   Static UI, i18n, routing, React state interactions
Phase 2         Voice page → ASR/TTS backend (FastAPI + Whisper)
Phase 3         Dashboard → GIS Agent + Crop Recommendation API
Phase 4         Sync → Firebase/Supabase + offline-first IndexedDB
Phase 5         Full multi-agent: each page owns a dedicated AI agent
```

---

*KisanSetu — Crafted for Sustainable Stewardship*
