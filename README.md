# DictFlow

Local push-to-talk dictation for macOS. Hold the Globe key, speak, release — the transcription is injected at the cursor in any app. No cloud, no API keys, no LLM in the loop.

Built around `mlx-whisper` (large-v3-turbo) running on the Apple Silicon GPU, with a heuristic post-processor that recovers punctuation from word-level pause timings and cleans up Spanish/English fillers.

## Why it's interesting

- **Punctuation inferred from silences, not guessed.** Whisper returns per-word timestamps. Pauses ≥ 700 ms become periods, ≥ 300 ms become commas. Stream-of-consciousness Spanish dictation comes out properly punctuated without an LLM.
- **Fully local.** No audio or text leaves the machine. Recordings are deleted after each transcription; only your own history file (`~/.config/dictflow/history.json`) persists.
- **Fast.** `large-v3-turbo` on MLX is meaningfully quicker than PyTorch on Apple Silicon. End-to-end latency from key release to text at the cursor is typically under a second for short utterances.

## Requirements

- macOS on Apple Silicon (M1 or newer)
- Python 3.10+
- `ffmpeg` (`brew install ffmpeg`)
- ~1.5 GB free disk for the Whisper model (downloaded on first run)
- Microphone + Accessibility permissions (macOS will prompt the first time)

## Install & run

```bash
git clone https://github.com/Jalbarpe/dictflow
cd dictflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./run.sh
```

The first launch downloads the model weights from Hugging Face. After that everything stays local.

## Use

- **Hold the Globe key (Fn)** to record, release to transcribe and inject.
- The **menu bar icon** lets you toggle filler-word cleanup, switch language (ES / EN / auto-detect), and view the last 10 transcriptions.
- **Custom vocabulary**: drop a text file at `~/.config/dictflow/prompt_es.txt` (or `prompt_en.txt`) with the proper nouns and brands you say often. Whisper will bias toward them.

## Architecture

```
recorder.py    captures mic audio while the hotkey is held
transcriber.py mlx-whisper, returns text + word timestamps
processor.py   punctuation from pauses, filler removal,
               list formatting, capitalization
injector.py    simulates a paste at the current cursor
main.py        rumps menubar app + glue
```

The post-processing pipeline is intentionally LLM-free: every step is deterministic regex / heuristic logic, so latency stays low and behavior is predictable.

## Build standalone .app

```bash
./build.sh
```

Produces `dist/DictFlow.app` via PyInstaller. The bundle is large (~900 MB) because it includes the Whisper weights.
