#!/usr/bin/env python3
"""CathedralOS Audio Foundry v6.2 — Ensemble Prototype.

Automation recommends. Human decides. Reality has the final vote.

Standard library only. Offline mono PCM WAV renderer.
"""

import math
import random
import struct
import wave
from pathlib import Path

# ------------------------------------------------------------
# RELEASE SETTINGS
# ------------------------------------------------------------

SAMPLE_RATE = 44100
TEMPO = 94
BEAT_SEC = 60.0 / TEMPO
BAR_SEC = BEAT_SEC * 4
TUNING_A4 = 432.0
SEED = 369

DELAY_MS = 159
DELAY_FEEDBACK = 0.38

OUTPUT = Path(__file__).resolve().parent / "cathedralos_v6_2_ensemble.wav"
rng = random.Random(SEED)

# Six bars: 2 + 0.5 + 3.5
MUSIC_SEC = BAR_SEC * 6
DELAY_SAMPLES = round(SAMPLE_RATE * DELAY_MS / 1000)
TAIL_SEC = (DELAY_MS / 1000) * 5
TOTAL_SAMPLES = round(MUSIC_SEC * SAMPLE_RATE)

# ------------------------------------------------------------
# MUSIC THEORY / HELPERS
# ------------------------------------------------------------

def midi_hz(note):
    return TUNING_A4 * (2.0 ** ((note - 69) / 12.0))


def envelope(t, duration, attack=0.015, release=0.12):
    if t < 0 or t >= duration:
        return 0.0
    a = min(1.0, t / max(attack, 0.0001))
    r = min(1.0, (duration - t) / max(release, 0.0001))
    return max(0.0, min(a, r))


def add_samples(destination, source, start=0, gain=1.0):
    end = min(len(destination), start + len(source))
    for i in range(start, end):
        destination[i] += source[i - start] * gain


def synth_tone(note, duration, voice="warm", gain=0.15):
    count = max(1, round(duration * SAMPLE_RATE))
    freq = midi_hz(note)
    output = [0.0] * count

    for i in range(count):
        t = i / SAMPLE_RATE
        env = envelope(t, duration, 0.025, 0.16)
        phase = 2.0 * math.pi * freq * t

        if voice == "warm":
            sample = (
                math.sin(phase)
                + 0.28 * math.sin(phase * 2.0)
                + 0.12 * math.sin(phase * 3.0)
            ) / 1.40
        elif voice == "pluck":
            decay = math.exp(-5.0 * t)
            sample = decay * (
                0.78 * math.sin(phase)
                + 0.22 * math.sin(phase * 2.01)
            )
        else:
            sample = math.sin(phase)

        output[i] = sample * env * gain

    return output


def synth_chord(notes, duration, gain=0.07):
    output = [0.0] * round(duration * SAMPLE_RATE)
    if not notes:
        return output

    voice_gain = gain / len(notes)
    for note in notes:
        add_samples(output, synth_tone(note, duration, "warm", voice_gain))
    return output


def add_note(destination, note, start_sec, duration, voice, gain):
    start = round(start_sec * SAMPLE_RATE)
    add_samples(destination, voice(note, duration, gain), start)


# ------------------------------------------------------------
# THE CONDUCTING CRAB — TENOR SAX
# ------------------------------------------------------------

def synth_sax(note, duration, gain=0.16):
    count = max(1, round(duration * SAMPLE_RATE))
    freq = midi_hz(note)
    output = [0.0] * count

    for i in range(count):
        t = i / SAMPLE_RATE
        vibrato = 1.0 + 0.0035 * math.sin(2 * math.pi * 5.5 * t)
        phase = 2 * math.pi * freq * vibrato * t
        breath = rng.uniform(-1.0, 1.0) * 0.012
        attack = min(1.0, t / 0.055)
        env = envelope(t, duration, 0.055, 0.14)

        harmonics = (
            math.sin(phase)
            + 0.48 * math.sin(phase * 2)
            + 0.25 * math.sin(phase * 3)
            + 0.10 * math.sin(phase * 5)
        ) / 1.83

        output[i] = (harmonics * attack + breath) * env * gain

    return output


# ------------------------------------------------------------
# THE PRECOG OWL — MUTED HARMON TRUMPET
# ------------------------------------------------------------

def synth_trumpet(note, duration, gain=0.105):
    count = max(1, round(duration * SAMPLE_RATE))
    base = midi_hz(note)
    output = [0.0] * count

    for i in range(count):
        t = i / SAMPLE_RATE
        scoop = 1.0 - 0.018 * math.exp(-t * 32.0)
        vibrato = 1.0 + 0.0018 * math.sin(2 * math.pi * 5.5 * t)
        phase = 2 * math.pi * base * scoop * vibrato * t
        env = envelope(t, duration, 0.018, 0.11)

        nasal = (
            math.sin(phase)
            + 0.34 * math.sin(phase * 2)
            + 0.38 * math.sin(phase * 3)
            + 0.18 * math.sin(phase * 4)
        ) / 1.90

        output[i] = nasal * env * gain

    return output


# ------------------------------------------------------------
# THE DUMPLING — FRACTAL FM ARPEGGIATOR
# ------------------------------------------------------------

def synth_dumpling(note, duration, gain=0.075):
    count = max(1, round(duration * SAMPLE_RATE))
    carrier = midi_hz(note)
    output = [0.0] * count

    for i in range(count):
        t = i / SAMPLE_RATE
        modulator = math.sin(2 * math.pi * 369.0 * t)
        phase = 2 * math.pi * carrier * t + 0.55 * modulator
        shimmer = 1.0 + 0.12 * math.sin(2 * math.pi * 9.0 * t)
        env = envelope(t, duration, 0.004, min(0.10, duration * 0.4))
        output[i] = math.sin(phase) * shimmer * env * gain

    return output


# ------------------------------------------------------------
# SOURDOUGH STARTER — UPRIGHT BASS
# ------------------------------------------------------------

def synth_upright(note, duration, gain=0.12):
    count = max(1, round(duration * SAMPLE_RATE))
    freq = midi_hz(note)
    output = [0.0] * count

    for i in range(count):
        t = i / SAMPLE_RATE
        # Small downward pitch movement gives the pluck a woody feel.
        phase = 2 * math.pi * freq * (t - 0.012 * (1 - math.exp(-t * 35)))
        body = (
            0.78 * math.sin(phase)
            + 0.20 * math.sin(phase * 2.0)
            + 0.08 * math.sin(phase * 3.0)
        )
        output[i] = body * math.exp(-3.8 * t) * gain

    return output


# ------------------------------------------------------------
# DEBUGGING KITTEN — 3 / 6 / 9 PERCUSSION
# ------------------------------------------------------------

def add_kick(destination, start_sec, gain=0.34):
    start = round(start_sec * SAMPLE_RATE)
    length = round(0.20 * SAMPLE_RATE)

    for i in range(length):
        t = i / SAMPLE_RATE
        freq = 90.0 - 48.0 * min(1.0, t / 0.20)
        sample = math.sin(2 * math.pi * freq * t) * math.exp(-18 * t)
        index = start + i
        if index < len(destination):
            destination[index] += sample * gain


def add_snare(destination, start_sec, gain=0.15):
    start = round(start_sec * SAMPLE_RATE)
    length = round(0.13 * SAMPLE_RATE)

    for i in range(length):
        t = i / SAMPLE_RATE
        noise = rng.uniform(-1.0, 1.0)
        tone = math.sin(2 * math.pi * 185 * t)
        sample = (noise * 0.72 + tone * 0.28) * math.exp(-24 * t)
        index = start + i
        if index < len(destination):
            destination[index] += sample * gain


def add_hat(destination, start_sec, gain=0.045):
    start = round(start_sec * SAMPLE_RATE)
    length = round(0.035 * SAMPLE_RATE)

    for i in range(length):
        t = i / SAMPLE_RATE
        noise = rng.uniform(-1.0, 1.0)
        metallic = math.sin(2 * math.pi * 3690 * t)
        sample = (noise * 0.75 + metallic * 0.25) * math.exp(-95 * t)
        index = start + i
        if index < len(destination):
            destination[index] += sample * gain


def render_drums(destination, start_bar, bars):
    for bar in range(bars):
        bar_start = (start_bar + bar) * BAR_SEC

        # Three kick anchors, six snare accents, nine hat subdivisions.
        for beat in (0, 1.5, 3):
            add_kick(destination, bar_start + beat * BEAT_SEC)

        for beat in (1, 3):
            add_snare(destination, bar_start + beat * BEAT_SEC)

        for step in range(9):
            add_hat(
                destination,
                bar_start + (step / 9.0) * BAR_SEC,
                gain=0.035 if step % 3 else 0.055,
            )


# ------------------------------------------------------------
# COSMIC PANCREAS — 159 ms SHIMMER / FEEDBACK
# ------------------------------------------------------------

def apply_pancreas_delay(audio):
    delayed = list(audio) + [0.0] * (DELAY_SAMPLES * 5)

    for i in range(DELAY_SAMPLES, len(delayed)):
        t = i / SAMPLE_RATE
        lfo = 0.5 + 0.5 * math.sin(2 * math.pi * 0.17 * t)
        feedback = DELAY_FEEDBACK * (0.92 + 0.08 * lfo)
        delayed[i] += feedback * delayed[i - DELAY_SAMPLES]

    return delayed


# ------------------------------------------------------------
# ARRANGEMENT
# ------------------------------------------------------------

def main():
    mix = [0.0] * TOTAL_SAMPLES

    # Proposed opening color: Bb minor 9.
    # The bridge pivots through F#7 into the Dm9 / G13 / Cmaj9 sequence.
    bbm9 = [46, 49, 53, 56, 60]
    fsharp7 = [42, 46, 49, 52, 56]
    dm9 = [50, 53, 57, 60, 64]
    g13 = [43, 47, 50, 53, 57, 64]
    cmaj9 = [48, 52, 55, 59, 62]

    # Chord bed: bars 0-2, bridge, then final 3.5 bars.
    chord_events = [
        (0.0, 1.0, bbm9),
        (1.0, 1.0, bbm9),
        (2.0, 0.5, fsharp7),
        (2.5, 1.0, dm9),
        (3.5, 1.0, g13),
        (4.5, 1.5, cmaj9),
    ]

    for start_bar, bars, chord in chord_events:
        start = round(start_bar * BAR_SEC * SAMPLE_RATE)
        duration = bars * BAR_SEC
        add_samples(mix, synth_chord(chord, duration, 0.085), start)

    # Sourdough Starter: walking bass line.
    bass_notes = [
        (0.0, 46), (0.5, 53), (1.0, 49), (1.5, 56),
        (2.0, 42), (2.25, 49),
        (2.5, 50), (3.0, 57), (3.5, 43), (4.0, 50),
        (4.5, 48), (5.0, 55), (5.5, 52),
    ]

    for beat_pos, note in bass_notes:
        add_note(
            mix, note, beat_pos * BEAT_SEC,
            BEAT_SEC * 0.46, synth_upright, 0.14
        )

    # Conducting Crab: tenor sax melodic phrases.
    sax_line = [
        (0.50, 70, 0.42), (1.00, 73, 0.42), (1.50, 75, 0.42),
        (2.00, 77, 0.38), (2.50, 75, 0.38), (3.00, 73, 0.42),
        (4.00, 78, 0.42), (4.50, 77, 0.42), (5.00, 74, 0.42),
        (5.50, 72, 0.42), (6.00, 74, 0.42), (6.50, 77, 0.42),
        (7.00, 75, 0.65), (8.00, 74, 0.42), (8.50, 72, 0.42),
        (9.00, 71, 0.42), (9.50, 72, 0.42), (10.00, 76, 0.42),
        (10.50, 79, 0.42), (11.00, 76, 0.42), (11.50, 74, 0.65),
        (12.50, 72, 0.42), (13.00, 74, 0.42), (13.50, 72, 0.42),
        (14.00, 67, 0.85),
    ]

    for beat_pos, note, duration_beats in sax_line:
        add_note(
            mix, note, beat_pos * BEAT_SEC,
            duration_beats * BEAT_SEC, synth_sax, 0.17
        )

    # Precog Owl: trumpet answers during the second section.
    owl_line = [
        (8.00, 69), (8.75, 72), (9.50, 74),
        (10.25, 76), (11.00, 74), (11.75, 72),
        (12.50, 71), (13.25, 67), (14.00, 72),
    ]

    for beat_pos, note in owl_line:
        add_note(
            mix, note, beat_pos * BEAT_SEC,
            BEAT_SEC * 0.48, synth_trumpet, 0.12
        )

    # Dumpling: nine-step repeating arpeggio, divided into 3/9 accents.
    arp_pattern = [74, 77, 81, 84, 81, 77, 86, 81, 77]

    for bar in range(6):
        for step, note in enumerate(arp_pattern):
            beat_pos = bar * 4 + (step / 9.0) * 4
            add_note(
                mix, note, beat_pos * BEAT_SEC,
                BEAT_SEC * 0.19, synth_dumpling, 0.085
            )

    # Independent 420 Hz pulse: short, gated accents.
    pulse = [0.0] * round(MUSIC_SEC * SAMPLE_RATE)
    pulse_length = round(0.12 * SAMPLE_RATE)

    for bar in range(6):
        for beat in (0, 2):
            start = round((bar * BAR_SEC + beat * BEAT_SEC) * SAMPLE_RATE)
            for i in range(pulse_length):
                t = i / SAMPLE_RATE
                index = start + i
                if index < len(pulse):
                    pulse[index] += (
                        math.sin(2 * math.pi * 420.0 * t)
                        * math.exp(-18 * t) * 0.055
                    )

    add_samples(mix, pulse)

    # Debugging Kitten percussion across the full six-bar arrangement.
    render_drums(mix, 0, 6)

    # Cosmic Pancreas delay and slow feedback shimmer.
    mix = apply_pancreas_delay(mix)

    # Peak-safe normalization; leave headroom.
    peak = max(abs(sample) for sample in mix) or 1.0
    scale = 0.88 / peak
    pcm = bytearray()

    for sample in mix:
        value = max(-1.0, min(1.0, sample * scale))
        pcm.extend(struct.pack("<h", int(value * 32767)))

    with wave.open(str(OUTPUT), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)

    print("=== CATHEDRALOS AUDIO FOUNDRY v6.2 ===")
    print("Status: ensemble prototype rendered")
    print(f"Output: {OUTPUT}")
    print(f"Tempo: {TEMPO} BPM")
    print(f"Tuning reference: A4 = {TUNING_A4} Hz")
    print("Independent pulse: 420 Hz")
    print("Rhythm grid: 3 / 6 / 9")
    print(f"Delay: {DELAY_MS} ms | feedback: {DELAY_FEEDBACK}")
    print(f"Seed: {SEED}")
    print(f"Music duration: {MUSIC_SEC:.3f} sec")
    print(f"Rendered duration: {len(mix) / SAMPLE_RATE:.3f} sec")
    print(f"Peak before normalization: {peak:.6f}")
    print(f"PCM: mono / 16-bit / {SAMPLE_RATE} Hz")


if __name__ == "__main__":
    main()
