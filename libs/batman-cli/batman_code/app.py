"""BatmanApp — minimal host app for the Batcave splash screen (Phase 1)."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Static

from batman_code.widgets.batcave import BatcaveScreen


class BatmanApp(App[int]):
    """Batman-themed AI coding TUI (Phase 1: loading screen demo)."""

    CSS_PATH = "app.tcss"

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash = no_splash

    def compose(self) -> ComposeResult:
        yield Static("", id="placeholder")

    def on_mount(self) -> None:
        self.push_screen(
            BatcaveScreen(no_splash=self._no_splash),
            callback=lambda _: self.exit(0),
        )
