"""
RSS/Atom feed fetcher for Raidió na Gaeltachta and other sources.

Fetches, parses, and extracts episode metadata from podcast feeds.
"""

from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import feedparser
import requests
from pydantic import BaseModel, Field, HttpUrl

from teanga.utils.logging import get_logger

logger = get_logger(__name__)


class FeedEntry(BaseModel):
    """Parsed RSS/Atom feed entry."""

    title: str
    audio_url: str
    pub_date: Optional[datetime] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    show_name: Optional[str] = None
    guid: Optional[str] = None

    @classmethod
    def from_feedparser_entry(cls, entry: Dict, show_name: Optional[str] = None) -> "FeedEntry":
        """
        Create FeedEntry from feedparser entry dict.

        Args:
            entry: feedparser entry dictionary
            show_name: Optional show name to include

        Returns:
            FeedEntry instance
        """
        # Extract audio URL from enclosures
        audio_url = None
        duration_seconds = None

        if hasattr(entry, "enclosures") and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get("type", "").startswith("audio/"):
                    audio_url = enclosure.get("href") or enclosure.get("url")
                    # Try to get duration from enclosure
                    duration_str = enclosure.get("length")
                    if duration_str and duration_str.isdigit():
                        duration_seconds = int(duration_str)
                    break

        # Fallback: check for link if no enclosure
        if not audio_url:
            if hasattr(entry, "link"):
                # Only use link if it looks like an audio file
                if any(entry.link.endswith(ext) for ext in [".mp3", ".m4a", ".wav"]):
                    audio_url = entry.link

        if not audio_url:
            logger.warning(
                "No audio URL found in entry",
                extra={"title": entry.get("title", "Unknown")},
            )
            raise ValueError("No audio URL found in feed entry")

        # Parse publication date
        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Failed to parse pub_date",
                    extra={"error": str(e), "raw_date": entry.published_parsed},
                )

        # Extract duration from itunes:duration if available
        if not duration_seconds and hasattr(entry, "itunes_duration"):
            try:
                # iTunes duration can be seconds or HH:MM:SS format
                duration_str = entry.itunes_duration
                if ":" in duration_str:
                    parts = duration_str.split(":")
                    if len(parts) == 3:  # HH:MM:SS
                        h, m, s = map(int, parts)
                        duration_seconds = h * 3600 + m * 60 + s
                    elif len(parts) == 2:  # MM:SS
                        m, s = map(int, parts)
                        duration_seconds = m * 60 + s
                else:
                    duration_seconds = int(duration_str)
            except (ValueError, AttributeError) as e:
                logger.debug(
                    f"Could not parse duration",
                    extra={"error": str(e), "raw_duration": entry.itunes_duration},
                )

        return cls(
            title=entry.get("title", "Untitled"),
            audio_url=audio_url,
            pub_date=pub_date,
            description=entry.get("description") or entry.get("summary"),
            duration_seconds=duration_seconds,
            show_name=show_name,
            guid=entry.get("id") or entry.get("guid"),
        )


class RSSFetcher:
    """Fetches and parses RSS/Atom feeds."""

    def __init__(self, timeout: int = 30):
        """
        Initialize RSS fetcher.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        logger.debug(f"Initialized RSSFetcher with timeout={timeout}s")

    def fetch_feed(self, feed_url: str) -> List[FeedEntry]:
        """
        Fetch and parse an RSS/Atom feed.

        Args:
            feed_url: URL of the RSS/Atom feed

        Returns:
            List of FeedEntry objects

        Raises:
            requests.RequestException: If feed cannot be fetched
            ValueError: If feed cannot be parsed
        """
        logger.info(f"Fetching RSS feed", extra={"url": feed_url})

        try:
            # Fetch feed with requests (more control than feedparser's built-in)
            response = requests.get(feed_url, timeout=self.timeout)
            response.raise_for_status()
            logger.debug(
                f"Feed fetched successfully",
                extra={"status_code": response.status_code, "size_bytes": len(response.content)},
            )
        except requests.Timeout as e:
            logger.error(f"Feed fetch timed out", extra={"url": feed_url, "timeout": self.timeout})
            raise
        except requests.RequestException as e:
            logger.error(
                f"Failed to fetch feed",
                extra={"url": feed_url, "error": str(e)},
            )
            raise

        # Parse feed
        feed = feedparser.parse(response.content)

        if feed.bozo:  # feedparser sets bozo=1 if there's a parsing error
            logger.warning(
                f"Feed has parsing issues",
                extra={"url": feed_url, "exception": str(feed.bozo_exception)},
            )

        # Extract show name from feed metadata
        show_name = feed.feed.get("title")
        logger.debug(f"Parsed feed", extra={"show_name": show_name, "entries": len(feed.entries)})

        # Convert entries
        entries = []
        for entry in feed.entries:
            try:
                feed_entry = FeedEntry.from_feedparser_entry(entry, show_name=show_name)
                entries.append(feed_entry)
            except ValueError as e:
                logger.warning(
                    f"Skipping entry without audio URL",
                    extra={"title": entry.get("title", "Unknown"), "error": str(e)},
                )
                continue

        logger.info(
            f"Feed parsed successfully",
            extra={"url": feed_url, "total_entries": len(entries)},
        )

        return entries

    def get_latest_episode(self, feed_url: str) -> Optional[FeedEntry]:
        """
        Get the most recent episode from a feed.

        Args:
            feed_url: URL of the RSS/Atom feed

        Returns:
            Most recent FeedEntry or None if feed is empty
        """
        entries = self.fetch_feed(feed_url)

        if not entries:
            logger.warning(f"No entries found in feed", extra={"url": feed_url})
            return None

        # Sort by pub_date (most recent first)
        entries_with_dates = [e for e in entries if e.pub_date is not None]

        if not entries_with_dates:
            # If no dates, return first entry
            logger.warning(f"No pub_dates found, returning first entry")
            return entries[0]

        latest = max(entries_with_dates, key=lambda e: e.pub_date)
        logger.info(
            f"Found latest episode",
            extra={"title": latest.title, "pub_date": latest.pub_date.isoformat() if latest.pub_date else None},
        )
        return latest

    def get_episode_by_date(self, feed_url: str, target_date: datetime) -> Optional[FeedEntry]:
        """
        Find an episode published on or closest to a target date.

        Args:
            feed_url: URL of the RSS/Atom feed
            target_date: Target publication date

        Returns:
            FeedEntry closest to target date or None
        """
        entries = self.fetch_feed(feed_url)

        entries_with_dates = [e for e in entries if e.pub_date is not None]

        if not entries_with_dates:
            logger.warning(f"No entries with dates found")
            return None

        # Find entry with pub_date closest to target_date
        closest = min(
            entries_with_dates,
            key=lambda e: abs((e.pub_date - target_date).total_seconds()),
        )

        logger.info(
            f"Found episode closest to target date",
            extra={
                "title": closest.title,
                "pub_date": closest.pub_date.isoformat(),
                "target_date": target_date.isoformat(),
            },
        )
        return closest


# Known feed URLs for Raidió na Gaeltachta shows
RNAG_FEEDS = {
    "adhmhaidin": "https://www.rte.ie/radio1/podcast/podcast_adhmhaidin.xml",
    "barrscealta": "https://www.rte.ie/radio1/podcast/podcast_barrscealta.xml",
    "bladhaire": "https://www.rte.ie/radio1/podcast/podcast_bladhairernag.xml",
    "ardtrathnona": "https://www.rte.ie/radio1/podcast/podcast_ardtrathnona.xml",
    # Note: Old "nuacht" URL (radioplayer/rss.php) no longer works
    # RnaG news is available via barrscealta (news summaries) instead
}


def get_rnag_feed_url(show: str) -> Optional[str]:
    """
    Get the RSS feed URL for a Raidió na Gaeltachta show.

    Args:
        show: Show name (e.g., 'nuacht')

    Returns:
        Feed URL or None if not found
    """
    url = RNAG_FEEDS.get(show.lower())
    if not url:
        logger.warning(
            f"Unknown RnaG show",
            extra={"show": show, "available_shows": list(RNAG_FEEDS.keys())},
        )
    return url
