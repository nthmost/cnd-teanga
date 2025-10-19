"""
Audio file downloader with progress tracking and validation.

Handles HTTP downloads of audio files with streaming and progress bars.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from teanga.utils.config import get_config
from teanga.utils.logging import get_logger

logger = get_logger(__name__)


class AudioDownloader:
    """Downloads audio files with progress tracking."""

    def __init__(self, timeout: int = 300, chunk_size: int = 8192):
        """
        Initialize audio downloader.

        Args:
            timeout: Download timeout in seconds
            chunk_size: Size of download chunks in bytes
        """
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.config = get_config()
        logger.debug(
            f"Initialized AudioDownloader",
            extra={"timeout": timeout, "chunk_size": chunk_size},
        )

    def download(
        self,
        url: str,
        output_path: Path,
        show_progress: bool = True,
    ) -> Path:
        """
        Download an audio file from URL.

        Args:
            url: URL of the audio file
            output_path: Where to save the downloaded file
            show_progress: Display progress bar

        Returns:
            Path to the downloaded file

        Raises:
            requests.RequestException: If download fails
            OSError: If file cannot be written
        """
        logger.info(f"Starting download", extra={"url": url, "output": str(output_path)})

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Start streaming download
            response = requests.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()

            # Get file size if available
            total_size = int(response.headers.get("content-length", 0))
            logger.debug(
                f"Download started",
                extra={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type"),
                    "size_bytes": total_size or "unknown",
                },
            )

            # Download with progress bar
            if show_progress:
                progress = Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                )

                with progress:
                    task = progress.add_task(
                        f"Downloading {output_path.name}",
                        total=total_size,
                    )

                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))
            else:
                # Download without progress bar
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)

            # Verify file was created
            if not output_path.exists():
                raise OSError(f"Download completed but file not found: {output_path}")

            file_size = output_path.stat().st_size
            logger.info(
                f"Download complete",
                extra={
                    "url": url,
                    "output": str(output_path),
                    "size_bytes": file_size,
                },
            )

            return output_path

        except requests.Timeout as e:
            logger.error(
                f"Download timed out",
                extra={"url": url, "timeout": self.timeout},
            )
            raise
        except requests.RequestException as e:
            logger.error(
                f"Download failed",
                extra={"url": url, "error": str(e)},
            )
            raise
        except OSError as e:
            logger.error(
                f"Failed to write file",
                extra={"path": str(output_path), "error": str(e)},
            )
            raise

    def get_filename_from_url(self, url: str) -> str:
        """
        Extract filename from URL.

        Args:
            url: URL to parse

        Returns:
            Filename extracted from URL or a default name
        """
        parsed = urlparse(url)
        path = Path(parsed.path)

        if path.name and path.suffix:
            filename = path.name
        else:
            # Generate default filename
            filename = "audio.mp3"

        logger.debug(f"Extracted filename from URL", extra={"url": url, "extracted_filename": filename})
        return filename

    def download_episode_audio(
        self,
        url: str,
        episode_id: str,
        filename: Optional[str] = None,
        show_progress: bool = True,
    ) -> Path:
        """
        Download audio for a specific episode.

        Args:
            url: URL of the audio file
            episode_id: Episode identifier
            filename: Optional custom filename (default: extracted from URL)
            show_progress: Display progress bar

        Returns:
            Path to the downloaded file
        """
        if not filename:
            filename = self.get_filename_from_url(url)

        # Ensure it's saved as 'original.*' to distinguish from processed versions
        file_ext = Path(filename).suffix
        filename = f"original{file_ext}"

        output_path = self.config.get_media_dir(episode_id) / filename

        logger.info(
            f"Downloading episode audio",
            extra={"episode_id": episode_id, "url": url, "target_filename": filename},
        )

        return self.download(url, output_path, show_progress=show_progress)
