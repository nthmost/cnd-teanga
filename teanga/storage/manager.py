"""
Episode-centric storage manager for artifacts and metadata.

Handles creation, reading, and updating of episode directory structures.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from teanga.utils.config import get_config
from teanga.utils.logging import get_logger

logger = get_logger(__name__)


class ProcessingStep(BaseModel):
    """Record of a processing step in the episode pipeline."""

    step: str = Field(description="Name of the processing step")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(description="success, failed, or in_progress")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional details about the step",
    )


class EpisodeMetadata(BaseModel):
    """Metadata for an episode and its artifacts."""

    episode_id: str
    source: str = Field(description="Source of the episode (e.g., raidio_na_gaeltachta)")
    show: str = Field(description="Show name")
    title: str
    pub_date: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    original_url: str
    audio_checksum: Optional[str] = None
    processing_history: List[ProcessingStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_processing_step(
        self,
        step: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a processing step to the history."""
        self.processing_history.append(
            ProcessingStep(step=step, status=status, details=details)
        )
        self.updated_at = datetime.utcnow()


class EpisodeManager:
    """Manages episode directories and metadata."""

    def __init__(self, episode_id: str, metadata: Optional[EpisodeMetadata] = None):
        """
        Initialize episode manager.

        Args:
            episode_id: Unique episode identifier
            metadata: Optional existing metadata (will be loaded if not provided)
        """
        self.episode_id = episode_id
        self.config = get_config()
        self.episode_dir = self.config.get_episode_dir(episode_id)
        self.metadata_path = self.episode_dir / "metadata.json"

        # Load or create metadata
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = self._load_metadata()

        logger.debug(
            f"Initialized EpisodeManager",
            extra={"episode_id": episode_id, "episode_dir": str(self.episode_dir)},
        )

    def _load_metadata(self) -> Optional[EpisodeMetadata]:
        """Load metadata from disk if it exists."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.debug(f"Loaded metadata from {self.metadata_path}")
                return EpisodeMetadata(**data)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse metadata JSON",
                    extra={"path": str(self.metadata_path), "error": str(e)},
                )
                raise
            except ValueError as e:
                logger.error(
                    f"Invalid metadata schema",
                    extra={"path": str(self.metadata_path), "error": str(e)},
                )
                raise
        return None

    def save_metadata(self) -> None:
        """Save metadata to disk."""
        self.metadata.updated_at = datetime.utcnow()

        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.metadata.model_dump(mode="json"),
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            logger.info(
                f"Saved metadata",
                extra={"episode_id": self.episode_id, "path": str(self.metadata_path)},
            )
        except OSError as e:
            logger.error(
                f"Failed to write metadata",
                extra={"path": str(self.metadata_path), "error": str(e)},
            )
            raise

    def add_processing_step(
        self,
        step: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a processing step and save metadata.

        Args:
            step: Name of the processing step
            status: Status (success, failed, in_progress)
            details: Optional additional details
        """
        self.metadata.add_processing_step(step, status, details)
        self.save_metadata()
        logger.info(
            f"Processing step recorded: {step}",
            extra={"episode_id": self.episode_id, "status": status},
        )

    def get_media_path(self, filename: str) -> Path:
        """Get path to a media file."""
        return self.config.get_media_dir(self.episode_id) / filename

    def get_transcript_path(self, filename: str) -> Path:
        """Get path to a transcript file."""
        return self.config.get_transcripts_dir(self.episode_id) / filename

    def get_gloss_path(self, filename: str) -> Path:
        """Get path to a gloss file."""
        return self.config.get_glosses_dir(self.episode_id) / filename

    def get_exercise_path(self, filename: str) -> Path:
        """Get path to an exercise file."""
        return self.config.get_exercises_dir(self.episode_id) / filename

    def get_analysis_path(self, filename: str) -> Path:
        """Get path to an analysis file."""
        return self.config.get_analysis_dir(self.episode_id) / filename

    @staticmethod
    def compute_file_checksum(file_path: Path) -> str:
        """
        Compute SHA256 checksum of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            checksum = sha256.hexdigest()
            logger.debug(
                f"Computed checksum",
                extra={"file": str(file_path), "checksum": checksum[:16] + "..."},
            )
            return checksum
        except OSError as e:
            logger.error(
                f"Failed to compute checksum",
                extra={"file": str(file_path), "error": str(e)},
            )
            raise

    def set_audio_checksum(self, file_path: Path) -> str:
        """
        Compute and store audio file checksum in metadata.

        Args:
            file_path: Path to the audio file

        Returns:
            The computed checksum
        """
        checksum = self.compute_file_checksum(file_path)
        self.metadata.audio_checksum = f"sha256:{checksum}"
        self.save_metadata()
        return checksum


def create_episode_id(source: str, show: str, pub_date: datetime) -> str:
    """
    Create a standardized episode ID.

    Args:
        source: Source identifier (e.g., 'rnag')
        show: Show name
        pub_date: Publication datetime

    Returns:
        Episode ID in format: {source}_{show}_{YYYYMMDD}_{HHMM}

    Example:
        >>> from datetime import datetime
        >>> create_episode_id("rnag", "nuacht", datetime(2025, 10, 18, 18, 0))
        'rnag_nuacht_20251018_1800'
    """
    date_str = pub_date.strftime("%Y%m%d")
    time_str = pub_date.strftime("%H%M")
    # Sanitize show name (replace spaces and special chars)
    show_clean = show.lower().replace(" ", "_").replace("-", "_")
    episode_id = f"{source}_{show_clean}_{date_str}_{time_str}"
    logger.debug(f"Created episode ID: {episode_id}")
    return episode_id
