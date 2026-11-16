import math
import random
import wave
import struct
from pathlib import Path

# CATHEDRALOS v6.1 — AUDIO FOUNDRY
# Pure Python prototype; no external dependencies.

SAMPLE_RATE = 44100
BPM = 94
BARS = 4
TUNING = 432.0
BASS_HZ = 420.0
DELAY_MS = 159
FEEDBACK = 0.38
SEED = 369

BAR_SECONDS = 240.0 / BPM
DURATION = BAR_SECONDS * BARS
TOTAL = round(DURATION * SAMPLE_RATE)

rng = random.Random(SEED)
audio = [0.0] * TOTAL


def midi_freq(note):
    return TUNING * (2.0 ** ((note - 69) / 12.0))


def add_tone(freq, start, duration, volume, release=0.2):
    first = max(0, round(start * SAMPLE_RATE))
    last = min(TOTAL, round((start + duration) * SAMPLE_RATE))
    attack = 0.025

    for i in range(first, last):
        t = (i - first) / SAMPLE_RATE
        remaining = (last - i) / SAMPLE_RATE
        envelope = min(1.0, t / attack, remaining / release)
        audio[i] += volume * envelope * math.sin(
            2.0 * math.pi * freq * t
        )


def add_drum(start, kind):
    length = 0.13 if kind == "hat" else 0.22
    first = round(start * SAMPLE_RATE)
    count = min(round(length * SAMPLE_RATE), TOTAL - first)

    phase = 0.0

    for j in range(count):
        t = j / SAMPLE_RATE
        envelope = math.exp(-t * (48 if kind == "hat" else 18))

        if kind == "hat":
            sample = rng.uniform(-1.0, 1.0)
            volume = 0.075
        elif kind == "snare":
            sample = rng.uniform(-1.0, 1.0)
            volume = 0.13
        else:
            phase += 2.0 * math.pi * (100 - 65 * t / length) / SAMPLE_RATE
            sample = math.sin(phase)
            volume = 0.23

        audio[first + j] += sample * envelope * volume


# Four-bar jazz progression: Dm9 -> G13 -> Cmaj9.
chords = [
    [50, 53, 57, 60, 64],
    [50, 53, 57, 60, 64],
    [43, 47, 50, 53, 57, 64],
    [48, 52, 55, 59, 62],
]

# Independent harmonic voices.
for bar, chord in enumerate(chords):
    start = bar * BAR_SECONDS

    for note in chord:
        add_tone(midi_freq(note), start, BAR_SECONDS, 0.035)

# Independent 420 Hz bass pulse.
for beat in range(BARS * 4):
    start = beat * 60.0 / BPM
    add_tone(BASS_HZ, start, 0.16, 0.12, release=0.12)

# Three nested rhythmic grids: 3, 6 and 9 hits per bar.
for bar in range(BARS):
    base = bar * BAR_SECONDS

    for hit in range(3):
        add_drum(base + hit * BAR_SECONDS / 3, "kick")

    for hit in range(6):
        add_drum(base + hit * BAR_SECONDS / 6, "snare")

    for hit in range(9):
        add_drum(base + hit * BAR_SECONDS / 9, "hat")

# Feedback echo: 159 ms, 38%.
delay = round(DELAY_MS * SAMPLE_RATE / 1000)

for i in range(delay, TOTAL):
    audio[i] += FEEDBACK * audio[i - delay]

# Normalize with headroom.
peak = max(abs(x) for x in audio)
if peak:
    scale = 0.90 / peak
    audio = [x * scale for x in audio]

# Export signed 16-bit mono PCM.
output = Path(__file__).parent / "cathedralos_v6_1_demo.wav"

with wave.open(str(output), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)

    frames = bytearray()
    for sample in audio:
        value = max(-32768, min(32767, round(sample * 32767)))
        frames.extend(struct.pack("<h", value))

    wav.writeframes(frames)

# Verify the actual artifact.
with wave.open(str(output), "rb") as wav:
    assert wav.getnchannels() == 1
    assert wav.getframerate() == SAMPLE_RATE
    assert wav.getnframes() == TOTAL

print("=== CATHEDRALOS AUDIO FOUNDRY ===")
print(f"[OK] Tempo: {BPM} BPM")
print(f"[OK] Tuning: A4 = {TUNING} Hz")
print(f"[OK] Independent bass: {BASS_HZ} Hz")
print("[OK] Rhythm: 3 / 6 / 9")
print(f"[OK] Echo: {DELAY_MS} ms")
print(f"[OK] Feedback: {FEEDBACK}")
print(f"[OK] Seed: {SEED}")
print(f"[OK] Duration: {DURATION:.3f} seconds")
print(f"[OK] Samples: {TOTAL}")
print(f"[OK] Peak before normalization: {peak:.4f}")
print(f"[SUCCESS] WAV created: {output}")
