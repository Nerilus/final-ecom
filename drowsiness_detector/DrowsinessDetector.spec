# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all necessary binaries, datas and hiddenimports for cv2
cv2_bins = []
cv2_datas = []
cv2_hiddenimports = []
for x in collect_all('cv2'):
    cv2_bins.extend(x[0])
    cv2_datas.extend(x[1])
    cv2_hiddenimports.extend(x[2])

# Collect all necessary binaries, datas and hiddenimports for mediapipe
mediapipe_bins = []
mediapipe_datas = []
mediapipe_hiddenimports = []
for x in collect_all('mediapipe'):
    mediapipe_bins.extend(x[0])
    mediapipe_datas.extend(x[1])
    mediapipe_hiddenimports.extend(x[2])

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=cv2_bins + mediapipe_bins,
    datas=[('data/alarm.wav', 'data')] + cv2_datas + mediapipe_datas,
    hiddenimports=['cv2', 'mediapipe', 'mediapipe.python', 'mediapipe.python.solutions',
                   'mediapipe.python.solutions.face_mesh', 'mediapipe.python.solutions.hands',
                   'mediapipe.python.solutions.drawing_utils', 'pygame'] + cv2_hiddenimports + mediapipe_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DrowsinessDetector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 