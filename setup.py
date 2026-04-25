#!/usr/bin/env python3
"""Setup script for building DictFlow.app with py2app."""

from setuptools import setup

APP = ['main.py']

OPTIONS = {
    'py2app': {
        'argv_emulation': False,
        'semi_standalone': True,  # Use system Python + venv packages
        'iconfile': 'icon.icns',
        'plist': {
            'CFBundleName': 'DictFlow',
            'CFBundleDisplayName': 'DictFlow',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleIdentifier': 'com.dictflow.app',
            'NSHighResolutionCapable': True,
            'LSUIElement': True,
            'LSMinimumSystemVersion': '12.0',
            'NSMicrophoneUsageDescription': 'DictFlow needs microphone access to transcribe your voice.',
        },
        'includes': [
            'recorder', 'transcriber', 'processor', 'hotkey',
            'injector', 'context', 'sounds', 'history', 'config',
        ],
        'packages': [
            'rumps', 'mlx', 'mlx_whisper', 'mlx.nn',
            'numpy', 'huggingface_hub', 'tqdm', 'tiktoken',
        ],
        'excludes': [
            'matplotlib', 'scipy', 'pandas', 'sklearn',
            'tensorflow', 'torch', 'PIL', 'cv2',
            'whisper', 'openai_whisper',
        ],
    }
}

setup(
    name='DictFlow',
    version='1.0.0',
    description='Local voice dictation for macOS',
    app=APP,
    options=OPTIONS,
    setup_requires=['py2app'],
)
