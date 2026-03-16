#!/usr/bin/env python3
"""
YouTube Transcript Fetcher

Fetches transcripts from YouTube videos using the youtube-transcript-api package.
Usage: python tools/youtube_transcript.py <video_url> [language_code]
"""

import sys
import re
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from: {url}")

def get_transcript(video_url, language='en'):
    """
    Fetch transcript from YouTube video.

    Args:
        video_url: YouTube video URL or video ID
        language: Language code (default: 'en' for English)

    Returns:
        str: Formatted transcript text
    """
    try:
        video_id = extract_video_id(video_url)
        print(f"Fetching transcript for video: {video_id}", file=sys.stderr)

        api = YouTubeTranscriptApi()

        # Try to get transcript in requested language, fall back to available languages
        try:
            transcript = api.fetch(video_id, languages=[language])
        except Exception as e:
            error_msg = str(e)
            print(f"Transcript not available in {language}", file=sys.stderr)

            # Extract available languages from error message
            if "available in the following languages:" in error_msg:
                # Parse the error to find available languages (format: " - ko ("Korean...")")
                lines = error_msg.split('\n')
                available = []
                for line in lines:
                    if line.strip().startswith('- '):
                        # Format: " - ko ("Korean (auto-generated)")"
                        parts = line.strip()[2:].split(' ', 1)
                        if parts:
                            lang_code = parts[0].strip()
                            if lang_code and len(lang_code) <= 5:
                                available.append(lang_code)

                if available:
                    print(f"Available languages: {available}", file=sys.stderr)
                    print(f"Fetching in {available[0]}...", file=sys.stderr)
                    transcript = api.fetch(video_id, languages=[available[0]])
                else:
                    raise ValueError(error_msg)
            else:
                raise ValueError(error_msg)

        # Format transcript: join all entries with newlines
        formatted = '\n'.join([entry.text for entry in transcript])
        return formatted

    except Exception as e:
        print(f"Error fetching transcript: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python tools/youtube_transcript.py <video_url> [language_code]")
        print("Example: python tools/youtube_transcript.py 'https://www.youtube.com/watch?v=Osvb2GDLEdw' en")
        sys.exit(1)

    video_url = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'en'

    transcript = get_transcript(video_url, language)
    print(transcript)
