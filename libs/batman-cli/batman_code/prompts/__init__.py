"""Persona prompt loading for bat-code."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_persona(name: str) -> str:
    """Load a persona prompt by name.

    Args:
        name: Persona name (e.g., "batman", "alfred").

    Returns:
        The persona prompt markdown content.

    Raises:
        FileNotFoundError: If the persona prompt file does not exist.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Persona prompt not found: {name}")
    return path.read_text()
