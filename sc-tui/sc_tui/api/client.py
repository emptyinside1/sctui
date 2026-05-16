import asyncio
import json
import yt_dlp
from typing import List, Dict, Any, Optional
from sc_tui.config import get_cache_db

class SoundCloudAPI:
    """
    Advanced SoundCloud API client using yt-dlp.
    Supports caching, pagination concepts and user libraries.
    """
    def __init__(self):
        self.base_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            # For authorized operations, we mock relying on browser cookies
            # if user has Chrome/Firefox logged into Soundcloud.
            'cookiesfrombrowser': ('chrome',),
        }
        self.cache_file = get_cache_db()
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception as e:
            pass

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Deep search using yt-dlp."""
        cache_key = f"search_deep:{query}:{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        def _search():
            opts = self.base_opts.copy()
            opts['extract_flat'] = True

            with yt_dlp.YoutubeDL(opts) as ydl:
                search_query = f"scsearch{limit}:{query}"
                try:
                    result = ydl.extract_info(search_query, download=False)
                    if not result:
                        return []
                    if 'entries' in result:
                        return list(result['entries'])
                    return [result]
                except Exception:
                    return []

        results = await asyncio.to_thread(_search)
        if results:
            self._cache[cache_key] = results
            self._save_cache()

        return results

    async def get_stream_url(self, track_url: str) -> Optional[str]:
        def _get_stream():
            opts = self.base_opts.copy()
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info = ydl.extract_info(track_url, download=False)
                    if info:
                        return info.get('url')
                except Exception:
                    return None
            return None
        return await asyncio.to_thread(_get_stream)

    # Stubs for User Library integration.
    # Without OAuth, full CRUD is hard via yt-dlp.
    # These would use aiohttp with soundcloud client_id for an actual robust auth implementation.
    async def get_likes(self, user_url: str) -> List[Dict[str, Any]]:
        """Fetch liked tracks for a user (via URL)."""
        def _fetch():
            opts = self.base_opts.copy()
            opts['extract_flat'] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    # yt-dlp usually parses soundcloud.com/user/likes
                    url = f"{user_url}/likes" if not user_url.endswith("/likes") else user_url
                    result = ydl.extract_info(url, download=False)
                    if result and 'entries' in result:
                        return list(result['entries'])
                    return []
                except Exception:
                    return []
        return await asyncio.to_thread(_fetch)

api = SoundCloudAPI()
