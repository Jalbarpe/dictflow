import subprocess
import threading


def _play(name):
    """Play a macOS system sound by name (works from any thread)."""
    path = f"/System/Library/Sounds/{name}.aiff"
    threading.Thread(
        target=lambda: subprocess.run(
            ["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ),
        daemon=True,
    ).start()


def play_start():
    """Sound when recording starts."""
    _play("Pop")


def play_stop():
    """Sound when recording stops."""
    _play("Tink")


def play_error():
    """Sound on error."""
    _play("Basso")
