#!/usr/bin/env python3
"""
Extract a test clip from an episode for quick transcription testing.

Usage:
    python scripts/extract_test_clip.py <episode_id> [--start START] [--duration DURATION]

Examples:
    python scripts/extract_test_clip.py rnag_barrscealta_20251017_1100
    python scripts/extract_test_clip.py rnag_adhmhaidin_20251017_0800 --start 120 --duration 180
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from teanga.utils.logging import setup_logger
from teanga.audio.converter import AudioConverter
from teanga.storage.manager import EpisodeManager

logger = setup_logger(__name__, level="INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Extract test clip from episode audio"
    )
    parser.add_argument(
        "episode_id",
        help="Episode ID (e.g., rnag_barrscealta_20251017_1100)"
    )
    parser.add_argument(
        "--start",
        type=float,
        default=60.0,
        help="Start time in seconds (default: 60 to skip intro)"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=300.0,
        help="Clip duration in seconds (default: 300 = 5 minutes)"
    )

    args = parser.parse_args()

    # Create episode manager (loads existing metadata)
    try:
        manager = EpisodeManager(args.episode_id)
    except Exception as e:
        logger.error(f"❌ Episode not found: {args.episode_id}")
        logger.info("💡 Check data/episodes/ for available episodes")
        return 1

    episode_metadata = manager.metadata

    # Get audio path
    audio_path = manager.get_media_path("normalized.wav")
    if not audio_path.exists():
        logger.error(f"❌ Normalized audio not found: {audio_path}")
        logger.info("💡 Try running the audio pipeline first:")
        logger.info(f"   python scripts/try_audio_pipeline.py <show_name>")
        return 1

    # Output path
    output_path = manager.get_media_path("test_clip.wav")

    logger.info("=" * 60)
    logger.info(f"🎬 EXTRACTING TEST CLIP")
    logger.info("=" * 60)
    logger.info(f"Episode: {episode_metadata.title}")
    logger.info(f"Source: {audio_path}")
    logger.info(f"Start: {args.start}s ({args.start/60:.1f} min)")
    logger.info(f"Duration: {args.duration}s ({args.duration/60:.1f} min)")
    logger.info(f"Output: {output_path}")
    logger.info("=" * 60)

    try:
        # Extract clip
        converter = AudioConverter()
        clip_path = converter.extract_clip(
            input_path=audio_path,
            output_path=output_path,
            start_seconds=args.start,
            duration_seconds=args.duration
        )

        # Get clip info
        clip_info = converter.get_audio_info(clip_path)

        logger.info("=" * 60)
        logger.info("✅ CLIP EXTRACTED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Path: {clip_path}")
        logger.info(f"Size: {clip_path.stat().st_size / (1024*1024):.2f} MB")
        logger.info(f"Duration: {clip_info['duration']:.1f}s ({clip_info['duration']/60:.1f} min)")
        logger.info(f"Sample rate: {clip_info['sample_rate']} Hz")
        logger.info(f"Channels: {clip_info['channels']}")
        logger.info("=" * 60)
        logger.info("\n💡 Now test transcription with:")
        logger.info(f"   python scripts/try_transcription.py {args.episode_id} --test-clip")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"❌ Clip extraction failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
