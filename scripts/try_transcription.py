#!/usr/bin/env python3
"""
Demo script for testing Whisper transcription on Irish audio.

Usage:
    python scripts/try_transcription.py <episode_id> [--model MODEL_SIZE]

Examples:
    python scripts/try_transcription.py rnag_barrscealta_20251017_1100
    python scripts/try_transcription.py rnag_adhmhaidin_20251017_0800 --model medium
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from teanga.utils.logging import setup_logger
from teanga.transcription.whisper import WhisperTranscriber
from teanga.storage.manager import EpisodeManager

logger = setup_logger(__name__, level="INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe Irish audio using Whisper"
    )
    parser.add_argument(
        "episode_id",
        help="Episode ID (e.g., rnag_barrscealta_20251017_1100)"
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Whisper model size (default: large-v3)"
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code (e.g., 'en', 'fr'). Default: None (auto-detect). Note: Irish 'ga' not supported."
    )
    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to run on (default: cuda)"
    )
    parser.add_argument(
        "--test-clip",
        action="store_true",
        help="Use test clip (test_clip.wav) instead of full audio"
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

    # Get audio path (test clip or full audio)
    if args.test_clip:
        audio_path = manager.get_media_path("test_clip.wav")
        if not audio_path.exists():
            logger.error(f"❌ Test clip not found: {audio_path}")
            logger.info("💡 Extract a test clip first:")
            logger.info(f"   python scripts/extract_test_clip.py {args.episode_id}")
            return 1
    else:
        audio_path = manager.get_media_path("normalized.wav")
        if not audio_path.exists():
            logger.error(f"❌ Normalized audio not found: {audio_path}")
            logger.info("💡 Try running the audio pipeline first:")
            logger.info(f"   python scripts/try_audio_pipeline.py <show_name>")
            return 1

    # Get transcripts directory
    transcripts_dir = manager.get_transcript_path("")  # Get directory
    transcripts_dir = transcripts_dir.parent  # transcripts/

    logger.info("=" * 60)
    logger.info(f"📝 TRANSCRIPTION TEST {'(TEST CLIP)' if args.test_clip else ''}")
    logger.info("=" * 60)
    logger.info(f"Episode: {episode_metadata.title}")
    logger.info(f"Audio: {audio_path}")
    logger.info(f"Type: {'🎬 Test clip (5 min)' if args.test_clip else '📼 Full episode'}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Language: {args.language}")
    logger.info(f"Device: {args.device}")
    logger.info("=" * 60)

    try:
        # Initialize transcriber
        logger.info("🔧 Loading Whisper model...")
        transcriber = WhisperTranscriber(
            model_size=args.model,
            device=args.device
        )

        # Transcribe and save
        logger.info("🎙️ Starting transcription...")
        result = transcriber.transcribe_and_save(
            audio_path=audio_path,
            output_dir=transcripts_dir,
            language=args.language
        )

        # Display results
        logger.info("=" * 60)
        logger.info("📊 TRANSCRIPTION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Language detected: {result.language}")
        logger.info(f"Language probability: {result.language_probability:.2%}")
        logger.info(f"Duration: {result.duration:.1f}s ({result.duration/60:.1f} min)")
        logger.info(f"Segments: {len(result.segments)}")
        logger.info("=" * 60)

        # Show first few segments
        logger.info("📝 First 3 segments:")
        for i, seg in enumerate(result.segments[:3], 1):
            start_min = seg["start"] / 60
            end_min = seg["end"] / 60
            logger.info(f"\n  [{i}] {start_min:.2f}-{end_min:.2f} min")
            logger.info(f"      {seg['text']}")
            logger.info(f"      (confidence: {seg['avg_logprob']:.2f})")

        logger.info("\n" + "=" * 60)
        logger.info("📁 Files saved:")
        logger.info(f"   - {transcripts_dir}/raw_whisper.json")
        logger.info(f"   - {transcripts_dir}/transcript.txt")
        logger.info(f"   - {transcripts_dir}/subtitles.vtt")
        logger.info("=" * 60)

        # Update episode metadata
        manager.add_processing_step(
            step="transcription",
            status="success",
            details={
                "model": args.model,
                "language": result.language,
                "language_probability": result.language_probability,
                "segments": len(result.segments),
                "duration": result.duration
            }
        )

        logger.info("✅ Transcription complete!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Transcription interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}", exc_info=True)
        manager.add_processing_step(
            step="transcription",
            status="failed",
            details={"error": str(e)}
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
