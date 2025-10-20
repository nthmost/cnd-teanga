# cnd-teanga

**Teanga** - Language processing toolkit for creating AI-enhanced learning materials from audio content.

Originally designed for Irish (Gaeilge) but extensible to other languages.

## Project Status

**Iteration 2 Complete** - Whisper transcription now working with GPU acceleration!

- ✅ **Iteration 1:** RSS fetching and audio processing
- ✅ **Iteration 2:** Whisper transcription with GPU support
- 🔄 **Next:** Irish language normalization (Claude/OpenAI post-processing)

See [PRODUCT/checkpoint_iteration2_transcription.md](PRODUCT/checkpoint_iteration2_transcription.md) for latest updates and [PRODUCT/poc_gaeilge.md](PRODUCT/poc_gaeilge.md) for the full vision.

## Quick Start

### Installation

```bash
# Install dependencies
pipenv install

# Activate virtual environment
pipenv shell
```

### Try RSS Fetching

```bash
python scripts/try_rss_fetch.py adhmhaidin
python scripts/try_rss_fetch.py barrscealta
```

### Try Full Audio Pipeline

```bash
python scripts/try_audio_pipeline.py adhmhaidin
```

Note: Audio conversion requires FFmpeg to be installed on your system.

### Try Transcription (NEW!)

```bash
# Extract a 5-minute test clip
pipenv run python scripts/extract_test_clip.py rnag_barrscealta_20251017_1100

# Transcribe with GPU (RECOMMENDED)
./scripts/run_with_cudnn.sh python scripts/try_transcription.py rnag_barrscealta_20251017_1100 --test-clip --model medium

# Or CPU (slower)
pipenv run python scripts/try_transcription.py rnag_barrscealta_20251017_1100 --test-clip --model medium --device cpu

# View transcript
cat data/episodes/rnag_barrscealta_20251017_1100/transcript.txt
```

**Note:** GPU transcription requires the `run_with_cudnn.sh` wrapper to set library paths correctly.

## Project Structure

```
teanga/                  # Main library package
├── utils/              # Logging, configuration
├── storage/            # Episode-centric artifact management
├── rss/                # RSS/Atom feed fetching
├── audio/              # Audio downloading and conversion
└── transcription/      # Whisper-based transcription

scripts/                # Test and demo scripts
data/episodes/          # Episode artifacts (gitignored)
PRODUCT/                # Design documents and POC specs
```

## Components

### RSS Fetcher
Fetches and parses RSS feeds from Raidió na Gaeltachta and other sources.

```python
from teanga.rss.fetcher import RSSFetcher, get_rnag_feed_url

fetcher = RSSFetcher()
feed_url = get_rnag_feed_url("nuacht")
latest = fetcher.get_latest_episode(feed_url)
```

### Audio Downloader
Downloads audio files with progress tracking.

```python
from teanga.audio.downloader import AudioDownloader

downloader = AudioDownloader()
audio_path = downloader.download_episode_audio(url, episode_id)
```

### Audio Converter
Normalizes audio to 16kHz mono WAV (Whisper-ready) and extracts clips for testing.

```python
from teanga.audio.converter import AudioConverter

converter = AudioConverter()

# Normalize full episode
normalized_path, info = converter.normalize_episode_audio(input_path, episode_id)

# Extract 5-minute clip for testing
clip_path = converter.extract_clip(
    input_path=normalized_path,
    output_path=output_path,
    start_seconds=60,    # Skip intro
    duration_seconds=300  # 5 minutes
)
```

### Whisper Transcriber
Transcribes audio using faster-whisper with GPU acceleration.

```python
from teanga.transcription.whisper import WhisperTranscriber

# Initialize with GPU
transcriber = WhisperTranscriber(
    model_size="medium",  # or large-v3 for best quality
    device="cuda"
)

# Transcribe and save all formats (JSON, TXT, VTT)
result = transcriber.transcribe_and_save(
    audio_path=audio_path,
    output_dir=transcripts_dir,
    language=None  # Auto-detect (Irish detected as Welsh)
)

print(f"Language: {result.language}")
print(f"Segments: {len(result.segments)}")
print(result.text)
```

**Note:** Irish ('ga') is not in faster-whisper's language list, so it detects as Welsh ('cy'). Post-processing with Claude/OpenAI will normalize to proper Irish.

### Episode Manager
Manages episode directory structure and metadata.

```python
from teanga.storage.manager import EpisodeManager, EpisodeMetadata

manager = EpisodeManager(episode_id, metadata)
manager.save_metadata()
manager.add_processing_step("download", status="success")
```

## Next Steps

- [x] ~~Implement Whisper transcription component~~
- [ ] **NEXT:** Irish language normalization (Claude/OpenAI post-processing)
- [ ] Build glossing and exercise generation
- [ ] Implement dialect detection
- [ ] Add Conductor workflow definitions
- [ ] Package as learning material bundles

## Known Issues

### GPU Transcription Requires Wrapper Script
Due to cuDNN library path issues, GPU transcription must use the wrapper:
```bash
./scripts/run_with_cudnn.sh python scripts/try_transcription.py [args]
```

### Irish Transcribed as Welsh
faster-whisper doesn't support Irish ('ga'), so it detects as Welsh ('cy') and uses Welsh orthography. This will be corrected in the next iteration with Claude/OpenAI normalization.

## Development Guidelines

See [CLAUDE.md](CLAUDE.md) for coding standards and collaboration guidelines.

## License

To be determined
