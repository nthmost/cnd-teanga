"""
Audio format conversion using FFmpeg.

Normalizes audio files to standard format for processing (16kHz mono WAV).
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple

import ffmpeg

from teanga.utils.config import get_config
from teanga.utils.logging import get_logger

logger = get_logger(__name__)


class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg is not found in system PATH."""
    pass


class AudioConversionError(Exception):
    """Raised when audio conversion fails."""
    pass


class AudioConverter:
    """Converts audio files to normalized format using FFmpeg."""

    def __init__(
        self,
        target_sample_rate: Optional[int] = None,
        target_channels: Optional[int] = None,
    ):
        """
        Initialize audio converter.

        Args:
            target_sample_rate: Target sample rate in Hz (default: from config)
            target_channels: Target number of channels (default: from config)
        """
        self.config = get_config()
        self.target_sample_rate = target_sample_rate or self.config.audio_sample_rate
        self.target_channels = target_channels or self.config.audio_channels

        # Check if FFmpeg is available
        if not self._check_ffmpeg():
            raise FFmpegNotFoundError(
                "FFmpeg not found in system PATH. Please install FFmpeg: "
                "https://ffmpeg.org/download.html"
            )

        logger.debug(
            f"Initialized AudioConverter",
            extra={
                "sample_rate": self.target_sample_rate,
                "channels": self.target_channels,
            },
        )

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_audio_info(self, input_path: Path) -> dict:
        """
        Get audio file information using ffprobe.

        Args:
            input_path: Path to audio file

        Returns:
            Dictionary with audio metadata

        Raises:
            AudioConversionError: If ffprobe fails
        """
        logger.debug(f"Probing audio file", extra={"path": str(input_path)})

        try:
            probe = ffmpeg.probe(str(input_path))

            # Find audio stream
            audio_stream = None
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            if not audio_stream:
                raise AudioConversionError(f"No audio stream found in {input_path}")

            info = {
                "codec": audio_stream.get("codec_name"),
                "sample_rate": int(audio_stream.get("sample_rate", 0)),
                "channels": int(audio_stream.get("channels", 0)),
                "duration": float(probe.get("format", {}).get("duration", 0)),
                "bit_rate": int(probe.get("format", {}).get("bit_rate", 0)),
                "format": probe.get("format", {}).get("format_name"),
            }

            logger.debug(
                f"Audio info retrieved",
                extra={"path": str(input_path), "info": info},
            )

            return info

        except ffmpeg.Error as e:
            logger.error(
                f"FFprobe failed",
                extra={"path": str(input_path), "error": e.stderr.decode() if e.stderr else str(e)},
            )
            raise AudioConversionError(f"Failed to probe audio file: {e}")

    def convert_to_wav(
        self,
        input_path: Path,
        output_path: Path,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
    ) -> Path:
        """
        Convert audio file to WAV format with specified parameters.

        Args:
            input_path: Path to input audio file
            output_path: Path for output WAV file
            sample_rate: Target sample rate (default: instance setting)
            channels: Target channels (default: instance setting)

        Returns:
            Path to converted file

        Raises:
            AudioConversionError: If conversion fails
        """
        sample_rate = sample_rate or self.target_sample_rate
        channels = channels or self.target_channels

        logger.info(
            f"Converting audio to WAV",
            extra={
                "input": str(input_path),
                "output": str(output_path),
                "sample_rate": sample_rate,
                "channels": channels,
            },
        )

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Build ffmpeg command
            stream = ffmpeg.input(str(input_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec="pcm_s16le",  # 16-bit PCM
                ar=sample_rate,       # Sample rate
                ac=channels,          # Number of channels
                loglevel="error",     # Only show errors
            )

            # Run conversion (overwrite output if exists)
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)

            # Verify output exists
            if not output_path.exists():
                raise AudioConversionError(f"Conversion completed but output not found: {output_path}")

            output_size = output_path.stat().st_size
            logger.info(
                f"Conversion complete",
                extra={
                    "input": str(input_path),
                    "output": str(output_path),
                    "size_bytes": output_size,
                },
            )

            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(
                f"FFmpeg conversion failed",
                extra={
                    "input": str(input_path),
                    "output": str(output_path),
                    "error": error_msg,
                },
            )
            raise AudioConversionError(f"Audio conversion failed: {error_msg}")

    def normalize_episode_audio(
        self,
        input_path: Path,
        episode_id: str,
    ) -> Tuple[Path, dict]:
        """
        Normalize episode audio to standard format.

        Args:
            input_path: Path to original audio file
            episode_id: Episode identifier

        Returns:
            Tuple of (output_path, audio_info)
        """
        # Get info about original audio
        audio_info = self.get_audio_info(input_path)

        # Determine output filename
        output_path = self.config.get_media_dir(episode_id) / "normalized.wav"

        logger.info(
            f"Normalizing episode audio",
            extra={
                "episode_id": episode_id,
                "input": str(input_path),
                "original_format": audio_info.get("codec"),
                "original_sample_rate": audio_info.get("sample_rate"),
            },
        )

        # Convert
        self.convert_to_wav(input_path, output_path)

        # Get normalized audio info
        normalized_info = self.get_audio_info(output_path)

        logger.info(
            f"Audio normalized",
            extra={
                "episode_id": episode_id,
                "output": str(output_path),
                "duration_seconds": normalized_info.get("duration"),
            },
        )

        return output_path, normalized_info
