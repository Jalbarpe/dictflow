import re

# Filler words to remove (Spanish + English).
# "bueno" intentionally excluded — it's also a discourse-marker starter
# (handled by _COMMA_AFTER_STARTERS) and removing it leaves orphan punctuation.
FILLERS = [
    r'\bo sea\b', r'\bpues\b', r'\blisto\b', r'\bajá\b',
    r'\bdigamos\b', r'\bcomo que\b', r'\b¿verdad\?\b', r'\b¿sí\?\b',
    r'\b¿no\?\b', r'\behh?\b', r'\bumm?\b', r'\buhh?\b',
    r'\beste\b(?=\s+(?:el|la|los|las|un|una|que|no|sí|yo|tú|es|hay|se)\b)',  # "este" only as filler, not demonstrative
]

# Colombian colloquialisms
COLLOQUIALISMS = {
    r'\bvaina\b': 'cosa',
    r'\bbacano\b': 'excelente',
    r'\bchévere\b': 'genial',
}

# Words whose repetition is intentional emphasis — never remove
EMPHASIS_WORDS = {"sí", "si", "no", "claro", "exacto", "ok", "dale", "ya"}

# Month names used to distinguish "10 de abril" (date) from "10. primer ítem" (list).
_MONTH_NAMES = (
    r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
    r"septiembre|setiembre|octubre|noviembre|diciembre|"
    r"january|february|march|april|may|june|july|august|"
    r"september|october|november|december"
)
_DATE_AFTER_NUMBER = re.compile(rf"^(?:de\s+)?(?:{_MONTH_NAMES})\b", re.IGNORECASE)

# Connectors/adverbs that typically take a comma BEFORE them in Spanish.
_COMMA_BEFORE = (
    r"pero|sino|aunque|mientras que|"
    r"sin embargo|no obstante|"
    r"por lo tanto|por tanto|por ende|por eso|"
    r"así que|de modo que|de manera que|de forma que|"
    r"es decir|o sea que|"
    r"por ejemplo|en cambio|"
    r"además|por cierto|de hecho|"
    r"ya que|puesto que|dado que"
)

# Discourse markers at the start of a sentence that take a comma AFTER them.
_COMMA_AFTER_STARTERS = (
    r"bueno|entonces|ahora bien|"
    r"en realidad|de hecho|por supuesto|"
    r"obviamente|efectivamente|"
    r"primero|segundo|tercero|cuarto|quinto|"
    r"finalmente|por último|"
    r"en resumen|en conclusión|en definitiva|"
    r"por cierto|sin embargo|no obstante|"
    r"por ejemplo|además|también|"
    r"sí|no|claro"
)

# Phrases that introduce an enumeration and should end in a colon.
_COLON_INTRO = re.compile(
    r"(?i)\b("
    r"lo siguiente|"
    r"los siguientes|las siguientes|"
    r"a continuación|"
    r"los pasos (?:son|a seguir)|"
    r"las tareas son|"
    r"son los siguientes|son las siguientes"
    r")\s*\.?\s*$"
)


# Pause thresholds (seconds) for inferring punctuation from word timings.
# Calibrated for stream-of-consciousness Spanish dictation: speakers rarely
# pause >700ms mid-clause, and 300ms is roughly a comma-length breath.
_LONG_PAUSE_S = 0.70
_SHORT_PAUSE_S = 0.30
_SENT_PUNCT = (".", "!", "?")
_ANY_PUNCT = (".", ",", ";", ":", "!", "?")


def _punctuate_from_pauses(segments, long_pause=_LONG_PAUSE_S, short_pause=_SHORT_PAUSE_S):
    """Rebuild text inserting '.' / ',' from inter-word silences.

    Whisper word_timestamps gives us start/end of every word. When the speaker
    pauses, the silence is in the timestamps even if the model didn't emit any
    punctuation. This is the only deterministic way to recover sentence
    boundaries in stream-of-consciousness dictation without an LLM.

    Capitalization after the inserted period is left to _capitalize_and_punctuate.
    """
    if not segments:
        return ""

    pieces = []
    prev_end = None

    for seg in segments:
        for w in (seg.get("words") or []):
            token = w.get("word", "")
            if not token:
                continue
            start = w.get("start")
            end = w.get("end")

            if prev_end is not None and pieces and start is not None:
                gap = start - prev_end
                last_strip = pieces[-1].rstrip()
                tok_strip = token.lstrip()
                already_before = last_strip.endswith(_ANY_PUNCT)
                already_after = tok_strip.startswith(_ANY_PUNCT) or tok_strip.startswith(("¿", "¡"))

                if not already_before and not already_after:
                    if gap >= long_pause:
                        pieces[-1] = last_strip + "."
                    elif gap >= short_pause:
                        pieces[-1] = last_strip + ","

            pieces.append(token)
            if end is not None:
                prev_end = end

    return "".join(pieces).strip()


def _remove_fillers(text):
    """Remove filler words using regex — no LLM needed."""
    for pattern in FILLERS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Clean up double spaces left behind
    text = re.sub(r'\s{2,}', ' ', text).strip()
    # Clean up leading commas/spaces after removal
    text = re.sub(r'^\s*,\s*', '', text)
    text = re.sub(r',\s*,', ',', text)
    # Orphan punctuation left when a filler sat between a sentence-ender
    # and the next clause: ". , foo" → ". foo"; "foo , ." → "foo."
    text = re.sub(r'([.!?])\s*,', r'\1', text)
    text = re.sub(r',\s*([.!?])', r'\1', text)
    return text.strip()


def _fix_colloquialisms(text):
    """Replace Colombian colloquialisms with neutral Spanish."""
    for pattern, replacement in COLLOQUIALISMS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _restore_punctuation(text):
    """Insert commas that Whisper tends to omit in dictation without pauses."""
    if not text:
        return text

    # Comma before connectors — only if not already preceded by punctuation.
    # The word-char lookbehind (via \w + Spanish letters) skips cases that
    # already have ',' ';' ':' '.' before the connector.
    text = re.sub(
        rf"(?i)(?<=[\wáéíóúñüÁÉÍÓÚÑÜ])\s+({_COMMA_BEFORE})\b",
        r", \1",
        text,
    )

    # Comma after sentence-initial discourse markers (start of string or
    # right after a sentence-ending punctuation mark / newline).
    text = re.sub(
        rf"(?im)(^|[.!?]\s+|\n)({_COMMA_AFTER_STARTERS})\s+(?=[a-záéíóúñü])",
        r"\1\2, ",
        text,
    )

    # Collapse any duplicates introduced above.
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+,", ",", text)

    return text


def _finalize_list_prefix(prefix):
    """Strip trailing punctuation and add a colon if the prefix introduces a list."""
    prefix = prefix.strip().rstrip(".,;:")
    if not prefix:
        return ""
    if _COLON_INTRO.search(prefix) or re.search(r"(?i)\b(?:son|hay|tengo|existen|incluyen|siguientes?)\s*$", prefix):
        return prefix + ":"
    return prefix + "."


def _format_structure(text):
    """Format numbered lists and line breaks from voice commands."""

    # Detect "1. X 2. Y 3. Z" patterns from Whisper
    numbered_match = re.split(r'(?<=[.!?,\s])\s*(\d+)[.\-)\s]+', text)
    if len(numbered_match) >= 5:
        # Skip if any number is actually the day of a date ("10 de abril", "15 mayo").
        looks_like_date = any(
            _DATE_AFTER_NUMBER.match(numbered_match[i + 1].lstrip())
            for i in range(1, len(numbered_match) - 1, 2)
        )
        if not looks_like_date:
            prefix = _finalize_list_prefix(numbered_match[0])
            items = []
            for i in range(1, len(numbered_match) - 1, 2):
                num = numbered_match[i]
                content = numbered_match[i + 1].strip().rstrip('.,').strip()
                if content:
                    items.append(f"{num}. {content}")
            if len(items) >= 2:
                text = (prefix + "\n" if prefix else "") + "\n".join(items)
                return text.strip()

    # Detect "A. X B. Y C. Z" letter-based lists
    # Letters can appear after space, period, or other punctuation
    letter_match = re.split(r'\s+([A-Z])\.\s+', text)
    if len(letter_match) >= 5:
        # Verify letters are sequential (A, B, C...)
        letters = [letter_match[i] for i in range(1, len(letter_match), 2)]
        is_sequential = all(ord(letters[i]) == ord(letters[0]) + i for i in range(len(letters)))
        if is_sequential and len(letters) >= 2:
            prefix = _finalize_list_prefix(letter_match[0])
            items = []
            for i in range(1, len(letter_match) - 1, 2):
                letter = letter_match[i]
                content = letter_match[i + 1].strip().rstrip('.,').strip()
                if content:
                    items.append(f"{letter}. {content}")
            if len(items) >= 2:
                text = (prefix + "\n" if prefix else "") + "\n".join(items)
                return text.strip()

    # "uno X dos Y tres Z" → "1. X\n2. Y\n3. Z"
    parts = re.split(r'(?i)\buno\b[,:]?\s+', text, maxsplit=1)
    if len(parts) == 2:
        prefix = _finalize_list_prefix(parts[0])
        rest = parts[1]
        items = re.split(r'(?i)\b(?:dos|tres|cuatro|cinco)\b[,:]?\s+', rest)
        if len(items) >= 2:
            numbered = [f"{i}. {item.strip().rstrip(',').strip()}" for i, item in enumerate(items, 1)]
            text = (prefix + "\n" if prefix else "") + "\n".join(numbered)

    # "primero X segundo Y tercero Z"
    if re.search(r'(?i)\bprimero\b', text):
        parts = re.split(r'(?i)\bprimero\b[,:]?\s+', text, maxsplit=1)
        if len(parts) == 2:
            prefix = _finalize_list_prefix(parts[0])
            rest = parts[1]
            items = re.split(r'(?i)\b(?:segundo|tercero|cuarto|quinto)\b[,:]?\s+', rest)
            if len(items) >= 2:
                numbered = [f"{i}. {item.strip().rstrip(',').strip()}" for i, item in enumerate(items, 1)]
                text = (prefix + "\n" if prefix else "") + "\n".join(numbered)

    # Voice commands for line breaks
    text = re.sub(r'(?i)\b(?:nueva línea|nuevo párrafo|punto y aparte|salto de línea|new line|new paragraph)\b[.,]?\s*', '\n', text)

    return text.strip()


_CAP_AFTER_SENT_END = re.compile(r'([.!?]\s+|[.!?]["\')\]]\s+)([a-záéíóúñü])')


def _capitalize_and_punctuate(text):
    """Capitalize line starts AND first letter after every .!?, then ensure ending punctuation."""
    if not text:
        return text

    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        line = line[0].upper() + line[1:]
        line = _CAP_AFTER_SENT_END.sub(lambda m: m.group(1) + m.group(2).upper(), line)
        if line[-1] not in ".!?:;":
            line += "."
        result.append(line)

    return '\n'.join(result)


def process_text(raw_text, context="general", segments=None):
    """Clean up dictated text — fast, local, no LLM.

    If `segments` (Whisper output with word_timestamps=True) is provided, we
    rebuild the text from word timings so silences become punctuation.
    Otherwise we fall back to raw_text as-is.
    """
    if not raw_text or not raw_text.strip():
        return ""

    if segments:
        rebuilt = _punctuate_from_pauses(segments)
        text = rebuilt or raw_text
    else:
        text = raw_text

    # Step 1: Remove filler words
    text = _remove_fillers(text)

    # Step 2: Fix colloquialisms
    text = _fix_colloquialisms(text)

    # Step 3: Insert commas Whisper usually skips in unbroken dictation
    text = _restore_punctuation(text)

    # Step 4: Format structure (lists, line breaks)
    text = _format_structure(text)

    # Step 5: Capitalize and punctuate
    text = _capitalize_and_punctuate(text)

    return text
