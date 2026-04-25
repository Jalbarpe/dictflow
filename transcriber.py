import os
import re
from config import WHISPER_LANGUAGE

# Ensure ffmpeg is in PATH (Homebrew)
if "/opt/homebrew/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

# whisper-large-v3-turbo: 4-layer decoder → ~4x más rápido que medium en Apple Silicon,
# con mejor WER en español. mlx_whisper mantiene el modelo en lru_cache tras la 1ra llamada.
MLX_MODEL = "mlx-community/whisper-large-v3-turbo"

# Initial prompt per language. Whisper uses this as context to bias vocabulary,
# language AND punctuation style. Per OpenAI discussion #117, long descriptive
# prompts tend to trigger repetition loops — keep it short and comma-rich.
#
# To bias toward your own proper nouns (names, brands, jargon) without
# committing personal data, drop a custom prompt at:
#   ~/.config/dictflow/prompt_es.txt   (or prompt_en.txt)
# It will override the default below for that language.
INITIAL_PROMPTS = {
    "es": "Hola, ¿cómo estás? Hoy quiero anotar varias ideas, pendientes y notas con comas y puntos.",
    "en": "Hello, how are you? Today I want to jot down several ideas, pending tasks, and notes with commas and periods.",
}

_PROMPT_OVERRIDE_DIR = os.path.expanduser("~/.config/dictflow")


def _load_initial_prompt(lang):
    """Return a per-user override prompt if present, else the bundled default."""
    if not lang:
        return None
    override = os.path.join(_PROMPT_OVERRIDE_DIR, f"prompt_{lang}.txt")
    if os.path.exists(override):
        try:
            with open(override) as f:
                custom = f.read().strip()
                if custom:
                    return custom
        except OSError:
            pass
    return INITIAL_PROMPTS.get(lang)


class Transcriber:
    def __init__(self):
        print("[DictFlow] Pre-cargando modelo mlx-whisper large-v3-turbo...")
        self._language = WHISPER_LANGUAGE
        from huggingface_hub import snapshot_download
        self._model_path = snapshot_download(MLX_MODEL)

        # Warm up GPU with a silent audio to avoid 2.5s delay on first real dictation
        import tempfile, wave, struct
        warmup_file = tempfile.mktemp(suffix=".wav")
        wf = wave.open(warmup_file, "wb")
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
        wf.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))
        wf.close()
        try:
            import mlx_whisper
            mlx_whisper.transcribe(warmup_file, path_or_hf_repo=self._model_path, language=self._language or "en")
        except Exception:
            pass
        finally:
            os.remove(warmup_file)

        print("[DictFlow] mlx-whisper listo (GPU warm).")

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, lang):
        self._language = lang
        print(f"[DictFlow] Idioma cambiado a: {lang}")

    def transcribe(self, audio_path, audio_duration=None):
        if not audio_path or not os.path.exists(audio_path):
            return "", []

        # Use the cached local path instead of HF repo name — avoids re-fetching
        import mlx_whisper
        # Only pass an initial_prompt if it matches the selected language.
        # In auto-detect mode (language=None) we skip it entirely so a
        # Spanish-biased prompt doesn't override detection.
        initial_prompt = _load_initial_prompt(self._language)

        # word_timestamps=True gives us per-word start/end times, which the
        # post-processor uses to insert punctuation from inter-word silences.
        # hallucination_silence_threshold only takes effect when word_timestamps
        # is on; it skips long silences that tend to produce phantom captions.
        params = dict(
            path_or_hf_repo=self._model_path,
            condition_on_previous_text=False,
            suppress_tokens=[],
            fp16=True,
            verbose=False,
            word_timestamps=True,
            hallucination_silence_threshold=2.0,
        )
        if initial_prompt:
            params["initial_prompt"] = initial_prompt
        if self._language:
            params["language"] = self._language

        result = mlx_whisper.transcribe(audio_path, **params)
        text = result.get("text", "").strip()
        segments = result.get("segments", []) or []

        if self._is_hallucination(text):
            print(f"[DictFlow] Skipped: {text[:50]}")
            return "", []

        return text, segments

    def _is_hallucination(self, text):
        if not text or len(text.strip()) < 3:
            return True

        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        if len(sentences) >= 4:
            from collections import Counter
            counts = Counter(s.lower() for s in sentences)
            if counts.most_common(1)[0][1] >= 4:
                return True

        patterns = [
            r"(?i)^thank(s| you) for watching\.?$",
            r"(?i)^please subscribe",
            r"(?i)^gracias por ver",
            r"(?i)^transcripci[oó]n literal",
            r"(?i)^\[.*?\]$",
            r"(?i)^♪+$",
        ]
        return any(re.search(p, text.strip()) for p in patterns)
