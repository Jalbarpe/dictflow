import os

# Whisper settings
WHISPER_LANGUAGE = None  # "es", "en", or None for auto-detect

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
AUDIO_FORMAT_WIDTH = 2  # 16-bit

# Hotkey
GLOBE_KEY_CODE = 63  # Fn/Globe key on Mac keyboards

# Temp files
TEMP_AUDIO_PATH = "/tmp/dictflow_recording.wav"

# Personal dictionary file
PERSONAL_DICT_PATH = os.path.expanduser("~/.config/dictflow/dictionary.txt")

# App context mapping: bundle_id prefix → context type
APP_CONTEXTS = {
    "com.microsoft.VSCode": "code",
    "com.todesktop.": "code",  # Cursor
    "dev.zed.": "code",
    "com.apple.Terminal": "code",
    "com.googlecode.iterm2": "code",
    "net.kovidgoyal.kitty": "code",
    "com.tinyspeck.slackmacgap": "chat",
    "com.apple.MobileSMS": "chat",
    "ru.keepcoder.Telegram": "chat",
    "net.whatsapp.WhatsApp": "chat",
    "com.hnc.Discord": "chat",
    "com.apple.mail": "chat",
    "com.google.Chrome": "general",
    "com.apple.Safari": "general",
}
