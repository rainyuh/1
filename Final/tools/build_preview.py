#!/usr/bin/env python3
"""Build the 75 s linear preview mix from the final assets."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy import signal

SR = 48_000
DUR = 75.0
ROOT = Path(__file__).resolve().parents[1]
AMB = ROOT / "audio" / "ambience"
SFX = ROOT / "audio" / "one-shots"
OUT = ROOT / "preview" / "rain_scene_demo.mp3"
TMP = ROOT / ".tmp_build"
TMP.mkdir(parents=True, exist_ok=True)


def load(path: Path) -> np.ndarray:
    sr, x = wavfile.read(path)
    if sr != SR:
        raise RuntimeError(f"{path}: expected {SR}, got {sr}")
    if x.dtype == np.int32:
        x = x.astype(np.float64) / 2147483648.0
    elif x.dtype == np.int16:
        x = x.astype(np.float64) / 32768.0
    else:
        x = x.astype(np.float64)
    if x.ndim == 1:
        x = np.column_stack([x, x])
    return x


def lowpass(x: np.ndarray, fc: float, sr: int = SR, order: int = 4) -> np.ndarray:
    sos = signal.butter(order, fc, btype="lowpass", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, x, axis=0)


def tile_to(x: np.ndarray, n: int) -> np.ndarray:
    reps = int(np.ceil(n / len(x)))
    return np.tile(x, (reps, 1))[:n]


def pan(x: np.ndarray, p: float) -> np.ndarray:
    theta = (p + 1.0) * np.pi / 4.0
    l = x[:, 0] * np.cos(theta) * np.sqrt(2.0)
    r = x[:, 1] * np.sin(theta) * np.sqrt(2.0)
    return np.column_stack([l, r])


total = int(DUR * SR)
mix = np.zeros((total, 2), dtype=np.float64)

# Beds: shelter at 0 dB, street already sits ~6 dB lower.
for name in ("AMB_Rain_Shelter_Loop_40s.wav", "AMB_Rain_Street_Loop_40s.wav"):
    bed = tile_to(load(AMB / name), total)
    mix += bed

# Events: (file, start s, gain dB, pan -1..1)
events = [
    ("SFX_StoreDoor_Chime_01.wav", 7.0, -10.0, +0.7),
    ("SFX_CarPass_Wet_01.wav", 13.0, +2.0, -0.7),
    ("SFX_EBike_Horn_01.wav", 23.0, -2.0, +0.35),
    ("SFX_CarPass_Wet_02.wav", 29.0, +2.0, +0.6),
    ("SFX_Bus_AirBrake_Door_01.wav", 37.0, +4.0, 0.0),
    ("SFX_CarPass_Wet_03.wav", 45.0, +2.0, -0.8),
    ("SFX_StoreDoor_Chime_01.wav", 51.0, -12.0, +0.7),
    ("SFX_CarPass_Wet_01.wav", 58.0, +1.0, +0.7),
    ("SFX_CarPass_Wet_02.wav", 66.0, +1.0, -0.6),
    ("SFX_EBike_Horn_01.wav", 72.0, -3.0, +0.45),
]

for name, start_s, gain_db, p in events:
    x = load(SFX / name)
    if "StoreDoor_Chime" in name:
        x = lowpass(x, 4_000.0)
    x = x * (10.0 ** (gain_db / 20.0))
    x = pan(x, p)
    i = int(round(start_s * SR))
    j = min(total, i + len(x))
    mix[i:j] += x[: j - i]

# Master fades and peak normalisation.
fade_in = int(2.0 * SR)
fade_out = int(2.5 * SR)
mix[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None]
mix[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None]
peak = float(np.max(np.abs(mix)))
mix *= 10.0 ** ((-1.5 - 20.0 * np.log10(peak + 1e-12)) / 20.0)

tmp_wav = TMP / "rain_scene_demo_f32.wav"
wavfile.write(tmp_wav, SR, mix.astype(np.float32))
subprocess.run(
    ["ffmpeg", "-v", "error", "-y", "-i", str(tmp_wav),
     "-c:a", "libmp3lame", "-b:a", "192k", str(OUT)],
    check=True,
)
print(f"wrote {OUT} ({DUR:.0f}s, peak -1.5 dBFS)")
