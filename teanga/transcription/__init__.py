"""
Transcription services for audio content.

Supports multiple backends:
- faster-whisper (local GPU)
- OpenAI Whisper API (cloud fallback)
"""

from teanga.transcription.whisper import WhisperTranscriber

__all__ = ["WhisperTranscriber"]
