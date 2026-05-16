from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Select, Input, Button
from textual.screen import ModalScreen

from sc_tui.config.settings import settings

class AuthModal(ModalScreen[None]):
    """Modal dialog for configuring authorization."""

    CSS = """
    AuthModal {
        align: center middle;
    }

    #auth_dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    .row {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="auth_dialog"):
            yield Label("Authorization Settings (for yt-dlp)", classes="row")

            # Authorization Method
            self.method_select = Select(
                [("None (Anonymous)", "none"), ("Browser Cookies", "browser"), ("Cookies File", "file")],
                prompt="Select Auth Method",
                value=settings.auth_method,
                id="auth_method"
            )
            yield self.method_select

            # Browser Selector (only visible if method == browser)
            self.browser_select = Select(
                [("Chrome", "chrome"), ("Firefox", "firefox"), ("Edge", "edge"), ("Safari", "safari"), ("Opera", "opera"), ("Brave", "brave"), ("Vivaldi", "vivaldi")],
                prompt="Select Browser",
                value=settings.auth_browser if settings.auth_method == "browser" else "chrome",
                id="auth_browser",
                classes="row"
            )
            self.browser_select.display = (settings.auth_method == "browser")
            yield self.browser_select

            # Cookie File Input (only visible if method == file)
            self.file_input = Input(
                placeholder="/path/to/cookies.txt",
                value=settings.auth_cookie_file,
                id="auth_file",
                classes="row"
            )
            self.file_input.display = (settings.auth_method == "file")
            yield self.file_input

            yield Button("Save & Close", variant="success", id="save_btn")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "auth_method":
            val = str(event.value) if event.value is not None else "none"
            self.browser_select.display = (val == "browser")
            self.file_input.display = (val == "file")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            m_val = self.method_select.value
            settings.auth_method = str(m_val) if m_val is not None else "none"

            b_val = self.browser_select.value
            settings.auth_browser = str(b_val) if b_val is not None else "chrome"

            settings.auth_cookie_file = self.file_input.value

            self.dismiss(None)
