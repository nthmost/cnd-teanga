# 🧠 Conductor’s Gaeilge Lab

### 🎯 Goal
Build an **open-source Orkes Conductor workflow suite** that discovers, processes, and transforms **native Irish-language (Gaeilge)** audio content into **AI-enhanced learning materials** — fully automated and runnable on **Conductor OSS**.

---

### 🗺️ High-Level Idea
Conductor orchestrates multiple AIs (e.g. locally-running LLama plus Claude) and open data sources (e.g., Raidió na Gaeltachta RSS feeds) to:

1. **Fetch authentic Irish dialogue audio** automatically.
2. **Transcribe and normalize** the speech (keeping dialect cues).
3. **Generate bilingual glosses and exercises** for learners.
4. **Analyze dialect features** (Ulster, Connacht, Munster) for awareness and study.
5. **Package results** into accessible learning “scene packs” (audio + transcript + practice materials).

---

### ⚙️ Constituent Workflows

#### 🧩 1. `rnag_fetch_episode_subflow`
- **Inputs:** `{ show, when }`
- Fetches RSS feed for a Raidió na Gaeltachta show.
- Extracts latest or date-specific episode and returns `{ audioUrl, title, pubDate }`.

#### 🧩 2. `audio_ingest_subflow`
- Downloads or captures MP3/HLS stream.
- Normalizes audio via FFmpeg to 16 kHz mono WAV.
- Stores processed audio for downstream tasks.

#### 🧩 3. `scene_to_study_v2_oss`
- Transcribes audio via **OpenAI Whisper**.
- **Claude** normalizes Irish text, preserving dialect hints.
- **OpenAI** generates glosses & idiom notes.
- **Claude** builds learner exercises (Markdown/Anki-ready).
- **Packager subflow** bundles all outputs into a study pack.

#### 🧩 4. `dialect_detective_v2_oss`
- Inline JS extracts phonetic/lexical cues.
- **Claude** hypothesizes dialect (Ulster/Munster/Connacht) with reasoning.
- **OpenAI** reviews hypothesis and scores confidence.
- Inline task merges both into an HTML learner card.
- Result is stored in static storage (e.g., S3).

---

### 🔄 Workflow Chain
`rnag_fetch_episode_subflow` → `audio_ingest_subflow` → `scene_to_study_v2_oss` → triggers `dialect_detective_v2_oss`

---

### 🧰 Technical Design (OSS-Ready)
- **Task types:** `HTTP`, `INLINE (GraalJS)`, `SUB_WORKFLOW`, `SWITCH`, `FORK_JOIN_DYNAMIC`
- **LLM access:** Standard REST calls to OpenAI + Anthropic APIs
- **Resilience:** Built-in HTTP retry/circuit breaker via Resilience4j
- **Secrets:** Managed via environment variables
- ✅ 100% compatible with Conductor OSS (no enterprise-only features)

---

### 🤖 Multi-Agent Roles
- **Claude:** Linguistic normalization, pedagogy, cultural insights  
- **OpenAI:** Structured generation, glossing, scoring, summaries

---

### 🧩 Output Artifacts
- Transcribed & annotated Irish dialogue (`.json`, `.vtt`)
- English glosses and idiom explanations
- AI-generated learner exercises (`.md` or `.csv`)
- Dialect awareness card (`.html`)
- Optional bundle ZIP / Anki export for learners

---

### 🌍 Impact & Community Value
- Demonstrates **creative AI orchestration** using Conductor OSS.
- Provides **real-world cultural and educational benefit**.
- Encourages **open linguistic data use** for minority languages.
- Serves as a **template for multi-agent workflow design**.
- Extensible to other languages (e.g., Welsh, Basque, Breton).

---

### 📦 Next Steps
- [ ] Implement `rnag_fetch_episode_subflow` (RSS → audio URL)
- [ ] Integrate audio ingest and conversion worker
- [ ] Validate end-to-end Scene-to-Study run
- [ ] Add Dialect Detective card rendering
- [ ] Package into a public “AI Language Learning” cookbook example

---

**Author:** *Naomi Most*  
**Version:** *Checkpoint 1 – October 2025*

