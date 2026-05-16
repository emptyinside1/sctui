import mpv
import asyncio
from typing import Callable, Optional, Dict, Any
from pathlib import Path
from sc_tui.config import get_cache_dir
from sc_tui.core.queue import QueueManager

class PlayerCore:
    """
    Advanced audio player backend using python-mpv.
    Includes caching integration and queue management.
    """
    def __init__(self):
        self.queue = QueueManager()

        # Determine mpv cache directory
        cache_dir = get_cache_dir() / "mpv_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Advanced mpv initialization for audio-only and caching
        self.mpv = mpv.MPV(
            video=False,
            ytdl=False,
            cache='yes',
            demuxer_max_bytes=150 * 1024 * 1024, # 150MB ram cache
            demuxer_max_back_bytes=50 * 1024 * 1024, # 50MB back cache
            cache_dir=str(cache_dir),
            cache_on_disk='yes'
        )

        # Callbacks
        self.on_track_end: Optional[Callable[[], None]] = None
        self.on_time_pos: Optional[Callable[[float], None]] = None

        # Bindings
        @self.mpv.property_observer('time-pos')
        def time_observer(_name, value):
            if value is not None and self.on_time_pos:
                self.on_time_pos(value)

        @self.mpv.event_callback('end-file')
        def end_file_event(event):
            reason = getattr(getattr(event, 'event', None), 'reason', -1)
            # 0 means EOF
            if reason == 0 and self.on_track_end:
                self.on_track_end()

    def play_url(self, stream_url: str):
        """Play a direct stream URL."""
        self.mpv.play(stream_url)

    def pause(self):
        self.mpv.pause = not self.mpv.pause

    def is_paused(self) -> bool:
        return self.mpv.pause

    def stop(self):
        self.mpv.stop()

    def seek(self, seconds: float):
        self.mpv.seek(seconds, reference='relative')

    def set_volume(self, volume: int):
        self.mpv.volume = max(0, min(100, volume))

    def get_volume(self) -> int:
        return self.mpv.volume

    def get_duration(self) -> float:
        return self.mpv.duration or 0.0

    def toggle_mute(self):
        self.mpv.mute = not self.mpv.mute
