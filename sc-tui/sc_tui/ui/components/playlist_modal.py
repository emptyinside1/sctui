from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Input, Button
from textual.screen import ModalScreen

class PlaylistModal(ModalScreen[str]):
    """Modal dialog for creating/selecting a playlist."""

    CSS = """
    PlaylistModal {
        align: center middle;
    }

    #dialog {
        padding: 1 2;
        width: 40;
        height: 12;
        border: thick $background 80%;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Add to Playlist", id="question")
            yield Input(placeholder="Playlist name...", id="playlist_input")
            yield Button("Create / Add", variant="success", id="add_btn")
            yield Button("Cancel", variant="primary", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_btn":
            val = self.query_one("#playlist_input").value
            self.dismiss(val)
        else:
            self.dismiss(None)
