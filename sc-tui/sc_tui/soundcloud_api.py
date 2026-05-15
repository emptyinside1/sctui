import asyncio
import json
import yt_dlp
from typing import List, Dict, Any
from pathlib import Path
from sc_tui.config import get_cache_db

class SoundCloudAPI:
    """
    Interface to interact with SoundCloud.
    Uses yt-dlp to search and extract stream URLs.
    All operations are asynchronous (using asyncio.to_thread) to avoid blocking the TUI.
    """

    def __init__(self):
        self.base_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        self.cache_file = get_cache_db()
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Loads metadata cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """Saves metadata cache to disk."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception as e:
            print(f"Failed to save cache: {e}")

    async def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tracks on SoundCloud.
        Returns a list of dictionaries containing track metadata.
        """
        cache_key = f"search:{query}:{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        def _search():
            opts = self.base_opts.copy()
            # Extract flat to avoid extracting the full streaming URL during search (much faster)
            opts['extract_flat'] = True

            with yt_dlp.YoutubeDL(opts) as ydl:
                # yt-dlp syntax for soundcloud search is scsearch[N]:query
                search_query = f"scsearch{limit}:{query}"
                try:
                    result = ydl.extract_info(search_query, download=False)
                    if not result:
                        return []

                    if 'entries' in result:
                        return list(result['entries'])
                    return [result]
                except Exception as e:
                    print(f"Search error: {e}")
                    return []

        results = await asyncio.to_thread(_search)
        if results:
            self._cache[cache_key] = results
            self._save_cache()

        return results

    async def get_stream_url(self, track_url: str) -> str | None:
        """
        Get the direct streaming URL for a specific track URL.
        """
        # We don't cache stream URLs forever because they expire (SoundCloud signs them).
        # We could cache them for a short time, but fetching directly is safer.
        def _get_stream():
            opts = self.base_opts.copy()
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(track_url, download=False)
                    if info:
                        return info.get('url')
                except Exception as e:
                    print(f"Extraction error: {e}")
                    return None
            return None
        return await asyncio.to_thread(_get_stream)

    async def get_track_info(self, track_url: str) -> Dict[str, Any] | None:
        """
        Get full metadata for a track, including the stream URL.
        """
        def _get_info():
            opts = self.base_opts.copy()
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    return ydl.extract_info(track_url, download=False)
                except Exception as e:
                    print(f"Extraction error: {e}")
                    return None
        return await asyncio.to_thread(_get_info)

# Global API instance
api = SoundCloudAPI()
