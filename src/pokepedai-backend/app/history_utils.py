import logging

logger = logging.getLogger(__name__)

DEFAULT_MAX_TURNS = 8
DEFAULT_MAX_CHARS = 3200


def trim_history(history, max_turns: int = DEFAULT_MAX_TURNS):
    """
    Trim conversation history so we only keep up to `max_turns` turns
    """
    if not history:
        return []

    trimmed = history[-max_turns:]

    logger.debug(
        "trim_history: original_len=%d trimmed_len=%d",
        len(history),
        len(trimmed),
    )

    return trimmed


def format_history(history, max_chars: int = DEFAULT_MAX_CHARS):
    """
    Format history into a standarized text format, truncate to `max_chars` length.
    """
    lines: List[str] = []
    for turn in history:
        role = turn.get("role", "user")
        speaker = "User" if role == "user" else "Assistant"
        msg = turn.get("message", "")
        lines.append(f"{speaker}: {msg}")

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[-max_chars:]

    logger.debug(
        "format_history: final_len=%d",
        len(text),
    )
    return text
