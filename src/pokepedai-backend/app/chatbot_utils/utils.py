import logging

logger = logging.getLogger(__name__)

DEFAULT_MAX_TURNS = 8
DEFAULT_MAX_CHARS = 3200

def extract_search_query(text):
    """
    Extract a search query from free-form reasoning text.
    - If there's a line starting with 'QUERY:', use that.
    - Otherwise, take the last non-trivial sentence.
    """
    lines = text.splitlines()
    for line in reversed(lines):
        if line.strip().upper().startswith("QUERY:"):
            return line.split(":", 1)[1].strip() or text.strip()

    sentences = text.split(".")
    for s in reversed(sentences):
        s = s.strip()
        if len(s) > 10:
            return s
    return text.strip()

def build_context(results, max_chars: int = DEFAULT_MAX_CHARS):
    '''
    Build context to be input into chat prompt from retrieved RAG documents.
    '''
    parts = []
    total_len = 0

    for r in results:
        m = r["doc"]
        if m.get("pokemon"):
            header = f"[{m.get('pokemon')} — {m.get('section')}]"
        else:
            header = f"[{m.get('section')}]"
        text = m.get("text") or ""

        chunk_str = header + "\n"
        chunk_str += text + "\n"

        if total_len + len(chunk_str) > max_chars:
            break

        parts.append(chunk_str)
        total_len += len(chunk_str)

    logger.debug("Built context of length %d characters", total_len)
    return "\n".join(parts)

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
