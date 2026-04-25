import wave
import threading
import pyaudio
from config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE, AUDIO_FORMAT_WIDTH, TEMP_AUDIO_PATH

# Larger buffer = less overhead during recording
OPTIMIZED_CHUNK = 4096


def _find_builtin_mic(audio):
    """Find the built-in microphone device index. Bluetooth mics don't work well with Whisper."""
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0 and "MacBook" in info["name"]:
            print(f"[DictFlow] Usando micrófono: {info['name']} (index {i})")
            return i
    return None  # fallback to default


class AudioRecorder:
    def __init__(self):
        self._recording = False
        self._frames = []
        self._thread = None
        # Keep PyAudio alive for the lifetime of the app
        self._audio = pyaudio.PyAudio()
        self._stream = None
        self._device_index = _find_builtin_mic(self._audio)

    def start(self):
        if self._recording:
            return
        self._recording = True
        self._frames = []
        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._recording:
            return None
        self._recording = False
        if self._thread:
            self._thread.join(timeout=2)

        if not self._frames:
            return None

        with wave.open(TEMP_AUDIO_PATH, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(AUDIO_FORMAT_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(self._frames))

        return TEMP_AUDIO_PATH

    def _record(self):
        try:
            open_params = dict(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=OPTIMIZED_CHUNK,
            )
            if self._device_index is not None:
                open_params["input_device_index"] = self._device_index
            self._stream = self._audio.open(**open_params)

            while self._recording:
                data = self._stream.read(OPTIMIZED_CHUNK, exception_on_overflow=False)
                self._frames.append(data)

        except Exception as e:
            print(f"[DictFlow] Recording error: {e}")
        finally:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None

    @property
    def is_recording(self):
        return self._recording
