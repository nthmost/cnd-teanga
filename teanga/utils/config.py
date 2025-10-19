"""
Configuration management for teanga.

Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load .env file if present
load_dotenv()


class TeangaConfig(BaseModel):
    """Configuration settings for teanga components."""

    # Base paths
    data_dir: Path = Field(
        default_factory=lambda: Path("data"),
        description="Root directory for all episode data",
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path("data/.cache"),
        description="Cache directory for temporary files",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_to_file: bool = Field(
        default=False,
        description="Enable file logging in addition to console",
    )

    # API Keys (optional, loaded from environment)
    openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API key for Whisper and GPT",
    )
    anthropic_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"),
        description="Anthropic API key for Claude",
    )

    # Audio processing
    audio_sample_rate: int = Field(
        default=16000,
        description="Target sample rate for audio normalization (Hz)",
    )
    audio_channels: int = Field(
        default=1,
        description="Target number of audio channels (1=mono, 2=stereo)",
    )

    # HTTP settings
    download_timeout: int = Field(
        default=300,
        description="Timeout for audio downloads (seconds)",
    )
    download_chunk_size: int = Field(
        default=8192,
        description="Chunk size for streaming downloads (bytes)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("data_dir", "cache_dir")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        """Create directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    def get_episode_dir(self, episode_id: str) -> Path:
        """Get the directory path for a specific episode."""
        episode_dir = self.data_dir / "episodes" / episode_id
        episode_dir.mkdir(parents=True, exist_ok=True)
        return episode_dir

    def get_media_dir(self, episode_id: str) -> Path:
        """Get the media directory for an episode."""
        media_dir = self.get_episode_dir(episode_id) / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        return media_dir

    def get_transcripts_dir(self, episode_id: str) -> Path:
        """Get the transcripts directory for an episode."""
        transcripts_dir = self.get_episode_dir(episode_id) / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)
        return transcripts_dir

    def get_glosses_dir(self, episode_id: str) -> Path:
        """Get the glosses directory for an episode."""
        glosses_dir = self.get_episode_dir(episode_id) / "glosses"
        glosses_dir.mkdir(parents=True, exist_ok=True)
        return glosses_dir

    def get_exercises_dir(self, episode_id: str) -> Path:
        """Get the exercises directory for an episode."""
        exercises_dir = self.get_episode_dir(episode_id) / "exercises"
        exercises_dir.mkdir(parents=True, exist_ok=True)
        return exercises_dir

    def get_analysis_dir(self, episode_id: str) -> Path:
        """Get the analysis directory for an episode."""
        analysis_dir = self.get_episode_dir(episode_id) / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        return analysis_dir


# Global config instance (singleton pattern)
_config: Optional[TeangaConfig] = None


def get_config() -> TeangaConfig:
    """
    Get the global configuration instance.

    Returns:
        TeangaConfig instance (creates one if it doesn't exist)

    Example:
        >>> from teanga.utils.config import get_config
        >>> config = get_config()
        >>> episode_dir = config.get_episode_dir("rnag_nuacht_20251018_1800")
    """
    global _config
    if _config is None:
        _config = TeangaConfig()
    return _config


def set_config(config: TeangaConfig) -> None:
    """
    Set a custom configuration instance.

    Args:
        config: TeangaConfig instance to use globally
    """
    global _config
    _config = config
