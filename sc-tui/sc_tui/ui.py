from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, DataTable, Label, Button, ProgressBar
from textual.binding import Binding
from textual import work

from sc_tui.soundcloud_api import api as soundcloud
from sc_tui.player import Player

class PlayerControls(Container):
    """Widget displaying current track and playback controls."""

    def compose(self) -> ComposeResult:
        with Vertical():
            self.track_label = Label("No track playing", id="track_label")
            yield self.track_label

            with Horizontal():
                self.progress = ProgressBar(total=100, show_eta=False, id="progress_bar")
                yield self.progress

            with Horizontal(id="controls"):
                yield Button("⏮", id="prev_btn", variant="primary")
                yield Button("⏯", id="play_pause_btn", variant="success")
                yield Button("⏭", id="next_btn", variant="primary")
                yield Button("⏹", id="stop_btn", variant="error")


class ScTuiApp(App):
    """A Textual TUI for SoundCloud."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #search_container {
        height: auto;
        padding: 1;
        border: solid green;
    }

    #search_input {
        width: 100%;
    }

    #results_table {
        height: 1fr;
        border: solid blue;
    }

    PlayerControls {
        height: 8;
        dock: bottom;
        border: solid red;
        padding: 1;
    }

    #controls {
        height: auto;
        align: center middle;
    }

    #controls Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_play", "Play/Pause"),
        Binding("n", "next_track", "Next"),
        Binding("p", "prev_track", "Prev"),
        Binding("/", "focus_search", "Search"),
        Binding("+", "vol_up", "Vol +"),
        Binding("-", "vol_down", "Vol -"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = Player()

        # Player callbacks
        self.player.on_track_end = self.handle_track_end
        self.player.on_time_pos = self.update_progress

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="search_container"):
            yield Input(placeholder="Search SoundCloud...", id="search_input")

        self.table = DataTable(id="results_table")
        self.table.cursor_type = "row"
        self.table.add_columns("Title", "Artist", "Duration (s)")
        yield self.table

        self.controls = PlayerControls()
        yield self.controls
        yield Footer()

    def on_mount(self):
        self.table.focus()

    @work(exclusive=True)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input."""
        query = event.value
        if not query:
            return

        self.table.clear()
        self.table.loading = True

        try:
            results = await soundcloud.search_tracks(query, limit=15)
            self.table.loading = False

            # Store results globally to access them later
            self.current_results = results

            for i, track in enumerate(results):
                title = track.get('title', 'Unknown Title')
                uploader = track.get('uploader', 'Unknown Artist')
                duration = str(int(track.get('duration') or 0))
                self.table.add_row(title, uploader, duration, key=str(i))

            if results:
                self.table.focus()

        except Exception as e:
            self.notify(f"Search failed: {e}", severity="error")
            self.table.loading = False

    @work
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle track selection from the table."""
        idx = int(event.row_key.value)
        track = self.current_results[idx]

        self.player.add_to_queue(track)
        self.notify(f"Added to queue: {track.get('title')}")

        # If nothing is playing, play immediately
        if self.player.current_index == -1:
            self.player.current_index = 0
            await self._play_track(track)

    async def _play_track(self, track: dict):
        url = track.get('url')
        if not url:
            return

        self.controls.track_label.update(f"Loading: {track.get('title')}...")

        stream_url = await soundcloud.get_stream_url(url)
        if stream_url:
            # We run play_url in an executor to not block if mpv does synchronous stuff momentarily
            self.player.play_url(stream_url)
            self.controls.track_label.update(f"Playing: {track.get('title')} by {track.get('uploader')}")

            dur = track.get('duration')
            if dur:
                self.controls.progress.total = float(dur)
        else:
            self.notify("Failed to get stream URL", severity="error")

    def handle_track_end(self):
        """Called by MPV when track finishes."""
        def _update():
            next_t = self.player.next_track()
            if next_t:
                # We are technically in MPV's callback thread, so we schedule the async play
                self.run_worker(self._play_track(next_t))
            else:
                self.controls.track_label.update("Queue finished")
                self.controls.progress.progress = 0

        self.call_from_thread(_update)

    def update_progress(self, time_pos: float):
        """Called by MPV when playback position changes."""
        def _update():
            # Sometimes total is not correctly set yet
            if self.controls.progress.total and time_pos <= self.controls.progress.total:
                self.controls.progress.progress = time_pos
        self.call_from_thread(_update)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the player."""
        btn_id = event.button.id
        if btn_id == "play_pause_btn":
            self.action_toggle_play()
        elif btn_id == "next_btn":
            self.action_next_track()
        elif btn_id == "prev_btn":
            self.action_prev_track()
        elif btn_id == "stop_btn":
            self.player.stop()
            self.controls.track_label.update("Stopped")
            self.controls.progress.progress = 0

    def action_toggle_play(self) -> None:
        self.player.pause()

    def action_next_track(self) -> None:
        next_t = self.player.next_track()
        if next_t:
            self.run_worker(self._play_track(next_t))

    def action_prev_track(self) -> None:
        prev_t = self.player.prev_track()
        if prev_t:
            self.run_worker(self._play_track(prev_t))

    def action_focus_search(self) -> None:
        self.query_one("#search_input").focus()

    def action_vol_up(self) -> None:
        vol = self.player.get_volume()
        self.player.set_volume(vol + 5)
        self.notify(f"Volume: {self.player.get_volume()}%")

    def action_vol_down(self) -> None:
        vol = self.player.get_volume()
        self.player.set_volume(vol - 5)
        self.notify(f"Volume: {self.player.get_volume()}%")
