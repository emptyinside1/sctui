from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, DataTable, Label, Button, ProgressBar, OptionList, Tree
from textual.binding import Binding
from textual import work

from sc_tui.api.client import api as soundcloud
from sc_tui.core.player import PlayerCore

# --- Components ---
class Sidebar(Container):
    """Navigation sidebar."""
    def compose(self) -> ComposeResult:
        self.nav = OptionList(
            "Search",
            "Trending",
            "My Likes",
            "Queue",
            id="nav_menu"
        )
        yield self.nav

class BottomPlayer(Container):
    """Status bar / Now Playing."""
    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="now_playing_info"):
                self.track_title = Label("No track", id="track_title")
                self.track_artist = Label("Artist", id="track_artist")
                yield self.track_title
                yield self.track_artist

            with Vertical(id="progress_container"):
                self.progress = ProgressBar(total=100, show_eta=False, id="progress_bar")
                with Horizontal(id="time_info"):
                    self.time_current = Label("0:00")
                    self.time_total = Label("0:00")
                    yield self.time_current
                    yield Label(" / ")
                    yield self.time_total
                yield self.progress

            with Horizontal(id="player_status"):
                self.status_lbl = Label("⏹ Stopped", id="status_icon")
                yield self.status_lbl

# --- Main App ---
class ScTuiApp(App):
    """Lazygit aesthetic TUI for SoundCloud."""

    CSS = """
    Screen {
        layout: vertical;
        /* Using system foreground/background to adapt */
        background: $background;
        color: $text;
    }

    #main_layout {
        layout: horizontal;
        height: 1fr;
    }

    Sidebar {
        width: 25;
        height: 1fr;
        border-right: solid $primary;
        padding: 1;
    }

    #content_area {
        width: 1fr;
        height: 1fr;
        layout: vertical;
        padding: 0 1;
    }

    #search_input {
        width: 100%;
        margin-bottom: 1;
        display: none;
    }

    #results_table {
        height: 1fr;
        border: none;
    }

    BottomPlayer {
        height: 6;
        dock: bottom;
        border-top: solid $primary;
        layout: horizontal;
        padding: 1;
    }

    #now_playing_info {
        width: 30%;
    }

    #track_title {
        text-style: bold;
        color: $accent;
    }

    #progress_container {
        width: 50%;
        align: center middle;
    }

    #time_info {
        height: 1;
        align: center middle;
    }

    #player_status {
        width: 20%;
        align: right middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "focus_next", "Focus Next"),
        Binding("shift+tab", "focus_prev", "Focus Prev"),
        Binding("space", "toggle_play", "Play/Pause"),
        Binding("n", "next_track", "Next"),
        Binding("p", "prev_track", "Prev"),
        Binding("/", "focus_search", "Search"),
        Binding("m", "toggle_mute", "Mute"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "go_top", "Top", show=False),
        Binding("G", "go_bottom", "Bottom", show=False),
        Binding("l", "like_track", "Like"),
        Binding("a", "add_to_playlist", "Add to Playlist"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = PlayerCore()

        # Callbacks
        self.player.on_track_end = self.handle_track_end
        self.player.on_time_pos = self.update_progress

        self.current_results = []
        self.current_view = "Search"
        self._search_query = ""
        self._search_offset = 0
        self._search_limit = 20

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_layout"):
            yield Sidebar()
            with Container(id="content_area"):
                yield Input(placeholder="Search...", id="search_input")
                self.table = DataTable(id="results_table")
                self.table.cursor_type = "row"
                self.table.add_columns("Title", "Artist", "Dur")
                yield self.table

        self.bottom_player = BottomPlayer()
        yield self.bottom_player
        yield Footer()

    def on_mount(self):
        self.query_one(Sidebar).nav.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        """Sidebar navigation handler."""
        view = event.option.prompt
        self.current_view = str(view)

        search_input = self.query_one("#search_input")
        if self.current_view == "Search":
            search_input.display = True
            search_input.focus()
            self.table.clear()
        elif self.current_view == "Queue":
            search_input.display = False
            self._render_queue()
        elif self.current_view == "My Likes":
            search_input.display = False
            self.run_worker(self._render_likes())
        else:
            search_input.display = False
            self.notify(f"{view} not fully implemented yet", severity="warning")

    async def _render_likes(self):
        """Mock rendering of user likes using yt-dlp stub."""
        self.table.clear()
        self.table.loading = True

        try:
            # Provide a fallback soundcloud user URL to scrape if unauthenticated
            mock_url = "https://soundcloud.com/sc-tui-mock-user/likes"
            results = await soundcloud.get_likes(mock_url)
            self.table.loading = False
            self.current_results = results

            if not results:
                self.notify("No likes found or unable to scrape likes (auth missing).", severity="warning")
                return

            for i, track in enumerate(results):
                title = track.get('title', 'Unknown Title')
                uploader = track.get('uploader', 'Unknown Artist')
                dur = self._format_time(track.get('duration') or 0)
                self.table.add_row(title, uploader, dur, key=str(i))

            if results:
                self.table.focus()
        except Exception as e:
            self.notify(f"Error loading likes: {e}", severity="error")
            self.table.loading = False

    def _render_queue(self):
        self.table.clear()
        self.current_results = self.player.queue.tracks
        for i, t in enumerate(self.current_results):
            title = t.get('title', 'Unknown')
            uploader = t.get('uploader', 'Unknown')
            dur = self._format_time(t.get('duration') or 0)
            # Decorate currently playing
            if i == self.player.queue.current_index:
                title = f"▶ {title}"
            self.table.add_row(title, uploader, dur, key=str(i))

    @work(exclusive=True)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        if not query or self.current_view != "Search": return

        self.table.clear()
        self.table.loading = True
        self._search_query = query
        self._search_offset = 0

        await self._load_more_search()

    async def _load_more_search(self):
        """Infinite pagination logic for search."""
        try:
            # yt-dlp scsearch doesn't have a clean offset parameter,
            # so we request a larger chunk simulating offset: search[N]:query
            # where N = offset + limit
            target_limit = self._search_offset + self._search_limit
            results = await soundcloud.search(self._search_query, limit=target_limit)

            # Slice only new results
            new_results = results[self._search_offset:]

            self.table.loading = False

            if not new_results and self._search_offset > 0:
                self.notify("No more results")
                return

            self.current_results.extend(new_results)

            start_idx = self._search_offset
            for i, track in enumerate(new_results):
                title = track.get('title', 'Unknown')
                uploader = track.get('uploader', 'Unknown')
                dur = self._format_time(track.get('duration') or 0)
                self.table.add_row(title, uploader, dur, key=str(start_idx + i))

            if new_results and self._search_offset == 0:
                self.table.focus()

            self._search_offset += len(new_results)

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.table.loading = False

    def action_go_bottom(self) -> None:
        if self.table.has_focus and self.table.row_count > 0:
            self.table.move_cursor(row=self.table.row_count - 1)
            # Trigger lazy load if we hit the bottom in Search view
            if self.current_view == "Search" and self._search_query:
                self.table.loading = True
                self.run_worker(self._load_more_search())

    @work
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = int(event.row_key.value)

        if self.current_view == "Search":
            track = self.current_results[idx]
            self.player.queue.add(track)
            self.notify(f"Added to queue: {track.get('title')}")

            if self.player.queue.current_index == -1:
                self.player.queue.set_current_index(0)
                await self._play_track(track)

        elif self.current_view == "Queue":
            self.player.queue.set_current_index(idx)
            track = self.player.queue.get_current()
            if track:
                await self._play_track(track)
                self._render_queue() # re-render to update the ▶ indicator

    async def _play_track(self, track: dict):
        self.bottom_player.track_title.update(f"⏳ {track.get('title')}")
        self.bottom_player.status_lbl.update("🔄 Loading")

        stream_url = await soundcloud.get_stream_url(track.get('url'))
        if stream_url:
            self.player.play_url(stream_url)
            self.bottom_player.track_title.update(track.get('title', 'Unknown'))
            self.bottom_player.track_artist.update(track.get('uploader', 'Unknown'))

            dur = float(track.get('duration') or 0)
            self.bottom_player.progress.total = dur
            self.bottom_player.time_total.update(self._format_time(dur))
            self.bottom_player.status_lbl.update("▶ Playing")
        else:
            self.notify("Failed to extract stream", severity="error")
            self.bottom_player.status_lbl.update("❌ Error")

    def handle_track_end(self):
        def _update():
            next_t = self.player.queue.get_next()
            if next_t:
                self.run_worker(self._play_track(next_t))
            else:
                self.bottom_player.status_lbl.update("⏹ Stopped")
                self.bottom_player.progress.progress = 0

            if self.current_view == "Queue":
                self._render_queue()

        self.call_from_thread(_update)

    def update_progress(self, time_pos: float):
        def _update():
            self.bottom_player.progress.progress = time_pos
            self.bottom_player.time_current.update(self._format_time(time_pos))
        self.call_from_thread(_update)

    def _format_time(self, seconds: float) -> str:
        s = int(seconds)
        m = s // 60
        s = s % 60
        return f"{m}:{s:02d}"

    # --- Actions ---
    def action_toggle_play(self) -> None:
        self.player.pause()
        if self.player.is_paused():
            self.bottom_player.status_lbl.update("⏸ Paused")
        else:
            self.bottom_player.status_lbl.update("▶ Playing")

    def action_next_track(self) -> None:
        next_t = self.player.queue.get_next()
        if next_t:
            self.run_worker(self._play_track(next_t))
        if self.current_view == "Queue":
            self._render_queue()

    def action_prev_track(self) -> None:
        prev_t = self.player.queue.get_prev()
        if prev_t:
            self.run_worker(self._play_track(prev_t))
        if self.current_view == "Queue":
            self._render_queue()

    def action_focus_search(self) -> None:
        if self.current_view == "Search":
            self.query_one("#search_input").focus()

    def action_toggle_mute(self) -> None:
        self.player.toggle_mute()

    def action_go_top(self) -> None:
        if self.table.has_focus:
            self.table.move_cursor(row=0)

    def action_like_track(self) -> None:
        if self.table.has_focus and self.table.row_count > 0:
            # We mock the like action for now.
            # In a real app with OAuth, we'd call `await soundcloud.like_track(...)`
            self.notify("Track liked (Mock) ♥")

    def action_add_to_playlist(self) -> None:
        if self.table.has_focus and self.table.row_count > 0:
            from sc_tui.ui.components.playlist_modal import PlaylistModal

            def handle_playlist_result(playlist_name: str | None):
                if playlist_name:
                    self.notify(f"Added to playlist '{playlist_name}' (Mock)")

            self.push_screen(PlaylistModal(), handle_playlist_result)
