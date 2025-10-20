#!/usr/bin/env python3
"""
Test script for Irish wav2vec2 ASR model from Hugging Face.

Usage:
    python scripts/try_irish_wav2vec2.py <episode_id> [--test-clip]

Examples:
    python scripts/try_irish_wav2vec2.py rnag_barrscealta_20251017_1100 --test-clip
"""

import sys
import argparse
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from teanga.utils.logging import setup_logger
from teanga.storage.manager import EpisodeManager

logger = setup_logger(__name__, level="INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Test Irish wav2vec2 ASR model"
    )
    parser.add_argument(
        "episode_id",
        help="Episode ID (e.g., rnag_barrscealta_20251017_1100)"
    )
    parser.add_argument(
        "--test-clip",
        action="store_true",
        help="Use test clip instead of full audio"
    )
    parser.add_argument(
        "--model",
        default="Aditya3107/wav2vec2-large-xls-r-1b-ga-ie",
        help="Hugging Face model ID (default: Aditya3107/wav2vec2-large-xls-r-1b-ga-ie)"
    )

    args = parser.parse_args()

    # Get episode info
    try:
        manager = EpisodeManager(args.episode_id)
    except Exception as e:
        logger.error(f"❌ Episode not found: {args.episode_id}")
        logger.info("💡 Check data/episodes/ for available episodes")
        return 1

    episode_metadata = manager.metadata

    # Get audio path
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
            return 1

    logger.info("=" * 60)
    logger.info(f"🇮🇪 IRISH WAV2VEC2 TEST {'(TEST CLIP)' if args.test_clip else ''}")
    logger.info("=" * 60)
    logger.info(f"Episode: {episode_metadata.title}")
    logger.info(f"Audio: {audio_path}")
    logger.info(f"Type: {'🎬 Test clip (5 min)' if args.test_clip else '📼 Full episode'}")
    logger.info(f"Model: {args.model}")
    logger.info("=" * 60)

    try:
        # Import here to avoid loading if not needed
        import torch
        import librosa
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔧 Using device: {device}")

        # Load model and processor
        logger.info(f"📥 Loading model: {args.model}")
        start_load = time.time()

        processor = Wav2Vec2Processor.from_pretrained(args.model)
        model = Wav2Vec2ForCTC.from_pretrained(args.model)
        model = model.to(device)

        load_time = time.time() - start_load
        logger.info(f"✅ Model loaded in {load_time:.1f}s")

        # Load and preprocess audio
        logger.info("🎵 Loading audio...")
        speech, sample_rate = librosa.load(str(audio_path), sr=16000)
        logger.info(f"   Sample rate: {sample_rate} Hz")
        logger.info(f"   Duration: {len(speech)/sample_rate:.1f}s ({len(speech)/sample_rate/60:.1f} min)")

        # Process in chunks if audio is long (to avoid memory issues)
        chunk_duration = 30  # seconds
        chunk_samples = chunk_duration * sample_rate

        if len(speech) > chunk_samples:
            logger.info(f"🔪 Processing in {chunk_duration}s chunks...")

            transcriptions = []
            num_chunks = (len(speech) + chunk_samples - 1) // chunk_samples

            for i in range(num_chunks):
                start_idx = i * chunk_samples
                end_idx = min((i + 1) * chunk_samples, len(speech))
                chunk = speech[start_idx:end_idx]

                logger.info(f"   Chunk {i+1}/{num_chunks} ({start_idx/sample_rate:.1f}s - {end_idx/sample_rate:.1f}s)")

                # Tokenize
                inputs = processor(chunk, sampling_rate=sample_rate, return_tensors="pt", padding=True)
                inputs = {k: v.to(device) for k, v in inputs.items()}

                # Transcribe
                with torch.no_grad():
                    logits = model(**inputs).logits

                predicted_ids = torch.argmax(logits, dim=-1)
                transcription = processor.batch_decode(predicted_ids)[0]
                transcriptions.append(transcription)

            full_transcription = " ".join(transcriptions)
        else:
            # Process all at once for shorter audio
            logger.info("🎙️ Transcribing...")
            start_time = time.time()

            inputs = processor(speech, sampling_rate=sample_rate, return_tensors="pt", padding=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = model(**inputs).logits

            predicted_ids = torch.argmax(logits, dim=-1)
            full_transcription = processor.batch_decode(predicted_ids)[0]

            transcribe_time = time.time() - start_time
            duration = len(speech) / sample_rate
            speed = duration / transcribe_time if transcribe_time > 0 else 0

            logger.info(f"✅ Transcription complete in {transcribe_time:.1f}s")
            logger.info(f"   Speed: {speed:.2f}x realtime")

        # Display results
        logger.info("=" * 60)
        logger.info("📊 TRANSCRIPTION RESULTS (IRISH)")
        logger.info("=" * 60)
        logger.info(f"Length: {len(full_transcription)} characters")
        logger.info("=" * 60)
        logger.info("📝 First 500 characters:")
        logger.info("")
        logger.info(full_transcription[:500])
        logger.info("")
        logger.info("=" * 60)
        logger.info("📝 Full transcript:")
        logger.info("")
        logger.info(full_transcription)
        logger.info("")
        logger.info("=" * 60)

        # Save to file
        output_path = manager.get_media_path("transcript_irish_wav2vec2.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_transcription)

        logger.info(f"💾 Saved to: {output_path}")
        logger.info("=" * 60)

        return 0

    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("💡 Install required packages:")
        logger.info("   pipenv install transformers librosa")
        return 1
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
