"""Unit tests for `batman_code.widgets.autocomplete.SLASH_COMMANDS`.

First test file for the autocomplete module (which was ported verbatim
in Phase 5 as a deep-import leaf). Scoped to the /batsignal
registration landed in Batch 13 — SlashCommandController /
FuzzyFileController / MultiCompletionManager filter behavior is
covered indirectly by the ChatInput integration tests + Phase 10
end-to-end.
"""

from __future__ import annotations

from batman_code.widgets.autocomplete import SLASH_COMMANDS


def test_batsignal_is_registered_in_slash_commands() -> None:
    names = [name for name, _desc in SLASH_COMMANDS]
    assert "/batsignal" in names


def test_batsignal_description_matches_spec() -> None:
    # Regression guard against wording drift. "Toggle bat-signal
    # overlay" was locked in the Phase 7 plan doc.
    entries = dict(SLASH_COMMANDS)
    assert entries["/batsignal"] == "Toggle bat-signal overlay"


def test_batsignal_is_appended_last() -> None:
    # /batsignal was added as the 13th entry after the original 12
    # verbatim-ported commands. Its position is a signal to future
    # readers that it landed in Phase 7 (later than the rest).
    assert SLASH_COMMANDS[-1][0] == "/batsignal"


def test_slash_commands_count_is_thirteen() -> None:
    # Regression guard against accidental entry removal. If this
    # count needs to change, do so deliberately + update the count
    # here in the same commit.
    assert len(SLASH_COMMANDS) == 13
