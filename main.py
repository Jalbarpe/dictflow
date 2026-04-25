#!/usr/bin/env python3
"""DictFlow — Local voice dictation app with AI post-processing."""

import os
import sys
import time
import fcntl
import threading
import rumps

from recorder import AudioRecorder
from transcriber import Transcriber
from processor import process_text
from injector import inject_text
from context import get_context
from hotkey import GlobeKeyListener
from sounds import play_start, play_stop, play_error
from history import add_entry, get_recent


class DictFlowApp(rumps.App):
    def __init__(self):
        super().__init__(
            "DictFlow",
            title="\U0001f3a4",
            quit_button=None,
        )

        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.listener = GlobeKeyListener(
            on_press=self._on_globe_press,
            on_release=self._on_globe_release,
        )
        self._processing = False
        self._record_start_time = 0

        # Menu items
        self.status_item = rumps.MenuItem("Status: Ready")
        self.status_item.set_callback(None)

        self.cleanup_toggle = rumps.MenuItem("Limpiar muletillas", callback=self._toggle_cleanup)
        self.cleanup_toggle.state = True

        # Language submenu
        self.lang_menu = rumps.MenuItem("Idioma")
        self.lang_es = rumps.MenuItem("Español", callback=self._set_lang_es)
        self.lang_en = rumps.MenuItem("English", callback=self._set_lang_en)
        self.lang_auto = rumps.MenuItem("Auto-detectar", callback=self._set_lang_auto)
        # Reflect the initial language from config
        from config import WHISPER_LANGUAGE
        if WHISPER_LANGUAGE == "es":
            self.lang_es.state = True
        elif WHISPER_LANGUAGE == "en":
            self.lang_en.state = True
        else:
            self.lang_auto.state = True
        self.lang_menu.update([self.lang_es, self.lang_en, self.lang_auto])

        # History submenu
        self.history_menu = rumps.MenuItem("Historial")
        self.history_menu.update([
            rumps.MenuItem("Ver últimas 10", callback=self._show_history),
            rumps.MenuItem("Limpiar historial", callback=self._clear_history),
        ])

        self.menu = [
            self.status_item,
            None,
            self.cleanup_toggle,
            self.lang_menu,
            self.history_menu,
            None,
            rumps.MenuItem("Quit DictFlow", callback=self._quit),
        ]

    def _on_globe_press(self):
        if self._processing:
            return
        self._set_status("Recording...", "\U0001f534")
        play_start()
        self._record_start_time = time.time()
        self.recorder.start()

    def _on_globe_release(self):
        if not self.recorder.is_recording:
            return
        play_stop()
        audio_path = self.recorder.stop()
        duration = time.time() - self._record_start_time

        if duration < 0.5:
            self._set_status("Ready", "\U0001f3a4")
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            return

        print(f"[DictFlow] Recorded {duration:.1f}s of audio")
        self._set_status("Processing...", "\u2699\ufe0f")

        threading.Thread(
            target=self._process_audio, args=(audio_path, duration), daemon=True
        ).start()

    def _process_audio(self, audio_path, record_duration):
        self._processing = True
        t_start = time.time()
        try:
            # Step 1: Transcribe
            self._set_status("Transcribing...", "\u2699\ufe0f")
            t0 = time.time()
            raw_text, segments = self.transcriber.transcribe(audio_path, audio_duration=record_duration)
            t_transcribe = time.time() - t0

            if not raw_text.strip():
                self._set_status("No speech detected", "\U0001f3a4")
                return

            print(f"[DictFlow] RAW ({t_transcribe:.1f}s): {raw_text}")

            # Step 2: Local text cleanup (no LLM, instant)
            context = get_context()
            if self.cleanup_toggle.state:
                final_text = process_text(raw_text, context, segments=segments)
            else:
                final_text = raw_text

            # Step 3: Inject at cursor
            inject_text(final_text)

            # Step 4: Save to history
            total_time = time.time() - t_start
            add_entry(raw_text, final_text, context, self.transcriber.language, record_duration)
            print(f"[DictFlow] Done in {total_time:.1f}s")

            self._set_status("Ready", "\U0001f3a4")

        except Exception as e:
            print(f"[DictFlow] Error: {e}")
            play_error()
            self._set_status("Error", "\u26a0\ufe0f")
        finally:
            self._processing = False
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    def _set_status(self, message, icon=None):
        if icon:
            self.title = icon
        self.status_item.title = f"Status: {message}"

    def _toggle_cleanup(self, sender):
        sender.state = not sender.state

    def _set_lang(self, lang, item):
        self.lang_es.state = False
        self.lang_en.state = False
        self.lang_auto.state = False
        item.state = True
        self.transcriber.language = lang

    def _set_lang_es(self, sender):
        self._set_lang("es", sender)

    def _set_lang_en(self, sender):
        self._set_lang("en", sender)

    def _set_lang_auto(self, sender):
        self._set_lang(None, sender)

    def _show_history(self, _):
        entries = get_recent(10)
        if not entries:
            rumps.alert("Historial", "No hay transcripciones aún.")
            return
        lines = []
        for e in reversed(entries):
            ts = e["timestamp"][11:19]
            lines.append(f"[{ts}] ({e['language']}, {e['duration_s']}s) {e['processed']}")
        rumps.alert("Últimas 10 transcripciones", "\n\n".join(lines))

    def _clear_history(self, _):
        from history import clear
        clear()
        rumps.alert("Historial", "Historial limpiado.")

    def _quit(self, _):
        self.listener.stop()
        rumps.quit_application()

    def run(self, **kwargs):
        self.listener.start()
        print("[DictFlow] Starting...")
        super().run(**kwargs)


LOCK_FILE = "/tmp/dictflow.lock"


def acquire_lock():
    """Ensure only one instance of DictFlow runs at a time."""
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("[DictFlow] Already running. Exiting duplicate instance.")
        sys.exit(0)
    lock_fd.write(str(os.getpid()))
    lock_fd.flush()
    return lock_fd  # must keep reference alive


if __name__ == "__main__":
    _lock = acquire_lock()
    app = DictFlowApp()
    app.run()
