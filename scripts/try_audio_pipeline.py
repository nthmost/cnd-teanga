#!/usr/bin/env python3
"""
Test script for the complete audio pipeline: RSS → Download → Convert.

Usage:
    python scripts/test_audio_pipeline.py [show_name]

Examples:
    python scripts/test_audio_pipeline.py nuacht
    python scripts/test_audio_pipeline.py  # uses default 'nuacht'
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import teanga
sys.path.insert(0, str(Path(__file__).parent.parent))

from teanga.audio.converter import AudioConverter, FFmpegNotFoundError
from teanga.audio.downloader import AudioDownloader
from teanga.rss.fetcher import RSSFetcher, get_rnag_feed_url
from teanga.storage.manager import EpisodeManager, EpisodeMetadata, create_episode_id
from teanga.utils.logging import setup_logger

logger = setup_logger(__name__, level="INFO")


def main():
    """Test the complete audio pipeline."""
    # Get show name from command line or use default
    show = sys.argv[1] if len(sys.argv) > 1 else "nuacht"

    logger.info(f"🎯 Testing audio pipeline for show: {show}")
    logger.info("=" * 60)

    # Step 1: Fetch RSS feed
    logger.info("\n📡 Step 1: Fetching RSS feed...")
    feed_url = get_rnag_feed_url(show)
    if not feed_url:
        logger.error(f"No feed URL found for show: {show}")
        return 1

    fetcher = RSSFetcher(timeout=30)

    try:
        latest = fetcher.get_latest_episode(feed_url)
        if not latest:
            logger.error("No episodes found in feed")
            return 1

        logger.info(f"✅ Found latest episode: {latest.title}")
        logger.info(f"   Published: {latest.pub_date}")
        logger.info(f"   Audio URL: {latest.audio_url}")

    except Exception as e:
        logger.error(f"Failed to fetch RSS feed: {e}", exc_info=True)
        return 1

    # Step 2: Create episode metadata and storage
    logger.info("\n📁 Step 2: Setting up episode storage...")

    try:
        # Create episode ID
        pub_date = latest.pub_date or datetime.utcnow()
        episode_id = create_episode_id("rnag", show, pub_date)
        logger.info(f"   Episode ID: {episode_id}")

        # Create episode metadata
        metadata = EpisodeMetadata(
            episode_id=episode_id,
            source="raidio_na_gaeltachta",
            show=show,
            title=latest.title,
            pub_date=latest.pub_date,
            duration_seconds=latest.duration_seconds,
            original_url=latest.audio_url,
        )

        # Create episode manager
        manager = EpisodeManager(episode_id, metadata)
        manager.save_metadata()
        manager.add_processing_step("rss_fetch", status="success")

        logger.info(f"✅ Episode storage created: {manager.episode_dir}")

    except Exception as e:
        logger.error(f"Failed to set up storage: {e}", exc_info=True)
        return 1

    # Step 3: Download audio
    logger.info("\n⬇️  Step 3: Downloading audio...")

    try:
        downloader = AudioDownloader(timeout=300)
        audio_path = downloader.download_episode_audio(
            latest.audio_url,
            episode_id,
            show_progress=True,
        )

        logger.info(f"✅ Audio downloaded: {audio_path}")

        # Compute checksum
        checksum = manager.set_audio_checksum(audio_path)
        logger.info(f"   Checksum: {checksum[:16]}...")

        manager.add_processing_step("download", status="success", details={
            "file_path": str(audio_path),
            "file_size": audio_path.stat().st_size,
        })

    except Exception as e:
        logger.error(f"Failed to download audio: {e}", exc_info=True)
        manager.add_processing_step("download", status="failed", details={"error": str(e)})
        return 1

    # Step 4: Convert audio
    logger.info("\n🔄 Step 4: Converting audio to normalized format...")

    try:
        converter = AudioConverter()
        normalized_path, audio_info = converter.normalize_episode_audio(audio_path, episode_id)

        logger.info(f"✅ Audio converted: {normalized_path}")
        logger.info(f"   Format: {audio_info['codec']} @ {audio_info['sample_rate']}Hz, {audio_info['channels']} channel(s)")
        logger.info(f"   Duration: {audio_info['duration']:.2f}s")

        # Update metadata with duration
        manager.metadata.duration_seconds = int(audio_info['duration'])
        manager.add_processing_step("normalize", status="success", details={
            "output_path": str(normalized_path),
            "sample_rate": audio_info['sample_rate'],
            "channels": audio_info['channels'],
            "duration_seconds": audio_info['duration'],
        })

    except FFmpegNotFoundError as e:
        logger.error(f"FFmpeg not found: {e}")
        logger.warning("⚠️  Skipping audio conversion step (FFmpeg not installed)")
        manager.add_processing_step("normalize", status="failed", details={"error": "FFmpeg not found"})
    except Exception as e:
        logger.error(f"Failed to convert audio: {e}", exc_info=True)
        manager.add_processing_step("normalize", status="failed", details={"error": str(e)})
        return 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Pipeline test completed successfully!")
    logger.info(f"\n📊 Summary:")
    logger.info(f"   Episode ID: {episode_id}")
    logger.info(f"   Title: {latest.title}")
    logger.info(f"   Storage: {manager.episode_dir}")
    logger.info(f"\n   Files created:")
    logger.info(f"   - {manager.metadata_path.name}")
    logger.info(f"   - media/{audio_path.name}")
    if normalized_path.exists():
        logger.info(f"   - media/{normalized_path.name}")

    logger.info(f"\n✅ Ready for next step: transcription and AI processing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
