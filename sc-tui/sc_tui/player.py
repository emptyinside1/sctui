import mpv
import asyncio
from typing import Callable, Optional, List, Dict, Any

class Player:
    """
    Audio player backend using python-mpv.
    Manages the playback queue and state.
    """
    def __init__(self):
        # We need to run mpv without video
        self.mpv = mpv.MPV(video=False, ytdl=False)
        self.queue: List[Dict[str, Any]] = []
        self.current_index: int = -1

        # Callbacks
        self.on_track_end: Optional[Callable[[], None]] = None
        self.on_time_pos: Optional[Callable[[float], None]] = None
        self.on_metadata: Optional[Callable[[Dict[str, Any]], None]] = None

        # MPV event bindings
        @self.mpv.property_observer('time-pos')
        def time_observer(_name, value):
            if value is not None and self.on_time_pos:
                # Use asyncio.get_event_loop().call_soon_threadsafe if we were strictly in asyncio loop here,
                # but textual handles thread-safe message posting nicely. For safety we just call it.
                self.on_time_pos(value)

        @self.mpv.event_callback('end-file')
        def end_file_event(event):
            # The event object is an MpvEvent struct wrapper
            reason = getattr(getattr(event, 'event', None), 'reason', -1)
            # reason 0 means EOF (mpv.MpvEventEndFile.EOF)
            if reason == 0:
                if self.on_track_end:
                    self.on_track_end()

    def play_url(self, stream_url: str, metadata: Dict[str, Any] = None):
        """Play a direct stream URL."""
        self.mpv.play(stream_url)
        if metadata and self.on_metadata:
            self.on_metadata(metadata)

    def pause(self):
        self.mpv.pause = not self.mpv.pause

    def stop(self):
        self.mpv.stop()

    def seek(self, seconds: float):
        self.mpv.seek(seconds, reference='relative')

    def set_volume(self, volume: int):
        """Set volume (0-100)"""
        self.mpv.volume = max(0, min(100, volume))

    def get_volume(self) -> int:
        return self.mpv.volume

    def get_duration(self) -> float:
        return self.mpv.duration or 0.0

    # --- Queue Management ---
    def add_to_queue(self, track: Dict[str, Any]):
        self.queue.append(track)

    def next_track(self) -> Dict[str, Any] | None:
        if self.current_index + 1 < len(self.queue):
            self.current_index += 1
            return self.queue[self.current_index]
        return None

    def prev_track(self) -> Dict[str, Any] | None:
        if self.current_index - 1 >= 0:
            self.current_index -= 1
            return self.queue[self.current_index]
        return None

    def get_current_track(self) -> Dict[str, Any] | None:
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    def clear_queue(self):
        self.queue.clear()
        self.current_index = -1
        self.stop()
