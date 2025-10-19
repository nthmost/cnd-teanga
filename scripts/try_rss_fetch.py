#!/usr/bin/env python3
"""
Test script for RSS feed fetching.

Usage:
    python scripts/test_rss_fetch.py [show_name]

Examples:
    python scripts/test_rss_fetch.py nuacht
    python scripts/test_rss_fetch.py  # uses default 'nuacht'
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import teanga
sys.path.insert(0, str(Path(__file__).parent.parent))

from teanga.rss.fetcher import RSSFetcher, get_rnag_feed_url
from teanga.utils.logging import setup_logger

logger = setup_logger(__name__, level="DEBUG")


def main():
    """Test RSS feed fetching."""
    # Get show name from command line or use default
    show = sys.argv[1] if len(sys.argv) > 1 else "nuacht"

    logger.info(f"Testing RSS fetch for show: {show}")

    # Get feed URL
    feed_url = get_rnag_feed_url(show)
    if not feed_url:
        logger.error(f"No feed URL found for show: {show}")
        return 1

    logger.info(f"Feed URL: {feed_url}")

    # Create fetcher
    fetcher = RSSFetcher(timeout=30)

    try:
        # Fetch all entries
        logger.info("Fetching all feed entries...")
        entries = fetcher.fetch_feed(feed_url)

        logger.info(f"Found {len(entries)} episodes")

        # Display first few entries
        for i, entry in enumerate(entries[:5], 1):
            logger.info(f"\n--- Episode {i} ---")
            logger.info(f"Title: {entry.title}")
            logger.info(f"Published: {entry.pub_date}")
            logger.info(f"Duration: {entry.duration_seconds}s" if entry.duration_seconds else "Duration: unknown")
            logger.info(f"Audio URL: {entry.audio_url}")
            if entry.description:
                desc_preview = entry.description[:100] + "..." if len(entry.description) > 100 else entry.description
                logger.info(f"Description: {desc_preview}")

        # Get latest episode
        logger.info("\n" + "=" * 60)
        logger.info("Fetching latest episode...")
        latest = fetcher.get_latest_episode(feed_url)

        if latest:
            logger.info(f"\n🎧 Latest Episode:")
            logger.info(f"  Title: {latest.title}")
            logger.info(f"  Published: {latest.pub_date}")
            logger.info(f"  Audio URL: {latest.audio_url}")
        else:
            logger.warning("No latest episode found")

        logger.info("\n✅ RSS fetch test completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
