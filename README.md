# AI-CONTENT-AUTOMATION

> A complete, locally-run AI-powered content production system targeting 3 videos per day.
> Built with Python, FFmpeg, Streamlit, and free/open-source tools.

---

## Three Independent Engines

| Engine | Purpose | Status |
|--------|---------|--------|
| ✂️ **AI Shorts Generator** | Auto-generate original short videos in 6 categories | Phase 5 |
| 🎮 **Streamer Clipper** | Find and clip highlights from authorised streamer content | Phase 6 |
| 📺 **AI YouTuber Engine** | Create original challenge/storytelling videos | Phase 7 |

---

## Quick Start

### Prerequisites

Install these before running:

1. **Python 3.11+** — [python.org](https://www.python.org/downloads/)  
   ⚠️ Check "Add Python to PATH" during installation

2. **FFmpeg (full build)** — [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)  
   Extract to `C:\ffmpeg\` and add `C:\ffmpeg\bin` to your PATH

3. **Git** — [git-scm.com](https://git-scm.com/download/win)

4. **Ollama** (optional, for local AI) — [ollama.com](https://ollama.com/download/windows)  
   After installing: `ollama pull llama3.2:3b`

### Installation

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up configuration
copy .env.example .env
# Edit .env with your API keys (see Configuration below)

# 4. Initialise the system
python main.py init

# 5. Check dependencies
python main.py check
```

### Launch Dashboard

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Launch dashboard
python main.py dashboard
# Opens at http://localhost:8501
```

### Start Scheduler

```powershell
# In a separate terminal (keep open while computer is on)
.venv\Scripts\Activate.ps1
python main.py scheduler
```

> ⚠️ **Windows Limitation:** The scheduler requires this computer to stay on and awake.
> It cannot produce videos while the computer is off, asleep, or hibernating.

---

## Configuration

Copy `.env.example` to `.env` and configure:

### Required for AI features

```env
# Get free key at: https://aistudio.google.com
GEMINI_API_KEY=your_key_here
```

### Required for stock footage

```env
# Free API at: https://www.pexels.com/api/
PEXELS_API_KEY=your_key_here

# Free API at: https://pixabay.com/api/docs/
PIXABAY_API_KEY=your_key_here
```

### Required for YouTube publishing

```env
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_ENABLED=true
```

---

## Project Structure

```
AI-CONTENT-AUTOMATION/
├── main.py                    # CLI entry point
├── config.py                  # All configuration
├── requirements.txt
├── .env.example               # Configuration template
│
├── engines/
│   ├── ai_shorts/             # Engine 1: AI Shorts (Phase 5)
│   ├── streamer_clipper/      # Engine 2: Streamer Clipper (Phase 6)
│   └── youtuber_engine/       # Engine 3: YouTuber Engine (Phase 7)
│
├── ai/                        # Shared AI services (Phase 3)
├── audio/                     # TTS + transcription (Phase 4)
├── video/                     # FFmpeg rendering (Phase 4)
├── integrations/              # Platform APIs (Phase 8)
├── publishers/                # Publishing queue (Phase 8)
├── permissions/               # Permission manager
├── scheduler/                 # Daily scheduler (Phase 9)
├── database/                  # SQLite + schema
├── analytics/                 # Analytics engine (Phase 9)
├── dashboard/                 # Streamlit dashboard
├── generated/                 # Output videos, audio, thumbnails
├── assets/                    # Licensed music, SFX, fonts
├── logs/                      # Application logs
└── tests/                     # Tests for all modules
```

---

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Architecture & Environment | ✅ Complete |
| 2 | Project Foundation | ✅ Complete |
| 3 | Shared AI Services | 🔜 Next |
| 4 | Audio & Video Services | ⏳ Planned |
| 5 | Engine 1 — AI Shorts | ⏳ Planned |
| 6 | Engine 2 — Streamer Clipper | ⏳ Planned |
| 7 | Engine 3 — YouTuber Engine | ⏳ Planned |
| 8 | Publishing Integrations | ⏳ Planned |
| 9 | Scheduler & Analytics | ⏳ Planned |
| 10 | Full Testing | ⏳ Planned |
| 11 | Final Setup & Docs | ⏳ Planned |

---

## Cost Summary

| Feature | Cost |
|---------|------|
| Python, FFmpeg, SQLite | Free |
| Streamlit dashboard | Free |
| Gemini Flash API (1,500 req/day) | Free |
| Ollama local AI | Free |
| edge-tts voice generation | Free |
| Whisper transcription (local) | Free |
| Pexels + Pixabay stock footage | Free |
| YouTube publishing (≤6 uploads/day) | Free |
| **Total (baseline)** | **₹0/month** |

Paid features are only used if you explicitly configure and enable them.

---

## Hardware Requirements

| Component | Minimum | Your System |
|-----------|---------|-------------|
| CPU | 4 cores | ✅ Ryzen 7 7445HS (8c/16t) |
| RAM | 8 GB | ✅ 16 GB |
| GPU | Optional (CPU fallback) | ✅ RTX 3050 4GB (NVENC) |
| Storage | 50 GB free | ✅ 512 GB SSD |
| OS | Windows 10/11 | ✅ Windows 11 |

---

## Running Tests

```powershell
.venv\Scripts\Activate.ps1
pytest tests/ -v
```

---

## Security Notes

- Never commit `.env` (it's in `.gitignore`)
- API keys and tokens are stored in environment variables only
- OAuth tokens are stored encrypted in the local database
- No credentials are exposed in logs
- Platform connections use official OAuth flows only

---

## Legal & Copyright

- Only licensed or original content is used
- Streamer Clipper requires explicit creator permission for all footage
- No browser automation, scraping, or unofficial API workarounds
- Platform ToS is respected for all integrations

---

## License

This project is for personal use. All third-party services, APIs, and media
must be used in accordance with their respective terms of service.
