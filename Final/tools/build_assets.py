#!/usr/bin/env python3
"""Build the final rainy-bus-stop assets from the sourced recordings.

Outputs (48 kHz / 24-bit / stereo WAV):
  audio/ambience/AMB_Rain_Shelter_Loop_40s.wav
  audio/ambience/AMB_Rain_Street_Loop_40s.wav
  audio/one-shots/SFX_CarPass_Wet_01.wav  (full pass)
  audio/one-shots/SFX_CarPass_Wet_02.wav  (distant, low-passed)
  audio/one-shots/SFX_CarPass_Wet_03.wav  (close, fast pass)
  audio/one-shots/SFX_StoreDoor_Chime_01.wav
  audio/one-shots/SFX_EBike_Horn_01.wav
  audio/one-shots/SFX_Bus_AirBrake_Door_01.wav

The source files live outside the repo in ../finalwork sound/ and are only
read; nothing is written there.  Processing is original: trim, fades,
equal-power crossfades, a circular loop crossfade for the beds, EQ on the
distant car variant, and loudness/peak normalisation.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.signal import fftconvolve

SR = 48_000
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "finalwork sound"
TMP = ROOT / ".tmp_build"
AMB = ROOT / "audio" / "ambience"
SFX = ROOT / "audio" / "one-shots"
DOCS = ROOT / "docs"

for _d in (TMP, AMB, SFX, DOCS):
    _d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# basic helpers
# --------------------------------------------------------------------------
def db(x: np.ndarray) -> float:
    return float(20.0 * np.log10(max(float(np.max(np.abs(x))), 1e-12)))


def rms_db(x: np.ndarray) -> float:
    return float(20.0 * np.log10(max(float(np.sqrt(np.mean(x * x))), 1e-12)))


def apply_gain(x: np.ndarray, gain_db: float) -> np.ndarray:
    return x * np.float32(10.0 ** (gain_db / 20.0))


def norm_rms(x: np.ndarray, target_db: float, peak_limit_db: float) -> tuple[np.ndarray, float]:
    """Gain to target RMS, but never let the peak exceed the limit."""
    gain = target_db - rms_db(x)
    gain = min(gain, peak_limit_db - db(x))
    return apply_gain(x, gain), float(gain)


def norm_peak(x: np.ndarray, target_db: float) -> tuple[np.ndarray, float]:
    gain = target_db - db(x)
    return apply_gain(x, gain), float(gain)


def fade_io(x: np.ndarray, fade_in_s: float, fade_out_s: float) -> np.ndarray:
    y = x.copy()
    n = len(y)
    fi = min(int(round(fade_in_s * SR)), n // 2)
    fo = min(int(round(fade_out_s * SR)), n // 2)
    if fi > 0:
        y[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)[:, None]
    if fo > 0:
        y[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)[:, None]
    return y


def lowpass(x: np.ndarray, cutoff: float, order: int = 4) -> np.ndarray:
    sos = signal.butter(order, cutoff, btype="lowpass", fs=SR, output="sos")
    return signal.sosfiltfilt(sos, x, axis=0).astype(np.float32)


def highpass(x: np.ndarray, cutoff: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, cutoff, btype="highpass", fs=SR, output="sos")
    return signal.sosfiltfilt(sos, x, axis=0).astype(np.float32)


def make_ir(rt60: float = 0.55, predelay: float = 0.012, seed: int = 1001) -> np.ndarray:
    """Small-room impulse response: decaying noise with a short pre-delay."""
    rng = np.random.default_rng(seed)
    n = int(round(rt60 * SR))
    t = np.arange(n, dtype=np.float32) / SR
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-6.9 * t / rt60)
    pre = min(int(round(predelay * SR)), n - 1)
    ir[:pre] = 0.0
    ir /= np.sqrt(np.sum(ir * ir)) + 1e-12
    return ir


def add_reverb(x: np.ndarray, wet: float = 0.08, rt60: float = 0.55,
               predelay: float = 0.012, seed: int = 1001) -> np.ndarray:
    """Short convolution reverb, truncated to the dry length."""
    ir = make_ir(rt60=rt60, predelay=predelay, seed=seed)
    out = np.empty_like(x)
    for ch in range(x.shape[1]):
        wet_sig = fftconvolve(x[:, ch], ir)[: len(x)]
        out[:, ch] = (1.0 - wet) * x[:, ch] + wet * wet_sig.astype(np.float32)
    return out.astype(np.float32)


def xfade(a: np.ndarray, b: np.ndarray, n: int) -> np.ndarray:
    """Equal-power crossfade: n samples from a into b."""
    if n <= 0:
        return b
    t = np.linspace(0.0, 1.0, n, dtype=np.float32)[:, None]
    return (a * np.cos(0.5 * np.pi * t) + b * np.sin(0.5 * np.pi * t)).astype(np.float32)


def tile_to(x: np.ndarray, total: int, fade: int, alternate_reverse: bool = False) -> np.ndarray:
    """Repeat x until total samples, crossfading each join.

    With alternate_reverse the copies alternate forward/reversed, which keeps
    a stochastic bed from repeating the same 26 s pattern.
    """
    out = x.copy()
    reverse = bool(alternate_reverse)
    guard = 0
    while len(out) < total:
        seg = x[::-1] if reverse else x
        f = min(fade, len(seg), len(out))
        out = np.concatenate([out[:-f], xfade(out[-f:], seg[:f], f), seg[f:]])
        if alternate_reverse:
            reverse = not reverse
        guard += 1
        if guard > 10_000:
            raise RuntimeError("tile_to did not converge")
    return out[:total].astype(np.float32)


def circular_loop(x: np.ndarray, loop_len: int, fade: int) -> np.ndarray:
    """Fold x[loop_len:loop_len+fade] back into x[:fade] for a seamless loop."""
    if len(x) < loop_len + fade:
        raise ValueError("source shorter than loop + fade")
    y = x[:loop_len].copy()
    tail = x[loop_len:loop_len + fade]
    t = np.linspace(0.0, 1.0, fade, dtype=np.float32)[:, None]
    y[:fade] = tail * np.cos(0.5 * np.pi * t) + y[:fade] * np.sin(0.5 * np.pi * t)
    return y


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------
def decode(path: Path, tag: str) -> np.ndarray:
    """Decode anything ffmpeg can read to 48 kHz stereo float32."""
    out = TMP / f"dec_{tag}.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(path),
         "-ar", str(SR), "-ac", "2", "-c:a", "pcm_f32le", str(out)],
        check=True,
    )
    sr, x = wavfile.read(out)
    if sr != SR:
        raise RuntimeError(f"unexpected sample rate {sr}")
    if x.ndim == 1:
        x = np.column_stack([x, x])
    return x.astype(np.float32)


def trim(x: np.ndarray, start_s: float, end_s: float) -> np.ndarray:
    return x[int(round(start_s * SR)):int(round(end_s * SR))]


def write_wav24(y: np.ndarray, path: Path) -> None:
    tmp = TMP / f"{path.stem}_f32.wav"
    wavfile.write(tmp, SR, np.clip(y, -1.0, 1.0).astype(np.float32))
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-c:a", "pcm_s24le", str(path)],
        check=True,
    )


def measure_lufs(path: Path) -> float | None:
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    hits = re.findall(r"I:\s+(-?\d+(?:\.\d+)?)\s+LUFS", p.stderr)
    return float(hits[-1]) if hits else None


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
manifest: list[dict] = []


def add_asset(path: Path, kind: str, description: str, source: str,
              edits: str, audio: np.ndarray) -> None:
    rel = path.relative_to(ROOT).as_posix()
    manifest.append({
        "file": rel,
        "kind": kind,
        "duration_s": round(len(audio) / SR, 3),
        "sample_rate": SR,
        "channels": int(audio.shape[1]),
        "bit_depth": 24,
        "peak_dbfs": round(db(audio), 2),
        "rms_dbfs": round(rms_db(audio), 2),
        "lufs": measure_lufs(path),
        "source": source,
        "description": description,
        "edits": edits,
    })
    print(f"  wrote {rel:60s} peak {db(audio):6.1f}  rms {rms_db(audio):6.1f}")


print("Bases")
rain1 = decode(SRC / "雨天基底1.wav", "rain1")
rainstreet = decode(SRC / "雨天车流声.wav", "rainstreet")

# Shelter bed: close rain, trim the loud tail, alternate forward/reverse tiles.
shelter_src = trim(rain1, 0.5, 27.0)
shelter_long = tile_to(shelter_src, int(42.0 * SR), int(2.0 * SR), alternate_reverse=True)
shelter = circular_loop(shelter_long, int(40.0 * SR), int(2.0 * SR))
shelter, g = norm_rms(shelter, -23.3, -3.0)
write_wav24(shelter, AMB / "AMB_Rain_Shelter_Loop_40s.wav")
add_asset(
    AMB / "AMB_Rain_Shelter_Loop_40s.wav", "ambience",
    "Steady rain on the bus-shelter roof, close perspective; seamless 40 s bed.",
    "爱给网 / 耳聆网 / BBC（逐条待确认）",
    f"trim 0.5-27.0 s; forward/reverse tiles with 2 s crossfades; 40 s circular loop; gain {g:+.1f} dB",
    shelter,
)

# Street bed: rain on asphalt + distant traffic, 6 dB under the shelter bed.
street_src = trim(rainstreet, 0.0, 31.74)
street_src = highpass(street_src, 20.0)
street_long = tile_to(street_src, int(42.0 * SR), int(4.0 * SR), alternate_reverse=False)
street = circular_loop(street_long, int(40.0 * SR), int(2.0 * SR))
street, g = norm_rms(street, -28.7, -3.0)
write_wav24(street, AMB / "AMB_Rain_Street_Loop_40s.wav")
add_asset(
    AMB / "AMB_Rain_Street_Loop_40s.wav", "ambience",
    "Rain on wet asphalt with distant traffic; far/wide bed, 6 dB below the shelter bed.",
    "爱给网 / 耳聆网 / BBC（逐条待确认）",
    f"trim 0.0-31.74 s; 4 s crossfade tiles; 40 s circular loop; 20 Hz HPF; gain {g:+.1f} dB",
    street,
)

print("One-shots")
car = decode(SRC / "车过积水.wav", "car")

# 01: full pass
car_full = trim(car, 5.0, 13.0)
car_full = fade_io(car_full, 0.05, 0.50)
car_full, g = norm_rms(car_full, -19.5, -1.5)
write_wav24(car_full, SFX / "SFX_CarPass_Wet_01.wav")
add_asset(
    SFX / "SFX_CarPass_Wet_01.wav", "one-shot",
    "Single car approaching, passing and receding on wet asphalt; water spray.",
    "爱给网（待确认）",
    f"trim 5.0-13.0 s; 50 ms in / 500 ms out; gain {g:+.1f} dB",
    car_full,
)

# 02: distant variant, low-passed, same RMS so the Random Container is level-stable
car_dist = trim(car, 5.0, 13.0)
car_dist = lowpass(car_dist, 2500.0)
car_dist = fade_io(car_dist, 0.05, 0.50)
car_dist, g = norm_rms(car_dist, -19.5, -1.5)
write_wav24(car_dist, SFX / "SFX_CarPass_Wet_02.wav")
add_asset(
    SFX / "SFX_CarPass_Wet_02.wav", "one-shot",
    "Distant, low-passed car pass derived from the same recording.",
    "爱给网（待确认）",
    f"trim 5.0-13.0 s; 2.5 kHz low-pass; 50 ms in / 500 ms out; gain {g:+.1f} dB",
    car_dist,
)

# 03: close, fast pass around the peak
car_close = trim(car, 7.5, 11.5)
car_close = fade_io(car_close, 0.03, 0.20)
car_close, g = norm_rms(car_close, -19.5, -1.5)
write_wav24(car_close, SFX / "SFX_CarPass_Wet_03.wav")
add_asset(
    SFX / "SFX_CarPass_Wet_03.wav", "one-shot",
    "Close, fast car pass with heavy water spray; the peak section of the same recording.",
    "爱给网（待确认）",
    f"trim 7.5-11.5 s; 30 ms in / 200 ms out; gain {g:+.1f} dB",
    car_close,
)

# Convenience-store door chime
chime = decode(SRC / "便利店门铃音效.wav", "chime")
chime = trim(chime, 0.05, 1.72)
chime = add_reverb(chime, wet=0.28, rt60=0.85, predelay=0.022, seed=3001)
chime = lowpass(chime, 5_500.0)
chime = fade_io(chime, 0.035, 0.22)
chime, g = norm_peak(chime, -8.0)
write_wav24(chime, SFX / "SFX_StoreDoor_Chime_01.wav")
add_asset(
    SFX / "SFX_StoreDoor_Chime_01.wav", "one-shot",
    "Convenience-store door chime heard from the bus stop, behind the e-bike: distant, low-passed, sitting inside the store ambience.",
    "耳聆网 / 爱给网（待确认）",
    f"trim 0.05-1.72 s; 28% room reverb (0.85 s); 5.5 kHz LPF; 35 ms in / 220 ms out; peak-normalised to -8 dBFS ({g:+.1f} dB); place behind the listener in Wwise",
    chime,
)

# E-bike horn
horn = decode(SRC / "电动车 喇叭_.mp3", "horn")
horn = trim(horn, 0.0, 0.65)
horn = fade_io(horn, 0.005, 0.08)
horn, g = norm_peak(horn, -3.0)
write_wav24(horn, SFX / "SFX_EBike_Horn_01.wav")
add_asset(
    SFX / "SFX_EBike_Horn_01.wav", "one-shot",
    "E-bike horn, two short beeps.",
    "耳聆网 / 爱给网（待确认）",
    f"trim 0.0-0.65 s; 5 ms in / 80 ms out; peak-normalised to -3 dBFS ({g:+.1f} dB)",
    horn,
)

# Bus air brake + door
bus = decode(SRC / "公交车进站停车开门关门开车.wav", "bus")
bus = trim(bus, 8.0, 12.8)
bus = fade_io(bus, 0.03, 0.30)
bus, g = norm_peak(bus, -1.5)
write_wav24(bus, SFX / "SFX_Bus_AirBrake_Door_01.wav")
add_asset(
    SFX / "SFX_Bus_AirBrake_Door_01.wav", "one-shot",
    "Bus air-brake release and door opening at the stop.",
    "耳聆网 / 爱给网（待确认）",
    f"trim 8.0-12.8 s; 30 ms in / 300 ms out; peak-normalised to -1.5 dBFS ({g:+.1f} dB)",
    bus,
)

# --------------------------------------------------------------------------
# metadata
# --------------------------------------------------------------------------
(DOCS / "asset-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

rows = []
for item in manifest:
    rows.append({
        "file": item["file"],
        "source_site": item["source"],
        "author": "待确认",
        "url": "",
        "license": "待确认",
        "edits": item["edits"],
    })

with (DOCS / "sources.csv").open("w", encoding="utf-8", newline="") as fh:
    import csv
    writer = csv.DictWriter(fh, fieldnames=["file", "source_site", "author", "url", "license", "edits"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done: {len(manifest)} assets, manifest and sources.csv updated.")
