# Iteration 1: Foundation & Component Design

**Date:** October 18, 2025
**Focus:** RSS Fetching & Audio Processing Components

---

## 🎯 Goals

Build standalone, testable components for:
1. RSS feed fetching (Raidió na Gaeltachta)
2. Audio downloading and format conversion
3. Supporting infrastructure (logging, config, storage)

**Philosophy:** Build components as if we're NOT using Conductor, validate they work independently, then orchestrate later.

---

## 🏗️ Architecture Decisions

### Package Structure: `teanga`

**Decision:** Create a reusable Python library called `teanga` (Irish for "language")

**Rationale:**
- Clean imports: `from teanga.rss import fetch_episode`
- Culturally relevant but abstract enough to generalize beyond Irish
- Future-proofs for multi-language expansion
- Allows code reuse across different orchestration approaches

**Structure:**
```
cnd-teanga/
├── teanga/                    # Main library package
│   ├── __init__.py
│   ├── utils/                 # Shared utilities
│   │   ├── __init__.py
│   │   ├── logging.py         # Rich-based colorized logging
│   │   └── config.py          # Environment & configuration
│   ├── storage/               # Artifact management
│   │   ├── __init__.py
│   │   └── manager.py         # Episode-centric storage
│   ├── rss/                   # RSS feed handling
│   │   ├── __init__.py
│   │   └── fetcher.py
│   └── audio/                 # Audio processing
│       ├── __init__.py
│       ├── downloader.py
│       └── converter.py
├── scripts/                   # Test/demo scripts
│   ├── test_rss_fetch.py
│   └── test_audio_pipeline.py
├── data/                      # Episode artifacts (gitignored)
│   └── episodes/
├── tests/                     # Unit tests
├── Pipfile                    # Dependencies
├── CLAUDE.md                  # AI collaboration guidelines
└── README.md
```

---

## 📦 Storage Architecture: Episode-Centric (Option A)

**Decision:** Hierarchical organization by episode with all related artifacts grouped together

**Structure:**
```
data/episodes/{episode_id}/
├── metadata.json              # Episode metadata, processing history
├── media/
│   ├── original.mp3           # Original download
│   ├── normalized.wav         # 16kHz mono processed audio
│   └── checksum.txt
├── transcripts/
│   ├── raw_whisper.json       # Unprocessed Whisper output
│   ├── normalized.txt         # Claude-normalized Irish text
│   └── subtitles.vtt          # Timed captions
├── glosses/
│   ├── bilingual.json         # Word/phrase translations
│   └── idioms.json            # Cultural/idiomatic notes
├── exercises/
│   ├── learner_exercises.md   # Practice materials
│   └── anki_deck.csv          # Flashcard export
└── analysis/
    ├── dialect_card.html      # Visual dialect summary
    └── dialect_analysis.json  # Machine-readable dialect data
```

**Episode ID Format:** `{source}_{show}_{date}_{time}` (e.g., `rnag_nuacht_20251018_1800`)

**Rationale:**
✅ **Human-readable** - Easy to browse, inspect, debug
✅ **Self-contained** - All related artifacts stay together
✅ **Simple backup/sharing** - Zip a folder, share complete episode
✅ **Clear lineage** - See progression from raw → processed → output
✅ **Works with logs** - Can store processing logs per episode
✅ **Easy cleanup** - Delete failed runs by removing folder

**Trade-off:** Slight storage duplication if same audio processed multiple ways (acceptable for clarity/simplicity)

**Metadata Schema:**
```json
{
  "episode_id": "rnag_nuacht_20251018_1800",
  "source": "raidio_na_gaeltachta",
  "show": "nuacht",
  "title": "Nuacht a hOcht",
  "pub_date": "2025-10-18T18:00:00Z",
  "duration_seconds": 420,
  "original_url": "https://...",
  "audio_checksum": "sha256:...",
  "processing_history": [
    {"step": "download", "timestamp": "...", "status": "success"},
    {"step": "normalize", "timestamp": "...", "status": "success"}
  ]
}
```

---

## 🛠️ Technology Choices

### Logging: `rich`

**Decision:** Use the `rich` library for console output and logging

**Rationale:**
- Beautiful colorized output with emoji support
- Built-in progress bars for downloads/processing
- Structured logging that's both human and machine-readable
- Excellent for debugging complex orchestrations
- Logs will be consumed by AI agents - needs to be clear

**Logging Standards:**
- `INFO` → Key milestones, successful operations 🟢
- `DEBUG` → Detailed diagnostics, data dumps 🔍
- `WARNING` → Unexpected but recoverable issues ⚠️
- `ERROR` → Operation failures ❌
- `CRITICAL` → System-level failures 🔥

### Dependencies

```toml
[packages]
rich = "*"              # Beautiful logging and console output
feedparser = "*"        # RSS/Atom feed parsing
requests = "*"          # HTTP downloads with progress
pydantic = "*"          # Data validation schemas
python-dotenv = "*"     # Environment variable management
ffmpeg-python = "*"     # FFmpeg wrapper for audio conversion
```

### Python Version
**Target:** Python 3.12 (already specified in Pipfile)

---

## 🎭 Component Responsibilities

### 1. RSS Fetcher (`teanga/rss/fetcher.py`)
- Fetch RSS/Atom feeds from URLs
- Parse XML and extract episode metadata
- Filter by date or show criteria
- Extract audio URLs (handle MP3, HLS streams)
- Return: `{audioUrl, title, pubDate, description}`

### 2. Audio Downloader (`teanga/audio/downloader.py`)
- Download audio files via HTTP
- Progress tracking with rich progress bars
- Handle direct MP3 and streaming formats
- Checksum generation for deduplication
- Store in episode-centric structure

### 3. Audio Converter (`teanga/audio/converter.py`)
- FFmpeg wrapper for format conversion
- Normalize to 16kHz mono WAV (Whisper-ready)
- Validate audio quality (duration, sample rate)
- Preserve original, store converted version

### 4. Storage Manager (`teanga/storage/manager.py`)
- Create/manage episode directory structures
- Read/write metadata.json
- Track processing history
- Helper methods for artifact paths
- Validation and cleanup utilities

### 5. Logging Utility (`teanga/utils/logging.py`)
- Configure rich logging with colors/emojis
- Support log level filtering
- Format logs for human AND agent consumption
- Provide consistent logger across all modules

### 6. Config Management (`teanga/utils/config.py`)
- Load environment variables
- Manage base paths (data directory, cache, temp)
- API key management (OpenAI, Anthropic)
- Configurable settings with sensible defaults

---

## 📋 Implementation Order

1. ✅ Project structure
2. ✅ Dependencies (Pipfile)
3. 🔄 Logging utilities
4. 🔄 Configuration management
5. 🔄 Storage manager
6. 🔄 RSS fetcher
7. 🔄 Audio downloader
8. 🔄 Audio converter
9. 🔄 Integration testing

---

## 🔮 Future Considerations

- **Conductor Integration:** Components designed to work standalone OR as Conductor workers
- **Multi-language Support:** Structure supports extension beyond Irish (Welsh, Basque, etc.)
- **Caching Strategy:** May add content-addressable storage later for deduplication
- **Database Index:** If episode catalog grows large, add SQLite index
- **Cloud Storage:** S3/GCS adapters can be added to storage manager

---

## 🎓 Key Principles Followed

1. **Component Isolation** - Each piece works independently
2. **Observability First** - Rich logging built in from the start
3. **Human-Friendly** - Directory structure and logs optimized for humans
4. **Machine-Readable** - JSON metadata and structured logs for automation
5. **Conductor-OSS Only** - No enterprise-only features assumed
6. **Exception Specificity** - No generic Exception catches, focused error handling
7. **Fail Clearly** - Errors are loud, informative, and actionable

---

**Next Iteration Preview:** Transcription & AI processing (Whisper, Claude, OpenAI integration)
