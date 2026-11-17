# CathedralOS — Audio Foundry v6.1

Automation recommends. Human decides. Reality has the final vote.

Release reference: 32400a834866b0b5806a0ec8720641a26ab4db19

## Architecture

| Branch | Harmonic Center | Tuning | Sponsor |
|---|---|---|---|
| A | Bb | 432 / 420 Hz | Electric Chartreuse #DFFF00 |
| Bridge | F#7 | 432 Hz | Tritone Pivot |
| B | Dm9 -> G13 -> Cmaj9 | 432 Hz | Mystic Burgundy #4A0E2E |

## Synthesis Engine

- Tempo: 94 BPM
- Slapback delay: 159 ms
- Feedback: 0.38
- Rhythm: 3 / 6 / 9
- Glitch chirps: 369 Hz
- Random generator: random.Random(SEED)
- Configured seed: 369

## Dependencies

Python 3 standard library:
- wave
- math
- struct
- random

No third-party dependencies.

## Demo Audio

File: cathedralos_v6_1_demo.wav

- PCM WAV
- 44,100 Hz
- 16-bit
- Mono
- Duration: 10.213 seconds

## Reproduction

Run from the repository root:

    python3 audio_foundry/render.py

Output:

    audio_foundry/cathedralos_v6_1_demo.wav

Bit-for-bit reproducibility should be verified by comparing SHA-256 hashes from two separate renders.

## Release Integrity

Original release reference:
32400a834866b0b5806a0ec8720641a26ab4db19

Future changes should be committed separately.

Where ritual becomes architecture. Where code becomes meaning.

---

## Prototype Track — Audio Foundry v6.2 (Ensemble)

Status: Verified Prototype (Termux / Python 3.13.13)
Output Artifact: audio_foundry/cathedralos_v6_2_ensemble.wav
Artifact SHA-256: 5a72509e79740ee3af5313a97ce9f47826e6d6a989f0618442e275c50d182316

### DSP & Voice Implementation

- Channel layout & delay: Mono output routed through a 159 ms feedback delay (`0.38` feedback gain) with five appended delay repeats (`15.319s` musical body, `16.114s` rendered tail). No stereo spatialization or chorus DSP is implemented.
- Harmonic bed: Additive dual-partial sine oscillators (`432.0 Hz` tuning reference and `420 Hz` independent pulse) sequencing `Bb`, an `F#7` pivot, and `Dm9 -> G13 -> Cmaj9` at `94 BPM`.
- Lead brass voice: Additive oscillator (`1st–5th` harmonics with emphasized `3rd`/`4th` partials), `35 ms` exponential pitch-scoop envelope, and `5.5 Hz` delayed frequency vibrato.
- Bass voice: Fundamental sine oscillator paired with a `20 ms` pitch-drop transient and decaying `2nd`-harmonic overtone.
- Percussion grid: Deterministic PRNG (`random.Random(369)`) white-noise bursts and `369 Hz` stepped sine chirps arranged on a `3 / 6 / 9` rhythm grid.

### Verified Artifact Telemetry

- Format: PCM WAV (`44,100 Hz`, `16-bit` signed little-endian, Mono)
- Rendered duration: `16.114 seconds` (`1,421,312 bytes`)
- Peak before normalization: `0.530408`
- Normalized peak amplitude: `87.9971%` (`0` clipped samples)
- Reproducibility scope: Bit-identical SHA-256 verified across consecutive renders on `Python 3.13.13` in Termux; cross-environment floating-point parity pending.

### Prototype Reproduction

Run from the repository root:

    python3 audio_foundry/render_v6_2_ensemble.py

Verify checksum:

    sha256sum audio_foundry/cathedralos_v6_2_ensemble.wav
