"""
Whisper transcription service using faster-whisper for local GPU inference.

Designed for Irish language (Gaeilge) audio transcription with word-level
timestamps and confidence scores.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Literal
from datetime import timedelta

from faster_whisper import WhisperModel
from faster_whisper.transcribe import Segment, Word

from teanga.utils.logging import get_logger

logger = get_logger(__name__)

# Model size options for faster-whisper
ModelSize = Literal["tiny", "base", "small", "medium", "large-v2", "large-v3"]


class TranscriptionResult:
    """Structured transcription result with text, segments, and metadata."""

    def __init__(
        self,
        text: str,
        segments: list[dict],
        language: str,
        language_probability: float,
        duration: float,
        model_size: str
    ):
        self.text = text
        self.segments = segments
        self.language = language
        self.language_probability = language_probability
        self.duration = duration
        self.model_size = model_size

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "segments": self.segments,
            "language": self.language,
            "language_probability": self.language_probability,
            "duration": self.duration,
            "model_size": self.model_size
        }

    def to_vtt(self) -> str:
        """Generate WebVTT subtitle format."""
        vtt_lines = ["WEBVTT", ""]

        for i, seg in enumerate(self.segments, 1):
            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])
            text = seg["text"].strip()

            vtt_lines.append(f"{i}")
            vtt_lines.append(f"{start} --> {end}")
            vtt_lines.append(text)
            vtt_lines.append("")

        return "\n".join(vtt_lines)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as VTT timestamp (HH:MM:SS.mmm)."""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


class WhisperTranscriber:
    """
    Whisper-based transcription service using faster-whisper.

    Optimized for local GPU inference with CUDA support.
    Designed for Irish language audio but supports multiple languages.
    """

    def __init__(
        self,
        model_size: ModelSize = "large-v3",
        device: str = "cuda",
        compute_type: str | None = None
    ):
        """
        Initialize Whisper transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to run on ("cuda" or "cpu")
            compute_type: Computation precision ("float16", "int8", etc.)
                         If None, auto-selects based on device (float16 for CUDA, int8 for CPU)

        Raises:
            RuntimeError: If CUDA requested but not available
            ValueError: If invalid model size specified
        """
        self.model_size = model_size
        self.device = device

        # Auto-select compute type based on device
        if compute_type is None:
            self.compute_type = "float16" if device == "cuda" else "int8"
        else:
            self.compute_type = compute_type

        logger.info(
            f"🎤 Initializing Whisper transcriber",
            extra={
                "model_size": model_size,
                "device": device,
                "compute_type": self.compute_type
            }
        )

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=self.compute_type
            )
            logger.info(f"✅ Whisper model loaded: {model_size}")
        except ValueError as e:
            logger.error(f"❌ Invalid model configuration: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"❌ Failed to initialize model (check CUDA availability): {e}")
            raise

    def transcribe(
        self,
        audio_path: Path | str,
        language: str | None = None,
        word_timestamps: bool = True,
        vad_filter: bool = True,
        beam_size: int = 5
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            language: Language code (e.g., "en" for English, "fr" for French)
                     If None, auto-detects language. Note: Irish ('ga') is not
                     supported by faster-whisper, use None for auto-detection.
            word_timestamps: Extract word-level timestamps
            vad_filter: Use voice activity detection to filter silence
            beam_size: Beam search size (higher = more accurate but slower)

        Returns:
            TranscriptionResult with text, segments, and metadata

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            logger.error(f"❌ Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(
            f"🎙️ Starting transcription: {audio_path.name}",
            extra={
                "language": language,
                "word_timestamps": word_timestamps,
                "vad_filter": vad_filter
            }
        )

        try:
            # Run transcription
            segments_iter, info = self.model.transcribe(
                str(audio_path),
                language=language,
                beam_size=beam_size,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter
            )

            logger.info(
                f"📊 Detected language: {info.language} "
                f"(probability: {info.language_probability:.2f})"
            )

            # Process segments
            segments = []
            full_text_parts = []

            for segment in segments_iter:
                segment_dict = self._process_segment(segment, word_timestamps)
                segments.append(segment_dict)
                full_text_parts.append(segment_dict["text"])

            full_text = " ".join(full_text_parts)

            result = TranscriptionResult(
                text=full_text,
                segments=segments,
                language=info.language,
                language_probability=info.language_probability,
                duration=info.duration,
                model_size=self.model_size
            )

            logger.info(
                f"✅ Transcription complete: {len(segments)} segments, "
                f"{info.duration:.1f}s duration"
            )

            return result

        except RuntimeError as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during transcription: {e}")
            raise RuntimeError(f"Transcription failed: {e}") from e

    def _process_segment(
        self,
        segment: Segment,
        include_words: bool
    ) -> dict:
        """
        Process a transcription segment into structured format.

        Args:
            segment: Whisper segment object
            include_words: Whether to include word-level timestamps

        Returns:
            Dictionary with segment data
        """
        segment_dict = {
            "id": segment.id,
            "start": segment.start,
            "end": segment.end,
            "text": segment.text,
            "avg_logprob": segment.avg_logprob,
            "no_speech_prob": segment.no_speech_prob
        }

        if include_words and segment.words:
            segment_dict["words"] = [
                {
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability
                }
                for word in segment.words
            ]

        return segment_dict

    def transcribe_and_save(
        self,
        audio_path: Path | str,
        output_dir: Path | str,
        language: str | None = None,
        save_formats: Optional[list[str]] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio and save results in multiple formats.

        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcription outputs
            language: Language code for transcription
            save_formats: List of formats to save ("json", "txt", "vtt")
                         If None, saves all formats

        Returns:
            TranscriptionResult

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription or saving fails
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if save_formats is None:
            save_formats = ["json", "txt", "vtt"]

        # Transcribe
        result = self.transcribe(audio_path, language=language)

        # Save in requested formats
        logger.info(f"💾 Saving transcription in formats: {', '.join(save_formats)}")

        try:
            if "json" in save_formats:
                json_path = output_dir / "raw_whisper.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Saved JSON: {json_path}")

            if "txt" in save_formats:
                txt_path = output_dir / "transcript.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(result.text)
                logger.info(f"✅ Saved plain text: {txt_path}")

            if "vtt" in save_formats:
                vtt_path = output_dir / "subtitles.vtt"
                with open(vtt_path, "w", encoding="utf-8") as f:
                    f.write(result.to_vtt())
                logger.info(f"✅ Saved VTT subtitles: {vtt_path}")

            return result

        except OSError as e:
            logger.error(f"❌ Failed to save transcription: {e}")
            raise RuntimeError(f"Failed to save transcription: {e}") from e
