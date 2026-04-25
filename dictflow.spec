# -*- mode: python ; coding: utf-8 -*-
import os
import site

# Find mlx native libraries
sp = site.getsitepackages()[0] if site.getsitepackages() else ''
venv_sp = os.path.join(os.path.dirname(SPECPATH), 'venv', 'lib', 'python3.14', 'site-packages')
if os.path.exists(venv_sp):
    sp = venv_sp

mlx_path = os.path.join(sp, 'mlx')
mlx_whisper_path = os.path.join(sp, 'mlx_whisper')

# Collect mlx native libs
mlx_binaries = []
for root, dirs, files in os.walk(mlx_path):
    for f in files:
        if f.endswith(('.dylib', '.so', '.metallib')):
            src = os.path.join(root, f)
            dst = os.path.relpath(root, sp)
            mlx_binaries.append((src, dst))

a = Analysis(
    ['main.py'],
    pathex=[SPECPATH],
    binaries=mlx_binaries,
    datas=[
        (mlx_whisper_path, 'mlx_whisper'),
        (os.path.join(sp, 'tiktoken_ext'), 'tiktoken_ext'),
    ],
    hiddenimports=[
        'rumps', 'pyaudio', 'numpy',
        'mlx', 'mlx.core', 'mlx.nn', 'mlx.nn.layers',
        'mlx._reprlib_fix',
        'mlx_whisper', 'mlx_whisper.audio', 'mlx_whisper.load_models',
        'mlx_whisper.tokenizer', 'mlx_whisper.decoding',
        'mlx_whisper.transcribe', 'mlx_whisper.whisper',
        'mlx_whisper.torch_whisper', 'mlx_whisper.timing',
        'mlx_whisper.writers', 'mlx_whisper._version',
        'tiktoken', 'tiktoken_ext', 'tiktoken_ext.openai_public',
        'huggingface_hub', 'huggingface_hub.file_download',
        'tqdm', 'tiktoken', 'regex',
        'AppKit', 'Quartz', 'Foundation', 'objc',
        'recorder', 'transcriber', 'processor', 'hotkey',
        'injector', 'context', 'sounds', 'history', 'config',
    ],
    excludes=[
        'matplotlib', 'pandas', 'sklearn',
        'tensorflow', 'torch', 'PIL', 'cv2',
        'whisper', 'openai_whisper',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DictFlow',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    target_arch='arm64',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='DictFlow',
)

app = BUNDLE(
    coll,
    name='DictFlow.app',
    icon='icon.icns',
    bundle_identifier='com.dictflow.app',
    info_plist={
        'CFBundleName': 'DictFlow',
        'CFBundleDisplayName': 'DictFlow',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': True,
        'LSMinimumSystemVersion': '12.0',
        'NSMicrophoneUsageDescription': 'DictFlow needs microphone access to transcribe your voice.',
    },
)
