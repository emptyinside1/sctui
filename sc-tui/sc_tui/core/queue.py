from typing import List, Dict, Any, Optional

class QueueManager:
    """Manages the playback queue, enabling reordering and 'Play Next'."""
    def __init__(self):
        self._tracks: List[Dict[str, Any]] = []
        self._current_index: int = -1

    @property
    def tracks(self) -> List[Dict[str, Any]]:
        return self._tracks

    @property
    def current_index(self) -> int:
        return self._current_index

    @current_index.setter
    def current_index(self, index: int):
        self._current_index = index

    def add(self, track: Dict[str, Any]):
        """Add to the end of the queue."""
        self._tracks.append(track)

    def add_next(self, track: Dict[str, Any]):
        """Insert track right after the currently playing one."""
        if self._current_index == -1:
            self.add(track)
        else:
            self._tracks.insert(self._current_index + 1, track)

    def remove(self, index: int):
        if 0 <= index < len(self._tracks):
            del self._tracks[index]
            if index < self._current_index:
                self._current_index -= 1
            elif index == self._current_index:
                # If removing the current track, logic should ideally jump to next,
                # but we just adjust the index bounds here for safety.
                pass

    def clear(self):
        self._tracks.clear()
        self._current_index = -1

    def move(self, old_index: int, new_index: int):
        """Move a track in the queue."""
        if 0 <= old_index < len(self._tracks) and 0 <= new_index < len(self._tracks):
            track = self._tracks.pop(old_index)
            self._tracks.insert(new_index, track)

            # Adjust current index
            if self._current_index == old_index:
                self._current_index = new_index
            elif old_index < self._current_index <= new_index:
                self._current_index -= 1
            elif new_index <= self._current_index < old_index:
                self._current_index += 1

    def get_current(self) -> Optional[Dict[str, Any]]:
        if 0 <= self._current_index < len(self._tracks):
            return self._tracks[self._current_index]
        return None

    def get_next(self) -> Optional[Dict[str, Any]]:
        if self._current_index + 1 < len(self._tracks):
            self._current_index += 1
            return self._tracks[self._current_index]
        return None

    def get_prev(self) -> Optional[Dict[str, Any]]:
        if self._current_index - 1 >= 0:
            self._current_index -= 1
            return self._tracks[self._current_index]
        return None

    def set_current_index(self, index: int):
        if 0 <= index < len(self._tracks):
            self._current_index = index
