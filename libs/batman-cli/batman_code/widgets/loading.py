"""Loading widget with bat-wing spinner for agent activity."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING

from textual.containers import Horizontal
from textual.widgets import Static

from batman_code.config import COLORS, get_glyphs

if TYPE_CHECKING:
    from textual.app import ComposeResult


# Bat-wing flutter — hardcoded so the spinner stays themed regardless of
# the active charset glyph set (UNICODE_GLYPHS uses Braille for general-purpose
# spinners; this widget is Batman-only).
_BAT_WING_FRAMES: tuple[str, ...] = ("( \\  )", "(  \\ )", "(  / )", "( /  )")

# Rotating Gotham status messages — cycled every ~5s while the spinner runs.
_GOTHAM_STATUS_MESSAGES: tuple[str, ...] = (
    "Analyzing with the Batcomputer",
    "Consulting the case files",
    "Scanning Gotham",
    "Running forensics",
)

_STATUS_ROTATION_SECONDS = 5.0


class Spinner:
    """Animated bat-wing spinner."""

    def __init__(self) -> None:
        """Initialize spinner."""
        self._position = 0

    @property
    def frames(self) -> tuple[str, ...]:
        """Get spinner frames."""
        return _BAT_WING_FRAMES

    def next_frame(self) -> str:
        """Get next animation frame.

        Returns:
            The next spinner character in the animation sequence.
        """
        frames = self.frames
        frame = frames[self._position]
        self._position = (self._position + 1) % len(frames)
        return frame

    def current_frame(self) -> str:
        """Get current frame without advancing.

        Returns:
            The current spinner character.
        """
        return self.frames[self._position]


class LoadingWidget(Static):
    """Animated loading indicator with bat-wing spinner, rotating Gotham
    status text, and elapsed time.

    Displays: <bat-wing> Analyzing with the Batcomputer... (3s, esc to interrupt)
    """

    DEFAULT_CSS = """
    LoadingWidget {
        height: auto;
        padding: 0 1;
        margin-top: 1;
    }

    LoadingWidget .loading-container {
        height: auto;
        width: 100%;
    }

    LoadingWidget .loading-spinner {
        width: auto;
        color: $warning;
    }

    LoadingWidget .loading-status {
        width: auto;
        color: $warning;
    }

    LoadingWidget .loading-hint {
        width: auto;
        color: $text-muted;
        margin-left: 1;
    }
    """

    def __init__(self, status: str | None = None) -> None:
        """Initialize loading widget.

        Args:
            status: Initial status text to display. When omitted, the widget
                rotates through Gotham status messages every ~5s. When provided
                explicitly, rotation is disabled until set_status is called
                with None.
        """
        super().__init__()
        self._caller_status = status  # explicit override; disables rotation
        self._rotation_index = 0
        self._status = status if status is not None else _GOTHAM_STATUS_MESSAGES[0]
        self._spinner = Spinner()
        self._start_time: float | None = None
        self._spinner_widget: Static | None = None
        self._status_widget: Static | None = None
        self._hint_widget: Static | None = None
        self._paused = False
        self._paused_elapsed: int = 0

    def compose(self) -> ComposeResult:
        """Compose the loading widget layout.

        Yields:
            Widgets for spinner, status text, and hint.
        """
        with Horizontal(classes="loading-container"):
            self._spinner_widget = Static(
                self._spinner.current_frame(), classes="loading-spinner"
            )
            yield self._spinner_widget

            self._status_widget = Static(
                f" {self._status}... ", classes="loading-status"
            )
            yield self._status_widget

            self._hint_widget = Static("(0s, esc to interrupt)", classes="loading-hint")
            yield self._hint_widget

    def on_mount(self) -> None:
        """Start animation on mount."""
        self._start_time = time()
        self.set_interval(0.1, self._update_animation)
        # Rotate Gotham status messages — only when caller didn't pin a status
        if self._caller_status is None:
            self.set_interval(_STATUS_ROTATION_SECONDS, self._rotate_status)

    def _update_animation(self) -> None:
        """Update spinner and elapsed time."""
        if self._paused:
            return

        if self._spinner_widget:
            frame = self._spinner.next_frame()
            self._spinner_widget.update(f"[{COLORS['bat_gold']}]{frame}[/]")

        if self._hint_widget and self._start_time is not None:
            elapsed = int(time() - self._start_time)
            self._hint_widget.update(f"({elapsed}s, esc to interrupt)")

    def _rotate_status(self) -> None:
        """Advance to the next Gotham status message."""
        if self._paused or self._caller_status is not None:
            return
        self._rotation_index = (self._rotation_index + 1) % len(_GOTHAM_STATUS_MESSAGES)
        self._status = _GOTHAM_STATUS_MESSAGES[self._rotation_index]
        if self._status_widget:
            self._status_widget.update(f" {self._status}... ")

    def set_status(self, status: str | None) -> None:
        """Update the status text.

        Args:
            status: New status text. Pass `None` to resume Gotham message rotation.
        """
        self._caller_status = status
        if status is None:
            # Resume rotation from current index
            self._status = _GOTHAM_STATUS_MESSAGES[self._rotation_index]
        else:
            self._status = status
        if self._status_widget:
            self._status_widget.update(f" {self._status}... ")

    def pause(self, status: str = "Awaiting decision") -> None:
        """Pause the animation and update status.

        Args:
            status: Status to show while paused
        """
        self._paused = True
        if self._start_time is not None:
            self._paused_elapsed = int(time() - self._start_time)
        self._status = status
        self._caller_status = status
        if self._status_widget:
            self._status_widget.update(f" {status}... ")
        if self._hint_widget:
            self._hint_widget.update(f"(paused at {self._paused_elapsed}s)")
        if self._spinner_widget:
            self._spinner_widget.update(f"[dim]{get_glyphs().bat_symbol}[/dim]")

    def resume(self) -> None:
        """Resume the animation."""
        self._paused = False
        self._caller_status = None
        self._status = _GOTHAM_STATUS_MESSAGES[self._rotation_index]
        if self._status_widget:
            self._status_widget.update(f" {self._status}... ")

    def stop(self) -> None:
        """Stop the animation (widget will be removed by caller)."""
