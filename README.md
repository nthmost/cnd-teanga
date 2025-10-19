# cnd-teanga

**Teanga** - Language processing toolkit for creating AI-enhanced learning materials from audio content.

Originally designed for Irish (Gaeilge) but extensible to other languages.

## Project Status

**Iteration 1 Complete** - RSS fetching and audio processing components ready for testing.

See [PRODUCT/iteration_1.md](PRODUCT/iteration_1.md) for detailed design decisions and [PRODUCT/poc_gaeilge.md](PRODUCT/poc_gaeilge.md) for the full vision.

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

## Project Structure

```
teanga/                  # Main library package
├── utils/              # Logging, configuration
├── storage/            # Episode-centric artifact management
├── rss/                # RSS/Atom feed fetching
└── audio/              # Audio downloading and conversion

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
Normalizes audio to 16kHz mono WAV (Whisper-ready).

```python
from teanga.audio.converter import AudioConverter

converter = AudioConverter()
normalized_path, info = converter.normalize_episode_audio(input_path, episode_id)
```

### Episode Manager
Manages episode directory structure and metadata.

```python
from teanga.storage.manager import EpisodeManager, EpisodeMetadata

manager = EpisodeManager(episode_id, metadata)
manager.save_metadata()
manager.add_processing_step("download", status="success")
```

## Next Steps

- [ ] Implement Whisper transcription component
- [ ] Add Claude/OpenAI integration for text processing
- [ ] Build glossing and exercise generation
- [ ] Implement dialect detection
- [ ] Add Conductor workflow definitions
- [ ] Package as learning material bundles

## Development Guidelines

See [CLAUDE.md](CLAUDE.md) for coding standards and collaboration guidelines.

## License

To be determined
