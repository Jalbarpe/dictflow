import os
import json
from datetime import datetime

HISTORY_PATH = os.path.expanduser("~/.config/dictflow/history.json")
MAX_ENTRIES = 100


def _load():
    if not os.path.exists(HISTORY_PATH):
        return []
    with open(HISTORY_PATH) as f:
        return json.load(f)


def _save(entries):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(entries[-MAX_ENTRIES:], f, ensure_ascii=False, indent=2)


def add_entry(raw_text, processed_text, context, language, duration):
    """Add a transcription entry to history."""
    entries = _load()
    entries.append({
        "timestamp": datetime.now().isoformat(),
        "raw": raw_text,
        "processed": processed_text,
        "context": context,
        "language": language,
        "duration_s": round(duration, 1),
    })
    _save(entries)


def get_recent(n=10):
    """Get the last n entries."""
    entries = _load()
    return entries[-n:]


def clear():
    """Clear all history."""
    _save([])
